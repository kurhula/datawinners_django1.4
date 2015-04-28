import unittest

from mock import MagicMock, Mock

from datawinners.search.submission_headers import SubmissionAnalysisHeader, AllSubmissionHeader, SuccessSubmissionHeader, ErroredSubmissionHeader, HeaderFactory
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.field import TextField, IntegerField, UniqueIdField, FieldSet
from mangrove.form_model.form_model import FormModel


class TestSubmissionHeader(unittest.TestCase):
    def setUp(self):
        self.field1 = TextField('text', 'q1', 'Enter Text')
        self.field2 = IntegerField('integer', 'q2', 'Enter a Number')
        self.field3 = UniqueIdField('clinic', 'unique_id_field', 'q3', 'Which clinic are you reporting on')
        self.field4 = UniqueIdField('school', 'unique_id_field2', 'q4', 'Which school are you reporting on')
        self.repeat_field = FieldSet('repeat','repeat', 'repeat label', field_set=[self.field1, self.field4])
        self.form_model = MagicMock(spec=FormModel)
        self.form_model.id = 'form_model_id'

    def test_get_header_dict_from_form_model_without_unique_id_question(self):
        self.form_model.fields = [self.field1, self.field2]
        self.form_model.entity_questions = []
        expected = {'date': 'Submission Date', 'ds_id': 'Datasender Id', 'ds_name': 'Data Sender',
                    'form_model_id_q1': 'Enter Text',
                    'form_model_id_q2': 'Enter a Number'}

        result = SubmissionAnalysisHeader(self.form_model).get_header_dict()

        self.assertDictEqual(expected, result)

    def test_get_field_names_as_header_dict(self):
        self.form_model.fields = [self.field1, self.field2, self.field3]
        self.form_model.entity_questions = [self.field3]
        expected = ['date', 'ds_id', 'ds_name',
                    'form_model_id_q1',
                    'form_model_id_q2',
                    'form_model_id_q3',
                    'form_model_id_q3_unique_code']

        result = SubmissionAnalysisHeader(self.form_model).get_field_names_as_header_name()

        self.assertListEqual(expected, result)


    def test_get_header_dict_from_form_model_with_single_unique_id_question(self):
        self.form_model.fields = [self.field1, self.field2, self.field3]
        self.form_model.entity_questions = [self.field3]
        expected = {'date': 'Submission Date', 'ds_id': 'Datasender Id', 'ds_name': 'Data Sender',
                    'form_model_id_q1': 'Enter Text',
                    'form_model_id_q2': 'Enter a Number', 'form_model_id_q3': 'Which clinic are you reporting on',
                    'form_model_id_q3_unique_code': 'clinic ID'}

        result = SubmissionAnalysisHeader(self.form_model).get_header_dict()

        self.assertDictEqual(expected, result)

    def test_get_header_dict_from_form_model_with_single_unique_id_question_inside_repeat(self):
        self.form_model.fields = [self.field1, self.field2, self.repeat_field]
        self.form_model.entity_questions = [self.field4]
        expected = {'date': 'Submission Date', 'ds_id': 'Datasender Id', 'ds_name': 'Data Sender',
                    'form_model_id_q1': 'Enter Text',
                    'form_model_id_q2': 'Enter a Number',  'form_model_id_repeat-q1': 'Enter Text',
                    'form_model_id_repeat-q4': 'Which school are you reporting on'}
        result = SubmissionAnalysisHeader(self.form_model).get_header_dict()
        self.assertDictEqual(expected, result)

    def test_should_return_submission_log_specific_header_fields(self):
        self.form_model.fields = [self.field1, self.field2, self.field3, self.field4]
        self.form_model.entity_questions = [self.field3, self.field4]

        headers = AllSubmissionHeader(self.form_model).get_header_field_names()

        expected = ["ds_id", "ds_name", "date", "status", "form_model_id_q1", "form_model_id_q2", "form_model_id_q3", "form_model_id_q3_unique_code", "form_model_id_q4", "form_model_id_q4_unique_code"]
        self.assertListEqual(expected, headers)


    def test_submission_status_headers_for_success_submissions(self):
        self.form_model.fields = [self.field1, self.field2, self.field3, self.field4]
        self.form_model.entity_questions = [self.field3, self.field4]

        headers = SuccessSubmissionHeader(self.form_model).get_header_field_names()

        expected = ["ds_id", "ds_name", "date", "form_model_id_q1", "form_model_id_q2", "form_model_id_q3", "form_model_id_q3_unique_code", "form_model_id_q4", "form_model_id_q4_unique_code"]
        self.assertListEqual(expected, headers)

    def test_submission_status_headers_for_errored_submissions(self):
        self.form_model.fields = [self.field1, self.field2, self.field3, self.field4]
        self.form_model.entity_questions = [self.field3, self.field4]

        headers = ErroredSubmissionHeader(self.form_model).get_header_field_names()

        expected = ["ds_id", "ds_name", "date","error_msg", "form_model_id_q1", "form_model_id_q2", "form_model_id_q3", "form_model_id_q3_unique_code", "form_model_id_q4", "form_model_id_q4_unique_code"]

        self.assertListEqual(expected, headers)


class TestHeaderFactory(unittest.TestCase):
    def test_should_return_header_instance_based_on_submission_type(self):
        form_model = Mock(spec=FormModel)
        dbm = Mock(spec=DatabaseManager)
        self.assertIsInstance(HeaderFactory(dbm, form_model).create_header("all"), AllSubmissionHeader)
        self.assertIsInstance(HeaderFactory(dbm, form_model).create_header("success"), SuccessSubmissionHeader)
        self.assertIsInstance(HeaderFactory(dbm, form_model).create_header("error"), ErroredSubmissionHeader)
        self.assertIsInstance(HeaderFactory(dbm, form_model).create_header("analysis"), SubmissionAnalysisHeader)