app_name = "aion_custom_hr"
app_title = "aion_custom_hr"
app_publisher = "ard"
app_description = "aion_custom_hr"
app_email = "lsi.louati@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "aion_custom_hr",
# 		"logo": "/assets/aion_custom_hr/logo.png",
# 		"title": "aion_custom_hr",
# 		"route": "/aion_custom_hr",
# 		"has_permission": "aion_custom_hr.api.permission.has_app_permission"
# 	}
# ]


# Includes in <head>
# ------------------
fixtures = [
    "Custom Field",
    "Salary Component",
    {"dt": "Salary Structure Assignment"}
]

# include js, css files in header of desk.html
# app_include_css = "/assets/aion_custom_hr/css/aion_custom_hr.css"
# app_include_js = "/assets/aion_custom_hr/js/aion_custom_hr.js"

# include js, css files in header of web template
# web_include_css = "/assets/aion_custom_hr/css/aion_custom_hr.css"
# web_include_js = "/assets/aion_custom_hr/js/aion_custom_hr.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "aion_custom_hr/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Attendance": "public/js/attendance_status.js",
    "Appraisal": "public/js/appraisal_monthly_score.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "aion_custom_hr/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "aion_custom_hr.utils.jinja_methods",
# 	"filters": "aion_custom_hr.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "aion_custom_hr.install.before_install"
# after_install = "aion_custom_hr.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "aion_custom_hr.uninstall.before_uninstall"
# after_uninstall = "aion_custom_hr.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "aion_custom_hr.utils.before_app_install"
# after_app_install = "aion_custom_hr.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "aion_custom_hr.utils.before_app_uninstall"
# after_app_uninstall = "aion_custom_hr.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "aion_custom_hr.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Appraisal": {
        "on_submit": "aion_custom_hr.api.update_monthly_appraisal_score_handler.update_monthly_appraisal_score_handler",
        "on_update": "aion_custom_hr.api.update_monthly_appraisal_score_handler.update_monthly_appraisal_score_handler"
    },
    "Attendance": {
        "validate": "aion_custom_hr.api.attendance_status.set_attendance_status"
    },
    "Leave Application": {
        "validate": "aion_custom_hr.api.leave_application.validate_leave_balance"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"aion_custom_hr.tasks.all"
# 	],
# 	"daily": [
# 		"aion_custom_hr.tasks.daily"
# 	],
# 	"hourly": [
# 		"aion_custom_hr.tasks.hourly"
# 	],
# 	"weekly": [
# 		"aion_custom_hr.tasks.weekly"
# 	],
# 	"monthly": [
# 		"aion_custom_hr.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "aion_custom_hr.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "aion_custom_hr.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "aion_custom_hr.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["aion_custom_hr.utils.before_request"]
# after_request = ["aion_custom_hr.utils.after_request"]

# Job Events
# ----------
# before_job = ["aion_custom_hr.utils.before_job"]
# after_job = ["aion_custom_hr.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"aion_custom_hr.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

