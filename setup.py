import os
import re
from setuptools import setup, find_packages

long_desc = """
Gloss is an integration engine for healthcare applications.

Gloss is a Twisted server that can translate and route HL7 messages,
batch file uploads and OPAL JSON messages.

Source code and documentation available at https://github.com/openhealthcare/gloss/
"""

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

HERE = os.path.realpath(os.path.dirname(__file__))

VERSION_FILE = os.path.join(HERE, "gloss/_version.py")
verstrline = open(VERSION_FILE, "rt").read()
VSRE = r'^__version__ = [\'"]([^\'"]*)[\'"]'
mo = re.search(VSRE,  verstrline, re.M)
if mo:
    VERSION = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in {0}".format(VERSION_FILE))


setup(
    name='glossolalia',
    version=VERSION,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    license='GPL3',  # example license
    description='An integration engine for healthcare applications.',
    long_description=long_desc,
    url='http://openhealthcare.org.uk/',
    author='Open Health Care UK',
    author_email='hello@openhealthcare.org.uk',
    install_requires=[
        'SQLAlchemy==1.0.12',
        'Twisted==15.5.0',
        'hl7==0.3.3',
        'python-dateutil==2.4.2',
        'pytz==2015.7',
        'txHL7==0.3.0',
        ]
)
