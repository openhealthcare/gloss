from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.python import usage, reflect
from twisted.application.service import IServiceMaker
from gloss.conf import settings

class Options(usage.Options):
    """Define the options accepted by the ``twistd multiple_mllp`` plugin"""
    synopsis = "[mllp options]"

    optParameters = [
        ['service', 'r', settings.DEFAULT_GLOSS_SERVICE, 'gloss.gloss_services.GLOSS_SERVICES'],
    ]

    longdesc = """\
    starts the gloss server
"""


class GlossServiceMaker(object):
    """Service maker for the MLLP server."""
    implements(IServiceMaker, IPlugin)
    tapname = "gloss"
    description = "A Gloss listening service"
    options = Options

    def makeService(self, options):
        """ Return a service, this will need to be changed to
            manage many services
        """
        gloss_service = reflect.namedObject(options['service'])
        return gloss_service.receiver(gloss_service)


serviceMaker = GlossServiceMaker()
