"""
Unittests for gloss.process_message
"""
from unittest import TestCase
from mock import patch, MagicMock

from datetime import date, datetime
from test_messages import (
    INPATIENT_ADMISSION, RESULTS_MESSAGE,
    RESULTS_CANCELLATION_MESSAGE, URINE_CULTURE_RESULT_MESSAGE,
    INPATIENT_DISCHARGE, INPATIENT_CANCEL_DISCHARGE,
    read_message, ALLERGY, NO_ALLERGY, PATIENT_DEATH, PATIENT_MERGE,
    PATIENT_UPDATE,
)

import gloss
from gloss.process_message import (
    MessageProcessor, InpatientAdmit, WinPathResults,
    InpatientDischarge, InpatientCancelDischarge,
    Allergy, PatientUpdate, PatientMerge,
)

from gloss.models import Session, get_gloss_id, InpatientEpisode
from gloss.tests.core import GlossTestCase


class MessageTypeTestCase(TestCase):
    def test_pid_segment_nhs_number_single(self):
        raw = read_message(RESULTS_CANCELLATION_MESSAGE)
        message = WinPathResults(raw)
        self.assertEqual('0918111222', message.pid.nhs_number)

    def test_pid_segment_nhs_number_multiple(self):
        raw = read_message(RESULTS_MESSAGE)
        message = WinPathResults(raw)
        self.assertEqual('1234567890', message.pid.nhs_number)

    def test_msh(self):
        raw = read_message(RESULTS_MESSAGE)
        message = WinPathResults(raw)
        self.assertEqual('UCLH', message.msh.sending_facility)


class AllergyTestCase(TestCase):
    @property
    def results_message(self):
        raw = read_message(ALLERGY)
        message = Allergy(raw)
        return message

    def test_allergies_pid(self):
        message = self.results_message
        self.assertEqual('97995111', message.pid.hospital_number)
        self.assertEqual('TESTPATIENT2', message.pid.surname)
        self.assertEqual('SABINE', message.pid.forename)
        self.assertEqual(date(1972, 02, 21), message.pid.date_of_birth)
        self.assertEqual('F', message.pid.gender)
        self.assertEqual('Allergies Known and Recorded', message.pid.allergy_status)

    def test_allergies_al1(self):
        message = self.results_message
        self.assertEqual('1', message.al1.allergy_type)
        self.assertEqual('Product Allergy', message.al1.allergy_type_description)
        self.assertEqual('CERT-1', message.al1.certainty_id)
        self.assertEqual('Definite', message.al1.certainty_description)
        self.assertEqual('CO-CODAMOL (Generic Manuf)', message.al1.allergy_reference_name)
        self.assertEqual('CO-CODAMOL (Generic Manuf) : ', message.al1.allergy_description)
        self.assertEqual(u'UDM', message.al1.allergen_reference_system)
        self.assertEqual('8f75c6d8-45b7-4b40-913f-8ca1f59b5350', message.al1.allergen_reference)
        self.assertEqual(u'1', message.al1.status_id)
        self.assertEqual(u'Active', message.al1.status_description)
        self.assertEqual(datetime(2015, 11, 19, 9, 16), message.al1.diagnosis_datetime)
        self.assertEqual(datetime(2015, 11, 19, 12, 00), message.al1.allergy_start_datetime)

    def test_allergies_no_al1(self):
        message = Allergy(read_message(NO_ALLERGY))
        # This is testing our suppression of the exception thrown by the underlying
        # HL7 library more than anything else.
        self.assertEqual(None, message.al1)


class InpatientAdmitTestCase(GlossTestCase):
    @property
    def results_message(self):
        raw = read_message(INPATIENT_ADMISSION)
        message = InpatientAdmit(raw)
        return message

    def test_inpatient_admit_has_pid(self):
        message = self.results_message
        self.assertEqual('50099878', message.pid.hospital_number)
        self.assertEqual('TUCKER', message.pid.surname)
        self.assertEqual('ANN', message.pid.forename)
        self.assertEqual(date(1962, 3, 4), message.pid.date_of_birth)
        self.assertEqual('F', message.pid.gender)
        self.assertEqual('940358', message.pid.patient_account_number)

    def test_inpatient_event(self):
        message = self.results_message
        self.assertEqual("A01", message.evn.event_type)
        self.assertEqual(
            datetime(2015, 11, 18, 17, 57),
            message.evn.recorded_datetime
        )
        self.assertEqual("ADM", message.evn.event_description)

    def test_inpatient_pv1(self):
        message = self.results_message
        self.assertEqual("INPATIENT", message.pv1.episode_type)
        self.assertEqual(
            datetime(2015, 11, 18, 17, 56), message.pv1.datetime_of_admission
        )
        self.assertEqual("BBNU", message.pv1.ward_code)
        self.assertEqual("BCOT", message.pv1.room_code)
        self.assertEqual("BCOT- 02B", message.pv1.bed_code)

    def test_process_message(self):
        with patch("gloss.process_message.fetch_demographics") as p:
            message = self.results_message
            message.process_message(self.session)
            gloss_id = get_gloss_id('50099878', self.session)
            self.assertTrue(gloss_id is not None)
            admissions = InpatientEpisode.get_from_gloss_id(
                gloss_id, self.session
            )
            self.assertEqual(len(admissions), 1)
            admission = admissions[0]
            self.assertEqual("BBNU", admission.ward_code)
            self.assertEqual("BCOT", admission.room_code)
            self.assertEqual("BCOT- 02B", admission.bed_code)
            self.assertEqual(
                datetime(2015, 11, 18, 17, 56), admission.datetime_of_admission
            )

