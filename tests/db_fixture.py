from ImageManager.DatabaseModels import *
from ImageManager.SerializationModels import *
from ImageManager.TenancyManager import init_tenant

# initialize DB
tenant = 'admin'
db.session.execute("drop schema IF EXISTS {} cascade".format(tenant))
db.session.commit()

if minioClient.bucket_exists(tenant):
    objects = minioClient.list_objects(tenant)
    for obj in objects:
        minioClient.remove_object(tenant, obj.object_name)
    minioClient.remove_bucket(tenant)

init_tenant(tenant, db, minioClient)

# Object Template
payload = {
    "label": "ExampleFW",
    "fw_version": "1.0.0-rc1",
    "hw_version": "1.0.0-revA",
    "sha1": "87acec17cd9dcd20a716cc2cf67417b71c8a7016",
    "confirmed": False
}

# Store First object
id = "b60aa5e9-cbe6-4b51-b76c-08cf8273db07"
data = image_schema.load(payload)
data['id'] = id
data['confirmed'] = True
minioClient.fput_object(tenant, id + '.hex', './example.hex')
orm_image = Image(**data)
db.session.add(orm_image)
db.session.commit()

# Store Second object
id = "51b39543-9de1-4751-9fe2-48c8d6038ba1"
data = image_schema.load(payload)
data['id'] = id
orm_image = Image(**data)
db.session.add(orm_image)
db.session.commit()
