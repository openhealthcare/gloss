import time
import random
import sys
import argparse
from hl7.client import MLLPClient
import copy
import os

sys.path.append(".")

from gloss.tests.test_messages import read_message, MESSAGES
from gloss import settings


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Script to load test Gloss',
    )
    parser.add_argument('amount')
    args = parser.parse_args()
    start_time = time.time()
    with MLLPClient(settings.HOST, settings.PORT) as client:
        amount =int(args.amount)/len(MESSAGES)
        for i in xrange(amount):
            for raw_message in MESSAGES:
                message = read_message(copy.copy(raw_message))
                message[2][3][0][0][0] = str(random.randint(0, 1000000000))
                client.send_message(str(message))
    print "end time %s" % (time.time() - start_time)
    sys.exit(0)
