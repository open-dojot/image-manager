FROM local/imagemanager:latest
WORKDIR /usr/src/app
ADD . /usr/src/app

# install npm
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash - && apt-get install -yq nodejs build-essential

# fix npm - not the latest version installed by apt-get
RUN npm install -g npm

# install dredd
RUN npm install --unsafe-perm -g dredd

RUN pip install -r requirements/test_requirements.txt

CMD ["dredd", "docs/api.apib", "http://image-manager:5000", "--language=python", "--hookfiles=tests/*_hooks.py"]