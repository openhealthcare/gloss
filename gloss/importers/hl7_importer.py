from collections import defaultdict

from gloss.utils import itersubclasses
from gloss.importers.base_importer import SafelImporter
from gloss.translators.hl7 import hl7_translator
from gloss import message_type as messages


class HL7TranslationToMessage(object):
    def __init__(self, hl7_msg):
        self.hl7_msg = hl7_msg

    def get_hospital_number(self):
        return self.hl7_msg.pid.hospital_number

    def import_hl7(self):
        raise NotImplementedError("This needs to be implemented")

    @classmethod
    def get_for_hl7(cls, hl7):
        for i in itersubclasses(cls):
            if i.hl7Translation == hl7.__class__:
                return i(hl7)


class PatientMergeImporter(HL7TranslationToMessage):
    hl7Translation = hl7_translator.PatientMerge

    def import_hl7(self):
        return [messages.PatientMergeMessage(
            new_id=self.hl7_msg.pid.hospital_number,
            hospital_number=self.hl7_msg.mrg.duplicate_hospital_number,
        )]

    def get_hospital_number(self):
        return self.hl7_msg.mrg.duplicate_hospital_number


class PatientUpdateImporter(HL7TranslationToMessage):
    hl7Translation = hl7_translator.PatientUpdate

    def import_hl7(self):
        interesting_fields = [
            "hospital_number",
            "surname",
            "first_name",
            "middle_name",
            "title",
            "date_of_birth",
            "sex",
            "marital_status",
            "religion",
            "ethnicity",
            "post_code",
            "date_of_death",
            "death_indicator",
        ]

        # if we get an empty field the way the message formatting is, we can
        # ignore it, unless its if the patient death has turned to negative
        # in which case we need to null out the date of death
        kwargs = {
            i: getattr(self.hl7_msg.pid, i) for i in interesting_fields if getattr(self.hl7_msg.pid, i)
        }

        kwargs["gp_practice_code"] = self.hl7_msg.pd1.gp_practice_code

        if self.hl7_msg.pid.death_indicator == False:
            kwargs["date_of_death"] = None

        return [
            messages.PatientMessage(**kwargs)
        ]


class InpatientAdmitImporter(HL7TranslationToMessage):
    hl7Translation = hl7_translator.InpatientAdmit

    def import_hl7(self):
        return [messages.InpatientAdmissionMessage(
            datetime_of_admission=self.hl7_msg.pv1.datetime_of_admission,
            ward_code=self.hl7_msg.pv1.ward_code,
            room_code=self.hl7_msg.pv1.room_code,
            bed_code=self.hl7_msg.pv1.bed_code,
            external_identifier=self.hl7_msg.pid.patient_account_number,
            hospital_number=self.hl7_msg.pid.hospital_number,
            issuing_source="uclh",
            datetime_of_discharge=self.hl7_msg.pv1.datetime_of_discharge,
            admission_diagnosis=self.hl7_msg.pv2.admission_diagnosis,
        )]


class InpatientDischargeImporter(InpatientAdmitImporter):
    hl7Translation = hl7_translator.InpatientDischarge


class InpatientAmendImporter(InpatientAdmitImporter):
    hl7Translation = hl7_translator.InpatientAmend


class InpatientCancelDischargeImporter(InpatientAdmitImporter):
    hl7Translation = hl7_translator.InpatientCancelDischarge


class InpatientTransferImporter(HL7TranslationToMessage):
    hl7Translation = hl7_translator.InpatientTransfer

    def import_hl7(self):
        message = messages.InpatientAdmissionTransferMessage(
            datetime_of_admission=self.hl7_msg.pv1.datetime_of_admission,
            ward_code=self.hl7_msg.pv1.ward_code,
            room_code=self.hl7_msg.pv1.room_code,
            bed_code=self.hl7_msg.pv1.bed_code,
            external_identifier=self.hl7_msg.pid.patient_account_number,
            hospital_number=self.hl7_msg.pid.hospital_number,
            issuing_source="uclh",
            datetime_of_discharge=self.hl7_msg.pv1.datetime_of_discharge,
            datetime_of_transfer=self.hl7_msg.evn.planned_datetime,
            admission_diagnosis=self.hl7_msg.pv2.admission_diagnosis
        )
        return [message]


