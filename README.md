# Gloss

[![Build Status](https://travis-ci.org/openhealthcare/gloss.svg?branch=master)](https://travis-ci.org/openhealthcare/gloss)
[![Coverage Status](https://coveralls.io/repos/github/openhealthcare/gloss/badge.svg?branch=master)](https://coveralls.io/github/openhealthcare/gloss?branch=master)

Gloss is an integration engine for healthcare applications.

Gloss comprises a Twisted server that can translate and route HL7 over MLLP, a
flask server that speaks OPAL JSON over HTTP, and also abitrary batch file
uploads/imports.

Gloss will also act as a shadow PAS, and includes archiving and demographic
query functionality.

## Getting Started

Some quick instructions to get you started

### Installation

From the source directory

    python setup.py install

You will also need the python dependencies:

    pip install -r requirements.txt

### Starting the server(s)

To run the HL7 server:

    twistd --nodaemon gloss --service [[ class string to the gloss service ]]

alternatively you can set the default gloss settings class in gloss.settings.DEFAULT_GLOSS_SERVICE


To run the OPAL/JSON/HTTP API:

    python -m gloss.api

## How Does Gloss work?

Gloss handles three types of upstream data sources.

  1. Query upstreams (e.g. an HL7 query or a database connection it can make queries via)
  2. Polling upstreams (e.g. reading a file produced by a daily batch process, or polling a server for updates every n minutes)
  3. Event upstreams (e.g. receiving a HL7 message every time a patient is admitted)

Each of these upstream data sources will provide data to a Gloss `Importer` - which take raw data from an upstream source and translate that data into `GlossMessage`s.

Gloss also defines `Subscribers` which perform actions whenever a new `GlossMessage` arrives, from any upstream source. The `Subscrier` is responsible for sending data on downstream, saving information locally, or any other processing that needs to be done.


## Upstream Services

### Event Upstreams

In order to configure Gloss to handle data from an Event Upstream, we define a `Receiver`.

A Receiver is a callable which returns a Twisted service. The Receiver function will be passed a `GlossService` as an argument.

#### MLLP Receiver

Gloss ships with an MLLP server (commonly used with HL7 messages), you can configure this with the ports

```python
    GlossApi(
      reciever=gloss.receivers.mullp_multi_servce(1190, 1999).make_service
    )
```

### Importers

Gloss has an imoprt stage that takes the output of a receiver (which should be for example an hl7 message or a files contents) and translates it to a subclass gloss.message_type.MessageType. For example an AllergyMessage.


### Translators

To help this translators should be used to to simplify for example the translation of hl7 to MessageType. Gloss comes with a tranlators to tranlate from hl7 in gloss.translators.hl7 nad to opal json (currently in serialisers, we'll probably change the name to serialisers so it will stay there)


### Subscriptions

A gloss service takes in one more subscriber methods, these take a message container (gloss.message_type.MessageContainer), which has an array of all messages that have just come in, and the gloss service itself.

Example subscribers are the database subscriber that will save all messages it receives to the database

### InformationSource

The Information source sits between the gloss api and the database layer for patient information. This allows different services to query external services if necessary for patient information.

By default it will check the database and if it doesn't find it, post an hl7 message. This functionality will be changed in future to just look in the database.

You can set your own by settings an INFORMATION_SOURCE path to a class in your settings. This class has a single method
called patient_information which takes an identifier. The class takes an intialiser of the information source.


## REST Query API

Gloss also implements a REST Query API.


### Patient Query Service

    /api/patient/$IDENTIFIER

    -> {'status': 'success': 'data': Patient.to_dict()}

    #data:
    dict(
        identifier='UCH-555',
        allergies=[
            allergy_1
        ],
        results= [
            result_1, result_2
        ],
        demographics=[
            dict(
                identifier='UCH-555'
                )
            ]
        )

       # Includes all Allergies, Results, Admissions/Episodes
    -> {'status': 'error': 'data': 'some error description to log'}


## Configuration

You can configure Gloss using a local_settings.py file.

Available settings are:

### DATABASE_STRING

The Sqlalchemy database string you would like to use.

### DATE_FORMAT and DATETIME_FORMAT

These are the date and datetime formatting strings we would like to use for broadcasting
dates. Defaults to:

    DATE_FORMAT = '%d/%m/%Y'
    DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'

### DEBUG

Turn on debugging. Defaults to False.

## Load testing

Our load test script will fire a given amount messages as as many ports as are given in settings.

    python gloss/tests/load_test.py {{ amount }}

### Database migrations

Database migrations use [![alembic]](http://alembic.readthedocs.org/)

To create a migration run "alembic revision --autogenerate"

To update to head run "alembic upgrade head"

To upgrade or downgrade you can use upgrade +1 (e.g. "alembic downgrade -1") or it pattern matches with the version number.

For example, if it is unique you can run "alembic upgrade ad" and it'll upgrade to the version number beginning
"ad"

## Licence

Gloss is released under the GNU Affero GPLv3

## Communications

hello@openhealthcare.org.uk

http://www.openhealthcare.org.uk

https://twitter.com/ohcuk
