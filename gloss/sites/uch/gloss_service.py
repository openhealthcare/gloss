from gloss.gloss_service import GlossService
from gloss.receivers.mllp_multi_service import MultiMLLPServer
from gloss.importers.hl7_importer import HL7Importer
from gloss.sites.uch.subscribe.production import NotifyOpalWhenSubscribed
from gloss.subscribers.send_all_messages import SendAllMessages


GLOSS_SERVICE = GlossService(
    receiver=MultiMLLPServer(ports=[2574, 2575], host="localhost").make_service,
    importer=HL7Importer().import_and_notify,
    subscribers=[
        NotifyOpalWhenSubscribed().notify,
        SendAllMessages(end_point="http://127.0.0.1:8000/glossapi/v0.1/glossapi/").notify
    ],
    issuing_source="uclh"
)
