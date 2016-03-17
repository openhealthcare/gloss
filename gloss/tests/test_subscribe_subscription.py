"""
Unittests for gloss.subscribe.subscription
"""
from gloss.tests.core import GlossTestCase

from gloss.subscribe.subscription import Subscription

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
