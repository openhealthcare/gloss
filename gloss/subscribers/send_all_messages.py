from gloss.subscribers.base_subscriber import BaseSubscriber
from gloss.serialisers.opal import send_to_opal
from gloss.models import atomic_method


class SendAllMessages(BaseSubscriber):
    def __init__(self, *args, **kwargs):
        self.end_point = kwargs.pop("end_point")
        super(SendAllMessages, self).__init__(*args, **kwargs)

    @atomic_method
    def notify(self, message_container, gloss_service, session):
        send_to_opal(message_container, self.end_point)
