class GlossService(object):
    def __init__(self, receiver, importer, subscribers, issuing_source):
        self.receiver = receiver
        self.importer = importer
        self.subscribers = subscribers
        self.issuing_source = issuing_source

    def notify_subscribers(self, message_container):
        for subscriber in self.subscribers:
            subscriber(message_container, self)
