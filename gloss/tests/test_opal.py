from gloss.tests.core import GlossTestCase
from mock import patch, MagicMock
from gloss.serialisers.opal import send_to_opal, OpalJSONSerialiser
from datetime import datetime, date
import json


class OpalTestCase(GlossTestCase):
    def test_json_serialiser(self):
        as_dict = {
            "a": datetime(2000, 2, 1, 10, 20),
            "b": date(2001, 3, 4)
        }
        found = json.loads(json.dumps(as_dict, cls=OpalJSONSerialiser))
        self.assertEqual(found["a"], "01/02/2000 10:20:00")
        self.assertEqual(found["b"], "04/03/2001")


    @patch("gloss.serialisers.opal.Logger")
    def test_send_to_opal(self, logger_mock):
        message_container = MagicMock()
        message_container.to_dict = MagicMock()
        message_container.to_dict.return_value = {"a": "dict"}
        response = MagicMock()
        response.status_code = 400
        self.mock_requests_post.return_value = response
        log = MagicMock()
        logger_mock.return_value = log
        log.error = MagicMock()
        send_to_opal(message_container, "fake")
        expected_msg = "failed to send to elcid with 400"
        log.error.assert_called_once_with(expected_msg)
        self.mock_requests_post.assert_called_once_with(
            "fake", json=json.dumps({"a": "dict"})
        )
