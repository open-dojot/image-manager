# Using ImageManager

Using ImageManager is indeed simple: create a template with attributes and then create images using that template. That's it.
This page will show how to do that.

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

A template is, simply put, a model from which images can be created. They can be merged to build a single image (or a set of images). It is created by sending a HTTP request to ImageManager:

```bash
curl -X POST http://localhost:8000/template \
-H "Authorization: Bearer ${JWT}" \
-H 'Content-Type:application/json' \
-d ' {
  "label": "SuperTemplate",
  "attrs": [
    {
      "label": "temperature",
      "type": "dynamic",
      "value_type": "float"
    },
    {
      "label": "pressure",
      "type": "dynamic",
      "value_type": "float"
    },
    {
      "label": "model",
      "type": "static",
      "value_type" : "string",
      "static_value" : "SuperTemplate Rev01"
    }
  ]
}'
```

-H "Authorization: Bearer ${JWT}" \
-H 'Content-Type:application/json' \
-d ' {
  "label": "ExtraTemplate",
  "attrs": [
    {
      "label": "gps",
      "type": "dynamic",
      "value_type": "geo"
    }
  ]
}'

```

Which results in:

```json
{
  "result": "ok",
  "template": {
    "created": "2018-01-05T15:47:02.993965+00:00",
    "attrs": [
      {
        "template_id": "2",
        "created": "2018-01-05T15:47:02.995541+00:00",
        "label": "gps",
        "value_type": "geo",
        "type": "dynamic",
        "id": 4
      }
    ],
    "id": 2,
    "label": "ExtraTemplate"
  }
}
```
