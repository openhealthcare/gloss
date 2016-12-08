from gloss import settings, models, exceptions, utils
from gloss.external_api import post_message_for_identifier

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
    issuing_source = getattr(settings, "ISSUING_SOURCE", "uclh")
    if hasattr(settings, "INFORMATION_SOURCE"):
        info_cls = utils.import_from_string(settings.INFORMATION_SOURCE)
        return info_cls(issuing_source)
    else:
        return InformationSource(issuing_source)


class InformationSource(object):
    def __init__(self, issuing_source):
        self.issuing_source = issuing_source

    def patient_information(self, identifier):
        with models.session_scope() as session:
            patient_exists = models.Patient.query_from_identifier(
                identifier, self.issuing_source, session
            ).count()

            if patient_exists:
                return models.patient_to_message_container(
                    identifier, self.issuing_source, session
                )
            if not patient_exists and settings.USE_EXTERNAL_LOOKUP:
                post_message_for_identifier(identifier)
                return models.patient_to_message_container(
                    identifier, self.issuing_source, session
                )
            else:
                raise exceptions.PatientNotFound(
                    "We can't find any patients with that identifier {}".format(
                        identifier
                    )
                )
