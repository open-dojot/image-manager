import requests
import json
import urllib.parse
import jwt
import time
import binascii
import os
import datetime

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')

service = 'test' + st + '_t'  # This ensures an isolated tenant each time this test suite is run
encode_data = {'userid': 1, 'name': 'Admin (superuser)', 'groups': [1], 'iat': 1517339633, 'exp': 1517340053,
               'email': 'admin@noemail.com', 'profile': 'admin', 'iss': 'eGfIBvOLxz5aQxA92lFk5OExZmBMZDDh',
               'service': service, 'jti': '7e3086317df2c299cef280932da856e5', 'username': 'admin'}

encoded = jwt.encode(encode_data, 'secret', algorithm='HS256')
jwt_token = str(encoded, 'ascii')

# Post metadata
base_url = 'http://localhost:8000/image/'
payload = {
    "label": "ExampleFW",
    "fw_version": "1.0.0-rc1",
    "hw_version": "1.0.0-revA",
    "sha1": "cf23df2207d99a74fbe169e3eba035e633b65d94"
}
headers = {'Authorization': 'Bearer ' + jwt_token}
r = requests.post(base_url, json=payload, headers=headers)
print(r.text)

# Get url
image_id = json.loads(r.text)['uuid']
binary_url = image_id + "/binary"
url = urllib.parse.urljoin(base_url, binary_url)
print(url)

# Upload File
headers = {'Authorization': 'Bearer ' + jwt_token}
files = {'image': open('example.hex', 'rb')}
r = requests.post(url, files=files, headers=headers)
print(r.text)
