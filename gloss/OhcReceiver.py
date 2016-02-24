import logging

from txHL7.receiver import AbstractHL7Receiver
from twisted.internet import defer

from process_message import MessageProcessor


class OhcReceiver(AbstractHL7Receiver):
    def handleMessage(self, container):
        message = container.message
        logging.info(message)
        message_processor = MessageProcessor()
        message_processor.process_message(message)

        # We succeeded, so ACK back (default is AA)
        return defer.succeed(container.ack())

    def getCodec(self):
        # Our messages are encoded in Windows-1252
        # WARNING this is an example and is not universally true! You will
        # need to figure out the encoding you are receiving.
        return 'cp1252'
