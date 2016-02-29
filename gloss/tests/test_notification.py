"""
Unittests for gloss.notification
"""
from mock import patch, MagicMock

from gloss.tests.core import GlossTestCase

from gloss import notification

class SendDownstreamTestCase(GlossTestCase):

    def test_has_no_method_for_protocol(self):
        class Thing(object): pass
        with self.assertRaises(ValueError):
            notification.send_downstream(('http:/foo/', 'OPAL'), Thing())

    @patch('gloss.notification.requests.post')
    def test_calls_to_protocol(self, post):
        mock_message = MagicMock(name='Mock Message')
        mock_message.to_OPAL.return_value = '{"some": "JSON"}'

        notification.send_downstream(('http://foo/', 'OPAL'), mock_message)

        mock_message.to_OPAL.assert_called_once_with()
        post.assert_called_once_with('http://foo/', json='{"some": "JSON"}')

class NotifyTestCase(GlossTestCase):

    @patch('gloss.notification.settings')
    def test_notify_checks_for_passthrough(self, settings):
        mock_message = MagicMock(name='Mock Message')
        settings.PASSTHROUGH_SUBSCRIPTIONS = {'OPAL_APP1': [('http://OPALAPP2/', 'OPAL')]}

        with patch.object(notification, 'send_downstream') as downstream:

            notification.notify('OPAL_APP1', mock_message)
            downstream.assert_called_once_with(('http://OPALAPP2/', 'OPAL'), mock_message)
