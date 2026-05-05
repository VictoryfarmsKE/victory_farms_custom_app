# Victory Farms Custom App

## 1. Overview

This app is a broad Victory Farms ERPNext/HRMS customization layer focused on payroll, leave, employee operations, appraisals, overtime, store deductions, and a set of finance/statutory reports. The codebase is primarily an HR/payroll and operations customization app with some inventory and banking/reporting utilities.

Key problems it solves:

- Extends payroll to support employees paid in currencies other than the company currency.
- Adds leave-related automations: yearly employee holiday lists, monthly earned-leave allocations, leave encashment payouts, and leave-liability journal entries.
- Turns store purchases into staged salary deductions through `Additional Salary` documents.
- Adds appraisal aggregation and payout generation for annual and quarterly cycles.
- Generates overtime timesheets from approved overtime requests.
- Captures spoilage item summaries from specific stock entry flows.
- Adds custom reports and export templates for payroll/statutory/bank operations.

Where it fits in the broader system:

- ERPNext core: `Employee`, `Company`, `Leave Type`, `Leave Allocation`, `Salary Component`, `Stock Entry`, `Journal Entry`, `Holiday List`, `Warehouse`, `Account`, `Additional Salary`.
- HRMS: `Payroll Entry`, `Salary Slip`, `Leave Application`, payroll periods, leave balances, leave encashment, and salary structure assignment logic.
- Other custom apps in this bench:
	- `nl_attendance_timesheet` for overtime timesheet generation.

## 2. Architecture & Design

High-level architecture:

- `hooks.py` is the main integration surface. It injects form/list JS, hooks document events, overrides HRMS DocType classes, schedules cron jobs, exports fixtures, and runs an `after_migrate` task.
- `migrate.py` applies JSON-defined custom fields and property setters after every site migrate.
- `victory_farms_custom_app/customization/` contains most behavior changes for core ERPNext/HRMS DocTypes.
- `victory_farms_custom_app/doctype/` contains custom business DocTypes for appraisals, deductions, overtime, leave grades, weekly off assignment, and related child tables.
- `victory_farms_custom_app/custom_fields/`, `property_setter/`, and `custom/` hold JSON-driven schema/UI customizations outside Python hooks.
- `report/` contains operational exports and analytics, especially payroll, bank, statutory, store, branch variance, and overtime reports.

Key DocTypes and relationships:

- `Store Deduction`
	- Creates or updates `Additional Salary` rows over multiple payroll periods.
	- Appends child-table rows into `Additional Salary.custom_store_deduction_details` using the `SD Details` child table.
- `Annual Appraisal`
	- Aggregates individual, department, and company scores.
	- Creates an `Appraisal Payout` document on submit.
	- Reads from `Appraisal`, `Appraisal Cycle`, `Department Appraisal`, `Company Appraisal`, and employee group-company rows.
- `Quarterly Average Appraisal`
	- Similar to annual appraisal but for a date range / quarter and creates a quarterly `Appraisal Payout`.
- `Commercial Holiday Pay`
	- Calculates payable days and creates an `Additional Salary` entry on submit.
- `Overtime Request`
	- Converts approved employee overtime rows into timesheets using functions from `nl_attendance_timesheet`.
- `Leave Grade`
	- Used by `Leave Type.custom_based_on_employee_grade` auto-allocation logic.
- `Item Summery` / spoilage-related child tables
	- Populated from `Stock Entry` when spoilage repacks are updated.

Custom scripts, hooks, background jobs, and APIs:

- `doctype_js` customizes:
	- `Additional Salary`
	- `Leave Encashment`
	- `Salary Structure Assignment`
	- `Stock Entry`
	- `Leave Type`
	- `Holiday List`
	- `Employee`
	- `Leave Application`
- `doctype_list_js`
	- `Employee Checkin` list view adds a bulk action to create missing logs.
- `override_doctype_class`
	- `Payroll Entry` → custom multi-currency employee loading and JV behavior.
	- `Salary Slip` → custom component evaluation and foreign-currency handling.
- `doc_events`
	- `Stock Entry.on_update`
	- `Leave Application.on_submit`
	- `Salary Slip.before_validate`, `Salary Slip.validate`
	- `Employee.validate`, `Employee.after_insert`
	- `Employee Checkin.validate`
	- `Appraisal.before_validate`
	- `Leave Allocation.on_submit`, `Leave Allocation.on_update_after_submit`
	- `Salary Structure Assignment.on_submit`
