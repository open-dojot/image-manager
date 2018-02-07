import requests
import json
import urllib.parse
import jwt
import time
import binascii
import os
import datetime
import hashlib

EXAMPLE_FILE = 'example.hex'
CORRUPTED_EXAMPLE_FILE = 'corrupted_example.hex'

sha1 = hashlib.sha1()
# Calculate sha1 for our example file
with open(EXAMPLE_FILE, 'rb') as f:
    data = f.read()
    sha1.update(data)

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')

service = 'test' + st + "t"  # This ensures an isolated tenant each time this test suite is run
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
    "sha1": sha1.hexdigest()
}
headers = {'Authorization': 'Bearer ' + jwt_token}
r = requests.post(base_url, json=payload, headers=headers)
assert r.status_code == requests.codes.ok
print(r.text)

# Get url
image_id = json.loads(r.text)['uuid']
image_url = urllib.parse.urljoin(base_url, image_id)
binary_url = urllib.parse.urljoin(image_url + "/", "binary")
print(image_url)
print(binary_url)

# Upload Corrupted File
headers = {'Authorization': 'Bearer ' + jwt_token}
files = {'image': open(CORRUPTED_EXAMPLE_FILE, 'rb')}
r = requests.post(binary_url, files=files, headers=headers)
assert r.status_code == requests.codes.bad_request
print(r.text)

# Upload File
headers = {'Authorization': 'Bearer ' + jwt_token}
files = {'image': open(EXAMPLE_FILE, 'rb')}
r = requests.post(binary_url, files=files, headers=headers)
assert r.status_code == requests.codes.ok
print(r.text)

# Upload File Again to see the error
headers = {'Authorization': 'Bearer ' + jwt_token}
files = {'image': open(EXAMPLE_FILE, 'rb')}
r = requests.post(binary_url, files=files, headers=headers)
assert r.status_code == requests.codes.bad_request
print(r.text)

# Get the metadata
r = requests.get(image_url, headers=headers)
assert r.status_code == requests.codes.ok
print(r.text)

# Get the file content
r = requests.get(binary_url, headers=headers)
assert r.status_code == requests.codes.ok
print(r.text)
