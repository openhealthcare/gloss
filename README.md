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

    twistd --nodaemon mllp --receiver gloss.ohc_receiver.OhcReceiver

## How Does Gloss work?

Gloss is a twisted server that listens for HL7v2 messages via MLLP.

### Subscriptions

Gloss receives hl7 messages into the OhcReceiver
these are translated into MessageTypes (as defined in gloss.message_types) by
the MessageImporter classes in import_message.

The MessageImporter returns a MessageContainer that has a MessageType class in
a message_type field

Subscriptions looks for this and runs all subscriptions that have that message
type class. These subscriptions should handle any db saving or sending
downstream logic.

MessageContainers and MessageTypes have to dict methods that recursively
translate the data structure into a dictionary for serialisation if needed.

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
