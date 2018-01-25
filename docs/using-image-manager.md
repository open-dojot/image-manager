# Using ImageManager

All examples in this page consider that all dojot's components are up and running (check [the documentation](http://dojotdocs.readthedocs.io/) for how to do that). All request will include a ```${JWT}``` variable - this was retrieved from [auth](https://github.com/dojot/auth) component.

------------

Since the upload process involves timeouts, testing it by hand may prove cumbersome.
Check out test/client.py for programatic examples of the API