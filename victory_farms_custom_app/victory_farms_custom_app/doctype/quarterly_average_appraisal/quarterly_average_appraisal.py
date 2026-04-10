import frappe
from frappe.utils import getdate, get_first_day, get_last_day, flt
from frappe.model.document import Document

class QuarterlyAverageAppraisal(Document):
	def before_submit(self):
		self.get_department_data()

	def on_submit(self):
		self.create_quarterly_payout()

	def create_quarterly_payout(self):
		"""Create an Appraisal Payout document for this quarterly appraisal uses this doc's
		`start_date`/`end_date` and sets `payout_frequency` to "Quarterly".
		"""
		ap_doc = frappe.new_doc("Appraisal Payout")
		ap_doc.posting_date = getattr(self, "posting_date", None)
		ap_doc.start_date = getattr(self, "start_date", None)
		ap_doc.end_date = getattr(self, "end_date", None)
		ap_doc.payout_frequency = "Quarterly"
		bonus_calculation_amount = ap_doc.get_amount_used_for_bonus_calculation(self.employee)

		# Individual
		individual_score_value = getattr(self, "total_individual_score", 0)
		individual_score = flt((individual_score_value * 100) / 5, 2)
		matrix_percent = ap_doc.get_matrix_percent(individual_score)
		individual_bonus_percent = ap_doc.get_bonus_percent(self.bonus_potential, matrix_percent)
		individual_bonus = flt((individual_bonus_percent / 100) * bonus_calculation_amount, 3)

		# Department
		department_score_value = getattr(self, "total_avg", 0)
		department_score = flt((department_score_value * 100) / 5, 2)
		matrix_percent = ap_doc.get_matrix_percent(department_score)
		department_bonus_percent = ap_doc.get_bonus_percent(self.bonus_potential_department, matrix_percent)
		department_bonus = flt((department_bonus_percent / 100) * bonus_calculation_amount, 3)

		ap_doc.append("appraisal_payout_details", {
			"employee": self.employee,
			"individual_score": individual_score,
			"individual_score_value": individual_score_value,
			"department_score": department_score,
			"department_score_value": department_score_value,
			"individual_bonus": individual_bonus,
			"department_bonus": department_bonus,
			"total_bonus": individual_bonus + department_bonus,
		})
		ap_doc.flags.ignore_permissions = True
		ap_doc.save()
		self.db_set("appraisal_payout", ap_doc.name)

	@frappe.whitelist()
	def get_department_data(self):
		"""Computes monthly and quarter-level department & individual scores.
		Uses this document's `start_date` and `end_date` to build quarter buckets,
		applies department weightings from the employee profile, populates
		per-month individual/department averages and computes final scores.
		"""
		self.department_map = {
			r.get("department"): (r.get("weightage") or 0)
			for r in self.get_employee_bonus_department_data()
		}

		month_ranges = self._build_month_ranges_from_dates(self.start_date, self.end_date)
		if not month_ranges:
			return

		# Individual scores per month
		indi_scores = self._get_individual_scores_for_months(month_ranges)
		for i, score in enumerate(indi_scores, start=1):
			self.db_set(f"month_{i}_individual", score or 0)

		# Department appraisals and weighted aggregation
		dep_rows = self._get_department_appraisals_for_months(month_ranges)
		dep_month_sum = {}
		dep_month_count = {}

		# clear child table if present
		if self.meta.get_field("monthly_department_details"):
			self.set("monthly_department_details", [])
		else:
			self._monthly_department_audit = []

		for r in dep_rows:
			sd = r.get("start_date")
			if not sd:
				continue
			month_index = next((i for i, (fr, to) in enumerate(month_ranges, start=1) if fr <= sd <= to), None)
			if not month_index:
				continue

			dept = r.get("department")
			weight = self.department_map.get(dept, 0)
			key = (month_index, dept, weight)
			dep_month_sum.setdefault(key, 0)
			dep_month_sum[key] += r.get("total_goal_score", 0) or 0
			dep_month_count.setdefault(key, 0)
			dep_month_count[key] += 1

			entry = {
				"month_index": month_index,
				"appraisal_cycle": r.get("appraisal_cycle"),
				"department": dept,
				"weightage": weight,
				"score": r.get("total_goal_score", 0),
			}
			if self.meta.get_field("monthly_department_details"):
				self.append("monthly_department_details", entry)
			else:
				self._monthly_department_audit.append(entry)

		month_count = len(month_ranges)
		month_weighted_avg = {i + 1: 0.0 for i in range(month_count)}
		for (month_index, _, weight), total in dep_month_sum.items():
			count = dep_month_count.get((month_index, _, weight), 1)
			month_weighted_avg[month_index] += flt((total / count) * (weight / 100.0), 3)

		for i in range(1, month_count + 1):
			self.db_set(f"month_{i}_department_avg", flt(month_weighted_avg.get(i, 0.0), 3))

		# Quarter-level individual average
		monthly_individuals = [flt(getattr(self, f"month_{i}_individual", 0)) for i in range(1, month_count + 1)]
		non_empty_individuals = [v for v in monthly_individuals if v and v > 0]
		self.total_individual_score = flt(sum(non_empty_individuals) / len(non_empty_individuals), 2) if non_empty_individuals else 0

		# Quarter-level department average
		monthly_depts = [month_weighted_avg.get(i, 0.0) for i in range(1, month_count + 1)]
		non_empty_depts = [v for v in monthly_depts if v and v > 0]
		self.total_avg = flt(sum(non_empty_depts) / len(non_empty_depts), 2) if non_empty_depts else 0

		# Total Department Average Score
		m1 = flt(getattr(self, "month_1_department_avg", 0.0))
		m2 = flt(getattr(self, "month_2_department_avg", 0.0))
		m3 = flt(getattr(self, "month_3_department_avg", 0.0))
		self.total_department_average_score = flt((m1 + m2 + m3) / 3.0, 4)

		
	def get_employee_bonus_department_data(self):
		"""Return employee department weight rows
		"""
		return frappe.get_all(
			"Department Details",
			filters={"parent": self.employee},
			fields=["department", "weightage"],
		)

	def _build_month_ranges_from_dates(self, start_date, end_date):
		if not start_date or not end_date:
			return []
		start = getdate(start_date)
		end = getdate(end_date)
		ranges = []
		cur = start.replace(day=1)
		while cur <= end and len(ranges) < 12:
			fr = get_first_day(cur)
			to = get_last_day(cur)
			fr = max(fr, start)
			to = min(to, end)
			ranges.append((fr, to))
			if cur.month == 12:
				cur = cur.replace(year=cur.year + 1, month=1)
			else:
				cur = cur.replace(month=cur.month + 1)
		return ranges

	def _get_individual_scores_for_months(self, month_ranges):
		APC = frappe.qb.DocType("Appraisal Cycle")
		APP = frappe.qb.DocType("Appraisal")

		q = (
			frappe.qb.from_(APP)
			.inner_join(APC)
			.on(APP.appraisal_cycle == APC.name)
			.select(APP.total_score, APC.start_date)
			.where((APP.employee == self.employee) & (APP.docstatus == 1) & (APC.start_date.between(month_ranges[0][0], month_ranges[-1][1])))
		)
		rows = q.run(as_dict=1)

		result = [0] * len(month_ranges)
		for r in rows:
			sd = r.get("start_date")
			if not sd:
				continue
			for idx, (fr, to) in enumerate(month_ranges, start=1):
				if fr <= sd <= to:
					result[idx - 1] = r.get("total_score") or 0
		return result

	def _get_department_appraisals_for_months(self, month_ranges):
		DPA = frappe.qb.DocType("Department Appraisal")
		APC = frappe.qb.DocType("Appraisal Cycle")

		year_start = month_ranges[0][0].replace(day=1)
		year_end = month_ranges[-1][1]

		q = (
			frappe.qb.from_(DPA)
			.inner_join(APC)
			.on(DPA.appraisal_cycle == APC.name)
			.select(DPA.department, DPA.total_goal_score, DPA.appraisal_cycle, APC.start_date)
			.where((DPA.docstatus == 1) & (DPA.department.isin(list(self.department_map.keys()))) & (APC.start_date.between(year_start, year_end)))
			.orderby(APC.start_date)
		)

		return q.run(as_dict=1)