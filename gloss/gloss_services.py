from gloss_service import GlossService
from gloss.receivers.mllp_multi_service import MultiMLLPServer
from gloss.importers.hl7_importer import HL7Importer

GLOSS_SERVICES = (
    GlossService(
        # the twisted service that brings in the data, its a function that receives
        # the
        receiver=MultiMLLPServer(ports=[2574, 2575], host="localhost").make_service,
        # translates the received message into message type receives the message
        # the gloss service
        importer=HL7Importer().import_and_notify,
        # listens to the output of the importer and sends/saves information
        subscribers=[],
        issuing_source="uclh"
    ),
)
