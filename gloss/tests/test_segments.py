from gloss.message_segments import *
from unittest import TestCase
from gloss.tests.test_messages import FULL_BLOOD_COUNT, read_message
from gloss.message_segments import HL7Message


class WinPathResults(HL7Message):
    message_type = u"ORU"
    trigger_event = u"R01"

    segments = (
        MSH, ResultsPID, ResultsPV1, ORC, RepeatingField(
            OBR,
            RepeatingField(OBX, section_name="obxs"),
            RepeatingField(NTE, section_name="ntes"),
            section_name="results"
            )
    )


class TestSegments(TestCase):
    def test_multi_levelled_message(self):
        hl7_msg = read_message(FULL_BLOOD_COUNT)
        msg = WinPathResults(hl7_msg)
        self.assertEqual(len(msg.results), 2)
