"""
Unittests for gloss.models
"""
from mock import patch

from gloss.tests.core import GlossTestCase
from ..models import (
    GlossolaliaReference, Subscription, PatientIdentifier,
    is_subscribed, get_gloss_reference, session_scope
)


class SessionScopeTestCase(GlossTestCase):

    @patch('gloss.models.Session')
    def test_rollback(self, sess):
        sess.return_value.commit.side_effect = ValueError('Fail')

        with self.assertRaises(ValueError):
            with session_scope() as s:
                s.add(None)

        sess.return_value.rollback.assert_called_with()


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
