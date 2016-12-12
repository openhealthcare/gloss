from datetime import datetime
from mock import patch, MagicMock
from gloss.tests.core import GlossTestCase
from gloss.sites.rfh.test_database_constructor.pathology_data import PATHOLOGY_DATA
from gloss.sites.rfh.importers import sql_importer
from gloss import message_type


@patch("gloss.sites.rfh.importers.sql_importer.get_rows")
class SQLImporterTestCase(GlossTestCase):
    def test_cast_to_message_container(self, get_rows):
        get_rows.side_effect = lambda x: [y for y in PATHOLOGY_DATA if y["Patient_Number"] == x]
        message_container = sql_importer.patient_information('20552710')
        assert(message_container.hospital_number == '20552710')
        assert(message_container.issuing_source == 'rfh')
        assert(len(message_container.messages) == 7)

    def test_cast_patient(self, get_rows):
        get_rows.side_effect = lambda x: [y for y in PATHOLOGY_DATA if y["Patient_Number"] == x]
        message_container = sql_importer.patient_information('20552710')
        patient = next(
            message for message in message_container.messages if message.__class__ == message_type.PatientMessage
        )
        assert(patient.surname == 'ZZZTEST')
        assert(patient.first_name == 'TEST')
        assert(patient.sex == 'Female')
        assert(patient.title == None)

    def test_cast_result(self, get_rows):
        # lets just check the first result
        get_rows.side_effect = lambda x: [y for y in PATHOLOGY_DATA if y["Patient_Number"] == x]
        message_container = sql_importer.patient_information('20552710')
        result = next(
            message for message in message_container.messages if message.__class__ == message_type.ResultMessage
        )
        assert(result.lab_number == '0013I245895_2')
        assert(result.last_edited == datetime(2015, 7, 18, 17, 0, 2, 240000))
        assert(result.observation_datetime == datetime(2015, 7, 18, 16, 26))
        observation = result.observations[0]
        assert(observation["observation_value"] == 'Negative')
        assert(observation["reference_range"] == ' -')
        assert(observation["result_status"] == 'Final')
        assert(observation["test_code"] == 'AN5')
        assert(observation["test_name"] == 'Brain homogenate Western blot')
        assert(observation["units"] == '')
