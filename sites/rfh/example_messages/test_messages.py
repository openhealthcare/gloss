from hl7.client import MLLPClient
import hl7
from gloss.conf import settings
from gloss.utils import import_from_string


TEST_RESULT_1 = """MSH|^~\&|WinPath HL7||TQuest|1234|201606161043||ORU^R01|24066424|P|2.3.1|||AL|||||
PID|||20687107^HOSP^^REFHOSP||ZZZTEST^RSCHDNA^^^||197801010000|F|||ROYAL FREE HAMPSTEAD NHS^ROYAL FREE HOSPITAL^POND STREET^^NW3 2QG|||||||||||||||||||
PV1||NHS|9W^RAL 9 WEST^IP||||C3262182_Baker Daryl||C3202434^DR. D. PATCH^|||||||||||||||||||||||||||||||||||||||||||
ORC|RE|73160877407|73160877407||CM||||201606161043|||||||||||
OBR|1|73160877407|73160877407|HLCM^IGM HEVYLITE CHAINS^WinPath|N|201606161042|201606161042||||||testing||^&                              ^|C3202434^DR. D. PATCH||||||201606161043||1|F|||^|||||||||||||||||||
OBX|1|NM|HLMK^Hevylite IgM Kappa^WinPath||1.00|g/L|0.29 - 1.82||||F|201606161043||201606161043||
OBX|2|NM|HLML^Hevylite IgM Lambda^WinPath||0.50|g/L|0.17 - 0.94||||F|201606161043||201606161043||
OBX|3|NM|HLMR^Hevylite IgM K:L Ratio^WinPath||2.00||0.96 - 2.3||||F|201606161043||201606161043||
OBX|4|NM|IGM^Immunoglobulin M^WinPath||2.0|g/L|0.4 - 2.3||||F|201606161042||201606161043||
OBR|2|73160877407|73160877407|HLCA^IGA HEVYLITE CHAINS^WinPath|N|201606161042|201606161042||||||testing||^&                              ^|C3202434^DR. D. PATCH||||||201606161042||1|F|||^|||||||||||||||||||
OBX|1|NM|HLAK^Hevylite IgA Kappa^WinPath||2.00|g/L|0.57 - 2.08||||F|201606161042||201606161043||
OBX|2|NM|HLAL^Hevylite IgA Lambda^WinPath||2.00|g/L|0.44 - 2.04||||F|201606161042||201606161043||
OBX|3|NM|HLAR^Hevylite IgA K:L Ratio^WinPath||1.00||0.78 - 1.94||||F|201606161042||201606161043||
OBX|4|NM|IGA^Immunoglobulin A^WinPath||3.0|g/L|0.7 - 4||||F|201606161042||201606161043||
OBR|3|73160877407|73160877407|HLCG^IGG HEVYLITE CHAINS^WinPath|N|201606161042|201606161042||||||testing||^&                              ^|C3202434^DR. D. PATCH||||||201606161043||1|F|||^|||||||||||||||||||
OBX|1|NM|HLGK^Hevylite IgG Kappa^WinPath||11.00|g/L|3.84 - 12.07||||F|201606161043||201606161043||
OBX|2|NM|HLGL^Hevylite IgG Lambda^WinPath||6.00|g/L|1.91 - 6.74||||F|201606161043||201606161043||
OBX|3|NM|HLGR^Hevylite IgG K:L Ratio^WinPath||1.83||1.12 - 3.21||||F|201606161043||201606161043||
OBX|4|NM|IGG^Immunoglobulin G^WinPath||15.0|g/L|7 - 16||||F|201606161042||201606161043||
"""

