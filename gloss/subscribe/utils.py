"""
Subscription Utilities
"""
import importlib

from gloss import settings
from gloss.subscribe import subscription
from gloss.utils import itersubclasses

IMPORTED_FROM_APPS = set()

def import_subscriptions():
    for module in settings.SUBSCRIPTIONS:
        importlib.import_module(module)
        global IMPORTED_FROM_APPS
        IMPORTED_FROM_APPS.add(module)
        return

def get_subscriptions():
    import_subscriptions()
    return itersubclasses(subscription.Subscription)
