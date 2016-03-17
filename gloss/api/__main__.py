import os
from gloss.api import app

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 6767
    port = int(os.environ.get('PORT', 6767))
    app.run(host='0.0.0.0', port=port)
