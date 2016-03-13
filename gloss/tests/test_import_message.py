from gloss.tests.core import GlossTestCase
from mock import patch, MagicMock
from gloss.import_message import MessageProcessor
from gloss.models import Error


class TestMessageImporter(GlossTestCase):

    @patch.object(MessageProcessor, "get_message_type")
    def test_error_saving(self, get_message_type_mock):
        message_type = MagicMock()
        get_message_type_mock.return_value = MagicMock(
            return_value=message_type
        )
        message_type.process = MagicMock(side_effect=ValueError('Fail'))
        message_processor = MessageProcessor()
        message_processor.process_message("some string")
        self.assertTrue(message_type.process)
        error = self.session.query(Error).one()
        self.assertEqual(error.message, "some string")
        self.assertEqual(error.error, "Fail")

    @patch.object(MessageProcessor, "get_message_type")
    def test_database_saving_throws_an_error(self, get_message_type_mock):
        message_type = MagicMock()
        get_message_type_mock.return_value = MagicMock(
            return_value=message_type
        )
        message_type.process = MagicMock(side_effect=ValueError('Fail'))
        message_processor = MessageProcessor()
        with patch.object(self.session, "add") as add_mock:
            add_mock.side_effect = ValueError("DB fail")
            message_processor.process_message("some string")
            self.assertTrue(message_type.process)
            error_count = self.session.query(Error).count()
            self.assertEqual(error_count, 0)
