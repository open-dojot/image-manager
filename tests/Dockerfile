FROM local/imagemanager:latest
WORKDIR /usr/src/app
ADD . /usr/src/app

# install npm
RUN apk update && apk add nodejs npm --no-cache

# install dredd
RUN npm install --unsafe-perm -g dredd

RUN pip install -r requirements/test_requirements.txt

CMD ["dredd", "docs/api.apib", "http://image-manager:5000", "--language=python", "--hookfiles=tests/*_hooks.py"]