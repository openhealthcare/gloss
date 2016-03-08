"""
Unittests for gloss.translate.files
"""
from gloss.tests.core import GlossTestCase

from gloss.translate import files

class FileTypeTestCase(GlossTestCase):

    def test_process_file_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            files.FileType(None).process()

class BaseFileRetrieverTestCase(GlossTestCase):

    def test_file_type_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            ft = files.BaseFileRetriever().file_type

    def test_fetch_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            files.BaseFileRetriever().fetch()