class InpatientDischargeTestCase(TestCase):
    @property
    def results_message(self):
        raw = read_message(INPATIENT_DISCHARGE)
        message = InpatientDischarge(raw)
        return message

    def test_discharge_pid(self):
        pid = self.results_message.pid
        self.assertEqual("50099886", pid.hospital_number)
        self.assertEqual("TOMLINSON", pid.surname)
        self.assertEqual("ELIZABETH", pid.forename)
        self.assertEqual(date(1935, 8, 4), pid.date_of_birth)
        self.assertEqual('F', pid.gender)
        self.assertEqual('940347', pid.patient_account_number)

    def test_inpatient_pv1(self):
        message = self.results_message
        self.assertEqual("INPATIENT", message.pv1.episode_type)
        self.assertEqual(
            datetime(2015, 11, 18, 12, 17), message.pv1.datetime_of_admission
        )
        self.assertEqual(
            datetime(2015, 11, 18, 16, 15), message.pv1.datetime_of_discharge
        )
        self.assertEqual("F3NU", message.pv1.ward_code)
        self.assertEqual("F3SR", message.pv1.room_code)
        self.assertEqual("F3SR-36", message.pv1.bed_code)

    def test_evn(self):
        message = self.results_message
        self.assertEqual('DISCH', message.evn.event_description)


class InpatientCancelDischargeTestCase(TestCase):
    @property
    def results_message(self):
        raw = read_message(INPATIENT_CANCEL_DISCHARGE)
        message = InpatientCancelDischarge(raw)
        return message

    def test_discharge_pid(self):
        pid = self.results_message.pid
        self.assertEqual("50099886", pid.hospital_number)
        self.assertEqual("TOMLINSON", pid.surname)
        self.assertEqual("ELIZABETH", pid.forename)
        self.assertEqual(date(1935, 8, 4), pid.date_of_birth)
        self.assertEqual('F', pid.gender)
        self.assertEqual('940347', pid.patient_account_number)

    def test_inpatient_pv1(self):
        message = self.results_message
        self.assertEqual("INPATIENT", message.pv1.episode_type)
        self.assertEqual(
            datetime(2015, 11, 18, 12, 17), message.pv1.datetime_of_admission
        )
        self.assertEqual("F3NU", message.pv1.ward_code)
        self.assertEqual("F3SR", message.pv1.room_code)
        self.assertEqual("F3SR-36", message.pv1.bed_code)

    def test_evn(self):
        message = self.results_message
        self.assertEqual('CDIS', message.evn.event_description)


class PatientDeathTestCase(TestCase):
    @property
    def results_message(self):
        raw = read_message(PATIENT_DEATH)
        message = PatientUpdate(raw)
        return message

    def test_patient_death_pid(self):
        message = self.results_message
        self.assertEqual('50092915', message.pid.hospital_number)
        self.assertEqual('TESTING MEDCHART', message.pid.surname)
        self.assertEqual('MEDHCART FIRSTNAME', message.pid.forename)
        self.assertEqual(date(1987, 6, 12), message.pid.date_of_birth)
        self.assertEqual('M', message.pid.gender)
        self.assertEqual('Y', message.pid.death_indicator)
        self.assertEqual(date(2014, 11, 01), message.pid.date_of_death)


class PatientMergeTestCase(TestCase):
    @property
    def results_message(self):
        raw = read_message(PATIENT_MERGE)
        message = PatientMerge(raw)
        return message

    def test_pid(self):
        pid = self.results_message.pid
        self.assertEqual("MV 19823", pid.hospital_number)
        self.assertEqual("TESTSOA", pid.surname)
        self.assertEqual("SPACEINHOSPIDCHANGE", pid.forename)
        self.assertEqual(date(1986, 11, 12), pid.date_of_birth)
        self.assertEqual('M', pid.gender)

    def test_mrg(self):
        mrg = self.results_message.mrg
        self.assertEqual(mrg.duplicate_hospital_number, "50028000")


