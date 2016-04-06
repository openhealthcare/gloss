import time
import random
import sys
import argparse
from hl7.client import MLLPClient
import copy
import os
import multiprocessing

sys.path.append(".")

from gloss.tests.test_messages import read_message, MESSAGES
from gloss import settings


def post_to_mllp_client(port, original_amount):
        with MLLPClient(settings.HOST, port) as client:
            amount = original_amount/len(MESSAGES)
            count = 1
            for i in xrange(amount):
                for raw_message in MESSAGES:
                    message = read_message(copy.copy(raw_message))
                    message[2][3][0][0][0] = str(random.randint(0, 1000000000))
                    client.send_message(str(message))
                    print "sending {0} of {1} to {2}".format(
                        count, original_amount, port
                    )
                    count += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Script to load test Gloss',
    )
    parser.add_argument('amount')
    args = parser.parse_args()
    amount = int(args.amount)/len(settings.PORTS)
    for port_num in settings.PORTS:
        p = multiprocessing.Process(
            target=post_to_mllp_client, args=(port_num, amount,)
        )
        p.start()
    sys.exit(0)
