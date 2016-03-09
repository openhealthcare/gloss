from subscriptions import *
from utils import itersubclasses


def get_subscription(message_container):
    classes = itersubclasses(Subscription)
    for subscription_class in classes:
        if subscription_class.message_type == message_container.message_type:
            yield subscription_class()


def notify(message_container):
    subscriptions = get_subscription(message_container)
    for subscription in subscriptions:
        subscription.notify(message_container)
