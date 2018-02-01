from .app import app

# initialize modules
from . import ImageManager
from . import ErrorManager

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
