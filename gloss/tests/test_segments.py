from gloss.message_segments import *
from unittest import TestCase
from gloss.tests.test_messages import (
    FULL_BLOOD_COUNT, read_message, CYTOPATHOLOGY_RESULTS_MESSAGE,
    ALLERGY
)
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


class TestWithWrongMessage(TestCase):
    def test_with_wrong_message(self):
        class SomeMsg(HL7Message):
            segments = (MSH, PV2,)

        with self.assertRaises(KeyError):
            SomeMsg(read_message(FULL_BLOOD_COUNT))

class TestResultsPID(TestCase):
    def test_with_no_date_of_birth(self):
        class SomeMsg(HL7Message):
            segments = (MSH, ResultsPID,)

        no_dob = CYTOPATHOLOGY_RESULTS_MESSAGE.replace("19881107", "")
        result = SomeMsg(read_message(no_dob))
        self.assertIsNone(result.pid.date_of_birth)

class TestAllergiesPID(TestCase):
    def test_with_no_date_of_birth(self):
        class SomeMsg(HL7Message):
            segments = (MSH, AllergiesPID,)

        no_dob = ALLERGY.replace("19720221", "")
        result = SomeMsg(read_message(no_dob))
        self.assertIsNone(result.pid.date_of_birth)
