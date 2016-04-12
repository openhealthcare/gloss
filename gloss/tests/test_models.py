"""
Unittests for gloss.models
"""
from mock import patch
from datetime import datetime, timedelta

from gloss.tests.core import GlossTestCase
from gloss import message_type

from gloss.models import (
    GlossolaliaReference, Subscription, PatientIdentifier,
    is_subscribed, get_gloss_reference, session_scope,
    OutgoingMessage, get_next_message_id, patient_to_message_container,
    InpatientLocation, subscribe, Merge, Patient
)


class SessionScopeTestCase(GlossTestCase):
    def test_rollback(self):
        with patch.object(self.session, "add", side_effect=ValueError('Fail')):
            with patch.object(self.session, "rollback") as rollback:
                with self.assertRaises(ValueError):
                    with session_scope() as s:
                        s.add(None)
                rollback.assert_called_once_with()


class IsSubscribedTestCase(GlossTestCase):
    def setUp(self):
        super(IsSubscribedTestCase, self).setUp()
        self.glossolalia_reference = GlossolaliaReference()
        self.session.add(self.glossolalia_reference)

    def test_is_subscribed(self):
        subscription = Subscription(
            system="elcid", gloss_reference=self.glossolalia_reference
        )
        self.session.add(subscription)

        hospital_identifier = PatientIdentifier(
            identifier="12341234",
            issuing_source="uclh",
            gloss_reference=self.glossolalia_reference
        )
        self.session.add(hospital_identifier)
        subscribed = is_subscribed("12341234", session=self.session)
        assert(subscribed)

    def test_is_not_subscribed(self):
        glossolalia_reference = GlossolaliaReference()
        self.session.add(glossolalia_reference)

        subscription = Subscription(
            system="elcid",
            gloss_reference=self.glossolalia_reference,
            active=False
        )
        self.session.add(subscription)

        hospital_identifier = PatientIdentifier(
            identifier="12341234",
            issuing_source="uclh",
            gloss_reference=glossolalia_reference
        )
        self.session.add(hospital_identifier)
        subscribed = is_subscribed("12341234", session=self.session)
        assert(not subscribed)


class GetGlossIdTestCase(GlossTestCase):
    def setUp(self):
        super(GetGlossIdTestCase, self).setUp()
        self.glossolalia_reference = GlossolaliaReference()
        self.session.add(self.glossolalia_reference)

    def test_get_gloss_reference(self):
        hospital_identifier = PatientIdentifier(
            identifier="12341234",
            issuing_source="uclh",
            gloss_reference=self.glossolalia_reference
        )
        self.session.add(hospital_identifier)
        glossolalia_reference = get_gloss_reference("12341234", self.session)
        self.assertEqual(self.glossolalia_reference, glossolalia_reference)

    def test_return_none(self):
        self.assertTrue(get_gloss_reference("2342334", self.session) is None)


class GetOutgoingMessageIdTestCase(GlossTestCase):
    def test_creates_a_unique_id(self):
        self.assertEqual(self.session.query(OutgoingMessage).count(), 0)
        self.assertEqual(get_next_message_id(), 1)
        self.assertEqual(self.session.query(OutgoingMessage).count(), 1)
        self.assertEqual(get_next_message_id(), 2)
        self.assertEqual(self.session.query(OutgoingMessage).count(), 1)


class InpatientLocationTestCase(GlossTestCase):

    def setUp(self):
        super(InpatientLocationTestCase, self).setUp()
        self.inpatient_admission = self.get_inpatient_admission(
            "hospital_number", "asd"
        )
        self.session.add(self.inpatient_admission)

    def test_get_location_with_no_locations(self):
        location = InpatientLocation.get_latest_location(
            self.inpatient_admission, self.session
        )
        self.assertIsNone(location)

    def test_get_locations_with_multiple_locations(self):
        location_1 = self.get_inpatient_location(self.inpatient_admission)
        location_1.datetime_of_transfer = datetime.now() - timedelta(1)
        self.session.add(location_1)

        location_2 = self.get_inpatient_location(self.inpatient_admission)
        self.session.add(location_2)

        found_location = InpatientLocation.get_latest_location(
            self.inpatient_admission, self.session
        )

        self.assertEqual(found_location, location_2)

    def test_get_location_in_the_past(self):
        location = self.get_inpatient_location(self.inpatient_admission)
        location.datetime_of_transfer = datetime.now() - timedelta(1)
        self.session.add(location)

        found_location = InpatientLocation.get_latest_location(
            self.inpatient_admission, self.session
        )

        self.assertEqual(found_location, location)

    def test_get_location_current(self):
        location = self.get_inpatient_location(self.inpatient_admission)
        self.session.add(location)

        found_location = InpatientLocation.get_latest_location(
            self.inpatient_admission, self.session
        )

        self.assertEqual(found_location, location)


