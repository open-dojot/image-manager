import dredd_hooks as hooks
import jwt
import time
import datetime

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')

service = 'test' + st + "t"  # This ensures an isolated tenant each time this test suite is run
encode_data = {'userid': 1, 'name': 'Admin (superuser)', 'groups': [1], 'iat': 1517339633, 'exp': 1517340053,
               'email': 'admin@noemail.com', 'profile': 'admin', 'iss': 'eGfIBvOLxz5aQxA92lFk5OExZmBMZDDh',
               'service': service, 'jti': '7e3086317df2c299cef280932da856e5', 'username': 'admin'}

encoded = jwt.encode(encode_data, 'secret', algorithm='HS256')
jwt_token = str(encoded, 'ascii')


@hooks.before_all
def my_before_all_hook(transactions):
    print('before all')


# @hooks.before_each
# def add_api_key(transaction):
#     # add query parameter to each transaction here
#     auth = 'Bearer ' + jwt_token
#     if 'Authorization' in transaction['request']['headers']:
#         transaction['request']['headers']['Authorization'] = auth


@hooks.before
def my_before_hook(transaction):
    print('before')


@hooks.before_each_validation
def my_before_each_validation_hook(transaction):
    print('before_each')


@hooks.before_validation
def my_before_validation_hook(transaction):
    print('before validations')


@hooks.after
def my_after_hook(transaction):
    print('after')


@hooks.after_each
def my_after_each(transaction):
    print('after_each')


@hooks.after_all
def my_after_all_hook(transactions):
    print('after_all')
