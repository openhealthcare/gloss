from mock import patch
from gloss.information_source import InformationSource
from gloss.tests.core import GlossTestCase
from gloss import exceptions


@patch("gloss.information_source.post_message_for_identifier")
class InformationSourceTestCase(GlossTestCase):
    def setUp(self):
        super(InformationSourceTestCase, self).setUp()
        self.information_source = InformationSource()

    def test_patient_information_with_patient(self, post_message):
        self.session.add(self.create_patient('555-yeppers', 'test'))
        patient_messages = self.information_source.patient_information('test', '555-yeppers')
        self.assertEqual(patient_messages.hospital_number, '555-yeppers')
        self.assertFalse(post_message.called)

    def test_patient_information_without_patient(self, post_message):
        self.session.add(self.get_allergy('555-yeppers', 'test'))
        patient = self.create_patient('555-yeppers', 'test')
        post_message.side_effect = lambda x: self.session.add(patient)
        patient_messages = self.information_source.patient_information('test', '555-yeppers')
        self.assertEqual(patient_messages.hospital_number, '555-yeppers')

    @patch("gloss.information_source.settings")
    def test_dont_get_if_settings(self, settings, post_message):
        settings.USE_EXTERNAL_LOOKUP = False
        with self.assertRaises(exceptions.PatientNotFound):
            self.information_source.patient_information('test', '555-yeppers')

    def test_results_without_patient(self, post_message):
        self.session.add(self.get_allergy('555-yeppers', 'test'))
        patient = self.create_patient('555-yeppers', 'test')
        post_message.side_effect = lambda x: self.session.add(patient)
        patient_messages = self.information_source.result_information('test', '555-yeppers')
        self.assertEqual(patient_messages.hospital_number, '555-yeppers')

    def test_patient_information_with_patient(self, post_message):
        self.session.add(self.create_patient('555-yeppers', 'test'))
        self.session.add(self.get_result('555-yeppers', 'uclh'))
        result_messages = self.information_source.result_information('test', '555-yeppers')
        self.assertEqual(result_messages.hospital_number, '555-yeppers')
        self.assertFalse(post_message.called)
