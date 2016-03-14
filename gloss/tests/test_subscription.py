import json
from mock import patch, MagicMock
from datetime import datetime, date
from gloss.import_message import MessageProcessor
from gloss.tests.core import GlossTestCase
from gloss.tests.test_messages import (
    INPATIENT_ADMISSION, read_message, PATIENT_MERGE, COMPLEX_WINPATH_RESULT,
    RESULTS_MESSAGE, INPATIENT_TRANSFER, INPATIENT_DISCHARGE, INPATIENT_AMEND,
    INPATIENT_SPELL_DELETE, INPATIENT_CANCEL_DISCHARGE, ALLERGY, NO_ALLERGY,
    COMPLEX_WINPATH_RESULT, PATIENT_DEATH, PATIENT_UPDATE
)
from gloss.models import (
    Merge, get_or_create_identifier, InpatientEpisode, get_gloss_reference,
    InpatientLocation, subscribe, Allergy, Result, Patient, Subscription)
from gloss.subscriptions import UclhPatientUpdateSubscription, OpalSerialiser
from gloss.message_type import PatientUpdateMessage, MessageContainer


class TestInpatientAdmissionFlow(GlossTestCase):
    def test_flow(self):
        subscribe('50099878', self.session, "uclh")
        message_processor = MessageProcessor()
        message_processor.process_message(read_message(INPATIENT_ADMISSION))
        gloss_reference = get_gloss_reference('50099878', self.session)
        self.assertTrue(gloss_reference is not None)
        admission = InpatientEpisode.get_from_gloss_reference(
            gloss_reference, self.session
        )
        self.assertEqual(
            datetime(2015, 11, 18, 17, 56), admission.datetime_of_admission
        )
        self.assertEqual(
            "TEST NON ELECTIVE PATIENT", admission.admission_diagnosis
        )
        location = self.session.query(InpatientLocation).one()
        self.assertEqual(location.inpatient_episode, admission)
        self.assertEqual(location.ward_code, "BBNU")
        self.assertEqual(location.room_code, "BCOT")
        self.assertEqual(location.bed_code, "BCOT-02B")
        self.assertIsNone(location.datetime_of_transfer)



class TestInpatientDischarge(GlossTestCase):
    hospital_number = "50099886"
    visit_number = "940347"

    def setUp(self):
        self.message = read_message(INPATIENT_DISCHARGE)
        self.message_processor = MessageProcessor()
        super(TestInpatientDischarge, self).setUp()

    def test_with_existing_inpatient_episode(self):
        old_inpatient_episode = self.get_inpatient_episode(
            self.hospital_number, "uclh"
        )
        old_inpatient_episode.visit_number = self.visit_number
        old_inpatient_episode.datetime_of_discharge = None
        old_inpatient_episode.datetime_of_admission = datetime(
            2014, 11, 18, 16, 15
        )

        old_inpatient_location = self.get_inpatient_location(
            old_inpatient_episode
        )
        self.session.add(old_inpatient_episode)
        self.session.add(old_inpatient_location)
        self.message_processor.process_message(self.message)
        inpatient_episode = self.session.query(InpatientEpisode).one()
        self.assertEqual(
            inpatient_episode.datetime_of_discharge,
            datetime(2015, 11, 18, 16, 15)
        )
        self.assertEqual(
            inpatient_episode.datetime_of_admission,
            datetime(2015, 11, 18, 12, 17)
        )
        inpatient_location = self.session.query(InpatientLocation).one()
        self.assertEqual(
            inpatient_location.inpatient_episode, inpatient_episode
        )
        self.assertEqual(inpatient_location.ward_code, "F3NU")
        self.assertEqual(inpatient_location.room_code, "F3SR")
        self.assertEqual(inpatient_location.bed_code, "F3SR-36")

    def test_without_existing_inpatient_episode(self):
        self.message_processor.process_message(self.message)
        inpatient_episode = self.session.query(InpatientEpisode).one()
        self.assertEqual(
            inpatient_episode.datetime_of_discharge,
            datetime(2015, 11, 18, 16, 15)
        )
        self.assertEqual(
            inpatient_episode.datetime_of_admission,
            datetime(2015, 11, 18, 12, 17)
        )
        inpatient_location = self.session.query(InpatientLocation).one()
        self.assertEqual(
            inpatient_location.inpatient_episode, inpatient_episode
        )
        self.assertEqual(inpatient_location.ward_code, "F3NU")
        self.assertEqual(inpatient_location.room_code, "F3SR")
        self.assertEqual(inpatient_location.bed_code, "F3SR-36")


