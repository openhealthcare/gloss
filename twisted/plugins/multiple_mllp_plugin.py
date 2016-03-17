from zope.interface import implements
from zope.interface.verify import verifyClass

from gloss.settings import PORTS, HOST
from twisted.python import usage, reflect
from twisted.plugin import IPlugin
from twisted.internet import endpoints
from twisted.application.service import IServiceMaker, MultiService
from twisted.application import internet

DEFAULT_RECEIVER = "txHL7.receiver.LoggingReceiver"


class Options(usage.Options):
    """Define the options accepted by the ``twistd multiple_mllp`` plugin"""
    synopsis = "[mllp options]"

    optParameters = [
        ['receiver', 'r', DEFAULT_RECEIVER, 'A txHL7.receiver.IHL7Receiver subclass to handle messages.'],
    ]

    longdesc = """\
Starts an MLLP server. If no arguments are specified,
it will be a demo server that logs and ACKs each message received."""


class MLLPMultiServiceMaker(object):
    """Service maker for the MLLP server."""
    implements(IServiceMaker, IPlugin)
    tapname = "multiple_mllp"
    description = "HL7 MLLP that listens to multiple ports."
    options = Options

    def makeService(self, options):
        """Construct a server using MLLPFactory.

        :rtype: :py:class:`twisted.application.internet.StreamServerEndpointService`
        """
        from twisted.internet import reactor
        from txHL7.mllp import IHL7Receiver, MLLPFactory

        receiver_name = options['receiver']
        receiver_class = reflect.namedClass(receiver_name)
        verifyClass(IHL7Receiver, receiver_class)
        factory = MLLPFactory(receiver_class())
        multi_service = MultiService()

        for port_number in PORTS:
            port = "tcp:interface={0}:port={1}".format(HOST, port_number,)
            endpoint = endpoints.serverFromString(reactor, port)
            server = internet.StreamServerEndpointService(endpoint, factory)
            server.setName(u"mllp-{0}-{1}".format(receiver_name, port_number))
            multi_service.addService(server)
        return multi_service

serviceMaker = MLLPMultiServiceMaker()
