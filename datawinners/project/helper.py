# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import logging
from babel.dates import format_date
from django.contrib.auth.models import User
from django.http import Http404
from django.utils.translation import gettext as _
from django.utils.translation import ugettext
from accountmanagement.models import NGOUserProfile
from datawinners.scheduler.smsclient import SMSClient
from mangrove.datastore.datadict import create_datadict_type, get_datadict_type_by_slug
from mangrove.errors.MangroveException import DataObjectNotFound, FormModelDoesNotExistsException
from mangrove.form_model.field import TextField, IntegerField, DateField, GeoCodeField
from mangrove.form_model.form_model import FormModel, get_form_model_by_code
from mangrove.form_model.validation import  TextLengthConstraint
from mangrove.utils.types import  is_sequence, sequence_to_str
from enhancer import field_enhancer
from messageprovider.messages import SMS
import models
from datetime import datetime
from mangrove.transport.submissions import  Submission, get_submissions
from models import Reminder
from mangrove.transport import Request, TransportInfo
from project.data_sender import DataSender

DEFAULT_DATE_FORMAT = 'dd.MM.yyyy'

field_enhancer.enhance()

NOT_AVAILABLE = "N/A"
NOT_AVAILABLE_DS = "Deleted Data Sender"

logger = logging.getLogger("datawinners.reminders")

def get_or_create_data_dict(dbm, name, slug, primitive_type, description=None):
    try:
        #  Check if is existing
        ddtype = get_datadict_type_by_slug(dbm, slug)
    except DataObjectNotFound:
        #  Create new one
        ddtype = create_datadict_type(dbm=dbm, name=name, slug=slug,
            primitive_type=primitive_type, description=description)
    return ddtype


def _create_entity_id_question(dbm, entity_id_question_code):
    entity_data_dict_type = get_or_create_data_dict(dbm=dbm, name="eid", slug="entity_id", primitive_type="string",
        description="Entity ID")
    name = ugettext("Which subject are you reporting on?")
    entity_id_question = TextField(name=name, code=entity_id_question_code,
        label=name,
        entity_question_flag=True, ddtype=entity_data_dict_type,
        constraints=[TextLengthConstraint(min=1, max=12)],
        instruction=(ugettext('Answer must be a word %d characters maximum') % 12))
    return entity_id_question


def hide_entity_question(fields):
    return [each for each in fields if not each.is_entity_field]


def is_submission_deleted(submission):
    return submission.is_void() if submission is not None else True


def adapt_submissions_for_template(questions, submissions):
    assert is_sequence(questions)
    assert is_sequence(submissions)
    for s in submissions:
        assert type(s) is Submission and s._doc is not None
    formatted_list = []
    for each in submissions:
        case_insensitive_dict = {key.lower(): value for key, value in each.values.items()}
        formatted_list.append(
            [each.uuid, each.destination, each.source, each.created, each.errors,
             "Success" if each.status else "Error"] +
            ["Yes" if is_submission_deleted(each.data_record) else "No"] + [
            get_according_value(case_insensitive_dict, q) for q in questions])

    return [tuple(each) for each in formatted_list]


def get_according_value(value_dict, question):
    value = value_dict.get(question.code.lower(), '--')
    if value != '--' and question.type in ['select1', 'select']:
        value_list = question.get_option_value_list(value)
        return ", ".join(value_list)
    return value


def generate_questionnaire_code(dbm):
    all_projects_count = models.count_projects(dbm)
    code = all_projects_count + 1
    code = "%03d" % (code,)
    while True:
        try:
            get_form_model_by_code(dbm, code)
            code = int(code) + 1
            code = "%03d" % (code,)
        except FormModelDoesNotExistsException:
            break
    return code


def get_org_id_by_user(user):
    return NGOUserProfile.objects.get(user=user).org_id


def get_datasender_by_mobile(dbm, mobile):
    rows = dbm.load_all_rows_in_view("datasender_by_mobile", startkey=[mobile], endkey=[mobile, {}])
    return rows[0].key[1:] if len(rows) > 0 else [ugettext(NOT_AVAILABLE_DS), None]


def get_data_sender(dbm, user, submission):
    return DataSenderHelper(dbm).get_data_sender(user, submission)


