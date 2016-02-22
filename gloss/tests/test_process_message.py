from test_messages import INPATIENT_ADMISSION, read_message
from ..process_message import MessageProcessor, InpatientAdmit


def test_message_processor():
    msg = read_message(INPATIENT_ADMISSION)
    result = MessageProcessor.get_message(msg)
    assert(result == InpatientAdmit)
