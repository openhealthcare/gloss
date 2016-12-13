"""
Load test for Gloss simulating UCH load
"""
import argparse
import copy
import multiprocessing
import os
import random
import sys
import time

import numpy
from hl7.client import MLLPClient

sys.path.append(".")

from gloss.tests import test_messages
from gloss.conf import settings

MESSAGE_NAMES =[ 'PATIENT_UPDATE', 'PATIENT_DEATH', 'PATIENT_MERGE',
                 'INPATIENT_ADMISSION', 'INPATIENT_DISCHARGE',
                 'ALLERGY', 'INPATIENT_CANCEL_DISCHARGE', 'RESULTS_MESSAGE',
                 'COMPLEX_WINPATH_RESULT', 'GYNAECOLOGY']

MESSAGE_TYPES = [
        ['Demographic', 0.1245],
        ['Inpatient',   0.4981],
        ['Pathology',   0.3736],
        ['Allergy',     0.0038]
]

MESSAGE_TYPE_MESSAGES = {
        'Demographic': [
                ['PATIENT_UPDATE', 0.8],
                ['PATIENT_DEATH',  0.15],
                ['PATIENT_MERGE',  0.05]
        ],
        'Inpatient': [
                ['INPATIENT_ADMISSION',        0.45],
                ['INPATIENT_DISCHARGE',        0.45],
                ['INPATIENT_CANCEL_DISCHARGE', 0.1]],
        'Pathology': [
                ['COMPLEX_WINPATH_RESULT', 0.3],
                ['GYNAECOLOGY',            0.3],
                ['RESULTS_MESSAGE',        0.4]
        ],
        'Allergy': [['ALLERGY', 1]],
}

MESSAGES = {name: getattr(test_messages, name).replace("\n", "\r") for name in MESSAGE_NAMES}

def weighted_choice(choices):
    return numpy.random.choice([i[0] for i in choices], p=[i[1] for i in choices])

def randomised(message):
    msg = test_messages.read_message(copy.copy(message))
    msg[2][3][0][0][0] = str(random.randint(0, 1000000000))
    return msg

def get_message():
    message_type = weighted_choice(MESSAGE_TYPES)
    message_name = weighted_choice(MESSAGE_TYPE_MESSAGES[message_type])
    message = MESSAGES[message_name]
    return str(randomised(message)), message_type, message_name


def should_continue(duration, t1):
    return time.time() - t1 < duration

def post_to_mllp_client(config):
    port, duration, throughput = config
    tstart = time.time()
    count = 0
    throughputsec = throughput / 60
    with MLLPClient('elcid-uch-test.openhealthcare.org.uk', port) as client:

        tbatch = time.time()
        while should_continue(duration, tstart):
            msg, typ, name = get_message()
            client.send_message(msg)
            count += 1
            print "sending {0} ({1} {2}) to {3}".format(
                    count, typ, name, port
            )
            if count % throughputsec == 0:
                print 'Made {0}'.format(throughputsec)
                tbatchend = time.time() - tbatch
                if tbatchend < 1:
                    print 'Sleeping for {0} on {1}'.format(
                        1-tbatchend, port
                    )
                    print 'Througphut for this worker was {0}msgs in {1}s'.format(
                        throughputsec, tbatchend
                    )
                    time.sleep(1-tbatchend)

                tbatch = time.time()

        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                description='Script to load test Gloss',
        )
    parser.add_argument('-d', '--duration', default='1', help="Desired duration in minutes")
    parser.add_argument('-t', '--throughput', default='600', help="Desired maximum throughput per minute")
    workers = len(settings.PORTS)
    args = parser.parse_args()
    duration = int(args.duration)
    throughput = int(args.throughput)
    print '%'*120
    print "Starting Load test run for {0} mins with a max throughput of {1}msg/min on {2} ports in 1s...".format(
            duration, throughput, workers
    )
    print '%'*120
    time.sleep(1)
    pool = multiprocessing.Pool(workers)

    pool.map(post_to_mllp_client, [(p, duration*60, throughput/workers) for p in settings.PORTS])
    pool.close()
