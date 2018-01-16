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

from DatabaseModels import *
from SerializationModels import *
from TenancyManager import init_tenant_context

from app import app

image = Blueprint('image', __name__)

LOGGER = logging.getLogger('image-manager.' + __name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.INFO)

global_imageid = 20


@image.route('/image/<imageid>', methods=['GET'])
def get_image(imageid):
    try:
        print(request)
        init_tenant_context(request, db)
        orm_image = assert_image_exists(imageid)
        result = {
            "label": orm_image.label,
            "fw_version": orm_image.fw_version,
            "hw_version": orm_image.hw_version,
            "sha1": orm_image.sha1
        }
        return make_response(json.dumps(result), 200)
    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


@image.route('/image/', methods=['POST'])
def create_image():
    """ Creates and configures the given image (in json) """
    try:
        tenant = init_tenant_context(request, db)
        image_data, json_payload = parse_payload(request, image_schema)
        # imageid = generate_image_id()
        global global_imageid
        imageid = str(global_imageid)
        global_imageid = global_imageid + 1
        image_data['id'] = imageid

        orm_image = Image(**image_data)
        db.session.add(orm_image)

        # # TODO remove this in favor of kafka as data broker....
        # ctx_broker_handler = OrionHandler(service=tenant)
        # ctx_broker_handler.create(full_image)
        #
        # kafka_handler = KafkaHandler()
        # kafka_handler.create(full_image, meta={"service": tenant})

        try:
            db.session.commit()
        except IntegrityError as error:
            handle_consistency_exception(error)

        else:
            result = {'message': 'image updated', 'image': imageid}

        print("Operation Successful - result: {}".format(result))
        return make_response(json.dumps(result), 200)

    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)


app.register_blueprint(image)
