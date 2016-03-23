"""
Unittests for gloss.subscribe.subscription
"""
from mock import patch, MagicMock
from gloss.tests.core import GlossTestCase
from gloss.subscribe.subscription import Subscription, NotifyOpalWhenSubscribed
from gloss.models import subscribe


class SubscriptionTestCase(GlossTestCase):

    def test_issuing_source(self):
        with self.assertRaises(NotImplementedError):
            Subscription().issuing_source

    def test_serialise(self):
        with self.assertRaises(NotImplementedError):
            Subscription().serialise()

    def test_process_data(self):
        with self.assertRaises(NotImplementedError):
            Subscription().process_data()

    def test_notify(self):
        with self.assertRaises(NotImplementedError):
            Subscription().notify(None)


@patch('gloss.subscribe.subscription.settings')
@patch('gloss.subscribe.subscription.send_to_opal')
class NotifyOpalWhenSubscribedTestCase(GlossTestCase):

    def test_send_down_stream_if_subscribed(
        self, send_to_opal_mock, settings_mock
    ):
        settings_mock.SEND_ALL_MESSAGES = None
        notify_opal_when_subscribed = NotifyOpalWhenSubscribed()
        mock_message_container = MagicMock(name="message_container")
        mock_message_container.hospital_number = "1"
        subscribe("1", "/foo/", self.session, "uclh")
        notify_opal_when_subscribed.notify_async(mock_message_container)
        send_to_opal_mock.assert_called_once_with(
            mock_message_container, "/foo/"
        )

    def test_send_down_stream_if_settings(
        self, send_to_opal_mock, settings_mock
    ):
        settings_mock.SEND_ALL_MESSAGES = "/foo/"
        notify_opal_when_subscribed = NotifyOpalWhenSubscribed()
        mock_message_container = MagicMock(name="message_container")
        mock_message_container.hospital_number = "1"
        notify_opal_when_subscribed.notify_async(mock_message_container)
        send_to_opal_mock.assert_called_once_with(
            mock_message_container, "/foo/"
        )

    def test_dont_send_down_stream(
        self, send_to_opal_mock, settings_mock
    ):
        settings_mock.SEND_ALL_MESSAGES = None
        notify_opal_when_subscribed = NotifyOpalWhenSubscribed()
        mock_message_container = MagicMock(name="message_container")
        mock_message_container.hospital_number = "1"
        notify_opal_when_subscribed.notify_async(mock_message_container)
        self.assertFalse(send_to_opal_mock.called)
