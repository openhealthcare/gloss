from unittest import TestCase
import hl7

from gloss.ohc_receiver import OhcReceiver
from gloss.tests.core import GlossTestCase
from gloss.import_message import MSH
from test_messages import PATIENT_UPDATE, read_message
from txHL7.receiver import HL7MessageContainer

class TestOhcReceiverTestCase(GlossTestCase):
    def test_ack_message(self):
        container = HL7MessageContainer(PATIENT_UPDATE.replace("\n", "\r"))
        ohc_receiver = OhcReceiver()
        ack = ohc_receiver.handleMessage(container).result
        msh = MSH(hl7.parse(ack).segment("MSH"))
        self.assertEqual(msh.sending_application, "ELCID")
        self.assertEqual(msh.sending_facility, "UCLH")

    def test_get_codec(self):
        self.assertEqual('cp1252', OhcReceiver().getCodec())
