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

So far an image stores only its metadata, follows a simple example of POST and GET

```bash
curl -X POST http://localhost:8000/image/ \
-H "Authorization: Bearer ${JWT}" \
-H 'Content-Type:application/json' \
-d ' {
  "label": "ExampleFW",
  "fw_version": "1.0.0-rc1",
  "hw_version": "1.0.0-revA",
  "sha1": "cf23df2207d99a74fbe169e3eba035e633b65d94"
}'
```
The answer is:

```json
{"message": "image updated", "image": "1"}
```


```bash
curl -X GET http://localhost:8000/image/1 -H "Authorization: Bearer ${JWT}" 
```
The answer is:

```json
{"message": "image updated", "image": "1"}
```