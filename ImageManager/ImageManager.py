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
from .utils import *

from .DatabaseModels import *
from .SerializationModels import *
from .TenancyManager import init_tenant_context

from .app import app

import uuid

image = Blueprint('image', __name__)

LOGGER = logging.getLogger('image-manager.' + __name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)


@image.route('/image/<imageid>', methods=['GET'])
def get_image(imageid):
    try:
        init_tenant_context(request, db)
        orm_image = assert_image_exists(imageid)
        result = image_schema.dump(orm_image)
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
        data = image_schema.dump(orm_image)

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
                      'uuid': imageid}

        return make_response(json.dumps(result), 200)

    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/<imageid>/binary', methods=['POST'])
def upload_image(imageid):
    try:
        tenant = init_tenant_context(request, db)
        orm_image = assert_image_exists(imageid)
        if orm_image.confirmed:
            raise HTTPRequestError(400, "Binary already exists")

        orm_image.confirmed = True
        file_data = parse_form_payload(request)

        try:
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