class InpatientSpellDeleteImporter(HL7TranslationToMessage):
    hl7Translation = hl7_translator.InpatientSpellDelete

    def import_hl7(self):
        return [messages.InpatientAdmissionDeleteMessage(
            external_identifier=self.hl7_msg.pid.patient_account_number,
            datetime_of_deletion=self.hl7_msg.evn.recorded_datetime,
            hospital_number=self.hl7_msg.pid.hospital_number,
            issuing_source="uclh"
        )]


class AllergyImporter(HL7TranslationToMessage):
    hl7Translation = hl7_translator.AllergyMessage

    def import_hl7(self):
        all_allergies = []
        for allergy in self.hl7_msg.allergies:
            all_allergies.append(messages.AllergyMessage(
                allergy_type_description=allergy.al1.allergy_type_description,
                certainty_id=allergy.al1.certainty_id,
                certainty_description=allergy.al1.certainty_description,
                allergy_reference_name=allergy.al1.allergy_reference_name,
                allergy_description=allergy.al1.allergy_description,
                allergen_reference_system=allergy.al1.allergen_reference_system,
                allergen_reference=allergy.al1.allergen_reference,
                status_id=allergy.al1.status_id,
                status_description=allergy.al1.status_description,
                diagnosis_datetime=allergy.al1.diagnosis_datetime,
                allergy_start_datetime=allergy.al1.allergy_start_datetime,
                issuing_source="uclh",
                no_allergies=False
            ))

        if not all_allergies:
            all_allergies.append(messages.AllergyMessage(
                no_allergies=True
            ))

        return all_allergies


class WinPathResultsOrderImporter(HL7TranslationToMessage):
    hl7Translation = hl7_translator.WinPathResultsOrder

    def import_hl7(self):
        """
        we don't process order messages at this time
        """
        return []


class WinPathResultsImporter(HL7TranslationToMessage):
    hl7Translation = hl7_translator.WinPathResults

    def import_hl7(self):
        # we still need to add NTEs to this
        def get_obx_dict(obxs, comments):
            units = obxs.obx.units
            if units:
                units = units.replace("\\S\\", "^")
            return dict(
                value_type=obxs.obx.value_type,
                test_code=obxs.obx.test_code,
                test_name=obxs.obx.test_name,
                observation_value=obxs.obx.observation_value,
                units=units,
                reference_range=obxs.obx.reference_range,
                result_status=obxs.obx.result_status,
                comments=comments.get(obxs.obx.set_id, None)
            )

        def get_comments(ntes):
            set_id_to_comment = defaultdict(list)
            for nte_package in ntes:
                set_id_to_comment[nte_package.nte.set_id].append(
                    nte_package.nte.comments
                )

            return {
                set_id: " ".join(comments) for set_id, comments in set_id_to_comment.iteritems()
            }

        gloss_messages = []

        for result in self.hl7_msg.results:
            set_id_to_comments = get_comments(result.ntes)
            gloss_messages.append(
                messages.ResultMessage(
                    hospital_number=self.hl7_msg.pid.hospital_number,
                    issuing_source="uclh",
                    lab_number=result.obr.lab_number,
                    profile_code=result.obr.profile_code,
                    profile_description=result.obr.profile_description,
                    request_datetime=result.obr.request_datetime,
                    observation_datetime=result.obr.observation_datetime,
                    last_edited=result.obr.last_edited,
                    result_status=result.obr.result_status,
                    observations=[get_obx_dict(i, set_id_to_comments) for i in result.obxs],
                )
            )
        return gloss_messages


class HL7Importer(SafelImporter):
    def import_message(self, msg, gloss_service):
        hl7 = hl7_translator.HL7Translator.translate(msg)
        importer = HL7TranslationToMessage.get_for_hl7(hl7)
        if importer:
            processed_messages = importer.import_hl7()
            hospital_number = importer.get_hospital_number()
            return messages.MessageContainer(
                messages=processed_messages,
                hospital_number=hospital_number,
                issuing_source=gloss_service.issuing_source
            )
