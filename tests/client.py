import requests
import json
import urllib.parse

# Get auth
payload = {"username": "admin", "passwd": "admin"}
url = 'http://localhost:8000/auth'
r = requests.post(url, json=payload)
jwt = json.loads(r.text)['jwt']

# Post metadata
base_url = 'http://localhost:8000/image/'
payload = {
    "label": "ExampleFW",
    "fw_version": "1.0.0-rc1",
    "hw_version": "1.0.0-revA",
    "sha1": "cf23df2207d99a74fbe169e3eba035e633b65d94"
}
headers = {'Authorization': 'Bearer ' + jwt}
r = requests.post(base_url, json=payload, headers=headers)
print(r.text)

# Get url
image_url = json.loads(r.text)['url']
url = urllib.parse.urljoin(base_url, image_url)

# Upload File
headers = {'Authorization': 'Bearer ' + jwt}
files = {'image': open('example.hex', 'rb')}
r = requests.post(url, files=files, headers=headers)
print(r.text)
