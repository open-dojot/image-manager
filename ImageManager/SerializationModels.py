# object to json sweetness
import json
from marshmallow import Schema, fields, post_dump
from utils import HTTPRequestError


class ImageSchema(Schema):
    id = fields.String(dump_only=True)
    label = fields.Str(required=True)
    created = fields.DateTime(dump_only=True)
    updated = fields.DateTime(dump_only=True)

    fw_version = fields.String(required=True)
    hw_version = fields.String(required=True)
    sha1 = fields.String(required=True)

    @post_dump
    def remove_null_values(self, data):
        return {key: value for key, value in data.items() if value is not None}


image_schema = ImageSchema()


def parse_payload(request, schema):
    try:
        content_type = request.headers.get('Content-Type')
        if (content_type is None) or (content_type != "application/json"):
            raise HTTPRequestError(400, "Payload must be valid JSON, and Content-Type set accordingly")
        json_payload = json.loads(request.data)
    except ValueError:
        raise HTTPRequestError(400, "Payload must be valid JSON, and Content-Type set accordingly")

    data, errors = schema.load(json_payload)
    if errors:
        results = {'message': 'failed to parse input', 'errors': errors}
        raise HTTPRequestError(400, results)
    return data, json_payload
