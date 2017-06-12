from gloss import models, exceptions, utils
from gloss.conf import settings
from gloss.external_api import post_message_for_identifier
from gloss import message_type


"""
    the information source is a data api, that by default gets
    from the database if possible, otherwise it queries an external
    service
"""

# TODO, we can just inherit this now...
if getattr(settings, "MOCK_EXTERNAL_API", None):
    post_message_for_identifier = utils.import_from_string(
        settings.MOCK_EXTERNAL_API
    )


def get_information_source():
    if hasattr(settings, "INFORMATION_SOURCE"):
        info_cls = utils.import_from_string(settings.INFORMATION_SOURCE)
        return info_cls()
    else:
        return InformationSource()


class InformationSource(object):
    def check_or_fetch_patient(self, session, issuing_source, identifier):
        """ checks if a patient exists locally, and if not
            queries upstream if possible
        """
        patient_already_exists = models.Patient.query_from_identifier(
            identifier, issuing_source, session
        ).count()

        if patient_already_exists:
            return True

        if not patient_already_exists:
            if settings.USE_EXTERNAL_LOOKUP:
                post_message_for_identifier(identifier)
                return True
        return False

    def result_information(self, issuing_source, identifier):
        with models.session_scope() as session:
            if self.check_or_fetch_patient(
                session, issuing_source, identifier
            ):
                messages = models.Result.to_messages(
                    identifier, issuing_source, session
                )
                return message_type.construct_message_container(
                    messages, identifier, issuing_source
                )
            else:
                raise exceptions.PatientNotFound(
                    "We can't find any patients with that identifier {}".format(
                        identifier
                    )
                )

    def patient_information(self, issuing_source, identifier):
        with models.session_scope() as session:
            if self.check_or_fetch_patient(
                session, issuing_source, identifier
            ):
                return models.patient_to_message_container(
                    identifier, issuing_source, session
                )
            else:
                raise exceptions.PatientNotFound(
                    "We can't find any patients with that identifier {}".format(
                        identifier
                    )
                )
