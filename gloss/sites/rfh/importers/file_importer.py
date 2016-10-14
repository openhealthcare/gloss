import datetime
from gloss.sites.rfh.coded_values import drugs
from gloss import message_type
from gloss.importers.file_importer import FileType


class RFHBloodCulturesFileType(FileType):

    def _to_date(self, datestr):
        return datetime.datetime.strptime(datestr, '%d/%m/%Y')

    def res(self, row):
        return [
            u"{0} {1}".format(drugs.abbreviations[a], getattr(row, a))
            for a in drugs.abbreviations if getattr(row, a) in ('R', 'r')
        ]

    def sens(self, row):
        return [
            u"{0} {1}".format(drugs.abbreviations[a], getattr(row, a))
            for a in drugs.abbreviations if getattr(row, a) in ('S', 's')
        ]

    def row_to_result_message(self, row):
        return message_type.ResultMessage(
            lab_number=row.labno,
            profile_code='BC',
            profile_description='BLOOD CULTURE',
            request_datetime=self._to_date(row.daterec),
            observation_datetime=self._to_date(row.datetest),
            last_edited=self._to_date(row.daterep),

            observations=[
                dict(
                    value_type='FT',
                    test_code='ORG',
                    test_name='ORGANISM',
                    observation_value=row.org
                ),
                dict(
                    value_type='FT',
                    test_code='RES',
                    test_name='RESISTENT',
                    observation_value=self.res(row)
                ),
                dict(
                    value_type='FT',
                    test_code='SENS',
                    test_name='SENSITIVE',
                    observation_value=self.sens(row)
                ),
                dict(
                    value_type='FT',
                    test_code='!STS',
                    test_name='RFH SAMPTESTS',
                    observation_value=row.samptests
                ),
                dict(
                    value_type='FT',
                    test_code='!STY',
                    test_name='RFH SAMPTYPE',
                    observation_value=row.samptype
                ),
                dict(
                    value_type='FT',
                    test_code='!RES',
                    test_name='RFH RESULT',
                    observation_value=row.result
                )
            ]


        )

    def import_message(self, gloss_service):
        self.log.info('processing')

        with self.path.csv(header=True) as csv:
            for row in csv:

                self.log.info('Processing result {0}'.format(row.labno))
                yield message_type.MessageContainer(
                    messages=[self.row_to_result_message(row)],
                    hospital_number=row.hospno,
                    issuing_source='RFH',
                )
