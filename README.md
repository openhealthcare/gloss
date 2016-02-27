# Gloss

[![Build Status](https://travis-ci.org/openhealthcare/gloss.svg?branch=master)](https://travis-ci.org/openhealthcare/gloss)
[![Coverage Status](https://coveralls.io/repos/github/openhealthcare/gloss/badge.svg?branch=master)](https://coveralls.io/github/openhealthcare/gloss?branch=master)

Gloss is an integration engine for healthcare applications.

Gloss is a Twisted server that can translate and route HL7 messages,
batch file uploads and OPAL JSON messages.

## Getting Started

Some quick instructions to get you started

### Installation

From the source directory

    python setup.py install

You will also need the python dependencies:

    pip install -r requirements.txt

### Starting the server

To run the server locally

    twistd --nodaemon mllp --receiver ohc_receiver.OhcReceiver

## How Does Gloss work?

Gloss is a twisted server that listens for HL7v2 messages via MLLP.

### Subscriptions

Applications can subscribe either to particualr patients, or to entire services.

Subscribing to particular patients takes place via the API, and subscriptions are
stored in the database. This is useful for cases when you expect a large volume of
irrelevant messages.

Subscribing to an entire service is better suited for occasions when you are seeking
a translation and passthrough service, expecting either to process every message at
your application layer, or for whatever reason preferring to do your filtering there.

### Configuration

You can configure Gloss using the file ./gloss/settings.py

### Load testing

Our load test script will fire 1200 messages at it and calculate the time it took.

    python tests/test_messages.py

## Licence

Gloss is released under the GNU Affero GPLv3

## Communications

hello@openhealthcare.org.uk

http://www.openhealthcare.org.uk

https://twitter.com/ohcuk
