"""
    Handles CRUD operations for images, and their configuration on the
    FIWARE backend
"""

import json
import logging
from time import time
from flask import request
from flask import make_response
from flask import Blueprint
from utils import *
from BackendHandler import OrionHandler, KafkaHandler
from sqlalchemy.exc import IntegrityError

from DatabaseModels import *
from SerializationModels import *
from TenancyManager import init_tenant_context

from app import app

image = Blueprint('image', __name__)

LOGGER = logging.getLogger('image-manager.' + __name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.INFO)


def serialize_full_image(orm_image):
    data = image_schema.dump(orm_image).data
    data['attrs'] = {}
    for template in orm_image.templates:
        data['attrs'][template.id] = attr_list_schema.dump(template.attrs).data
    return data


def auto_create_template(json_payload, new_image):
    if ('attrs' in json_payload) and (new_image.templates is None):
        image_template = DeviceTemplate(label="image.%s template" % new_image.id)
        db.session.add(image_template)
        new_image.templates = [image_template]
        load_attrs(json_payload['attrs'], image_template, DeviceAttr, db)


def parse_template_list(template_list, new_image):
    new_image.templates = []
    for templateid in template_list:
        new_image.templates.append(assert_template_exists(templateid))


def generate_image_id():
    # TODO this is awful, makes me sad, but for now also makes demoing easier
    # We might want to look into an auto-configuration feature for images, such that ids are
    # not input manually on images
    _attempts = 0
    generated_id = ''
    while _attempts < 10 and len(generated_id) == 0:
        _attempts += 1
        new_id = create_id()
        if Device.query.filter_by(id=new_id).first() is None:
            return new_id

    raise HTTPRequestError(500, "Failed to generate unique image_id")


@image.route('/image', methods=['GET'])
def get_images():
    """
        Fetches known images, potentially limited by a given value.
        Ordering might be user-configurable too.
    """
    try:
        init_tenant_context(request, db)

        page_number, per_page = get_pagination(request)
        page = Device.query.paginate(page=page_number, per_page=per_page, error_out=False)
        images = []
        for d in page.items:
            images.append(serialize_full_image(d))

        result = json.dumps({
            'pagination': {
                'page': page.page,
                'total': page.pages,
                'has_next': page.has_next,
                'next_page': page.next_num
            },
            'images': images
        })
        return make_response(result, 200)
    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image', methods=['POST'])
def create_image():
    """ Creates and configures the given image (in json) """
    try:
        tenant = init_tenant_context(request, db)
        try:
            count = int(request.args.get('count', '1'))
            clength = len(str(count))
            verbose = request.args.get('verbose', 'false') in ['true', '1', 'True']
            if verbose and count != 1:
                raise HTTPRequestError(400, "Verbose can only be used for single image creation")
        except ValueError as e:
            LOGGER.error(e)
            raise HTTPRequestError(400, "If provided, count must be integer")

        images = []
        for i in range(0, count):
            image_data, json_payload = parse_payload(request, image_schema)
            image_data['id'] = generate_image_id()
            image_data['label'] = image_data['label'] + "_%0*d" % (clength, i)
            image_data.pop('templates', None)  # handled separately by parse_template_list
            orm_image = Device(**image_data)
            parse_template_list(json_payload.get('templates', []), orm_image)
            auto_create_template(json_payload, orm_image)
            db.session.add(orm_image)

            images.append({'id': image_data['id'], 'label': image_data['label']})

            full_image = serialize_full_image(orm_image)

            # TODO remove this in favor of kafka as data broker....
            ctx_broker_handler = OrionHandler(service=tenant)
            ctx_broker_handler.create(full_image)

            kafka_handler = KafkaHandler()
            kafka_handler.create(full_image, meta={"service": tenant})

        try:
            db.session.commit()
        except IntegrityError as error:
            handle_consistency_exception(error)

        if verbose:
            result = json.dumps({
                'message': 'image created',
                'image': full_image
            })
        else:
            result = json.dumps({
                'message': 'images created',
                'images': images
            })

        # TODO revisit iotagent notification procedure
        # protocol_handler = IotaHandler(service=tenant)
        # image_type = "virtual"
        # if orm_image.protocol != "virtual":
        #     image_type = "image"
        #     protocol_handler.create(orm_image)
        # TODO revisit history management
        # subscription_handler = PersistenceHandler(service=tenant)
        # orm_image.persistence = subscription_handler.create(orm_image.image_id, "image")

        return make_response(result, 200)

    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/<imageid>', methods=['GET'])
def get_image(imageid):
    try:
        init_tenant_context(request, db)
        orm_image = assert_image_exists(imageid)
        return make_response(json.dumps(serialize_full_image(orm_image)), 200)
    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/<imageid>', methods=['DELETE'])