class DataSenderGetter(object):
    def data_sender_by_email(self, org_id, email):
        data_sender = User.objects.get(email=email)
        reporter_id = NGOUserProfile.objects.filter(user=data_sender, org_id=org_id)[0].reporter_id or "admin"

        return data_sender.get_full_name(), reporter_id, email

    def list_data_sender(self, org_id):
        ngo_user_profiles = list(NGOUserProfile.objects.filter(org_id=org_id).all())
        return [DataSender(each.user.email, each.user.get_full_name(), each.reporter_id or "admin") for each in ngo_user_profiles]


class DataSenderHelper(object):
    def __init__(self, dbm):
        self.manager = dbm
        self.dataSenderGetter = DataSenderGetter()

    def get_data_sender(self, org_id, submission):
        if submission.channel == 'sms':
            data_sender = self._get_data_sender_for_sms(submission)
        else:
            data_sender = self._get_data_sender_for_not_sms(submission, org_id)

        return data_sender if data_sender[0] != "TEST" else ("TEST", "", "TEST")

    def get_all_sms_data_senders_with_submission(self):
        data_sender_info_list = [each for each in (self._get_all_submission_data_sender_info()) if each[0] == SMS]
        source_to_data_sender_dict = {each.source: each for each in self._get_all_sms_data_senders()}

        return map(
            lambda x: source_to_data_sender_dict.get(x[1], DataSender(x[1], ugettext(NOT_AVAILABLE_DS), None)),
            data_sender_info_list)

    def get_all_non_sms_data_senders_with_submission(self, org_id):
        data_sender_list = self.dataSenderGetter.list_data_sender(org_id)
        source_to_data_sender_dict = {each.source: each for each in data_sender_list}
        data_sender_info_list = [each for each in (self._get_all_submission_data_sender_info()) if each[0] != SMS]

        return map(
            lambda x: source_to_data_sender_dict.get(x[1], DataSender(x[1], ugettext(NOT_AVAILABLE_DS), None)),
            data_sender_info_list)

    def _get_data_sender_for_sms(self, submission):
        return tuple(self._data_sender_by_mobile(submission.source) + [submission.source])

    def _get_data_sender_for_not_sms(self, submission, org_id):
        try:
            data_sender = self.dataSenderGetter.data_sender_by_email(org_id, submission.source)
        except:
            data_sender = (ugettext(NOT_AVAILABLE_DS), None, submission.source)

        return data_sender

    def _data_sender_by_mobile(self, mobile):
        rows = self.manager.load_all_rows_in_view("datasender_by_mobile", startkey=[mobile], endkey=[mobile, {}])
        return rows[0].key[1:] if len(rows) > 0 else [ugettext(NOT_AVAILABLE_DS), None]

    def _get_all_sms_data_senders(self):
        rows = self.manager.load_all_rows_in_view("datasender_by_mobile")

        return map(lambda x: DataSender(*x.key), rows)

    def _get_all_submission_data_sender_info(self):
        return [each.key for each in self.manager.load_all_rows_in_view("submission_data_sender_info", group_level=2)]


def case_insensitive_lookup(search_key, dictionary):
    assert isinstance(dictionary, dict)
    for key, value in dictionary.items():
        if key.lower() == search_key.lower():
            return value
    return None

def _to_str(value, form_field=None):
    if value is None:
        return u"--"
    if is_sequence(value):
        return sequence_to_str(value)
    if isinstance(value, datetime):
        date_format = DateField.FORMAT_DATE_DICTIONARY.get(
            form_field.date_format) if form_field else DEFAULT_DATE_FORMAT
        return format_date(value, date_format)
    return value


def get_formatted_time_string(time_val):
    try:
        time_val = datetime.strptime(time_val, '%d-%m-%Y %H:%M:%S')
    except Exception:
        return None
    return time_val.strftime('%d-%m-%Y %H:%M:%S')


def remove_reporter(entity_type_list):
    removable = None
    for each in entity_type_list:
        if each[0].lower() == 'reporter':
            removable = each
    entity_type_list.remove(removable)
    entity_type_list.sort()
    return entity_type_list


