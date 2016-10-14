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

Gloss has 4 stages
  1) The Receiver, e.g. hl7/file, this should be a twisted server
  2) Importer, receives what is given by the receiver and translates it to one or more GlossMessages
  3) Subscriber, receives the outputs of the Importer and sends down stream, saves to the datbase etc


# Receivers
At the moment receivers should take a function or a method that returns a twisted service
the function/method should take the importer as the argument

Gloss ships with an mllp server, you can configure this with the ports

example usage
    GlossApi(
      reciever=gloss.receivers.mullp_multi_servce(1190, 1999).make_service
    )


### Importers

Gloss has an imoprt stage that takes the output of a receiver (which should be for example an hl7 message or a files contents) and translates it to a subclass gloss.message_type.MessageType. For example an AllergyMessage.


### Translators

To help this translators should be used to to simplify for example the translation of hl7 to MessageType. Gloss comes with a tranlators to tranlate from hl7 in gloss.translators.hl7 nad to opal json (currently in serialisers, we'll probably change the name to serialisers so it will stay there)


### Subscriptions

A gloss service takes in one more subscriber methods, these take a message container (gloss.message_type.MessageContainer), which has an array of all messages that have just come in, and the gloss service itself.

Example subscribers are the database subscriber that will save all messages it receives to the database


## REST Query API

Gloss also implements a REST Query API.

### Demographics Query Service

    /api/demographics/$IDENTIFIER
    -> {'status': 'success': 'data': Demographics.to_dict()}
    -> {'status': 'error': 'data': 'some error description to log'}

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
