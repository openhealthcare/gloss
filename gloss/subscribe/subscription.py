"""
Base classes for Gloss subscriptions
"""
from gloss.models import atomic_method, get_or_create_identifier

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
