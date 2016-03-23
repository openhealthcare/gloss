import json
import datetime
import requests
from gloss import settings


class OpalJSONSerializer(json.JSONEncoder):
    """ Encodes a dictionary to json in the format that OPAL likes it
    """
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime(settings.DATETIME_FORMAT)
        elif isinstance(o, datetime.date):
            return datetime.datetime.combine(
                    o, datetime.datetime.min.time()
                ).strftime(settings.DATE_FORMAT)
        super(OpalJSONSerializer, self).default(o)


def send_to_opal(message_container, end_point):
    """ sends a message to an opal application
    """
    url = "{0}".format(end_point, message_container.hospital_number)
    as_dict = message_container.to_dict()
    requests.post(url, json=json.dumps(as_dict, cls=OpalJSONSerializer))
    return