class TestInpatientAmend(GlossTestCase):
    hospital_number = "50030204"
    visit_number = "930882"

    def setUp(self):
        self.message = read_message(INPATIENT_AMEND)
        self.message_processor = MessageProcessor()
        super(TestInpatientAmend, self).setUp()

    def test_with_existing_inpatient_episode(self):
        existing_inpatient_episode = self.get_inpatient_episode(
            self.hospital_number, "uclh"
        )
        existing_inpatient_episode.datetime_of_admission = datetime(
            2012, 10, 10, 10, 10
        )
        existing_inpatient_episode.datetime_of_discharge = datetime(
            2013, 10, 10, 10, 10
        )
        existing_inpatient_episode.visit_number = self.visit_number
        existing_inpatient_location = self.get_inpatient_location(
            existing_inpatient_episode
        )
        existing_inpatient_location.ward_code = "A03"
        existing_inpatient_location.room_code = "A03"
        existing_inpatient_location.bed_code = "A03"
        self.session.add(existing_inpatient_episode)
        self.session.add(existing_inpatient_location)
        self.message_processor.process_message(self.message)
        inpatient_episode = self.session.query(InpatientEpisode).one()
        self.assertEqual(
            inpatient_episode.datetime_of_admission,
            datetime(2012, 9, 19, 18, 22)
        )
        self.assertEqual(
            inpatient_episode.datetime_of_discharge,
            datetime(2012, 12, 8, 14, 30)
        )
        self.assertEqual(
            "ANY FOR TESTING",
            inpatient_episode.admission_diagnosis
        )
        inpatient_location = self.session.query(InpatientLocation).one()
        self.assertEqual(
            existing_inpatient_episode, inpatient_location.inpatient_episode
        )
        self.assertEqual(inpatient_location.ward_code, "T03")
        self.assertEqual(inpatient_location.room_code, "T03A")
        self.assertEqual(inpatient_location.bed_code, "T03-14")

    def test_without_existing_inpatient_episode(self):
        self.message_processor.process_message(self.message)
        inpatient_episode = self.session.query(InpatientEpisode).one()
        self.assertEqual(
            inpatient_episode.datetime_of_admission,
            datetime(2012, 9, 19, 18, 22)
        )
        self.assertEqual(
            inpatient_episode.datetime_of_discharge,
            datetime(2012, 12, 8, 14, 30)
        )
        inpatient_location = self.session.query(InpatientLocation).one()
        self.assertEqual(
            inpatient_episode, inpatient_location.inpatient_episode
        )
        self.assertEqual(inpatient_location.ward_code, "T03")
        self.assertEqual(inpatient_location.room_code, "T03A")
        self.assertEqual(inpatient_location.bed_code, "T03-14")


class TestInpatientCancelDischarge(GlossTestCase):
    hospital_number = "40716752"
    visit_number = "4449234"

    def setUp(self):
        self.message = read_message(INPATIENT_CANCEL_DISCHARGE)
        self.message_processor = MessageProcessor()
        super(TestInpatientCancelDischarge, self).setUp()

    def test_with_existing_inpatient_episode(self):
        self.inpatient_episode = self.get_inpatient_episode(
            self.hospital_number, "uclh"
        )
        self.inpatient_episode.datetime_of_admission = datetime(
            2012, 10, 10, 10, 10
        )
        self.inpatient_episode.datetime_of_discharge = datetime(
            2013, 10, 10, 10, 10
        )
        self.inpatient_location = self.get_inpatient_location(
            self.inpatient_episode
        )
        self.inpatient_location.ward_code = "A03"
        self.inpatient_location.room_code = "A03"
        self.inpatient_location.bed_code = "A03"
        self.session.add(self.inpatient_episode)
        self.session.add(self.inpatient_location)
        self.message_processor.process_message(self.message)
        inpatient_episode = self.session.query(InpatientEpisode).one()
        self.assertEqual(
            inpatient_episode.datetime_of_admission,
            datetime(2015, 11, 18, 12, 17)
        )
        self.assertIsNone(
            inpatient_episode.datetime_of_discharge,
        )
        inpatient_location = self.session.query(InpatientLocation).one()
        self.assertEqual(
            inpatient_episode, inpatient_location.inpatient_episode
        )
        self.assertEqual(inpatient_location.ward_code, "F3NU")
        self.assertEqual(inpatient_location.room_code, "F3SR")
        self.assertEqual(inpatient_location.bed_code, "F3SR-36")


