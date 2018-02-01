"""
    Handles CRUD operations for firmware binary images
"""

import json
import logging
import os
from time import time
from flask import request
from flask import make_response
from flask import redirect, url_for
from flask import send_from_directory
from flask import Blueprint
from werkzeug.utils import secure_filename
from minio.error import ResponseError

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


@image.route('/image/', methods=['GET'])
def get_all():
    try:
        init_tenant_context(request, db, minioClient)
        images = get_all_images()
        json_images = [image_schema.dump(i).data for i in images]
        return make_response(json.dumps(json_images), 200)
    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/<imageid>', methods=['GET'])
def get_image(imageid):
    try:
        init_tenant_context(request, db, minioClient)
        orm_image = assert_image_exists(imageid)
        result = image_schema.dump(orm_image).data
        return make_response(json.dumps(result), 200)
    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/<imageid>/binary', methods=['GET'])
def get_image_binary(imageid):
    try:
        init_tenant_context(request, db, minioClient)
        orm_image = assert_image_exists(imageid)
        filename = imageid + '.hex'
        return send_from_directory(directory='/tmp/', filename=filename)

    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/<imageid>', methods=['DELETE'])
def delete_image(imageid):
    try:
        init_tenant_context(request, db, minioClient)
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
        tenant = init_tenant_context(request, db, minioClient)
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
        tenant = init_tenant_context(request, db, minioClient)
        orm_image = assert_image_exists(imageid)
        if orm_image.confirmed:
            raise HTTPRequestError(400, "Binary already exists")

        orm_image.confirmed = True
        file_data = parse_form_payload(request)
        extension = file_data.filename.rsplit('.', 1)[1].lower()
        filename = imageid + '.' + extension
        file_data.save(os.path.join('/tmp/', filename))
        try:
            minioClient.fput_object(tenant, filename, os.path.join('/tmp/', filename))
            orm_image.confirmed = True
            db.session.commit()
        except ResponseError as err:
            print(err)
        except IntegrityError as error:
            handle_consistency_exception(error)

        else:
            result = {'message': 'image uploaded', 'image': imageid}

        return make_response(json.dumps(result), 200)

    except HTTPRequestError as e:
        db.session.rollback()
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


app.register_blueprint(image)
