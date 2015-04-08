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

# NAME_TB = by_xpath(".//*[@id='id_name']")
# WEB_CB = by_css("input#id_devices_1")
# MOBILE_NUMBER_TB = by_xpath(".//*[@id='id_telephone_number']")
# EMAIL_TB = by_css("input#id_email")
# COMMUNE_TB = by_xpath(".//*[@id='id_location']")
# GPS_TB = by_xpath(".//*[@id='id_geo_code']")
# OPEN_IMPORT_DIALOG_LINK = by_css("#import-datasenders")
# UNIQUE_ID_TB_LOCATOR = by_css("#id_short_code")
# CB_LET_US_GENERATE_ID_FOR_U = by_css("#id_generated_id")
# REGISTERED_DATASENDERS_LOCATOR = by_xpath("//a[text()='Registered Data Senders']")
# CANCEL = by_css("#cancel")
# REGISTER_BTN = by_css("input#id_register_button")
# ERROR_MESSAGE_LABEL = by_css(".errorlist>li")
# FLASH_MESSAGE_LABEL = by_css("#flash-message")
# DS_SETTING_DESCRIPTION = by_css("#setting_description")
GROUP_NAME_TB = by_css(".add_group_dialog input")
CANCEL_POP = by_css("input#close_pop")
