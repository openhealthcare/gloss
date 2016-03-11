from unittest import TestCase
from gloss.utils import itersubclasses, AbstractClass


class UtilsTest(TestCase):
    def test_tree_structure(self):
        class A(object):
            pass

        class B(A):
            pass

        class C(B, AbstractClass):
            pass

        class D(C):
            pass

        results = {i for i in itersubclasses(A)}
        self.assertEqual(results, set([B, D]))
