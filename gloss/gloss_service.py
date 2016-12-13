from gloss.receivers.mllp_multi_service import MultiMLLPServer
from gloss.importers.hl7_importer import HL7Importer
from gloss.conf import settings
from gloss.gloss_service_base import GlossService

GLOSS_SERVICE = GlossService(
        # the twisted service that brings in the data, its a function that receives
        # the
        receiver=MultiMLLPServer(ports=[2574, 2575], host="localhost").make_service,
        # translates the received message into message type receives the message
        # the gloss service
        importer=HL7Importer().import_and_notify,
        # listens to the output of the importer and sends/saves information
        subscribers=[
            SendAllMessages(end_point="http://127.0.0.1:8000/glossapi/v0.1/glossapi/").notify
        ],
        issuing_source=settings.ISSUING_SOURCE
)
