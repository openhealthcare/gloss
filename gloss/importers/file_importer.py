"""
Gloss to translators for file formats
"""
from gloss.importers.base_importer import SafelImporter


class FileType(SafelImporter):
    """
    Base class for Files that we'll be processing
    with Gloss
    """
    def __init__(self, path):
        self.path = path
