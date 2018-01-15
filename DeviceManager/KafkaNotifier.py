import logging
import json
from conf import CONFIG
from kafka import KafkaProducer
from kafka.errors import KafkaTimeoutError

LOGGER = logging.getLogger('image-manager.' + __name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)


class DeviceEvent:
    CREATE = "create"
    UPDATE = "update"
    REMOVE = "remove"
    CONFIGURE = "configure"


class NotificationMessage:
    event = ""
    data = None
    meta = None

    def __init__(self, ev, d, m):
        self.event = ev
        self.data = d
        self.meta = m

    def to_json(self):
        return {"event": self.event, "data": self.data, "meta": self.meta}


kafka_address = CONFIG.kafka_host + ':' + CONFIG.kafka_port
kf_prod = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'), bootstrap_servers=kafka_address)


def send_notification(event, image, meta):
    # TODO What if Kafka is not yet up?
    full_msg = NotificationMessage(event, image, meta)
    try:
        future = kf_prod.send('dojot.image-manager.image', full_msg.to_json())
        kf_prod.flush()
    except KafkaTimeoutError:
        LOGGER.error("Kafka timed out.")
