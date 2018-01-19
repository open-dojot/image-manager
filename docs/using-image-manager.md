# Using ImageManager

All examples in this page consider that all dojot's components are up and running (check [the documentation](http://dojotdocs.readthedocs.io/) for how to do that). All request will include a ```${JWT}``` variable - this was retrieved from [auth](https://github.com/dojot/auth) component.

## Creating templates and images

Right off the bat, let's retrieve a token from `auth`:

```bash
curl -X POST http://localhost:8000/auth \
-H 'Content-Type:application/json' \
-d '{"username": "admin", "passwd" : "admin"}'
```

```json
{
  "jwt": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIU..."
}
```

This token will be stored in ```bash ${JWT}``` bash variable, referenced in all requests.

*IMPORTANT*: Every request made with this token will be valid only for the tenant (user "service") associated with this token. For instance, listing created images will return only those images which were created using this tenant.

-------------

This is a simple example featuring all 4 available methods POST/PUT/GET/DELETE.
So far only the image's metadata is stored and the file itself is discarded

-------------

Create a simple application

```bash
echo "0123456789" > example.hex
```

POST your example

```bash
curl -X POST \
-F 'image=@./example.hex' \
-F 'data={
  "label": "ExampleFW",
  "fw_version": "1.0.0-rc1",
  "hw_version": "1.0.0-revA",
  "sha1": "cf23df2207d99a74fbe169e3eba035e633b65d94"
}' \
-H "Authorization: Bearer ${JWT}" \
http://localhost:8000/image/
```
The answer is:
```json
{"message": "image created", "image": "21"}
```
You can also update your image using PUT

```bash
curl -X PUT \
-F 'image=@./example.hex' \
-F 'data={
  "label": "ExampleFW",
  "fw_version": "1.0.0-rc1",
  "hw_version": "1.0.0-revA",
  "sha1": "cf23df2207d99a74fbe169e3eba035e633b65d94"
}' \
-H "Authorization: Bearer ${JWT}" \
http://localhost:8000/image/21

```
and get:
```json
{"message": "image updated", "image": "21"}
```

You can retrieve the image contents with GET
```bash
curl -X GET http://localhost:8000/image/21 -H "Authorization: Bearer ${JWT}" 
```
The answer is:
```json
{
  "updated": "2018-01-19T21:35:12.822211+00:00",
  "sha1": "cf23df2207d99a74fbe169e3eba035e633b65d94",
  "hw_version": "1.0.0-revA",
  "created": "2018-01-19T21:10:36.386000+00:00",
  "fw_version": "1.0.0-rc1",
  "label": "ExampleFW", 
  "id": "21"
}
```

And finally, you can delete your image
```bash
curl -X DELETE http://localhost:8000/image/21 -H "Authorization: Bearer ${JWT}" 
```
```json
{
  "result": "ok", 
  "removed_image": {
    "updated": "2018-01-19T21:35:12.822211+00:00",
    "sha1": "cf23df2207d99a74fbe169e3eba035e633b65d94",
    "hw_version": "1.0.0-revA",
    "created": "2018-01-19T21:10:36.386000+00:00",
    "fw_version": "1.0.0-rc1",
    "label": "ExampleFW",
    "id": "21"
   }
}
```