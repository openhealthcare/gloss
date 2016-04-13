import os
from gloss.api import app
from gloss.settings import GLOSS_API_PORT, GLOSS_API_HOST

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 6767
    port = int(os.environ.get('PORT', GLOSS_API_PORT))
    app.run(host=GLOSS_API_HOST, port=port)
