"""
Errors and exceptions for Gloss
"""

class Error(Exception): pass

class APIError(Error):

    def __init__(self, msg, *a, **kw):
        self.msg = msg
        super(APIError, self).__init__(*a, **kw)
