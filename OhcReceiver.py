from txHL7.receiver import AbstractHL7Receiver
from twisted.internet import defer
import logging


class OhcReceiver(AbstractHL7Receiver):
    def handleMessage(self, container):
        message = container.message
        logging.info(message)


        # Our business logic
        mrn = message.segment('PID')
        # # Do something with mrn

        for i in mrn:
            print "===="
            for y in i:
                print y

        # We succeeded, so ACK back (default is AA)
        return defer.succeed(container.ack())

    def getCodec(self):
        # Our messages are encoded in Windows-1252
        # WARNING this is an example and is not universally true! You will
        # need to figure out the encoding you are receiving.
        return 'cp1252'
