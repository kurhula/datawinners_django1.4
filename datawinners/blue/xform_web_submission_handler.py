import json
from django.contrib import messages
from django.http import HttpResponseBadRequest, HttpResponse
from django.utils.translation import ugettext
from datawinners.accountmanagement.models import NGOUserProfile, Organization
from datawinners.feeds.database import get_feeds_database
from datawinners.feeds.mail_client import mail_feed_errors
from datawinners.main.database import get_database_manager
from datawinners.messageprovider.messages import WEB
from datawinners.submission.views import check_quotas_and_update_users, check_quotas_for_trial
from datawinners.xforms.views import sp_submission_logger, logger, get_errors, is_authorized_for_questionnaire
from mangrove.transport import Request, TransportInfo
from mangrove.errors.MangroveException import ExceedSMSLimitException
from mangrove.transport.player.new_players import XFormPlayerV2
from mangrove.transport.repository.survey_responses import get_survey_response_by_id
from mangrove.utils.dates import py_datetime_to_js_datestring


class XFormWebSubmissionHandler():

    def __init__(self, request):
        self.request = request
        self.request_user = request.user
        self.manager = get_database_manager(self.request_user)
        self.player = XFormPlayerV2(self.manager, get_feeds_database(self.request_user))
        self.xml_submission_file = request.POST['form_data']
        self.retain_files = request.POST['retain_files'].split(',') if request.POST.get('retain_files') else None

        self.user_profile = NGOUserProfile.objects.get(user=self.request_user)
        self.mangrove_request = Request(message=self.xml_submission_file, media=request.FILES,
            retain_files=self.retain_files,
            transportInfo=
            TransportInfo(transport=WEB,
                source=self.request_user.email,
                destination=''
            ))
        self.organization = Organization.objects.get(org_id=self.user_profile.org_id)

    def create_new_submission_response(self):
        try:
            if not is_authorized_for_questionnaire(self.manager, self.request_user, self.request.POST['form_code']):
                return HttpResponse(status=403)
            if self.organization.in_trial_mode:
                check_quotas_for_trial(self.organization)
        except Exception as e:
            if not isinstance(e, ExceedSMSLimitException):
                raise e
        player_response = self.player.add_survey_response(self.mangrove_request, self.user_profile.reporter_id,
                                                          logger=sp_submission_logger)
        return self._post_save(player_response)

    def update_submission_response(self, survey_response_id):

        if not is_authorized_for_questionnaire(self.manager, self.request_user, self.form_code):
            return HttpResponse(status=403)

        survey_response = get_survey_response_by_id(self.manager, survey_response_id)
        if not survey_response:
            raise LookupError()

        player_response = self.player.update_survey_response(self.mangrove_request,
                                                      logger=sp_submission_logger, survey_response=survey_response)
        return self._post_save(player_response)

    def _post_save(self, response):
        mail_feed_errors(response, self.manager.database_name)
        if response.errors:
            logger.error("Error in submission : \n%s" % get_errors(response.errors))
            messages.error(self.request, ugettext('Submission failed %s' % get_errors(response.errors)), extra_tags='error')
            return HttpResponseBadRequest()

        self.organization.increment_message_count_for(incoming_web_count=1)
        content = json.dumps({'submission_uuid': response.survey_response_id,
                              'version': response.version,
                              'created': py_datetime_to_js_datestring(response.created)})
        success_response = HttpResponse(content, status=201, content_type='application/json')
        success_response['submission_id'] = response.survey_response_id
        messages.success(self.request, ugettext('Successfully submitted'), extra_tags='success')

        check_quotas_and_update_users(self.organization)
        return success_response