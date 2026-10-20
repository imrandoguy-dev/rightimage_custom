"""Applies (and exports) Right Image's own setup.

Every record in data/*.json is written to the site after each migrate, so a
hiper_solar update can never leave Right Image with the standard versions of
these records. Records are compared first and only saved when they differ, so
an unchanged site is not touched.

To capture a change made on the site (run on the server, then commit):
    bench --site rightimage.hipersignerp.cloud execute rightimage_custom.sync.export_all
To add a new record to the app:
    bench --site rightimage.hipersignerp.cloud execute rightimage_custom.sync.export_doc \
        --kwargs "{'doctype': 'Client Script', 'name': 'My Script'}"
"""

import json
import os

import frappe

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Applied in this order: doctypes before the fields and scripts that use them.
FILES = [
	("DocType", "doctype"),
	("Custom Field", "custom_field"),
	("Property Setter", "property_setter"),
	("Client Script", "client_script"),
	("Server Script", "server_script"),
	("Print Format", "print_format"),
	("Custom HTML Block", "custom_html_block"),
	("Workspace Sidebar", "workspace_sidebar"),
]

META = {
	"owner",
	"creation",
	"modified",
	"modified_by",
	"docstatus",
	"idx",
	"_user_tags",
	"_comments",
	"_assign",
	"_liked_by",
	"_last_update",
	"_seen",
	"migration_hash",
}
CHILD_META = (META - {"idx"}) | {"name", "parent", "parenttype", "parentfield"}


# ---------------------------------------------------------------- helpers


def _read(filename):
	path = os.path.join(DATA_DIR, f"{filename}.json")
	if not os.path.exists(path):
		return []
	with open(path, encoding="utf-8") as fh:
		return json.load(fh)


def _write(filename, docs):
	path = os.path.join(DATA_DIR, f"{filename}.json")
	with open(path, "w", encoding="utf-8") as fh:
		json.dump(docs, fh, indent=1, ensure_ascii=False)
		fh.write("\n")


def _norm(v):
	if v is None:
		return ""
	if isinstance(v, bool):
		return str(int(v))
	if isinstance(v, float) and v.is_integer():
		return str(int(v))
	return str(v)


def _clean(d):
	out = {}
	for k, v in d.items():
		if k in META:
			continue
		if isinstance(v, list):
			out[k] = [
				{ck: cv for ck, cv in row.items() if ck not in CHILD_META}
				for row in v
				if isinstance(row, dict)
			]
		else:
			out[k] = v
	return out


def _differs(existing, desired):
	for key, want in desired.items():
		if key in ("doctype", "name"):
			continue
		have = existing.get(key)
		if isinstance(want, list):
			have = have or []
			if len(have) != len(want):
				return True
			for h_row, w_row in zip(have, want):
				for ck, cv in w_row.items():
					if ck in ("doctype", "idx"):
						continue
					if _norm(h_row.get(ck)) != _norm(cv):
						return True
		elif _norm(have) != _norm(want):
			return True
	return False


def _custom_field_order(docs):
	"""Create custom fields after the custom field they are inserted after."""
	pending = list(docs)
	ordered = []
	while pending:
		names = {(d["dt"], d["fieldname"]) for d in pending}
		ready = [d for d in pending if (d["dt"], d.get("insert_after")) not in names]
		if not ready:  # cycle; just keep the rest as they are
			ready = pending
		ordered.extend(ready)
		pending = [d for d in pending if d not in ready]
	return ordered


def _missing_dependency(desired):
	"""A default print format that this site doesn't have yet (e.g. hiper_solar
	not updated) would break printing, so wait until it exists."""
	if desired["doctype"] == "Property Setter" and desired.get("property") == "default_print_format":
		return not frappe.db.exists("Print Format", desired.get("value"))
	return False


def upsert(desired):
	doctype, name = desired["doctype"], desired["name"]
	if _missing_dependency(desired):
		return "waiting"
	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		existing = _clean(doc.as_dict())
		if not _differs(existing, desired):
			return "same"
		doc.update({k: v for k, v in desired.items() if k not in ("doctype", "name")})
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)
		return "updated"
	doc = frappe.get_doc(dict(desired))
	doc.insert(ignore_permissions=True, set_name=name)
	return "created"


# ---------------------------------------------------------------- apply


def apply_all():
	counts = {"created": 0, "updated": 0, "same": 0, "waiting": 0, "failed": 0}
	failures = []
	for doctype, filename in FILES:
		docs = _read(filename)
		if doctype == "Custom Field":
			docs = _custom_field_order(docs)
		for desired in docs:
			try:
				result = upsert(desired)
				counts[result] += 1
				frappe.db.commit()
			except Exception:
				frappe.db.rollback()
				counts["failed"] += 1
				failures.append(f"{doctype} {desired.get('name')}")
				frappe.log_error(
					title=f"rightimage_custom: could not apply {doctype} {desired.get('name')}",
					message=frappe.get_traceback(),
				)

	frappe.clear_cache()
	summary = ", ".join(f"{k} {v}" for k, v in counts.items())
	print(f"rightimage_custom: {summary}")
	if failures:
		print("rightimage_custom: failed (see Error Log): " + "; ".join(failures))
	return counts


# ---------------------------------------------------------------- export


def _export_one(doctype, name):
	d = _clean(frappe.get_doc(doctype, name).as_dict())
	d["doctype"] = doctype
	return d


def export_all():
	"""Refresh every data file from the site's current records."""
	for doctype, filename in FILES:
		docs = []
		for existing in _read(filename):
			if frappe.db.exists(doctype, existing["name"]):
				docs.append(_export_one(doctype, existing["name"]))
			else:
				print(f"rightimage_custom: {doctype} {existing['name']} no longer exists, dropped")
		_write(filename, docs)
	print("rightimage_custom: export done, commit the data/ folder")


def export_doc(doctype, name):
	"""Add one record to the app (or refresh it)."""
	filename = dict(FILES).get(doctype)
	if not filename:
		frappe.throw(f"{doctype} is not handled by rightimage_custom")
	docs = [d for d in _read(filename) if d["name"] != name]
	docs.append(_export_one(doctype, name))
	_write(filename, docs)
	print(f"rightimage_custom: exported {doctype} {name}")
