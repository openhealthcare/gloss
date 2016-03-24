"""
Base classes for Gloss subscriptions
"""
from gloss.models import (
    atomic_method, get_or_create_identifier, get_subscription_endpoint
)
from gloss.serialisers.opal import send_to_opal
from gloss import settings
from twisted.logger import Logger
from gloss.utils import AbstractClass


def db_message_processor(some_fun):
    def add_gloss_ref(self, message_container, session=None):
        gloss_ref = get_or_create_identifier(
            message_container.hospital_number,
            session,
            issuing_source=message_container.issuing_source
        )
        return some_fun(
            self,
            message_container,
            session=session,
            gloss_ref=gloss_ref,
        )
    return atomic_method(add_gloss_ref)


class Subscription(object):
    log = Logger(namespace="subscription")

    @classmethod
    def cares_about(cls, message_container):
        if message_container.message_type in cls.message_types:
            return True
        return False

    @property
    def issuing_source(self):
        raise NotImplementedError("you need to implement 'issuing source'")

    def serialise(self):
        raise NotImplementedError("you need to implement 'serialise'")

    def process_data(self):
        raise NotImplementedError("you need to implement 'post data'")

    def notify(self, message, *args, **kwargs):
        raise NotImplementedError("you need to implement 'post data'")

    def notify_async(self, message, *args, **kwargs):
        # implement if you want a function run asynchronously
        pass


class NotifyOpalWhenSubscribed(Subscription, AbstractClass):
    """ checks whether we're subscribed, sends a message to an opal
        application if so
    """
    @atomic_method
    def get_endpoint_if_it_exists(self, message_container, session=None):
        send_all_messages = getattr(settings, "SEND_ALL_MESSAGES", False)

        if send_all_messages:
            return send_all_messages

        result = get_subscription_endpoint(
            message_container.hospital_number, session
        )
        return result

    def notify_async(self, message_container):
        end_point = self.get_endpoint_if_it_exists(message_container)

        if end_point:
            self.log.info("posting {0} to {1}".format(
                message_container.message_type, end_point
            ))
            send_to_opal(message_container, end_point)