- Whitelisted methods are used by JS buttons and utilities, including leave allocation creation, employee holiday-list generation, employee checkin completion, and probation checks.

## 3. Installation & Setup

```bash
cd /path/to/frappe-bench
bench get-app /path/to/apps/victory_farms_custom_app
bench --site <site-name> install-app victory_farms_custom_app
bench build
bench --site <site-name> migrate
```

## 4. Configuration

Key settings and custom fields:

- `Company`
	- `custom_leave_liability_account`
	- `custom_leave_expense_account`
	- payroll/withholding defaults and bonus-potential fields
- `Leave Type`
	- `custom_create_auto_allocation`
	- `custom_based_on_employee_grade`
	- `custom_max_active_allowed_leaves`
	- `custom_create_liability_entries`
	- `custom_salary_component`
	- `custom_restricted_in_probation`
- `Salary Component`
	- `custom_is_negative_component`
	- `custom_is_in_employee_currency`
	- `is_for_store_deduction`
	- `ignore_for_jv`
	- `custom_debit_account`
- `Employee`
	- custom fields for holiday-list creation, exchange rates, appraisal details, and department weighting are expected by the code.
- `Holiday List`
	- a template list is selected via `custom_template_holiday_list`.

Operational master-data dependencies:

- `Salary Component` must have exactly one component flagged `is_for_store_deduction` for the store-deduction flow to behave predictably.
- `Company` must have leave liability and expense accounts configured for leave allocation and leave-application journal entries.
- `Navari Custom Payroll Settings` single DocType from [Navari VF custom app](https://github.com/navariltd/navari_vf) is required by `Overtime Request` to resolve overtime activity types.
- Appraisal flows expect related DocTypes such as `Appraisal Payout`, `Appraisal Cycle`, `Department Appraisal`, `Company Appraisal`, and `New Earned Bonus vs Attained Score` to exist and be populated.

Feature flags:

- The app uses custom fields as feature flags rather than a separate settings DocType.
- Examples:
	- `Leave Type.custom_create_auto_allocation`
	- `Leave Type.custom_based_on_employee_grade`
	- `Leave Type.custom_create_liability_entries`
	- `Employee.custom_create_individual_holiday_list`
	- `Employee.custom_appraisal_on_group`

## 5. Key Workflows

### Multi-currency payroll processing

1. `Payroll Entry` is replaced by `CustomPayrollEntry`.
2. `fill_employee_details()` selects employees by company and salary currency, then filters further by branch/department/designation.
3. `get_emp_list()` treats company-currency and non-company-currency employees differently.
4. JV generation is customized so salary-component accounts can depend on employee payroll cost center and special debit-account rules.

### Salary slip component conversion and net-pay adjustments

1. `Salary Slip` is replaced by `CustomSalarySlip`.
2. During `before_validate`, start/end dates are clipped to employee joining and relieving dates.
3. Structure components and additional salaries are recalculated, with optional exchange-rate conversion when `Salary Component.custom_is_in_employee_currency` is enabled.
4. Bonus-related fields and `custom_net_pay_excluding_bonus` are recomputed for specific salary structures.
5. Foreign-currency display fields are updated from the payroll exchange rate.

### Leave application to payout + liability reversal

1. When a `Leave Application` is submitted, `create_additional_salary()` calculates one or more payroll-period amounts based on the leave span and the 25th payroll cutoff.
2. The salary component is read from `Leave Type.custom_salary_component`.
3. Existing draft `Additional Salary` rows for the same employee/payroll date are reused when possible.
4. If `Leave Type.custom_create_liability_entries` is enabled, `create_reverse_jv()` creates a reversing leave-liability journal entry.
5. On the form, a probation check may warn users before approving restricted leave types.

### Leave allocation and leave-liability accounting

1. On the last day of the month, `auto_create_leave_allocation()` enqueues leave allocations for eligible earned leave types.
2. `create_leave_allocation()` filters active employees, optionally by grade, prorates allocations for mid-year joins, and updates/creates `Leave Allocation` rows.
3. When `Leave Allocation` is submitted or updated after submit, the app creates journal entries against company leave liability and expense accounts.
4. When a new `Salary Structure Assignment` is submitted, liability is recalculated for each eligible leave type using current remaining leave balances.

### Individual holiday list management

1. When an employee is inserted and `custom_create_individual_holiday_list` is checked, the app clones the active template holiday list and assigns it to that employee.
2. A yearly cron job and manual UI buttons can create new holiday lists for all active eligible employees.

### Store deduction lifecycle

1. On submit, `Store Deduction` creates the first draft `Additional Salary` entry using a store-deduction salary component.
2. The posting date and 25th-day cutoff determine the first payroll date.
3. `remaining_payments` is initialized to `period_of_payment - 1`.
4. During the 20th-24th scheduler window each month, `create_remaining_payments()` creates the next draft `Additional Salary` entry or appends to an existing one.
5. If the employee has a relieving date, remaining deductions are accelerated into the final applicable payroll date.

### Stock spoilage summary

1. `Stock Entry.on_update` runs only for draft `Stock Entry` documents of type `Repack Spoilage`.
2. Source-warehouse items are collected.
3. If any target warehouse is of type `Spoilage`, those items are copied into `custom_item_summery`.

### Appraisal payout generation

1. `Annual Appraisal` and `Quarterly Average Appraisal` aggregate scores from submitted appraisal data.
2. Department weighting is taken from employee-related department detail rows.
3. Company scoring may be single-company or weighted across group companies.
4. On submit, an `Appraisal Payout` document is created and linked back to the source appraisal document.

### Overtime request to timesheet creation

1. On submit, `Overtime Request` looks up overtime activities from `Navari Custom Payroll Settings`.
2. Each employee row is matched to approved attendance for the overtime date.
3. The app decides whether to create 1.5x or 2.0x overtime based on holiday detection.
4. Timesheets are created using helpers from `nl_attendance_timesheet`.

## 6. Code Structure

Folder breakdown:

- `victory_farms_custom_app/hooks.py`
	- App wiring: JS hooks, doc events, scheduler, override classes, fixtures, `after_migrate`.
- `victory_farms_custom_app/migrate.py`
	- Applies JSON custom fields and property setters after migrate.
- `victory_farms_custom_app/public/py/`
	- Python doc-event handler for stock entry spoilage summary.
- `victory_farms_custom_app/victory_farms_custom_app/customization/`
	- Core ERPNext/HRMS behavior extensions.
- `victory_farms_custom_app/victory_farms_custom_app/doctype/`
	- Custom business DocTypes and child tables.
- `victory_farms_custom_app/victory_farms_custom_app/custom_fields/`
	- JSON definitions of required custom fields on core DocTypes.
- `victory_farms_custom_app/victory_farms_custom_app/property_setter/`
	- JSON property setters, currently for appraisal-related DocTypes.
- `victory_farms_custom_app/victory_farms_custom_app/custom/`
	- Additional standard customizations exported as JSON.
- `victory_farms_custom_app/victory_farms_custom_app/report/`
	- Operational and compliance reports/export templates.

Important files:

- `hooks.py`: the best entry point for understanding what is actually active.
- `migrate.py`: critical for schema/application consistency after deploys.
- `customization/payroll_entry/payrol_entry.py`: main payroll override.
- `customization/salary_slip/salary_slip.py`: main salary-slip override.
- `customization/leave_type/leave_type.py`: leave auto-allocation logic.
- `customization/leave_application/utils/additional_salary.py`: leave payout and reverse-JV logic.
- `doctype/store_deduction/store_deduction.py`: staged employee deduction engine.

Entry points:

- Hook entry points from `hooks.py`
- Whitelisted utility methods used by client-side buttons
- Scheduler jobs:
	- leave allocation
	- store deduction continuation
	- new-year holiday-list creation

## 7. Customizations & Overrides

Overridden core behaviors:

- `Payroll Entry` class override via `CustomPayrollEntry`
- `Salary Slip` class override via `CustomSalarySlip`
- Form and list scripts on multiple core HR/payroll DocTypes
- `after_migrate` schema enforcement on core DocTypes through JSON custom fields and property setters

Non-override customizations :

- Store deduction writes custom child rows into `Additional Salary`.
- Leave application creates `Additional Salary` and `Journal Entry` records.
- Leave allocation and salary structure assignment create journal entries.
- Appraisal submit flows create `Appraisal Payout` documents.


## 8. Background Jobs & Scheduled Tasks

Configured cron jobs:

- `0 0 20-24 * *`
	- `leave_type.auto_create_leave_allocation`
	- `store_deduction.create_remaining_payments`
- `0 2 1 1 *`
	- `employee.create_holiday_list_for_new_year`

What they do:

- Leave allocation job creates monthly/yearly earned-leave allocations for active employees.
- Store deduction job creates follow-up `Additional Salary` rows for pending deductions.
- Holiday-list job clones the active holiday template list for each eligible employee.

## License

MIT