class TestInpatientDeleteSpell(GlossTestCase):
    hospital_number = "40716752"
    visit_number = "4449234"

    def setUp(self):
        self.message = read_message(INPATIENT_SPELL_DELETE)
        self.message_processor = MessageProcessor()
        super(TestInpatientDeleteSpell, self).setUp()

    def test_without_existing_inpatient_episode(self):
        self.inpatient_episode = self.get_inpatient_episode(
            self.hospital_number, "uclh"
        )
        self.inpatient_episode.datetime_of_admission = datetime(
            2012, 10, 10, 10, 10
        )
        self.inpatient_episode.datetime_of_discharge = datetime(
            2013, 10, 10, 10, 10
        )
        self.inpatient_episode.visit_number = self.visit_number
        self.inpatient_location = self.get_inpatient_location(
            self.inpatient_episode
        )
        self.inpatient_location.ward_code = "A03"
        self.inpatient_location.room_code = "A03"
        self.inpatient_location.bed_code = "A03"
        self.session.add(self.inpatient_episode)
        self.session.add(self.inpatient_location)
        self.message_processor.process_message(self.message)
        num_inpatients = self.session.query(InpatientEpisode).count()
        self.assertEqual(num_inpatients, 0)
        num_locations = self.session.query(InpatientEpisode).count()
        self.assertEqual(num_locations, 0)

    def test_with(self):
        self.message_processor.process_message(self.message)
        num_inpatients = self.session.query(InpatientEpisode).count()
        self.assertEqual(num_inpatients, 0)
        num_locations = self.session.query(InpatientEpisode).count()
        self.assertEqual(num_locations, 0)


class TestInpatientTransfer(GlossTestCase):
    hospital_number = "50099878"

    def setUp(self):
        super(TestInpatientTransfer, self).setUp()

        self.message = read_message(INPATIENT_TRANSFER)
        self.message_processor = MessageProcessor()

    def test_flow_if_with_previous(self):
        transfer_time = datetime(2012, 12, 14, 11, 0)

        self.inpatient_episode = self.get_inpatient_episode(
            self.hospital_number, "uclh"
        )
        self.inpatient_episode.visit_number = '930375'
        self.inpatient_location = self.get_inpatient_location(
            self.inpatient_episode
        )

        self.session.add(self.inpatient_episode)
        self.session.add(self.inpatient_location)
        self.session.commit()

        self.message_processor.process_message(self.message)

        # make sure we're not creating multiple episodes
        self.session.query(InpatientEpisode).one()

        # we should have 2 locations, the old and the new
        inpatient_locations = self.session.query(InpatientLocation).all()

        old_location = inpatient_locations[0]
        self.assertEqual(old_location.datetime_of_transfer, transfer_time)

        self.assertEqual(
            old_location.inpatient_episode, self.inpatient_episode
        )
        self.assertEqual(
            old_location.room_code, self.inpatient_location.room_code
        )
        self.assertEqual(
            old_location.ward_code, self.inpatient_location.ward_code
        )
        self.assertEqual(
            old_location.bed_code, self.inpatient_location.bed_code
        )

        new_location = inpatient_locations[1]
        self.assertIsNone(new_location.datetime_of_transfer)
        self.assertEqual("T06", new_location.ward_code)
        self.assertEqual("T06A", new_location.room_code)
        self.assertEqual("T06-04", new_location.bed_code)

    def test_flow_if_no_previous(self):
        self.message_processor.process_message(self.message)
        self.session.query(InpatientEpisode).one()
        inpatient_location = self.session.query(InpatientLocation).one()
        self.assertIsNone(inpatient_location.datetime_of_transfer)
        self.assertEqual("T06", inpatient_location.ward_code)
        self.assertEqual("T06A", inpatient_location.room_code)
        self.assertEqual("T06-04", inpatient_location.bed_code)


