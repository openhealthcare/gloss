from twisted.logger import Logger


class BaseSubscriber(object):
    log = Logger(namespace="subscription")

    def notify(self, msg, gloss_service):
        raise NotImplementedError("this needs to be implemented")
