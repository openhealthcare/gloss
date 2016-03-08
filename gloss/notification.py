from subscriptions import *
from utils import itersubclasses


def get_subscription(messages):
    classes = itersubclasses(Subscription)
    for subscription_class in classes:
        if subscription_class.message_type == messages[0].__class__:
            yield subscription_class()


def notify(messages):
    subscriptions = get_subscription(messages)
    for subscription in subscriptions:
        subscription.notify(messages)
