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

    twistd --nodaemon multiple_mllp --receiver gloss.ohc_receiver.OhcReceiver

To run the OPAL/JSON/HTTP API:

    python -m gloss.api

## How Does Gloss work?

Data coming into Gloss is understood to be a `Message`. Gloss understands various
message types commonly found in a healthcare environment.

Data coming into Gloss will go through the folliwing steps:

    Translate ->
    Identify ->
    Notify (via Subscriptions ) ->
    Archive ->
    Broadcast ->

### Translate

#### HL7 Integrations

Gloss receives hl7 messages into the OhcReceiver
these are translated into MessageTypes (as defined in gloss.message_types) by
the MessageImporter classes in import_message.

The MessageImporter returns a MessageContainer that has a MessageType class in
a message_type field. These messages are then passed on to the Notify service.

### Identify

### Notify

### Subscriptions

Subscriptions handle any db saving or downstream broadcast logic. Subscriptions may be
for a complete feed from an upstream source, or granular per patient. Subscriptions are
filtered by the message_type property. Their `notify()` method will be called with the
`gloss.message_types.MessageContainer` for all incoming messages of the relevant type.

Subscriptions are implemented by subclassing `gloss.subscriptions.Subscription`. A simple
subscription might be:


    class WinPathMessage(Subscription, OpalSerialiser):
        message_type = ResultMessage

        def notify(self, message_container):
            self.send_to_opal(message_container)

#### Subscription API

### Archive

### Broadcast

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

### PORTS
gloss will listen one or more ports by default these are 2574 and 2575

## Load testing

Our load test script will fire a given amount messages as as many ports as are given in settings.

    python gloss/tests/load_test.py {{ amount }}

### Database migrations

database migrations are done using [![alembic]](http://alembic.readthedocs.org/)

to create a migration run "alembic revision --autogenerate"
to update to head run "alembic upgrade head"
to upgrade or downgrade you can use upgrade +1 (e.g. "alembic downgrade -1") or it pattern matches with the version number.

ie if its unique you can run "alembic upgrade ad" and it'll upgrade to the version number beginning
"ad"

## Licence

Gloss is released under the GNU Affero GPLv3

## Communications

hello@openhealthcare.org.uk

http://www.openhealthcare.org.uk

https://twitter.com/ohcuk