def remove_image(imageid):
    try:
        init_tenant_context(request, db)
        orm_image = assert_image_exists(imageid)
        data = serialize_full_image(orm_image)
        db.session.delete(orm_image)
        db.session.commit()

        results = json.dumps({'result': 'ok', 'removed_image': data})
        return make_response(results, 200)
    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/<imageid>', methods=['PUT'])
def update_image(imageid):
    try:
        tenant = init_tenant_context(request, db)
        old_image = assert_image_exists(imageid)

        image_data, json_payload = parse_payload(request, image_schema)
        image_data.pop('templates')
        updated_image = Device(**image_data)
        parse_template_list(json_payload.get('templates', []), updated_image)
        updated_image.id = imageid

        # update sanity check
        if 'attrs' in json_payload:
            error = "Attributes cannot be updated inline. Update the associated template instead."
            return format_response(400, error)

        # TODO revisit iotagent notification mechanism
        # protocolHandler = IotaHandler(service=tenant)
        # image_type = 'virtual'
        # old_type = old_image.protocol
        # new_type = updated_image.protocol
        # if (old_type != 'virtual') and (new_type != 'virtual'):
        #     image_type = 'image'
        #     protocolHandler.update(updated_image)
        # if old_type != new_type:
        #     if old_type == 'virtual':
        #         image_type = 'image'
        #         protocolHandler.create(updated_image)
        #     elif new_type == 'virtual':
        #         protocolHandler.remove(updated_image.id)

        # TODO revisit image data persistence
        # subsHandler = PersistenceHandler(service=tenant)
        # subsHandler.remove(old_image.persistence)
        # updated_image.persistence = subsHandler.create(imageid, image_type)

        # TODO remove this in favor of kafka as data broker....
        ctx_broker_handler = OrionHandler(service=tenant)
        ctx_broker_handler.update(serialize_full_image(old_image))

        db.session.delete(old_image)
        db.session.add(updated_image)

        try:
            db.session.commit()
        except IntegrityError as error:
            handle_consistency_exception(error)

        result = {'message': 'image updated', 'image': serialize_full_image(updated_image)}
        return make_response(json.dumps(result))

    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/<imageid>/attrs', methods=['PUT'])
def configure_image(imageid):
    try:
        tenant = init_tenant_context(request, db)
        # In fact, the actual image is not needed. We must be sure that it exists.
        assert_image_exists(imageid)
        json_payload = json.loads(request.data)
        kafka_handler = KafkaHandler()
        # Remove topic metadata from JSON to be sent to the image
        # Should this be moved to a HTTP header?
        topic = json_payload["topic"]
        del json_payload["topic"]

        kafka_handler.configure(json_payload, meta = { "service" : tenant, "id" : imageid, "topic": topic})

        result = {'message': 'configuration sent'}
        return make_response(result, 200)

    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


# Convenience template ops
@image.route('/image/<imageid>/template/<templateid>', methods=['POST'])
def add_template_to_image(imageid, templateid):
    """ associates given template with image """

    try:
        tenant = init_tenant_context(request, db)
        orm_image = assert_image_exists(imageid)
        orm_template = assert_template_exists(templateid)

        orm_image.templates.append(orm_template)

        try:
            db.session.commit()
        except IntegrityError as error:
            handle_consistency_exception(error)

        result = {'message': 'image updated', 'image': serialize_full_image(orm_image)}
        return make_response(json.dumps(result))
    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/<imageid>/template/<templateid>', methods=['DELETE'])
def remove_template_from_image(imageid, templateid):
    """ removes given template from image """
    try:
        tenant = init_tenant_context(request, db)
        image = assert_image_exists(imageid)
        relation = assert_image_relation_exists(imageid, templateid)

        # Here (for now) there are no more validations to perform, as template removal
        # cannot violate attribute constraints

        db.session.remove(relation)
        db.session.commit()
        result = {'message': 'image updated', 'image': serialize_full_image(image)}
        return make_response(json.dumps(result))
    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/template/<templateid>', methods=['GET'])
def get_by_template(templateid):
    try:
        init_tenant_context(request, db)

        page_number, per_page = get_pagination(request)
        page = (
            db.session.query(Device)
            .join(DeviceTemplateMap)
            .filter_by(template_id=templateid)
            .paginate(page=page_number, per_page=per_page, error_out=False)
        )
        images = []
        for d in page.items:
            images.append(serialize_full_image(d))

        result = json.dumps({
            'pagination': {
                'page': page.page,
                'total': page.pages,
                'has_next': page.has_next,
                'next_page': page.next_num
            },
            'images': images
        })
        return make_response(result, 200)
    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


app.register_blueprint(image)
