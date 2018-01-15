"""
    Defines common handler interface and implementations for images
"""

import json
import logging
import traceback
import requests

from utils import HTTPRequestError

from KafkaNotifier import send_notification, DeviceEvent

LOGGER = logging.getLogger('image-manager.' + __name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)


# TODO: this actually is a symptom of bad responsability management.
# All image bookkeeping should be performed on a single (perhaps this) service, with the
# services that implement specific features referring back to the single image management
# service for their transient data.
class BackendHandler(object):
    """
        Abstract class that represents an implementation backend on the internal middleware
        infrastructure.
    """

    def create(self, image):
        """
            Creates the given image on the implemented backend.
            :param image: Dictionary with the full image configuration
            :returns: True if operation succeeded
            :raises HTTPRequestError
        """
        raise NotImplementedError('Abstract method called')

    def remove(self, image_id):
        """
            Removes the image identified by the given id
            :param image_id: unique identifier of the image to be removed
            :raises HTTPRequestError
        """
        raise NotImplementedError('Abstract method called')

    def update(self, image):
        """
            Updates the given image on the implemented backend.
            :param image: Dictionary with the full image configuration. Must contain an 'id'
                           field with the unique identifier of the image to be updated. That
                           field must not be changed.
            :raises HTTPRequestError
        """
        raise NotImplementedError('Abstract method called')


# KafkaHandler is the preferred handler
class OrionHandler(BackendHandler):

    def __init__(self, service='devm', base_url='http://orion:1026/v2/entities'):
        self.baseUrl = base_url
        self.service = service
        self._noBodyHeaders = {
            'Fiware-service': service,
            'Fiware-servicePath': '/',
            'cache-control': 'no-cache'
        }
        self._headers = self._noBodyHeaders
        self._headers['Content-Type'] = 'application/json'

    @staticmethod
    def parse_image(image, generated_id=False):
        body = {}
        type_descr = "template"
        for dev_type in image['attrs'].keys():
            type_descr += "_" + str(dev_type)
        if generated_id:
            body = {
                "type": type_descr,
                "id": image['id']
            }
        for tpl in image['attrs']:
            for attr in image['attrs'][tpl]:
                body[attr['label']] = {"type": attr['value_type']}

        return body

    def create_update_image(self, image, is_update=True):
        target_url = "%s/%s/attrs?type=image" % (self.baseUrl, image['id'])
        body = json.dumps(OrionHandler.parse_image(image, not is_update))
        if not is_update:
            target_url = self.baseUrl

        try:
            LOGGER.info("about to create image in ctx broker")
            LOGGER.debug("%s", body)
            response = requests.post(target_url, headers=self._headers, data=body)
            if 200 <= response.status_code < 300:
                LOGGER.debug("Broker update successful")
            else:
                LOGGER.info("Failed to update ctx broker: %d", response.status_code)
                try:
                    LOGGER.debug("%s", response.json())
                except Exception as e:
                    LOGGER.error(e)
        except requests.ConnectionError:
            raise HTTPRequestError(500, "Broker is not reachable")

    def create(self, image):
        self.create_update_image(image, False)

    def remove(self, image_id):
        # removal is ignored, thus leaving removed image data lingering in the system
        # (this allows easier recovery/rollback of data by the user)
        pass

    def update(self, image):
        self.create_update_image(image)


class KafkaHandler:

    def __init__(self):
        pass

    def create(self, image, meta):
        """
            Publishes event to kafka broker, notifying image creation
        """
        send_notification(DeviceEvent.CREATE, image, meta)

    def remove(self, image_id, meta):
        """
            Publishes event to kafka broker, notifying image removal
        """
        send_notification(DeviceEvent.REMOVE, image_id, meta)

    def update(self, image, meta):
        """
            Publishes event to kafka broker, notifying image update
        """
        send_notification(DeviceEvent.UPDATE, image, meta)

    def configure(self, image, meta):
        """
            Publishes event to kafka broker, notifying image configuration
        """
        send_notification(DeviceEvent.CONFIGURE, image, meta)


