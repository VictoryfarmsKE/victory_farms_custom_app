from . import __version__ as app_version

app_name = "victory_farms_custom_app"
app_title = "Victory Farms Custom App"
app_publisher = "Solufy"
app_description = "Custom Inventory Report"
app_email = "contact@solufy.in"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/victory_farms_custom_app/css/victory_farms_custom_app.css"
# app_include_js = "/assets/victory_farms_custom_app/js/victory_farms_custom_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/victory_farms_custom_app/css/victory_farms_custom_app.css"
# web_include_js = "/assets/victory_farms_custom_app/js/victory_farms_custom_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "victory_farms_custom_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Additional Salary" : "victory_farms_custom_app/customization/additional_salary/additional_salary.js",
    "Leave Encashment" : "victory_farms_custom_app/customization/leave_encashment/leave_encashment.js",
    "Salary Structure Assignment": "victory_farms_custom_app/customization/salary_structure_assignment/salary_structure_assignment.js",
    "Stock Entry": "victory_farms_custom_app/customization/stock_entry_detail/stock_entry_detail.js",
    "Leave Type": "victory_farms_custom_app/customization/leave_type/leave_type.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "victory_farms_custom_app.utils.jinja_methods",
#	"filters": "victory_farms_custom_app.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "victory_farms_custom_app.install.before_install"
# after_install = "victory_farms_custom_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "victory_farms_custom_app.uninstall.before_uninstall"
# after_uninstall = "victory_farms_custom_app.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "victory_farms_custom_app.utils.before_app_install"
# after_app_install = "victory_farms_custom_app.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "victory_farms_custom_app.utils.before_app_uninstall"
# after_app_uninstall = "victory_farms_custom_app.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "victory_farms_custom_app.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Payroll Entry": "victory_farms_custom_app.victory_farms_custom_app.customization.payroll_entry.payrol_entry.CustomPayrollEntry",
    "Salary Slip": "victory_farms_custom_app.victory_farms_custom_app.customization.salary_slip.salary_slip.CustomSalarySlip"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }
doc_events = {
	"Stock Entry": {
		"on_update": "victory_farms_custom_app.public.py.stock_entry.stock_entry",
	},
    "Leave Application": {
        "on_submit" : "victory_farms_custom_app.victory_farms_custom_app.customization.leave_application.leave_application.on_submit"
    },
    "Salary Slip": {
        "before_validate": "victory_farms_custom_app.victory_farms_custom_app.customization.salary_slip.salary_slip.before_validate",
        "validate": "victory_farms_custom_app.victory_farms_custom_app.customization.salary_slip.salary_slip.validate"
    }
}
# Scheduled Tasks
# ---------------

scheduler_events = {
    "cron": {
        "0 0 28-31 * *": [
            "victory_farms_custom_app.victory_farms_custom_app.customization.leave_type.leave_type.auto_create_leave_allocation"
        ],
        "0 0 1 * *": [
            "victory_farms_custom_app.victory_farms_custom_app.doctype.store_deduction.store_deduction.create_remaining_payments"
        ]
    }
}


# Testing
# -------

# before_tests = "victory_farms_custom_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "victory_farms_custom_app.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "victory_farms_custom_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["victory_farms_custom_app.utils.before_request"]
# after_request = ["victory_farms_custom_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["victory_farms_custom_app.utils.before_job"]
# after_job = ["victory_farms_custom_app.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"victory_farms_custom_app.auth.validate"
# ]
fixtures = [{
    "doctype": "Custom Field",
        "filters": {
            "module": ["in", ["Victory Farms Custom App"]]
            }
    },
    {
    "doctype": "Client Script",
        "filters": {
            "module": ["in", ["Victory Farms Custom App"]]
            }
    }
]

after_migrate = "victory_farms_custom_app.migrate.after_migrate"
