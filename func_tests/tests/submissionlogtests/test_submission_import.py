import os
import tempfile
import unittest

from django.test import Client
from nose.plugins.attrib import attr
import xlrd
from tests.logintests.login_data import TRIAL_CREDENTIALS_VALIDATES


@attr('functional_test')
class TestSubmissionImport(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.client.login(username="chinatwu4@gmail.com", password="chinatwu")

    def test_import_template(self):

        resp = self.client.get('/entity/entity/template/cli051/?filename=clinic%20test%20project')

        xlfile_fd, xlfile_name = tempfile.mkstemp(".xls")
        os.write(xlfile_fd, resp.content)
        os.close(xlfile_fd)
        workbook = xlrd.open_workbook(xlfile_name)
        sheet = workbook.sheet_by_index(0)
        self.assertEqual(
            [
                #u'I am submitting this data on behalf of\n\nIf you are sending data on behalf of someone, you can enter their Data Sender ID. Otherwise you can leave it blank.\n\nExample: rep42',
                u'What is associat\xe9d entity?\n\nEnter the unique ID for each clinic.\nYou can find the clinic List on the My clinic page.\n\nExample: cli01',
                u'Name\n\nAnswer must be a word 10 characters maximum\n\n',
                u'Father age\n\nEnter a number between 18-100.\n\n',
                u'Report date\n\nAnswer must be a date in the following format: day.month.year\n\nExample: 25.12.2011',
                u'What is your blood group?\n\nEnter 1 answer from the list.\n\nExample: a',
                u'Symptoms\n\nEnter 1 or more answers from the list.\n\nExample: a or ab',
                u'What is the GPS code for clinic?\n\nAnswer must be GPS coordinates in the following format (latitude,longitude).\n\nExample: -18.1324,27.6547',
                u'Required Medicines\n\nEnter 1 or more answers from the list.\n\nExample: a or ab'
              ], sheet.row_values(0, 0, 9))