def get_preview_for_field(field):
    preview = {"description": field.name, "code": field.code, "type": field.type, "instruction": field.instruction}
    constraints = field.get_constraint_text() if field.type not in ["select", "select1"] else\
    [(option["text"], option["val"]) for option in field.options]
    preview.update({"constraints": constraints})
    return preview


def delete_project(manager, project, void=True):
    project_id, qid = project.id, project.qid
    [reminder.void(void) for reminder in (Reminder.objects.filter(project_id=project_id))]
    questionnaire = FormModel.get(manager, qid)
    [submission.void(void) for submission in get_submissions(manager, questionnaire.form_code, None, None)]
    questionnaire.void(void)
    project.set_void(manager, void)


def get_activity_report_questions(dbm):
    reporting_period_dict_type = get_or_create_data_dict(dbm=dbm, name="rpd", slug="reporting_period",
        primitive_type="date",
        description="activity reporting period")
    activity_report_question = DateField(name=ugettext("What is the reporting period for the activity?"), code='q1',
        label="Period being reported on", ddtype=reporting_period_dict_type,
        date_format="dd.mm.yyyy", event_time_field_flag=True)

    return [activity_report_question]


def get_subject_report_questions(dbm):
    entity_id_question = _create_entity_id_question(dbm, 'q1')
    reporting_period_dict_type = get_or_create_data_dict(dbm=dbm, name="rpd", slug="reporting_period",
        primitive_type="date",
        description="activity reporting period")
    activity_report_question = DateField(name=ugettext("What is the reporting period for the activity?"), code='q2',
        label="Period being reported on", ddtype=reporting_period_dict_type,
        date_format="dd.mm.yyyy", event_time_field_flag=True)
    return [entity_id_question, activity_report_question]


def broadcast_message(data_senders, message, organization_tel_number, other_numbers, message_tracker):
    sms_client = SMSClient()
    sms_sent = None
    for data_sender in data_senders:
        phone_number = data_sender.get(
            'mobile_number') #This should not be a dictionary but the API in import_data should be fixed to return entity
        if phone_number is not None:
            logger.info(("Sending broadcast message to %s from %s") % (phone_number, organization_tel_number))
            sms_sent = sms_client.send_sms(organization_tel_number, phone_number, message)
        if sms_sent:
            message_tracker.increment_outgoing_message_count_by(1)

    for number in other_numbers:
        number = number.strip()
        logger.info(("Sending broadcast message to %s from %s") % (number, organization_tel_number))
        sms_sent = sms_client.send_sms(organization_tel_number, number, message)
        if sms_sent:
            message_tracker.increment_outgoing_message_count_by(1)

    return sms_sent


def create_request(questionnaire_form, username, is_update=None):
    return Request(message=questionnaire_form.cleaned_data,
        transportInfo=
        TransportInfo(transport="web",
            source=username,
            destination=""
        ), is_update=is_update)


def _translate_messages(error_dict, fields):
    errors = dict()

    for field in fields:
        if field.code in error_dict:
            error = error_dict[field.code][0]
            if type(field) == TextField:
                text, code = error.split(' ')[1], field.code
                errors[code] = [_("Answer %s for question %s is longer than allowed.") % (text, code)]
            if type(field) == IntegerField:
                number, error_context = error.split(' ')[1], error.split(' ')[6]
                errors[field.code] = [
                    _("Answer %s for question %s is %s than allowed.") % (number, field.code, _(error_context),)]
            if type(field) == GeoCodeField:
                errors[field.code] = [_(
                    "Incorrect GPS format. The GPS coordinates must be in the following format: xx.xxxx,yy.yyyy. Example -18.8665,47.5315")]
            if type(field) == DateField:
                answer, format = error.split(' ')[1], field.date_format
                errors[field.code] = [_("Answer %s for question %s is invalid. Expected date in %s format") % (
                    answer, field.code, format)]

    return errors


def errors_to_list(errors, fields):
    error_dict = dict()
    for key, value in errors.items():
        error_dict.update({key: [value] if not isinstance(value, list) else value})
    return _translate_messages(error_dict, fields)


def is_project_exist(f):
    def wrapper(*args, **kw):
        try:
            ret = f(*args, **kw)
        except AttributeError, e:
            if e[0] == "'NoneType' object has no attribute 'qid'":
                raise Http404
            raise e
        return ret

    return wrapper