class TestMergeFlow(GlossTestCase):
    def test_complete_flow(self):
        old_hospital_id = "50028000"
        old_gloss_reference = get_or_create_identifier(
            hospital_number=old_hospital_id,
            session=self.session,
            issuing_source="uclh"
        )
        message_processor = MessageProcessor()
        message_processor.process_message(read_message(PATIENT_MERGE))
        session = self.session
        result = session.query(Merge).one()
        old_gloss_id = result.old_reference_id
        self.assertEqual(old_gloss_reference.id, old_gloss_id)


class TestAllergyFlow(GlossTestCase):

    def setUp(self):
        super(TestAllergyFlow, self).setUp()
        self.message_processor = MessageProcessor()

    def test_with_allergies(self):
        allergy = self.get_allergy("97995111", issuing_source="uclh")
        self.session.add(allergy)
        self.message_processor.process_message(read_message(ALLERGY))
        found_allergy = self.session.query(Allergy).one()
        self.assertEqual('1', found_allergy.allergy_type)
        self.assertEqual('Product Allergy', found_allergy.allergy_type_description)
        self.assertEqual('CERT-1', found_allergy.certainty_id)
        self.assertEqual('Definite', found_allergy.certainty_description)
        self.assertEqual('CO-CODAMOL (Generic Manuf)', found_allergy.allergy_reference_name)
        self.assertEqual('CO-CODAMOL (Generic Manuf) : ', found_allergy.allergy_description)
        self.assertEqual(u'UDM', found_allergy.allergen_reference_system)
        self.assertEqual('8f75c6d8-45b7-4b40-913f-8ca1f59b5350', found_allergy.allergen_reference)
        self.assertEqual(u'1', found_allergy.status_id)
        self.assertEqual(u'Active', found_allergy.status_description)
        self.assertEqual(datetime(2015, 11, 19, 9, 16), found_allergy.diagnosis_datetime)
        self.assertEqual(datetime(2015, 11, 19, 12, 00), found_allergy.allergy_start_datetime)
        gloss_ref = get_gloss_reference(
            "97995111", session=self.session, issuing_source="uclh"
        )
        self.assertEqual(gloss_ref, found_allergy.gloss_reference)

    def test_with_no_allergies(self):
        allergy = self.get_allergy("97995000", issuing_source="uclh")
        self.session.add(allergy)
        self.message_processor.process_message(read_message(NO_ALLERGY))
        found_allergy = self.session.query(Allergy).one()
        self.assertTrue(found_allergy.no_allergies)
        gloss_ref = get_gloss_reference(
            "97995000", session=self.session, issuing_source="uclh"
        )
        self.assertEqual(gloss_ref, found_allergy.gloss_reference)


