from datetime import datetime
from mock import patch, MagicMock
from gloss.tests.core import GlossTestCase
from sites.rfh.test_database_constructor.pathology_data import PATHOLOGY_DATA
from gloss import message_type
from sites.rfh.information_source import InformationSource


class InformationSourceTestCase(GlossTestCase):
    def setUp(self):
        super(InformationSourceTestCase, self).setUp()
        self.information_source = InformationSource()

    def test_cast_to_message_container(self):
        with patch.object(self.information_source, "get_rows") as get_rows:
            get_rows.side_effect = lambda x: [y for y in PATHOLOGY_DATA if y["Patient_Number"] == x]
            message_container = self.information_source.patient_information(
                'issuing_identifier', '20552710'
            )
        assert(message_container.hospital_number == '20552710')
        assert(message_container.issuing_source == 'rfh')
        assert(len(message_container.messages) == 7)

    def test_cast_patient(self):
        with patch.object(self.information_source, "get_rows") as get_rows:
            get_rows.side_effect = lambda x: [y for y in PATHOLOGY_DATA if y["Patient_Number"] == x]
            message_container = self.information_source.patient_information(
                'issuing_identifier', '20552710'
            )
            patient = next(
                message for message in message_container.messages if message.__class__ == message_type.PatientMessage
            )
        assert(patient.surname == 'ZZZTEST')
        assert(patient.first_name == 'TEST')
        assert(patient.sex == 'Female')
        assert(patient.title == None)

    def test_cast_result(self):
        # lets just check the first result
        with patch.object(self.information_source, "get_rows") as get_rows:
            get_rows.side_effect = lambda x: [y for y in PATHOLOGY_DATA if y["Patient_Number"] == x]
            message_container = self.information_source.patient_information(
                'issuing_identifier', '20552710'
            )
        result = next(
            message for message in message_container.messages if message.__class__ == message_type.ResultMessage
        )
        assert(result.lab_number == '0013I245895_2')
        assert(result.last_edited == datetime(2015, 7, 18, 17, 0, 2, 240000))
        assert(result.observation_datetime == datetime(2015, 7, 18, 16, 26))
        observation = result.observations[0]
        assert(observation.observation_value == 'Negative')
        assert(observation.reference_range == ' -')
        assert(observation.result_status == 'Final')
        assert(observation.test_code == 'AN5')
        assert(observation.test_name == 'Brain homogenate Western blot')
        assert(observation.units == '')
        assert(observation.external_identifier == '20334305')


    @patch('sites.rfh.information_source.settings')
    @patch('sites.rfh.information_source.pytds')
    def test_read_row(self, pytds, settings):
        settings.db_username = "username"
        settings.db_password = "password"
        settings.server = "server"
        settings.database = "database"

        cur = MagicMock(name="cur")
        cur.fetch_many.return_value = "some results"
        conn = MagicMock(name="conn")
        conn.cursor().__enter__ = MagicMock(return_value=cur)
        pytds.connect().__enter__ = MagicMock(return_value=conn)
        assert(self.information_source.get_rows("some identifier") == "some results")
        assert(pytds.connect.call_args[0] == (
            'server', 'database', 'username', 'password'
        ))
        found_query = cur.execute.call_args[0][0]
        expected_query = """
            select * from tQuest_Pathology_Result_View where Patient_Number='some identifier' ORDER BY Event_Date
        """.strip()
        assert(found_query == expected_query)
