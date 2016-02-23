from test_messages import INPATIENT_ADMISSION, read_message
from ..process_message import MessageProcessor, InpatientAdmit


def test_message_processor():
    msg = read_message(INPATIENT_ADMISSION)
    message_processor = MessageProcessor()
    result = message_processor.get_message_type(msg)
    assert(result == InpatientAdmit)