# deprecated
class IotaHandler(BackendHandler):
    """ Abstracts interaction with iotagent-json for MQTT image management """
    # TODO: this should be configurable (via file or environment variable)
    def __init__(self, base_url='http://iotagent:4041/iot',
                 orion_url='http://orion:1026/v1/contextEntities',
                 service='devm'):
        self.baseUrl = base_url
        self.orionUrl = orion_url
        self.service = service
        self._headers = {
            'Fiware-service': service,
            'Fiware-servicePath': '/',
            'Content-Type': 'application/json',
            'cache-control': 'no-cache'
        }
        self._noBodyHeaders = {
            'Fiware-service': service,
            'Fiware-servicePath': '/',
            'cache-control': 'no-cache'
        }

    def __get_topic(self, image):

        if image.topic:
            topic = image.topic
        else:
            topic = "/%s/%s/attrs" % (self.service, image.image_id)

        return topic

    def __get_config(self, image):

        base_config = {
            # this is actually consumed by iotagent
            'image_id': image.image_id,
            # becomes entity type for context broker
            'entity_type': 'image',
            # becomes entity id for context broker
            'entity_name': image.image_id,
            'attributes': [],
            # this is actually consumed by iotagent
            'internal_attributes': {
                "attributes" : [],
                "timeout": {"periodicity": image.frequency, "waitMultiplier": 3}
            },
            'static_attributes': []
        }

        for attr in image.template.attrs:
            if attr.type == 'dynamic':
                base_config['attributes'].append({
                    'name': attr.label,
                    'type': attr.value_type
                })
            elif attr.type == 'static':
                base_config['static_attributes'].append({
                    'name': attr.label,
                    'type': attr.value_type,
                    'value': attr.static_value
                })
            elif (attr.type == 'meta') and (attr.label == 'mqtt_topic'):
                # @BUG however nice, this doesn't seem to work with iotagent-json
                base_config['internal_attributes']['attributes'].append({
                    {"topic": "tcp:mqtt:%s" % attr.static_value},
                })
        return base_config

    def create(self, image):
        """ Returns boolean indicating image creation success. """

        try:
            svc = json.dumps({
                "services": [{
                    "resource": "devm",
                    "apikey": self.service,
                    "entity_type": 'image'
                }]
            })
            response = requests.post(self.baseUrl + '/services', headers=self._headers, data=svc)
            if not (response.status_code == 409 or
                    (200 <= response.status_code < 300)):
                error = "Failed to configure ingestion subsystem: service creation failed"
                raise HTTPRequestError(500, error)
        except requests.ConnectionError:
            raise HTTPRequestError(500, "Cannot reach ingestion subsystem (service)")

        try:
            response = requests.post(self.baseUrl + '/images', headers=self._headers,
                                     data=json.dumps({'images':[self.__get_config(image)]}))
            if not (200 <= response.status_code < 300):
                error = "Failed to configure ingestion subsystem: image creation failed"
                raise HTTPRequestError(500, error)
        except requests.ConnectionError:
            raise HTTPRequestError(500, "Cannot reach ingestion subsystem (image)")

    def remove(self, imageid):
        """ Returns boolean indicating image removal success. """

        try:
            response = requests.delete(self.baseUrl + '/images/' + imageid,
                                       headers=self._noBodyHeaders)
            if 200 <= response.status_code < 300:
                response = requests.delete('%s/%s' % (self.orionUrl, imageid),
                                           headers=self._noBodyHeaders)
                if not (200 <= response.status_code < 300):
                    error = "Failed to configure ingestion subsystem: image removal failed"
                    raise HTTPRequestError(500, error)
        except requests.ConnectionError:
            raise HTTPRequestError(500, "Cannot reach ingestion subsystem")

    def update(self, image):
        """ Returns boolean indicating image update success. """

        self.remove(image.image_id)
        return self.create(image)


# Temporarily create a subscription to persist image data
# TODO this must be revisited in favor of a orchestrator-based solution
class PersistenceHandler(object):
    """
        Abstracts the configuration of subscriptions targeting the default
        history backend (STH)
    """
    # TODO: this should be configurable (via file or environment variable)
    def __init__(self, service='devm',
                 base_url='http://orion:1026/v1/contextSubscriptions',
                 target_url="http://sth:8666/notify"):
        self.baseUrl = base_url
        self.targetUrl = target_url
        self.service = service
        self._headers = {
            'Fiware-service': service,
            'Fiware-servicePath': '/',
            'Content-Type': 'application/json',
            'cache-control': 'no-cache'
        }
        self._noBodyHeaders = {
            'Fiware-service': service,
            'Fiware-servicePath': '/',
            'cache-control': 'no-cache'
        }

    def create(self, image_id, image_type='image'):
        """ Returns subscription id on success. """

        try:
            svc = json.dumps({
                "entities": [{
                    "type": image_type,
                    "isPattern": "false",
                    "id": image_id
                }],
                "reference" : self.targetUrl,
                "duration": "P10Y",
                "notifyConditions": [{"type": "ONCHANGE"}]
            })
            response = requests.post(self.baseUrl, headers=self._headers, data=svc)
            if not (response.status_code == 409 or
                    (200 <= response.status_code < 300)):
                raise HTTPRequestError(500, "Failed to create subscription")

            # return the newly created subs
            reply = response.json()
            return reply['subscribeResponse']['subscriptionId']
        except ValueError:
            LOGGER.error('Failed to create subscription')
            raise HTTPRequestError(500, "Failed to create subscription")
        except requests.ConnectionError:
            raise HTTPRequestError(500, "Broker is not reachable")

    def remove(self, subsId):
        """ Returns boolean indicating subscription removal success. """

        try:
            response = requests.delete(self.baseUrl + '/' + subsId, headers=self._noBodyHeaders)
            if not (200 <= response.status_code < 300):
                raise HTTPRequestError(500, "Failed to remove subscription")
        except requests.ConnectionError:
            raise HTTPRequestError(500, "Broker is not reachable")
