"""
Unittests for gloss.models
"""
import json
from mock import patch

from gloss.tests.core import GlossTestCase

from gloss import models
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


class WinPathMessageTestCase(GlossTestCase):
    def test_to_OPAL(self):
        from gloss import process_message
        from gloss.tests import test_messages
        message = test_messages.read_message(test_messages.RESULTS_MESSAGE)
        results = process_message.WinPathResults(message)

        as_dict = {
                'lab_number': u'10U111970',
                'profile_code': u'ELU',
                'profile_description': u'RENAL PROFILE',
                'request_datetime': '2014/01/17 20:45',
                'observation_datetime': '2014/01/17 17:00',
                'last_edited': '2014/01/17 22:58',
                'result_status': 'FINAL',
                'observations': [
                    {
                        'value_type': u'NM',
                        'test_code': u'NA',
                        'test_name': u'Sodium',
                        'observation_value': u'143',
                        'units': u'mmol/L',
                        'reference_range': u'135-145',
                        'result_status': 'FINAL'
                    },
                    {
                        'value_type': u'NM',
                        'test_code': u'K',
                        'test_name': u'Potassium',
                        'observation_value': u'3.9',
                        'units': u'mmol/L',
                        'reference_range': u'3.5-5.1',
                        'result_status': 'FINAL'
                    },
                    {
                        'value_type': u'NM',
                        'test_code': u'UREA',
                        'test_name': u'Urea',
                        'observation_value': u'3.9',
                        'units': u'mmol/L',
                        'reference_range': u'1.7-8.3',
                        'result_status': 'FINAL'
                    },
                    {
                        'value_type': u'NM',
                        'test_code': u'CREA',
                        'test_name': u'Creatinine',
                        'observation_value': u'61',
                        'units': u'umol/L',
                        'reference_range': u'49-92',
                        'result_status': 'FINAL'
                    },
                    {
                        'value_type': u'NM',
                        'test_code': u'GFR',
                        'test_name': u'Estimated GFR',
                        'observation_value': u'>90',
                        'units': u'.',
                        'reference_range': None,
                        'result_status': 'FINAL'
                    }
                ]
            }

        result = models.WinPathMessage(results).to_OPAL()
        obs = result['data'].pop('observations')
        self.assertEqual(as_dict['observations'], json.loads(obs))
        for k in result['data']:
            self.assertEqual(as_dict[k], result['data'][k])
