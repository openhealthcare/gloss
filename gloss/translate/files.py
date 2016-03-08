"""
Gloss to translators for file formats
"""
import datetime
import json
import logging

from gloss import notification
from gloss.models import session_scope
from gloss.translate import drugs

class FileType(object):
    """
    Base class for Files that we'll be processing
    with Gloss
    """
    def __init__(self, path):
        self.path = path

    def process(self):
        """
        Enforce transactions for processing
        """
        with session_scope() as session:
            self.process_file(session)

    def process_file(self, session):
        raise NotImplementedError(
            'Must implement {0}.process_file()'.format(self.__class__.__name__))


class FileProcessor(object):
    """
    Base processor for data we're getting via (e.g. CSV) files
    """
    def get_file_type(self, path):
        return

    def process_file(self, path):
        return


class BaseFileRetriever(object):
    """
    Base File class that we expect to be implemented for every
    file based integration.
    """

    @property
    def file_type(self):
        raise NotImplementedError(
            'Must set file_type for {0}'.format(self.__class__.__name__))

    def fetch(self):
        raise NotImplementedError(
            'Must implement {0}.fetch()'.format(self.__class__.__name__)
        )


class RFHBloodCultureRow(object):
    def __init__(self, row):
        self.row = row

    def _to_datestring(self, datestr):
        as_date = datetime.datetime.strptime(datestr, '%d/%m/%Y')
        return as_date.strftime('%Y/%m/%d %H:%M')

    def to_OPAL(self):
        res = [
            u"{0} {1}".format(drugs.abbreviations[a], getattr(self.row, a))
            for a in drugs.abbreviations if getattr(self.row, a) in ('R', 'r')
        ]
        sens = [
            u"{0} {1}".format(drugs.abbreviations[a], getattr(self.row, a))
            for a in drugs.abbreviations if getattr(self.row, a) in ('S', 's')
        ]

        return dict(
            identifier=self.row.hospno,
            data=dict(
                lab_number=self.row.labno,
                profile_code='BC',
                profile_description='BLOOD CULTURE',
                request_datetime=self._to_datestring(self.row.daterec),
                observation_datetime=self._to_datestring(self.row.datetest),
                last_edited=self._to_datestring(self.row.daterep),
                observations=json.dumps([
                    dict(
                        value_type='FT',
                        test_code='ORG',
                        test_name='ORGANISM',
                        observation_value=self.row.org
                    ),
                dict(
                    value_type='FT',
                    test_code='RES',
                    test_name='RESISTENT',
                    observation_value=res
                ),
                dict(
                    value_type='FT',
                    test_code='SENS',
                    test_name='SENSITIVE',
                    observation_value=sens
                ),
                dict(
                    value_type='FT',
                    test_code='!STS',
                    test_name='RFH SAMPTESTS',
                    observation_value=self.row.samptests
                ),
                dict(
                    value_type='FT',
                    test_code='!STY',
                    test_name='RFH SAMPTYPE',
                    observation_value=self.row.samptype
                ),
                dict(
                    value_type='FT',
                    test_code='!RES',
                    test_name='RFH RESULT',
                    observation_value=self.row.result
                )
            ])
                )
        )


class RFHBloodCulturesFileType(FileType):
    def process_file(self, session):
        print 'processing'
        with self.path.csv(header=True) as csv:
            for row in csv:
                logging.error('Processing result {0}'.format(row.labno))
                notification.notify('WINPATH', RFHBloodCultureRow(row))

                # stuff_we_know_about = self.get_lab_numbers() # ['874893', '48309']
                # for row in self.csv(): ## There will be 60K/night of these at the Free
                #     if self.get_lab_number(row) not in stuff_we_know_about:
                #         self.notify(patient, PathologyResults(row))
