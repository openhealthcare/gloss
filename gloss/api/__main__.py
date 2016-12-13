from gloss.api import app
from gloss.conf import settings
import os
import sys

if __name__ == '__main__':
    if not len(sys.argv):
        raise ValueError("please pass in the name of that app that you wish to run")

    # Bind to PORT if defined, otherwise default to 6767
    port = int(os.environ.get('PORT', settings.GLOSS_API_PORT))
    app.run(host=settings.GLOSS_API_HOST, port=port)
