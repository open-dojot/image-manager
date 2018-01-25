"""
    Handles CRUD operations for firmware binary images
"""

import json
import logging
from time import time
from flask import request
from flask import make_response
from flask import redirect, url_for
from flask import Blueprint
from utils import *

from DatabaseModels import *
from SerializationModels import *
from TenancyManager import init_tenant_context

from app import app

import uuid
from threading import Timer

image = Blueprint('image', __name__)

LOGGER = logging.getLogger('image-manager.' + __name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)

# global_imageid = 20


UPLOAD_TIMEOUT = 5  # seconds


def confirm_image_uploaded(imageid):
    LOGGER.debug("Testing if image {} was uploaded".format(imageid))
    orm_image = assert_image_exists(str(imageid))
    data = image_schema.dump(orm_image).data
    if data['confirmed']:
        LOGGER.debug("Image {} was uploaded, metadata confirmed".format(imageid))
        return
    LOGGER.info("Image {} not uploaded, metadata discarded".format(imageid))
    db.session.delete(orm_image)
    db.session.commit()


@image.route('/image/<imageid>', methods=['GET'])
def get_image(imageid):
    try:
        init_tenant_context(request, db)
        orm_image = assert_image_exists(imageid)
        result = image_schema.dump(orm_image).data
        return make_response(json.dumps(result), 200)
    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/<imageid>', methods=['DELETE'])
def delete_image(imageid):
    try:
        init_tenant_context(request, db)
        orm_image = assert_image_exists(imageid)
        data = image_schema.dump(orm_image).data

        db.session.delete(orm_image)
        db.session.commit()

        result = json.dumps({'result': 'ok', 'removed_image': data})
        return make_response(result, 200)
    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/', methods=['POST'])
def create_image():
    # print(request.__dict__)
    """ Creates and configures the given image (in json) """
    try:
        tenant = init_tenant_context(request, db)
        image_data, json_payload = parse_json_payload(request, image_schema)
        # TODO Add a better id generation procedure
        # global global_imageid
        # imageid = global_imageid
        # global_imageid = global_imageid + 1
        imageid = str(uuid.uuid4())
        image_data['id'] = imageid

        orm_image = Image(**image_data)
        db.session.add(orm_image)

        try:
            db.session.commit()
        except IntegrityError as error:
            handle_consistency_exception(error)

        else:
            result = {'message': 'image created, awaiting upload',
                      'url': url_for('image.upload_image', imageid=imageid)}

        Timer(UPLOAD_TIMEOUT, confirm_image_uploaded, [imageid]).start()
        return make_response(json.dumps(result), 200)

    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/<imageid>', methods=['POST'])
def upload_image(imageid):
    try:
        tenant = init_tenant_context(request, db)
        orm_image = assert_image_exists(imageid)
        if orm_image.confirmed:
            raise HTTPRequestError(400, "Binary already exists")

        orm_image.confirmed = True
        file_data = parse_form_payload(request)

        try:
            pass
            db.session.commit()
        except IntegrityError as error:
            handle_consistency_exception(error)

        else:
            result = {'message': 'image updated', 'image': imageid}

        return make_response(json.dumps(result), 200)

    except HTTPRequestError as e:
        db.session.rollback()
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


app.register_blueprint(image)
