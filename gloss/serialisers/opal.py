import json
import datetime
from twisted.python import log
import requests
from gloss import settings


class OpalJSONSerializer(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime(settings.DATETIME_FORMAT)
        elif isinstance(o, datetime.date):
            return datetime.datetime.combine(
                    o, datetime.datetime.min.time()
                ).strftime(settings.DATE_FORMAT)
        super(OpalJSONSerializer, self).default(o)


class OpalSerialiser(object):
    def send_to_opal(self, message_container):
        subs = settings.PASSTHROUGH_SUBSCRIPTIONS
        url = subs.get(message_container.issuing_source, None)

        if not url:
            raise ValueError('no url for issuing source {}'.format(
                message_container.issuing_source
            ))
        log.msg('Sending Downstream message to {0}'.format(url))

        as_dict = message_container.to_dict()
        requests.post(url, json=json.dumps(as_dict, cls=OpalJSONSerializer))
        return
