app_name = "return_bottle"
app_title = "Return Bottle"
app_publisher = "Amr Basha"
app_description = "This app for pos return bottles"
app_email = "amrbasha9000@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "return_bottle",
# 		"logo": "/assets/return_bottle/logo.png",
# 		"title": "Return Bottle",
# 		"route": "/return_bottle",
# 		"has_permission": "return_bottle.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/return_bottle/css/return_bottle.css"
# app_include_js = "/assets/return_bottle/js/return_bottle.js"

# include js, css files in header of web template
# web_include_css = "/assets/return_bottle/css/return_bottle.css"
# web_include_js = "/assets/return_bottle/js/return_bottle.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "return_bottle/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "return_bottle/public/icons.svg"

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
# 	"methods": "return_bottle.utils.jinja_methods",
# 	"filters": "return_bottle.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "return_bottle.install.before_install"
# after_install = "return_bottle.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "return_bottle.uninstall.before_uninstall"
# after_uninstall = "return_bottle.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "return_bottle.utils.before_app_install"
# after_app_install = "return_bottle.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "return_bottle.utils.before_app_uninstall"
# after_app_uninstall = "return_bottle.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "return_bottle.notifications.get_notification_config"

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"return_bottle.tasks.all"
# 	],
# 	"daily": [
# 		"return_bottle.tasks.daily"
# 	],
# 	"hourly": [
# 		"return_bottle.tasks.hourly"
# 	],
# 	"weekly": [
# 		"return_bottle.tasks.weekly"
# 	],
# 	"monthly": [
# 		"return_bottle.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "return_bottle.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "return_bottle.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "return_bottle.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["return_bottle.utils.before_request"]
# after_request = ["return_bottle.utils.after_request"]

# Job Events
# ----------
# before_job = ["return_bottle.utils.before_job"]
# after_job = ["return_bottle.utils.after_job"]

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
# 	"return_bottle.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }



# Keep the standard ERPNext POS page; inject a small optional toolbar action.
page_js = {"point-of-sale": "public/js/bottle_return_pos.js"}

# POS invoices can redeem bottle points but do not earn points from sales.
# Important: if another app overrides POS Invoice, merge the override classes.
override_doctype_class = {
    "POS Invoice": "return_bottle.overrides.BottleReturnPOSInvoice",
}

# Create per-profile fields on install and migration; do not update ERPNext core.
after_install = "return_bottle.pos_profile.setup_pos_profile_fields"
after_migrate = "return_bottle.pos_profile.setup_pos_profile_fields"
doc_events = {
    "POS Profile": {
        "validate": "return_bottle.pos_profile.validate_pos_profile",
    },
}
