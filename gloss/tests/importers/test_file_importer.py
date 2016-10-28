"""
Unittests for gloss.translate.files
"""
from gloss.tests.core import GlossTestCase

from gloss.importers import file_importer


class FileTypeTestCase(GlossTestCase):
    def test_init_path(self):
        file_type = file_importer.FileType("somePath")
        self.assertEqual(file_type.path, "somePath")
