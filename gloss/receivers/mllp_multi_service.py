from twisted.internet import endpoints
from twisted.application.service import MultiService
from twisted.application import internet
from twisted.logger import Logger
from txHL7.receiver import AbstractHL7Receiver
from twisted.internet import defer

DEFAULT_SERVICES=""


class OhcReceiver(AbstractHL7Receiver):
    log = Logger(namespace="receiver")

    def __init__(self, gloss_service):
        self.gloss_service = gloss_service

    def handleMessage(self, container):
        message = container.message
        self.log.info(str(message).replace("\r", "\n"))
        self.gloss_service.importer(message, self.gloss_service)
        # We succeeded, so ACK back (default is AA)
        return self.ack(container)

    def getCodec(self):
        # Our messages are encoded in Windows-1252
        # WARNING this is an example and is not universally true! You will
        # need to figure out the encoding you are receiving.
        return 'cp1252'

    def ack(self, container):
        ack_message = unicode(container.message.create_ack(
            application="ELCID", facility="UCLH"
        ))
        self.log.info(ack_message.replace("\r", "\n"))
        return defer.succeed(ack_message)



class MultiMLLPServer(object):
    def __init__(self, ports, host):
        self.ports = ports
        self.host = host

    def make_service(self, gloss_service):
        """Construct a server using MLLPFactory.

        :rtype: :py:class:`twisted.application.internet.StreamServerEndpointService`
        """
        from twisted.internet import reactor
        from txHL7.mllp import MLLPFactory
        factory = MLLPFactory(OhcReceiver(gloss_service))
        multi_service = MultiService()

        for port_number in self.ports:
            port = "tcp:interface={0}:port={1}".format(self.host, port_number,)
            endpoint = endpoints.serverFromString(reactor, port)
            server = internet.StreamServerEndpointService(endpoint, factory)
            server.setName(u"gloss-mllp-{0}".format(port_number))
            multi_service.addService(server)
        return multi_service