TEST_RESULT_2 = """
MSH|^~\&|WinPath HL7||TQuest|1234|201609131315||ORU^R01|25530303|P|2.3.1|||AL|||||
PID||7041547825|20142110^HOSP^^REFHOSP||ZZZTESTPATIENT^AE^^^||198406110000|F|||11 THE DRIVE^LONDON^^^NW11 9SU|||||||||||||||||||
PV1||NHS|REF^REFERRED LOCATION^REF||||                    ||REF^REFERRED CLINICIAN^RF|||||||||||||||||||||||||||||||||||||||||||
ORC|RE||0016V999999||CM||||201609131315|||||||||||
OBR|1||0016V999999|ART^HIV VIRAL LOAD PCR ASSAY^WinPath|N|201609120956|201609120000||||||TESTING TESTINT TESTING||CLOT  ^Clotted Blood                                     &     ^|REF^REFERRED CLINICIAN||||||201609121001||4|F|||^|||||||||||||||||||
OBX|1|ST|ART^HIV-1 Viral Load PCR Assay....^WinPath||<40 copies/ml|| - ||||F|201609121001||201609121012||
OBR|2||0016V999999|PHCV^HCV PCR^WinPath|N|201609120956|201609120000||||||TESTING TESTINT TESTING||CLOT  ^Clotted Blood                                     &     ^|REF^REFERRED CLINICIAN||||||201609121013||4|F|||^|||||||||||||||||||
OBX|1|ST|PHCV^HCV PCR ..............^WinPath||HCV RNA detected|| - ||||F|201609120957||201609131314||
OBX|2|ST|HCVQ^HCV RNA Level.........^WinPath||125,256,255 copies/ml|| - ||||F|201609120959||201609131314||
OBR|3||0016V999999|PHBV^HBV DNA^WinPath|N|201609120956|201609120000||||||TESTING TESTINT TESTING||CLOT  ^Clotted Blood                                     &     ^|REF^REFERRED CLINICIAN||||||201609121013||4|F|||^|||||||||||||||||||
OBX|1|ST|PHBV^HBV PCR ..............^WinPath||HBV DNA detected|| - ||||F|201609121000||201609131314||
OBX|2|ST|HBVQ^HBV DNA level.........^WinPath||10 IU/mL|| - ||||F|201609120959||201609131314||
"""


TEST_RESULT_3 = """
MSH|^~\&|WinPath HL7||TQuest|1234|201609201459||ORU^R01|25654288|P|2.3.1|||AL|||||
PID|||20403706^HOSP^^REFHOSP||ZZZTESTFATHER^TEST1^^^||198001010000|M|||THE STAG^67 FLEET ROAD^LONDON^^NW3 2QU|||||||||||||||||||
PV1||NHS|HAE^Haematology^OP||||C6087218_McNamara Ch||C3558506^DR. R. RAKHIT^|||||||||||||||||||||||||||||||||||||||||||
ORC|RE|73161366185|73161366185||CM||||201609201459|||||||||||
OBR|1|73161366185|73161366185|FBC^FULL BLOOD COUNT^WinPath|N|201609201456|201609201456||||||Test RDW 20092016||B^Blood&                              ^|C3558506^DR. R. RAKHIT||||||201609201459||2|F|||^|||||||||||||||||||
OBX|1|NM|HBU^Hb^WinPath||150|g/l|135 - 170||||F|201609201457||201609201459||
OBX|2|NM|WBC^WBC^WinPath||10.00|10^9/L|3.5 - 11||||F|201609201457||201609201459||
OBX|3|NM|PLT^Platelets^WinPath||300|10^9/L|140 - 400||||F|201609201457||201609201459||
OBX|4|NM|RBC^RBC^WinPath||5.00|10^12/L|4.3 - 5.6||||F|201609201457||201609201459||
OBX|5|NM|HCT^HCT^WinPath||0.400|L/L|0.34 - 0.5||||F|201609201458||201609201459||
OBX|6|NM|MCV^MCV^WinPath||80.0|fL|79 - 98||||F|201609201458||201609201459||
OBX|7|NM|MCH^MCH^WinPath||30.0|pg|27 - 33||||F|201609201458||201609201459||
OBX|8|NM|MCHU^MCHC^WinPath||350|g/l|295 - 360||||F|201609201458||201609201459||
OBX|9|NM|NEUT^Neutrophils^WinPath||5.50|10^9/L|1.7 - 7.5||||F|201609201458||201609201459||
OBX|10|NM|LYMP^Lymphocytes^WinPath||3.00|10^9/L|1 - 4||||F|201609201459||201609201459||
OBX|11|NM|MONO^Monocytes^WinPath||1.00|10^9/L|0.2 - 1.5||||F|201609201459||201609201459||
OBX|12|NM|EOS^Eosinophils^WinPath||0.40|10^9/L|0 - 0.5||||F|201609201459||201609201459||
OBX|13|NM|BASO^Basophils^WinPath||0.10|10^9/L|0 - 0.1||||F|201609201459||201609201459||
"""

RAW_MESSAGES = [
    TEST_RESULT_1,
    TEST_RESULT_2,
    TEST_RESULT_3,
]


# MESSAGES = [i.replace("\n", "\r") for i in RAW_MESSAGES]
MESSAGES = RAW_MESSAGES

def read_message(some_msg):
    return hl7.parse(some_msg.replace("\n", "\r"))

def send_messages(messages):
    gloss_service = import_from_string(settings.GLOSS_SERVICE)
    port = gloss_service.receiver.ports[0]
    host = gloss_service.receiver.host
    with MLLPClient(host, port) as client:
        for message in messages:
            client.send_message(message)
