from twisted.logger import Logger
from gloss.models import session_scope, Error


class AbstractImporter(object):
    """ for the moment this translates to the message container
        for for the subscriber, we'll remove this later and just
        send an list of messages
    """
    log = Logger(namespace="importer")

    def import_message(self, msg, gloss_service):
        raise NotImplementedError("This Must be implemented")

    def import_and_notify(self, msg, gloss_service):
        message_container = self.import_message(msg, gloss_service)

        if len(message_container.messages):
            gloss_service.notify_subscribers(message_container)


class SafelImporter(AbstractImporter):
    """ this catches all messages we can't process and
        saves them to the database with an explanation
        for now we'll translate these into a message
        container, we'll look at removing the message
        container later
    """
    def import_and_notify(self, msg, gloss_service):
        try:
            super(SafelImporter, self).import_and_notify(msg, gloss_service)
        except Exception as e:
            self.log.error("failed to parse")
            self.log.error(str(msg).replace("\r", "\n"))
            self.log.error("with %s" % e)
            try:
                with session_scope() as session:
                    err = Error(
                        error=str(e),
                        message=str(msg)
                    )
                    session.add(err)
            except Exception as e:
                self.log.error("failed to save error to database")
                self.log.error("with %s" % e)
            raise
