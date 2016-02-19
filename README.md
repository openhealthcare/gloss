Gloss
====

a very quick hl7 implementation

to run the server locally
twistd --nodaemon mllp --receiver OhcReceiver.OhcReceiver


to run fire 1200 messages at it and get a timestamp run
python tests/test_message_send.py 