class TestResultsFlow(GlossTestCase):
    """
        currently a shell of a test that makes sure we get no errors
        from repeating fields
    """
    def test_message_with_notes(self):
        message_processor = MessageProcessor()
        message_processor.process_message(read_message(RESULTS_MESSAGE))
        result = self.session.query(Result).one()
        expected_comments = " ".join([
            "Units: mL/min/1.73sqm Multiply eGFR by 1.21 for people of",
            "African Caribbean origin. Interpret with regard to UK CKD",
            "guidelines: www.renal.org/CKDguide/ckd.html Use with caution",
            "for adjusting drug dosages - contact clinical pharmacist for",
            "advice."
        ])

        expected_observations = [
            {
                "result_status": "FINAL",
                "observation_value": "143",
                "comments": expected_comments,
                "test_code": "NA",
                "value_type": "NM",
                "test_name": "Sodium",
                "units": "mmol/L",
                "reference_range": "135-145"
            },
            {
                "result_status": "FINAL",
                "observation_value": "3.9",
                "comments": None,
                "test_code": "K",
                "value_type": "NM",
                "test_name": "Potassium",
                "units": "mmol/L",
                "reference_range": "3.5-5.1"
            },
            {
                "result_status": "FINAL",
                "observation_value": "3.9",
                "comments": None,
                "test_code": "UREA",
                "value_type": "NM",
                "test_name": "Urea",
                "units": "mmol/L",
                "reference_range": "1.7-8.3"
            },
            {
                "result_status": "FINAL",
                "observation_value": "61",
                "comments": None,
                "test_code": "CREA",
                "value_type": "NM",
                "test_name": "Creatinine",
                "units": "umol/L",
                "reference_range": "49-92"
            },
            {
                "result_status": "FINAL",
                "observation_value": ">90",
                "comments": None,
                "test_code": "GFR",
                "value_type": "NM",
                "test_name": "Estimated GFR",
                "units": ".",
                "reference_range": None
            }
        ]
        self.assertEqual(
            expected_observations, json.loads(result.observations)
        )

        self.assertEqual(
            datetime(2014, 1, 17, 20, 45), result.request_datetime
        )

        self.assertEqual(
            datetime(2014, 1, 17, 17, 0), result.observation_datetime
        )

        self.assertEqual('ELU', result.profile_code)
        self.assertEqual('FINAL', result.result_status)

    def test_complex_message(self):
        message_processor = MessageProcessor()
        message_processor.process_message(read_message(COMPLEX_WINPATH_RESULT))
        results = self.session.query(Result).all()
        self.assertEqual(2, len(results))
        result_1 = results[0]
        expected_observations_1 = [
            {
                u'comments': None,
                u'observation_value': u'8.00',
                u'reference_range': u'3.0-10.0',
                u'result_status': None,
                u'test_code': u'WCC',
                u'test_name': u'White cell count',
                u'units': u'x10^9/L',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'3.20',
                u'reference_range': u'4.4-5.8',
                u'result_status': None,
                u'test_code': u'RCC',
                u'test_name': u'Red cell count',
                u'units': u'x10^12/L',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'87',
                u'reference_range': None,
                u'result_status': None,
                u'test_code': u'HBGL',
                u'test_name': u'Haemoglobin (g/L)',
                u'units': u'g/L',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'0.350',
                u'reference_range': u'0.37-0.50',
                u'result_status': None,
                u'test_code': u'HCTU',
                u'test_name': u'HCT',
                u'units': u'L/L',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'78.0',
                u'reference_range': u'80-99',
                u'result_status': None,
                u'test_code': u'MCVU',
                u'test_name': u'MCV',
                u'units': u'fL',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'28.0',
                u'reference_range': u'27.0-33.5',
                u'result_status': None,
                u'test_code': u'MCHU',
                u'test_name': u'MCH',
                u'units': u'pg',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'300',
                u'reference_range': None,
                u'result_status': None,
                u'test_code': u'MCGL',
                u'test_name': u'MCHC (g/L)',
                u'units': u'g/L',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'17.0',
                u'reference_range': u'11.5-15.0',
                u'result_status': None,
                u'test_code': u'RDWU',
                u'test_name': u'RDW',
                u'units': u'%',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'250',
                u'reference_range': u'150-400',
                u'result_status': None,
                u'test_code': u'PLT',
                u'test_name': u'Platelet count',
                u'units': u'x10^9/L',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'10.0',
                u'reference_range': u'7-13',
                u'result_status': None,
                u'test_code': u'MPVU',
                u'test_name': u'MPV',
                u'units': u'fL',
                u'value_type': u'NM'
            }
        ]

        self.assertEqual(
            expected_observations_1, json.loads(result_1.observations)
        )

        self.assertEqual('98U000057', result_1.lab_number)
        self.assertEqual(
            datetime(2014, 11, 12, 16, 0), result_1.observation_datetime
        )
        self.assertEqual(
            datetime(2014, 11, 12, 16, 6), result_1.request_datetime
        )
        self.assertEqual("FINAL", result_1.result_status)
        self.assertEqual("FBCY", result_1.profile_code)

        result_2 = results[1]

        expected_observations_2 = [
            {
                u'comments': None,
                u'observation_value': u'55.0%  4.40',
                u'reference_range': u'2.0-7.5',
                u'result_status': None,
                u'test_code': u'NE',
                u'test_name': u'Neutrophils',
                u'units': u'x10^9/L',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'25.0%  2.00',
                u'reference_range': u'1.2-3.65',
                u'result_status': None,
                u'test_code': u'LY',
                u'test_name': u'Lymphocytes',
                u'units': u'x10^9/L',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'15.0%  1.20',
                u'reference_range': u'0.2-1.0',
                u'result_status': None,
                u'test_code': u'MO',
                u'test_name': u'Monocytes',
                u'units': u'x10^9/L',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'3.0%  0.24',
                u'reference_range': u'0.0-0.4',
                u'result_status': None,
                u'test_code': u'EO',
                u'test_name': u'Eosinophils',
                u'units': u'x10^9/L',
                u'value_type': u'NM'
            },
            {
                u'comments': None,
                u'observation_value': u'2.0%  0.16',
                u'reference_range': u'0.0-0.1',
                u'result_status': None,
                u'test_code': u'BA',
                u'test_name': u'Basophils',
                u'units': u'x10^9/L',
                u'value_type': u'NM'
            }
        ]

        self.assertEqual(
            expected_observations_2, json.loads(result_2.observations)
        )

        self.assertEqual('98U000057', result_2.lab_number)
        self.assertEqual(
            datetime(2014, 11, 12, 16, 0), result_2.observation_datetime
        )
        self.assertEqual(
            datetime(2014, 11, 12, 16, 6), result_2.request_datetime
        )
        self.assertEqual("FINAL", result_2.result_status)
        self.assertEqual("FBCZ", result_2.profile_code)


