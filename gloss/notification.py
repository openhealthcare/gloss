"""
Notifiying downstream systems of messages.
"""
import requests

from gloss import settings

def send_downstream(target, message):
    url, protocol = target
    if not hasattr(message, 'to_{0}'.format(protocol)):
        raise ValueError('{0} must have a to_{1} method'.format(message, protocol))
    serialised = getattr(message, 'to_{0}'.format(protocol))()
    requests.post(url, json=serialised)
    return

def notify(system, message):
    if system in settings.PASSTHROUGH_SUBSCRIPTIONS:
        for target in settings.PASSTHROUGH_SUBSCRIPTIONS[system]:
            send_downstream(target, message)
    return
