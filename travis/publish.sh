#!/bin/bash -ex

version="latest"
if [ ${TRAVIS_BRANCH} != "master" ] ; then
  version=${TRAVIS_BRANCH}
fi
tag="dojot/image-manager:${version}"

docker login -u="${DOCKER_USERNAME}" -p="${DOCKER_PASSWORD}"
docker tag local/imagemanager ${tag}
docker push ${tag}