class PatientToMessageContainersTestCase(GlossTestCase):

    def test_creates_only_patient_container(self):
        """ creates only a container with no allergies, only patient details
        """
        patient = self.create_patient("50092915", "uclh")
        self.session.add(patient)
        message_container = patient_to_message_container(
            "50092915", "uclh", self.session
        )
        self.assertEqual(len(message_container.messages), 1)
        self.assertEqual(
            message_container.messages[0].__class__,
            message_type.PatientMessage
        )

    def test_with_episode_admission(self):
        """ episode admission is a compound model of the latest
            episode location and the admission.

            location on the other hand should not be serialised
            as its already included in the admission.
        """
        patient = self.create_patient("50092915", "uclh")
        self.session.add(patient)

        inpatient_admission = self.get_inpatient_admission("50092915", "uclh")
        self.session.add(inpatient_admission)

        inpatient_location_1 = self.get_inpatient_location(inpatient_admission)
        inpatient_location_1.bed_code = "old-bed"
        inpatient_location_1.datetime_of_transfer = datetime.now() - timedelta(1)

        inpatient_location_2 = self.get_inpatient_location(inpatient_admission)
        inpatient_location_2.bed_code = "new-bed"
        self.session.add(inpatient_location_2)

        message_container = patient_to_message_container(
            "50092915", "uclh", self.session
        )

        self.assertEqual(len(message_container.messages), 2)

        self.assertEqual(
            message_container.messages[0].__class__, message_type.PatientMessage
        )

        found_admission = message_container.messages[1]
        self.assertEqual(found_admission.ward_code, "BBNU")
        self.assertEqual(found_admission.room_code, "BCOT")
        self.assertEqual(found_admission.bed_code, "new-bed")
        self.assertEqual(found_admission.external_identifier, "940347")
        self.assertEqual(found_admission.datetime_of_admission, datetime(
            2012, 10, 10, 17, 12
        ))
        self.assertEqual(found_admission.datetime_of_discharge, None)
        self.assertEqual(found_admission.admission_diagnosis, "vertigo")

    def test_some_models_are_not_serialised(self):
        """ we don't want Merge, Subscription or PatientIdentifier to be
            serialised
        """
        patient = self.create_patient("50092915", "uclh")
        patient.first_name = "Sue"
        self.session.add(patient)
        old_patient = self.create_patient("500929150-old", "uclh")
        self.session.add(old_patient)
        merge = Merge(old_reference=old_patient.gloss_reference)
        self.session.add(merge)
        subscribe("50092915", "some_end_point", self.session, "uclh")

        message_container = patient_to_message_container(
            "50092915", "uclh", self.session
        )
        self.assertEqual(len(message_container.messages), 1)
        patient_message = message_container.messages[0]
        self.assertEqual(patient_message.first_name, "Sue")

    def test_allergies_serialisation(self):
        patient = self.create_patient("50092915", "uclh")
        self.session.add(patient)
        allergy = self.get_allergy("50092915", "uclh")
        self.session.add(allergy)
        message_container = patient_to_message_container(
            "50092915", "uclh", self.session
        )

        self.assertEqual(len(message_container.messages), 2)

        self.assertEqual(
            message_container.messages[0].__class__,
            message_type.PatientMessage
        )

        found_allergy = message_container.messages[1]
        expected_dict = self.get_allergy_dict()

        for k, v in expected_dict.iteritems():
            self.assertEqual(getattr(found_allergy, k), v)

    def test_results_serialisation(self):
        patient = self.create_patient("50092915", "uclh")
        self.session.add(patient)
        result = self.get_result("50092915", "uclh")
        self.session.add(result)
        message_container = patient_to_message_container(
            "50092915", "uclh", self.session
        )
        #
        # self.assertEqual(len(message_container.messages), 2)
        #
        # self.assertEqual(
        #     message_container.messages[0].__class__,
        #     message_type.PatientMessage
        # )
        #
        # found_result = message_container.messages[1]
        # expected_dict = self.get_result_dict()
        #
        # for k, v in expected_dict.iteritems():
        #     self.assertEqual(getattr(found_result, k), v)



def get_messages(cls, identifier, issuing_source, session):
    import pdb; pdb.set_trace()
    pass


class TestGetMessagesOverride(GlossTestCase):

    @patch("gloss.models.settings")
    def test_message_override(self, settings_mock):
        settings_mock.MOCK_API = "gloss.tests.test_models.get_messages"
        mock_str = "gloss.tests.test_models.get_messages"
        with patch(mock_str) as messages_mock:
            Patient.to_messages("123", "uclh", self.session)

        messages_mock.assert_called_once_with(
            Patient, "123", "uclh", self.session
        )
