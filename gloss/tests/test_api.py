"""
Unittests for gloss.api
"""
import json

from gloss import models
from gloss.tests.core import GlossTestCase

from gloss import api

NOPE = '{"status": "error", "data": "We\'ve not implemented this yet - sorry"}'

class PatientQueryTestCase(GlossTestCase):
    def test_not_found(self):
        msg = '{"status": "error", "data": "We can\'t find any patients with that identifier"}'
        resp = api.patient_query('555-nope')
        self.assertEqual(msg, resp.data)

    def test_with_patient(self):
        self.session.add(self.create_patient('555-yeppers', 'uclh'))

        resp = api.patient_query('555-yeppers')
        data = json.loads(resp.data)

        demographics = [{
            'first_name': 'Jane',
            'surname': 'Smith',
            'middle_name': None,
            'title': 'Ms',
            'date_of_birth': '12/12/1983'
        }]

        self.assertEqual('success', data['status'])
        self.assertEqual(demographics, data['data']['demographics'])
        self.assertEqual([], data['data']['results'])

class DemographicsCreateTestCase(GlossTestCase):
    def test_unimplemented(self):
        resp = api.demographics_create()
        self.assertEqual(NOPE, resp.data)


class DemographicsQueryTestCase(GlossTestCase):
    def test_not_found(self):
        msg = '{"status": "error", "data": "We can\'t find any patients with that identifier"}'
        resp = api.demographics_query('555-nope')
        self.assertEqual(msg, resp.data)

    def test_with_patient(self):
        self.session.add(self.create_patient('555-yeppers', 'uclh'))

        resp = api.demographics_query('555-yeppers')
        data = json.loads(resp.data)

        demographics = [{
            'first_name': 'Jane',
            'surname': 'Smith',
            'middle_name': None,
            'title': 'Ms',
            'date_of_birth': '12/12/1983'
        }]

        self.assertEqual('success', data['status'])
        self.assertEqual(demographics, data['data']['demographics'])


class SubscribeTestCase(GlossTestCase):
    def test_subscription(self):
        resp = api.subscribe(
            "1", "http://someOpalApplication/api"
        )
        subscription = models.Subscription.query_from_identifier(
            "1", "uclh", self.session
        ).one()
        self.assertEqual(
            subscription.end_point, "http://someOpalApplication/api"
        )
        self.assertTrue(subscription.active)
        self.assertTrue(json.loads(resp.data)["status"], "success")

        resp = api.unsubscribe("1")

        subscription = models.Subscription.query_from_identifier(
            "1", "uclh", self.session
        ).one()
        self.assertEqual(
            subscription.end_point, "http://someOpalApplication/api"
        )
        self.assertFalse(subscription.active)
        self.assertTrue(json.loads(resp.data)["status"], "success")

    def test_unsubscribe_when_no_subscription(self):
        self.assertEqual(0, self.session.query(models.Subscription).count())
        resp = api.unsubscribe("1")
        self.assertTrue(json.loads(resp.data)["status"], "success")
        self.assertEqual(0, self.session.query(models.Subscription).count())

    def test_multiple_subsciptions(self):
        api.subscribe(
            "1", "http://someOpalApplication/api"
        )
        api.subscribe(
            "1", "http://someOpalApplication/api"
        )
        subscription = models.Subscription.query_from_identifier(
            "1", "uclh", self.session
        ).one()
        self.assertEqual(
            subscription.end_point, "http://someOpalApplication/api"
        )
        self.assertTrue(subscription.active)