class PatientUpdateTestCase(TestCase):
    @property
    def results_message(self):
        raw = read_message(PATIENT_DEATH)
        message = PatientUpdate(raw)
        return message

    def test_patient_death_pid(self):
        message = self.results_message
        self.assertEqual('50092915', message.pid.hospital_number)
        self.assertEqual('TESTING MEDCHART', message.pid.surname)
        self.assertEqual('MEDHCART FIRSTNAME', message.pid.forename)
        self.assertEqual(date(1987, 6, 12), message.pid.date_of_birth)
        self.assertEqual('M', message.pid.gender)
        self.assertEqual('Y', message.pid.death_indicator)
        self.assertEqual(date(2014, 11, 1), message.pid.date_of_death)


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
        self.assertEqual(date(1982, 5, 15), message.pid.date_of_birth)
        self.assertEqual('F', message.pid.gender)

    def test_has_obr(self):
        message = self.results_message
        self.assertEqual('10U111970', message.obr.lab_number)
        self.assertEqual('ELU', message.obr.profile_code)
        self.assertEqual('RENAL PROFILE', message.obr.profile_description)
        self.assertEqual(datetime(2014, 1, 17, 20, 45), message.obr.request_datetime)
        self.assertEqual(datetime(2014, 1, 17, 17, 00), message.obr.observation_datetime)
        self.assertEqual(datetime(2014, 1, 17, 22, 58), message.obr.last_edited)
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
        self.assertEqual(date(1988, 6, 8), message.pid.date_of_birth)
        self.assertEqual('M', message.pid.gender)

        # Investigation medatada
        self.assertEqual('12V777833', message.obr.lab_number)
        self.assertEqual('URNC', message.obr.profile_code)
        self.assertEqual('URINE CULTURE', message.obr.profile_description)
        self.assertEqual(
            datetime(2012, 5, 20, 17, 15), message.obr.request_datetime
        )
        self.assertEqual(
            datetime(2012, 5, 20, 14, 13), message.obr.observation_datetime
        )
        self.assertEqual(
            datetime(2012, 5, 21, 11, 00), message.obr.last_edited
        )
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


class MessageProcessorTestCase(TestCase):
    def test_get_msh_for_message(self):
        msg = read_message(PATIENT_DEATH)
        message_processor = MessageProcessor()
        msh = message_processor.get_msh_for_message(msg)
        self.assertEqual(msh.trigger_event, "A31")
        self.assertEqual(msh.message_type, "ADT")
        self.assertEqual(msh.sending_application, "CARECAST")
        self.assertEqual(msh.sending_facility, "UCLH")

    def test_inpatient_admission(self):
        msg = read_message(INPATIENT_ADMISSION)
        message_processor = MessageProcessor()
        result = message_processor.get_message_type(msg)
        assert(result == InpatientAdmit)

    def test_winpath_results(self):
        msg = read_message(RESULTS_MESSAGE)
        message_processor = MessageProcessor()
        result = message_processor.get_message_type(msg)
        assert(result == WinPathResults)

    def test_inpatient_discharge(self):
        msg = read_message(INPATIENT_DISCHARGE)
        message_processor = MessageProcessor()
        result = message_processor.get_message_type(msg)
        assert(result == InpatientDischarge)

    def test_cancel_inpatient_discharge(self):
        msg = read_message(INPATIENT_CANCEL_DISCHARGE)
        message_processor = MessageProcessor()
        result = message_processor.get_message_type(msg)
        assert(result == InpatientCancelDischarge)

    def test_inpatient_allergy(self):
        msg = read_message(ALLERGY)
        message_processor = MessageProcessor()
        result = message_processor.get_message_type(msg)
        assert(result == Allergy)

    def test_inpatient_no_allergy(self):
        msg = read_message(NO_ALLERGY)
        message_processor = MessageProcessor()
        result = message_processor.get_message_type(msg)
        assert(result == Allergy)

    def test_patient_merge(self):
        msg = read_message(PATIENT_MERGE)
        message_processor = MessageProcessor()
        result = message_processor.get_message_type(msg)
        assert(result == PatientMerge)

    def test_patient_death(self):
        msg = read_message(PATIENT_DEATH)
        message_processor = MessageProcessor()
        result = message_processor.get_message_type(msg)
        assert(result == PatientUpdate)

    def test_patient_update(self):
        msg = read_message(PATIENT_UPDATE)
        message_processor = MessageProcessor()
        result = message_processor.get_message_type(msg)
        assert(result == PatientUpdate)

    def test_process_message_no_message_type(self):
        msg = MagicMock(name='mock_message')
        processor = MessageProcessor()
        with patch.object(gloss.process_message.logging, 'info') as info:
            with patch.object(processor,'get_message_type') as getter:
                getter.return_value = None
                processor.process_message(msg)
                info.assert_called_once_with('unable to find message type for None')
