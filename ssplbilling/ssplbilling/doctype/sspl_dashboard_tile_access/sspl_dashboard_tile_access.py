import frappe
from frappe import _
from frappe.model.document import Document


class SSPLDashboardTileAccess(Document):
	def validate(self):
		if self.applies_to == "User":
			self.user_group = None
			if not self.user:
				frappe.throw(_("User is required when Applies To is 'User'"))
			self.title = self.user
			dup_filters = {"applies_to": "User", "user": self.user}
		else:
			self.user = None
			if not self.user_group:
				frappe.throw(_("User Group is required when Applies To is 'User Group'"))
			self.title = self.user_group
			dup_filters = {"applies_to": "User Group", "user_group": self.user_group}

		dup_filters["name"] = ["!=", self.name]
		duplicate = frappe.db.exists("SSPL Dashboard Tile Access", dup_filters)
		if duplicate:
			frappe.throw(
				_("A Dashboard Tile Access record already exists for {0} ({1})").format(
					self.title, duplicate
				)
			)

		# Drop duplicate tile rows silently
		seen = set()
		unique_rows = []
		for row in self.tiles:
			if row.tile and row.tile not in seen:
				seen.add(row.tile)
				unique_rows.append(row)
		self.tiles = unique_rows
