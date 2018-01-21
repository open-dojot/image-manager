from app import app

# initialize modules
import ImageManager
import ErrorManager

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
