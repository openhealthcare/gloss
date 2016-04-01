import datetime
from unittest import TestCase

from gloss.tests.test_messages import (
    COMPLEX_WINPATH_RESULT, read_message
)
from gloss.import_message import WinPathResults
from gloss import message_type

expected = {'hospital_number': u'50031772',
 'issuing_source': 'uclh',
 'messages': {"result": [{
                        'lab_number': u'98U000057',
                        'last_edited': datetime.datetime(2014, 11, 12, 16, 8),
                        'observation_datetime': datetime.datetime(2014, 11, 12, 16, 0),
                        'external_identifier': "98U000057.FBCY",
                        'observations': [{
                                 'comments': None,
                                 'observation_value': u'8.00',
                                 'reference_range': u'3.0-10.0',
                                 'result_status': None,
                                 'test_code': u'WCC',
                                 'test_name': u'White cell count',
                                 'units': u'x10^9/L',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'3.20',
                                 'reference_range': u'4.4-5.8',
                                 'result_status': None,
                                 'test_code': u'RCC',
                                 'test_name': u'Red cell count',
                                 'units': u'x10^12/L',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'87',
                                 'reference_range': None,
                                 'result_status': None,
                                 'test_code': u'HBGL',
                                 'test_name': u'Haemoglobin (g/L)',
                                 'units': u'g/L',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'0.350',
                                 'reference_range': u'0.37-0.50',
                                 'result_status': None,
                                 'test_code': u'HCTU',
                                 'test_name': u'HCT',
                                 'units': u'L/L',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'78.0',
                                 'reference_range': u'80-99',
                                 'result_status': None,
                                 'test_code': u'MCVU',
                                 'test_name': u'MCV',
                                 'units': u'fL',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'28.0',
                                 'reference_range': u'27.0-33.5',
                                 'result_status': None,
                                 'test_code': u'MCHU',
                                 'test_name': u'MCH',
                                 'units': u'pg',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'300',
                                 'reference_range': None,
                                 'result_status': None,
                                 'test_code': u'MCGL',
                                 'test_name': u'MCHC (g/L)',
                                 'units': u'g/L',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'17.0',
                                 'reference_range': u'11.5-15.0',
                                 'result_status': None,
                                 'test_code': u'RDWU',
                                 'test_name': u'RDW',
                                 'units': u'%',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'250',
                                 'reference_range': u'150-400',
                                 'result_status': None,
                                 'test_code': u'PLT',
                                 'test_name': u'Platelet count',
                                 'units': u'x10^9/L',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'10.0',
                                 'reference_range': u'7-13',
                                 'result_status': None,
                                 'test_code': u'MPVU',
                                 'test_name': u'MPV',
                                 'units': u'fL',
                                 'value_type': u'NM'}],
               'profile_code': u'FBCY',
                   'profile_description': u'FULL BLOOD COUNT',
                   'request_datetime': datetime.datetime(2014, 11, 12, 16, 6),
               'result_status': 'FINAL'},
              {'lab_number': u'98U000057',
               'external_identifier': "98U000057.FBCZ",
               'last_edited': datetime.datetime(2014, 11, 12, 16, 9),
               'observation_datetime': datetime.datetime(2014, 11, 12, 16, 0),
               'observations': [{'comments': None,
                                 'observation_value': u'55.0%  4.40',
                                 'reference_range': u'2.0-7.5',
                                 'result_status': None,
                                 'test_code': u'NE',
                                 'test_name': u'Neutrophils',
                                 'units': u'x10^9/L',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'25.0%  2.00',
                                 'reference_range': u'1.2-3.65',
                                 'result_status': None,
                                 'test_code': u'LY',
                                 'test_name': u'Lymphocytes',
                                 'units': u'x10^9/L',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'15.0%  1.20',
                                 'reference_range': u'0.2-1.0',
                                 'result_status': None,
                                 'test_code': u'MO',
                                 'test_name': u'Monocytes',
                                 'units': u'x10^9/L',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'3.0%  0.24',
                                 'reference_range': u'0.0-0.4',
                                 'result_status': None,
                                 'test_code': u'EO',
                                 'test_name': u'Eosinophils',
                                 'units': u'x10^9/L',
                                 'value_type': u'NM'},
                                {'comments': None,
                                 'observation_value': u'2.0%  0.16',
                                 'reference_range': u'0.0-0.1',
                                 'result_status': None,
                                 'test_code': u'BA',
                                 'test_name': u'Basophils',
                                 'units': u'x10^9/L',
                                 'value_type': u'NM'}],
               'profile_code': u'FBCZ',
               'profile_description': u'DIFFERENTIAL',
               'request_datetime': datetime.datetime(2014, 11, 12, 16, 6),
               'result_status': 'FINAL'}]}}


class TestToDict(TestCase):
    def test_pathology_to_dict(self):
        msg = read_message(COMPLEX_WINPATH_RESULT)
        message_container = WinPathResults(msg).construct_container()
        result = message_container.to_dict()
        self.assertEqual(result, expected)

    def test_to_dict_function(self):
        class A(message_type.MessageType):
            a = "c"
            def to_dict(self):
                return {"a": "b"}

        self.assertEqual(A().to_dict(), {"a": "b"})

    def test_to_dict_array(self):
        class A(message_type.MessageType):
            def __init__(self, some_value):
                self.c = some_value

        class B(message_type.MessageType):
            def __init__(self, some_value):
                self.x = some_value

        all_a = A([B(1), B(2)])
        self.assertEqual(all_a.to_dict(), {"c": [{"x": 1}, {"x": 2}]})

    def test_nested_dicts(self):
        class A(message_type.MessageType):
            def __init__(self, some_dict):
                self.x = some_dict

        a = A({"b": 1})

        self.assertEqual(a.to_dict(), {"x": {"b": 1}})


class ResultMessageTestCase(TestCase):

    def test_result_status_optional(self):
        message = message_type.ResultMessage(
            lab_number='555',
            profile_code='BC',
            profile_description='BLOOD COUNT',
            request_datetime='yesterday',
            observation_datetime='yesterday',
            last_edited='yesterday',
            observations=[]
        )
        self.assertTrue(message.result_status is None)

    def test_add_external_identifier(self):
        message = message_type.ResultMessage(
            lab_number='555',
            profile_code='BC',
            profile_description='BLOOD COUNT',
            request_datetime='yesterday',
            observation_datetime='yesterday',
            last_edited='yesterday',
            observations=[]
        )
        result = message.to_dict()
        self.assertEqual(result["external_identifier"], "555.BC")
