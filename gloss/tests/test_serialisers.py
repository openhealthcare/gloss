from unittest import TestCase
from datetime import date, datetime
import json
from mock import patch, MagicMock
from gloss.tests.core import GlossTestCase
from gloss.serialisers.opal import OpalJSONSerialiser, send_to_opal


class JsonSerialiserTestCase(TestCase):
    def test_date_serialisation(self):
        input_dict = dict(
            today=date(2016, 03, 11),
            now=datetime(2016, 03, 11, 10, 10)
        )
        expected_dict = dict(
            today="11/03/2016",
            now="11/03/2016 10:10:00"
        )

        input_json = json.dumps(input_dict, cls=OpalJSONSerialiser)
        self.assertEqual(expected_dict, json.loads(input_json))


@patch('gloss.serialisers.opal.settings')
@patch("requests.post")
class SendDownstreamTestCase(GlossTestCase):
    def test_send_down_stream(self, post_mock, settings_mock):
        settings_mock.PASSTHROUGH_SUBSCRIPTIONS = {'foo': 'http://fee.com/'}
        message_container = MagicMock()
        message_container.issuing_source = "foo"
        message_container.to_dict = MagicMock(return_value={"fee": "fo"})
        message_container.hospital_number = "1"
        send_to_opal(message_container, 'http://fee.com/')
        self.assertTrue(message_container.to_dict.called)
        post_mock.assert_called_once_with(
            'http://fee.com/', json='{"fee": "fo"}'
        )
