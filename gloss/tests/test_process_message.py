from unittest import TestCase
from test_messages import (
    INPATIENT_ADMISSION, RESULTS_MESSAGE,
    RESULTS_CANCELLATION_MESSAGE, URINE_CULTURE_RESULT_MESSAGE,
    INPATIENT_DISCHARGE, read_message
)
from gloss.process_message import (
    MessageProcessor, InpatientAdmit, WinPathResults
)


def test_message_processor():
    msg = read_message(INPATIENT_ADMISSION)
    message_processor = MessageProcessor()
    result = message_processor.get_message_type(msg)
    assert(result == InpatientAdmit)

def test_winpath_results():
    msg = read_message(RESULTS_MESSAGE)
    message_processor = MessageProcessor()
    result = message_processor.get_message_type(msg)
    assert(result == WinPathResults)

class MessageTypeTestCase(TestCase):
    def test_pid_segment_nhs_number_single(self):
        raw = read_message(RESULTS_CANCELLATION_MESSAGE)
        message = WinPathResults(raw)
        self.assertEqual('0918111222', message.pid.nhs_number)

    def test_pid_segment_nhs_number_multiple(self):
        raw = read_message(RESULTS_MESSAGE)
        message = WinPathResults(raw)
        self.assertEqual('1234567890', message.pid.nhs_number)


class InpatientAdmitTestCase(TestCase):
    @property
    def results_message(self):
        raw = read_message(INPATIENT_ADMISSION)
        message = InpatientAdmit(raw)
        return message

    def test_inpatient_admit_has_pid(self):
        message = self.results_message
        self.assertEqual('50099878', message.pid.hospital_number)
        self.assertEqual('9949657660', message.pid.nhs_number)
        self.assertEqual('TUCKER', message.pid.surname)
        self.assertEqual('ANN', message.pid.forename)
        self.assertEqual('196203040000', message.pid.date_of_birth)
        self.assertEqual('F', message.pid.gender)

    def test_inpatient_event(self):
        message = self.results_message
        self.assertEqual("A01", message.evn.event_type)
        self.assertEqual("201511181757", message.evn.recorded_time)
        self.assertEqual("ADM", message.evn.event_description)


class InpatientDischargeTestCase(TestCase):
    @property
    def results_message(self):
        raw = read_message(INPATIENT_DISCHARGE)
        message = InpatientAdmit(raw)
        return message

    def test_discharge_pid(self):
        pid = self.results_message.pid
        self.assertEqual("50099886", pid.hospital_number)
        self.assertEqual("TOMLINSON", pid.surname)
        self.assertEqual("ELIZABETH", pid.forename)
        self.assertEqual('193508040000', pid.date_of_birth)
        self.assertEqual('F', pid.gender)


class WinPathResultsTestCase(TestCase):

    @property
    def results_message(self):
        raw = read_message(RESULTS_MESSAGE)
        message = WinPathResults(raw)
        return message

    def test_winpath_results_has_pid(self):
        message = self.results_message
        self.assertEqual('12345678', message.pid.hospital_number)
        self.assertEqual('ISURNAME', message.pid.surname)
        self.assertEqual('FIRSTNAME MNAME', message.pid.forename)
        self.assertEqual('19820515', message.pid.date_of_birth)
        self.assertEqual('F', message.pid.gender)

    def test_has_obr(self):
        message = self.results_message
        self.assertEqual('10U111970', message.obr.lab_number)
        self.assertEqual('ELU', message.obr.profile_code)
        self.assertEqual('RENAL PROFILE', message.obr.profile_description)
        self.assertEqual('201401172045', message.obr.request_datetime)
        self.assertEqual('201401171700', message.obr.observation_datetime)
        self.assertEqual('201401172258', message.obr.last_edited)
        self.assertEqual('FINAL', message.obr.result_status)

    def test_get_obx_test(self):
        message = self.results_message
        self.assertEqual('NA', message.obx[0].test_code)
        self.assertEqual('CREA', message.obx[3].test_code)
        self.assertEqual('Sodium', message.obx[0].test_name)
        self.assertEqual('Creatinine', message.obx[3].test_name)

    def test_get_obx_observation(self):
        message = self.results_message
        self.assertEqual('143', message.obx[0].observation_value)
        self.assertEqual('mmol/L', message.obx[0].units)
        self.assertEqual('135-145', message.obx[0].reference_range)

        self.assertEqual('61', message.obx[3].observation_value)
        self.assertEqual('umol/L', message.obx[3].units)
        self.assertEqual('49-92', message.obx[3].reference_range)

    def test_get_obx_result_status(self):
        message = self.results_message
        self.assertEqual('FINAL', message.obx[0].result_status)

    def test_get_nte_note(self):
        note = "\n".join(["Units: mL/min/1.73sqm",
                          "Multiply eGFR by 1.21 for people of African",
                          "Caribbean origin. Interpret with regard to",
                          "UK CKD guidelines: www.renal.org/CKDguide/ckd.html",
                          "Use with caution for adjusting drug dosages -",
                          "contact clinical pharmacist for advice."])
        self.assertEqual(note, self.results_message.nte.comments)

    def test_urine_culture_result(self):
        #
        # This test may well be adding nothing to the above.
        # Consider deleting - it's just belt & braces for initial
        # exploration
        #
        message = WinPathResults(read_message(URINE_CULTURE_RESULT_MESSAGE))
        #PID
        self.assertEqual('C2088885408', message.pid.hospital_number)
        self.assertEqual('GRECE', message.pid.surname)
        self.assertEqual('POPEDULE', message.pid.forename)
        self.assertEqual('19880608', message.pid.date_of_birth)
        self.assertEqual('M', message.pid.gender)

        # Investigation medatada
        self.assertEqual('12V777833', message.obr.lab_number)
        self.assertEqual('URNC', message.obr.profile_code)
        self.assertEqual('URINE CULTURE', message.obr.profile_description)
        self.assertEqual('201205201715', message.obr.request_datetime)
        self.assertEqual('201205201413', message.obr.observation_datetime)
        self.assertEqual('201205211100', message.obr.last_edited)
        self.assertEqual('FINAL', message.obr.result_status)

    def test_obx_free_text_value_type(self):
        message = WinPathResults(read_message(URINE_CULTURE_RESULT_MESSAGE))

        # Values
        self.assertEqual('URNC', message.obx[0].test_code)
        self.assertEqual('URINE CULTURE', message.obx[0].test_name)
        self.assertEqual('URINE CULTURE REPORT', message.obx[0].observation_value)
        self.assertEqual('FINAL', message.obx[0].result_status)

        self.assertEqual('UPRE', message.obx[1].test_code)
        self.assertEqual('Culture', message.obx[1].test_name)
        self.assertEqual('Screening culture negative.', message.obx[1].observation_value)
        self.assertEqual('FINAL', message.obx[1].result_status)

        self.assertEqual('URST', message.obx[2].test_code)
        self.assertEqual('STATUS', message.obx[2].test_name)
        self.assertEqual('COMPLETE: 21/08/13', message.obx[2].observation_value)
        self.assertEqual('FINAL', message.obx[2].result_status)
