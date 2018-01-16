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
from TenancyManager import init_tenant_context

from app import app

image = Blueprint('image', __name__)

LOGGER = logging.getLogger('image-manager.' + __name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.INFO)

@image.route('/image/<imageid>', methods=['GET'])
def get_image(imageid):
    try:
        print(request)
        init_tenant_context(request, db)
        orm_image = assert_image_exists(imageid)
        return make_response(json.dumps(serialize_full_image(orm_image)), 200)
    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)

@image.route('/image/<imageid>', methods=['POST'])
def update_image(imageid):
    try:
        print(request)
        result = {'message': 'image updated', 'image': imageid}
        return make_response(json.dumps(result))

    except HTTPRequestError as e:
        if isinstance(e.message, dict):
            return make_response(json.dumps(e.message), e.error_code)
        else:
            return format_response(e.error_code, e.message)

app.register_blueprint(image)
