from mock import patch, MagicMock
from gloss.sites.uch import mock_api
from gloss.tests.core import GlossTestCase
from gloss.models import Patient, Allergy, Merge
from gloss.message_type import AllergyMessage, PatientMessage


class TestMockPatient(GlossTestCase):
    def test_get_with_allergy(self):
        allergy = self.get_allergy("123123", "uclh")
        self.session.add(allergy)
        result = mock_api.get_mock_data(
            Allergy, "123123", "uclh", self.session
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].__class__, AllergyMessage)
        self.assertEqual(
            result[0].allergen_reference, allergy.allergen_reference
        )

    @patch("gloss.sites.uch.mock_api.nullable")
    def test_with_no_nullable(self, n):
        n.side_effect = lambda x: x()

        result = mock_api.get_mock_data(
            Patient, "123123", "uclh", self.session
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].__class__, PatientMessage)
        self.assertIsNone(result[0].date_of_death)
        self.assertIsNone(result[0].death_indicator)

        for k, v in vars(result[0]).iteritems():
            if not k == "date_of_death" and not k == "death_indicator":
                print "k %s v %s" % (k, v)
                self.assertIsNotNone(getattr(result[0], k))

        self.assertTrue(n.called)

    @patch("gloss.sites.uch.mock_api.random.randint")
    def test_nullable_false(self, randint_mock):
        randint_mock.return_value = 5
        some_func = MagicMock(return_value=3)
        result = mock_api.nullable(some_func)
        self.assertEqual(result, 3)
        self.assertTrue(some_func.called)

    @patch("gloss.sites.uch.mock_api.random.randint")
    def test_nullable_true(self, randint_mock):
        randint_mock.return_value = 1
        some_func = MagicMock(return_value=3)
        result = mock_api.nullable(some_func)
        self.assertIsNone(result)
        self.assertFalse(some_func.called)

    @patch("gloss.models.GlossSubrecord._to_messages")
    def test_with_xxx_demographics(self, to_messages_mock):
        result = mock_api.get_mock_data(
            Patient, "xxx123123", "uclh", self.session
        )
        self.assertEqual(len(result), 0)
        self.assertFalse(to_messages_mock.called)

    def test_create_mock(self):
        mock_api.save_mock_patients("1000000")
        c = Patient.query_from_identifier(
            "1000000", "uclh", self.session
        )
        self.assertEqual(c.count(), 1)
        self.assertEqual(self.session.query(Merge).count(), 0)

    def test_dont_create_mock_with_xxx(self):
        mock_api.save_mock_patients("xxx1000000")
        c = self.session.query(Patient)

        self.assertEqual(c.count(), 0)

    def test_create_merge_with_mmm(self):
        mock_api.save_mock_patients("mmm1000000")
        c = Patient.query_from_identifier(
            "mmm1000000", "uclh", self.session
        ).one()

        m = self.session.query(Merge).filter(
            Merge.gloss_reference == c.gloss_reference
        ).one()

        new_exists = self.session.query(Patient).filter(
            Patient.gloss_reference == m.new_reference
        ).count()
        self.assertTrue(new_exists, 1)
