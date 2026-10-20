import frappe
from frappe import _

from rightimage_custom import hooks
from rightimage_custom.sync import apply_all


def site_allowed() -> bool:
	return frappe.local.site in hooks.ALLOWED_SITES or bool(frappe.conf.get("rightimage_custom_allowed"))


def before_install():
	if not site_allowed():
		frappe.throw(
			_(
				"rightimage_custom is only for the Right Image site ({0}). "
				"It cannot be installed on {1}."
			).format(", ".join(hooks.ALLOWED_SITES), frappe.local.site),
			title=_("Wrong site"),
		)


def after_install():
	apply_all()


def after_migrate():
	if not site_allowed():
		# The app ended up on another site (e.g. a restored copy under a new
		# domain). Leave that site untouched.
		print(f"rightimage_custom: {frappe.local.site} is not an allowed site, skipping.")
		return
	apply_all()
