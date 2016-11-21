import hl7
import mock

from gloss.receivers.mllp_multi_service import OhcReceiver
from gloss.tests.core import GlossTestCase
from gloss.translators.hl7.segments import MSH
from test_messages import PATIENT_UPDATE, read_message
from txHL7.receiver import HL7MessageContainer

class TestOhcReceiverTestCase(GlossTestCase):
    def test_ack_message(self):
        container = HL7MessageContainer(PATIENT_UPDATE.replace("\n", "\r"))
        service = mock.MagicMock()
        ohc_receiver = OhcReceiver(service)
        ack = ohc_receiver.handleMessage(container).result
        msh = MSH(hl7.parse(ack).segment("MSH"))
        self.assertEqual(msh.sending_application, "ELCID")
        self.assertEqual(msh.sending_facility, "UCLH")
        self.assertTrue(service.importer.called)

    def test_get_codec(self):
        self.assertEqual('cp1252', OhcReceiver(mock.MagicMock()).getCodec())
