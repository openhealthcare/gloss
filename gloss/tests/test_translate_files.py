"""
Unittests for gloss.translate.files
"""
import datetime
from mock import patch

from gloss import message_type
from gloss.tests.core import GlossTestCase

from gloss.translate import files

class FileTypeTestCase(GlossTestCase):

    def test_process(self):

        class MyFileType(files.FileType):
            def process_file(self):
                return [None]

        with patch('gloss.notification.notify') as notify:
            MyFileType('notareal.file').process()
            notify.assert_called_with(None)

    def test_process_file_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            files.FileType(None).process()


class BaseFileRetrieverTestCase(GlossTestCase):

    def test_file_type_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            ft = files.BaseFileRetriever().file_type

    def test_fetch_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            files.BaseFileRetriever().fetch()


class RFHBloodCulturesFileTypeTestCase(GlossTestCase):

    @property
    def row(self):
        class Row(object):
            def __init__(self, **kw):
                for k in kw:
                    setattr(self, k, kw[k])

        return Row(
            nhsno='890123456',
            hospno='555345',
            surn='Henderson',
            fn='Heather',
            dob='12121984',
            sex='F',
            loc='P701',
            cons='Dr C Chalmers-Watson',
            postcode='NW1 6XE',
            labno='348789729',
            pttype='NHS',
            loc2='GP',
            ward='P701',
            datetest='31/05/2013',
            daterec='01/06/2013',
            daterep='02/06/2013',
            samptests='URIN,URIN,LBLB',
            samptype='URI',
            result='Culture Result : Urine :',
            org='Escherichia coli',
            ami='s',
            amo='',
            amb='',
            amp='R',
            cas='',
            aug='R',
            pos='',
            azt='s',
            vor='',
            car='',
            cap='',
            cem='',
            cee='',
            cez='',
            cei='s',
            cex='',
            ceo='',
            ctx='',
            cfo='',
            cxn='s',
            cef='',
            cta='s',
            cfu='s',
            cfx='R',
            cep='',
            crd='',
            chl='',
            cin='',
            cip='s',
            cla='',
            cli='',
            clf='',
            clo='',
            col='s',
            cot='s',
            cse='',
            dap='',
            dor='',
            dox='',
            ery='',
            ert='s',
            eta='',
            eth='',
            flu='',
            flz='',
            fivefl='',
            fos='',
            fuc='',
            gen='S',
            ges='',
            imi='',
            iso='',
            itr='',
            kan='',
            ket='',
            lin='',
            lev='s',
            lom='',
            mec='',
            mer='s',
            met='',
            mdz='',
            mez='',
            mil='',
            min='',
            mox='',
            mof='',
            mup='',
            mph='',
            nal='',
            neo='',
            net='',
            nfu='S',
            nor='',
            nov='',
            nys='',
            ofl='',
            oxa='',
            pas='',
            pen='',
            pe2='',
            peo='',
            pe0='',
            pip='s',
            prl='s',
            pol='s',
            pri='',
            pro='',
            pyr='',
            rif='',
            rib='',
            rox='',
            sep='',
            sis='',
            spe='',
            str='',
            syn='',
            sub='',
            sud='',
            sul='',
            tei='',
            tem='',
            tet='',
            tri='',
            van='',
            esbl='',
            ampc='',
            ampcdr='',
            blank='')

    def test_to_date(self):
        filetype = files.RFHBloodCulturesFileType('notareal.file')
        self.assertEqual(datetime.datetime(1976, 4, 23), filetype._to_date('23/4/1976'))

    def test_res(self):
        filetype = files.RFHBloodCulturesFileType('notareal.file')
        expected = [u'Cefixime R', u'Augmentin R', u'Amphotericin R']
        self.assertEqual(expected, filetype.res(self.row))

    def test_sens(self):
        filetype = files.RFHBloodCulturesFileType('notareal.file')
        expected = [u'Piperacillin-Tazobactam s', u'Amikacin s', u'Nitrofurantoin S',
                    u'Levofloxacin s',
                    u'Meropenem s', u'Gentamicin S', u'Ertapenem s', u'Ciprofloxacin s',
                    u'Aztreonam s',
                    u'Colistin s']
        self.assertEqual(expected, filetype.sens(self.row))

    def test_row_to_result_message(self):
        filetype = files.RFHBloodCulturesFileType('notareal.file')
        msg = filetype.row_to_result_message(self.row)
        self.assertIsInstance(msg, message_type.ResultMessage)
        self.assertEqual('BC', msg.profile_code)

    def test_process_file(self):
        filetype = files.RFHBloodCulturesFileType('notareal.file')
        with patch.object(filetype, 'path') as mock_path:
            mock_path.csv.return_value.__enter__.return_value.__iter__.return_value = [self.row]

            for container in filetype.process_file():
                self.assertEqual('RFH', container.issuing_source)
                self.assertEqual('555345', container.hospital_number)
                self.assertEqual(message_type.ResultMessage, container.message_type)