class TestPatientUpdate(GlossTestCase):
    def setUp(self):
        super(TestPatientUpdate, self).setUp()
        self.message_processor = MessageProcessor()
        self.patient = self.create_patient("50092915", "uclh")
        self.session.add(self.patient)

    def test_patient_update(self):
        self.message_processor.process_message(read_message(PATIENT_UPDATE))
        patient = self.session.query(Patient).one()
        self.assertEqual("TESTING MEDCHART", patient.surname)
        self.assertEqual("MEDHCART FIRSTNAME", patient.first_name)
        self.assertEqual("MEDCHART JONES", patient.middle_name)
        self.assertEqual("MR", patient.title)
        self.assertEqual("N2 9DU", patient.post_code)
        self.assertEqual("P816881", patient.gp_practice_code)
        self.assertEqual("British", patient.ethnicity)
        self.assertIsNone(patient.date_of_death)

    def test_patient_death(self):
        self.message_processor.process_message(read_message(PATIENT_DEATH))
        patient = self.session.query(Patient).one()
        self.assertEqual("TESTING MEDCHART", patient.surname)
        self.assertEqual("MEDHCART FIRSTNAME", patient.first_name)
        self.assertEqual("MEDCHART JONES", patient.middle_name)
        self.assertEqual("MR", patient.title)
        self.assertEqual(date(2014, 11, 1), patient.date_of_death)

    def test_patient_only_update_known_patients(self):
        self.session.query(Subscription).delete()
        self.message_processor.process_message(read_message(PATIENT_DEATH))
        patient = self.session.query(Patient).one()
        self.assertEqual("Smith", patient.surname)
        self.assertEqual("Jane", patient.first_name)
        self.assertEqual(None, patient.middle_name)
        self.assertEqual("Ms", patient.title)
        self.assertEqual(date(1983, 12, 12), patient.date_of_birth)


    def test_only_update_with_existent_fields(self):
        messages = [PatientUpdateMessage(
            first_name="Mary"
        )]
        container = MessageContainer(
            message_type=PatientUpdateMessage,
            messages=messages,
            hospital_number="50092915",
            issuing_source="uclh"
        )
        subscription = UclhPatientUpdateSubscription()
        subscription.notify(container)
        patient = self.session.query(Patient).one()

        # only update first name
        self.assertEqual("Mary", patient.first_name)
        self.assertEqual("Smith", patient.surname)
        self.assertEqual(None, patient.middle_name)
        self.assertEqual("Ms", patient.title)
        self.assertEqual(date(1983, 12, 12), patient.date_of_birth)
