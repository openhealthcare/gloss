Gloss
====
[![Build Status](https://travis-ci.org/openhealthcare/gloss.svg?branch=master)](https://travis-ci.org/openhealthcare/gloss)
[![Coverage Status](https://coveralls.io/repos/github/openhealthcare/gloss/badge.svg?branch=master)](https://coveralls.io/github/openhealthcare/gloss?branch=master)

a very quick hl7 implementation

to run the server locally
twistd --nodaemon mllp --receiver OhcReceiver.OhcReceiver


to run fire 1200 messages at it and get a timestamp run
python tests/test_messages.py
