# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from framework.utils.common_utils import *

# By default every locator should be CSS
# Abbr:
# TB - Text Box
# CB - Check Box
# RB - Radio Button
# BTN - Button
# DD - Drop Down
# LINK - Links
# LABEL - Label


# variable to access locators
LOCATOR = "locator"
BY = "by"

DATASENDERS_TAB = by_id("data_senders_tab")
DATA_TAB = by_id("data_tab")
SUBJECTS_TAB = by_id("subjects_tab")
REMINDERS_TAB = by_id("reminders_tab")
PROJECT_EDIT_LINK = by_id("edit_project")
PROJECT_STATUS_LABEL = by_css("span.project_status>span")
TEST_QUESTIONNAIRE_LINK = by_css("a.sms_tester")
MESSAGES_AND_REMINDERS_TAB = by_id("messages_and_reminders_tab")
SEND_MESSAGE_TAB = by_id("send_message_tab")
QUESTIONNAIRE_TAB = by_id("questionnaire_tab")
PROJECT_TITLE_LOCATOR = by_css(".project_title")
QUESTION_CODE_CONTAINER = by_css(".questionnaire-code")
WEB_QUESTIONNAIRE_PAGE = by_css(".web_questionnaire")
