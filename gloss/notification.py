"""
Notifying downstream of stuff what happened
"""
from gloss import subscribe

def get_subscription_classes(message_container):
    for subscription_class in subscribe.get_subscriptions():
        if subscription_class.cares_about(message_container):
            yield subscription_class()

def notify(message_container):
    for subscription in get_subscription_classes(message_container):
        print subscription
        subscription.notify(message_container)
