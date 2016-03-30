import json
import datetime
import requests
from gloss import settings
from twisted.logger import Logger


class OpalJSONSerialiser(json.JSONEncoder):
    """ Encodes a dictionary to json in the format that OPAL likes it
    """
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime(settings.DATETIME_FORMAT)
        elif isinstance(o, datetime.date):
            return datetime.datetime.combine(
                    o, datetime.datetime.min.time()
                ).strftime(settings.DATE_FORMAT)
        super(OpalJSONSerialiser, self).default(o)


def send_to_opal(message_container, end_point):
    """ sends a message to an opal application
    """
    as_dict = message_container.to_dict()
    response = requests.post(
        end_point, json=json.dumps(as_dict, cls=OpalJSONSerialiser)
    )

    if response.status_code > 300:
        log = Logger(namespace="to_opal")
        log.error(
            "failed to send to elcid with {}".format(response.status_code)
        )

    return
