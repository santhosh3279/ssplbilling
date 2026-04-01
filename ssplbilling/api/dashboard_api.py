import json
import os
import frappe
import re

@frappe.whitelist()
def get_allowed_series():
    """Return a list of naming series allowed for the current user.

    Logic:
    1. Read 'SSPL Billing Settings' -> 'user_series' table for the current user.
    2. If no record for the user exists, return all available series (fallback).
    3. Split comma-separated series values and collect prefixes.
    4. If 'ALL' is among the prefixes, return all available series.
    5. Compare alphabetic parts of available series with allowed prefixes.
    """

    def get_alpha(s):
        return re.sub(r"[^A-Za-z]", "", s or "")

    def _fallback_series():
        """Read series from Property Setter or DocType meta as last resort."""
        try:
            prop_value = frappe.db.get_value(
                "Property Setter",
                {"doc_type": "Sales Invoice", "field_name": "naming_series", "property": "options"},
                "value",
            )
            if prop_value:
                series = [s.strip() for s in prop_value.split("\n") if s.strip()]
                if series:
                    return series
        except Exception:
            pass
        try:
            meta = frappe.get_meta("Sales Invoice")
            sf = meta.get_field("naming_series")
            if sf and sf.options:
                series = [s.strip() for s in sf.options.split("\n") if s.strip()]
                if series:
                    return series
        except Exception:
            pass
        return ["SINV-.YY.-"]

    settings = None
    available = []
    user_series_rows = []
    try:
        settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
        available = [r.series for r in settings.billing_series if r.series]
        user_series_rows = list(settings.user_series or [])
    except Exception:
        pass

    # If billing_series table is empty, fall back to ERPNext naming series
    if not available:
        available = _fallback_series()

    user = frappe.session.user

    # Administrator / admin gets everything
    if user in ["Administrator", "admin"]:
        return {"allowed_series": available, "user_allowed_string": "ALL"}

    # Find rows for this user
    user_rows = [r for r in user_series_rows if r.user == user]
    if not user_rows:
        return {"allowed_series": available, "user_allowed_string": ""}  # Fallback: show all

    # Extract and split allowed series prefixes
    allowed_prefixes = []
    for r in user_rows:
        raw = r.allowed_series_seperated_by_comma or ""
        if raw:
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            allowed_prefixes.extend(parts)

    # Check for "ALL"
    if "ALL" in allowed_prefixes:
        return {"allowed_series": available, "user_allowed_string": ",".join(allowed_prefixes)}

    allowed_alphas = [get_alpha(p)[:3] for p in allowed_prefixes]

    # Filter available series by matching alpha parts (up to first 3 chars)
    result = [s for s in available if any(get_alpha(s)[:3].startswith(a) for a in allowed_alphas)]

    return {
        "allowed_series": result if result else available,
        "user_allowed_string": ",".join(allowed_prefixes),
    }

@frappe.whitelist()
def save_default_zoom(zoom):
	"""Persist zoom_value to the current user's row in the user_series child table."""
	user = frappe.session.user
	doc = frappe.get_doc("SSPL Billing Settings", "SSPL Billing Settings")
	user_row = next((r for r in doc.user_series if r.user == user), None)
	if not user_row:
		frappe.throw(f"No user series row found for {user}. Add the user in SSPL Billing Settings first.")
	user_row.zoom_value = str(int(float(zoom)))
	doc.save(ignore_permissions=True)
	frappe.clear_document_cache("SSPL Billing Settings", "SSPL Billing Settings")
	return {"user_zoom": user_row.zoom_value}


@frappe.whitelist()
def get_system_stats():
	"""Return current RAM and CPU usage for the server."""
	import psutil
	mem = psutil.virtual_memory()
	cpu = psutil.cpu_percent(interval=0.2)
	return {
		"ram_used_gb": round(mem.used / (1024 ** 3), 1),
		"ram_total_gb": round(mem.total / (1024 ** 3), 1),
		"ram_percent": round(mem.percent, 1),
		"cpu_percent": round(cpu, 1),
	}


@frappe.whitelist()
def clear_ram_cache():
	"""Drop Linux page cache.

	Strategy (tried in order):
	1. Direct write to /proc/sys/vm/drop_caches — works when running as root (Docker).
	2. sudo tee /proc/sys/vm/drop_caches — works on bare-metal with a sudoers rule.
	"""
	import os
	import subprocess
	import psutil

	mem_before = psutil.virtual_memory()
	freed = False
	error = ""

	# Strategy 1: direct write (root / Docker)
	try:
		with open("/proc/sys/vm/drop_caches", "w") as f:
			f.write("3")
		freed = True
	except PermissionError:
		pass
	except Exception as e:
		error = str(e)

	# Strategy 2: sudo tee (bare-metal with sudoers rule)
	if not freed:
		try:
			result = subprocess.run(
				["sudo", "tee", "/proc/sys/vm/drop_caches"],
				input=b"3",
				capture_output=True,
				timeout=10,
			)
			if result.returncode == 0:
				freed = True
			else:
				error = result.stderr.decode().strip() or "sudo tee failed"
		except FileNotFoundError:
			error = "sudo not found"
		except Exception as e:
			error = str(e)

	mem_after = psutil.virtual_memory()
	return {
		"freed": freed,
		"error": error if not freed else "",
		"ram_used_gb": round(mem_after.used / (1024 ** 3), 1),
		"ram_total_gb": round(mem_after.total / (1024 ** 3), 1),
		"ram_percent": round(mem_after.percent, 1),
		"freed_gb": round((mem_before.used - mem_after.used) / (1024 ** 3), 1),
	}


@frappe.whitelist()
def get_active_sessions():
	"""Return users currently active on this site (session updated within last 15 minutes)."""
	rows = frappe.db.sql(
		"""
		SELECT user, ipaddress, MAX(lastupdate) AS last_seen
		FROM tabSessions
		WHERE status = 'Active'
		  AND lastupdate >= NOW() - INTERVAL 15 MINUTE
		  AND user != 'Guest'
		GROUP BY user, ipaddress
		ORDER BY last_seen DESC
		""",
		as_dict=True,
	)
	unique_ips = len({r.ipaddress for r in rows if r.ipaddress})
	return {
		"sessions": [
			{
				"user": r.user,
				"ip": r.ipaddress or "unknown",
				"last_seen": str(r.last_seen),
			}
			for r in rows
		],
		"unique_users": len({r.user for r in rows}),
		"unique_ips": unique_ips,
	}


@frappe.whitelist()
def get_active_sites():
	"""Return all site names (directories containing site_config.json) in this bench."""
	sites_path = os.path.join(os.path.dirname(frappe.get_site_path()))
	sites = []
	for entry in os.scandir(sites_path):
		if entry.is_dir() and os.path.exists(os.path.join(entry.path, "site_config.json")):
			sites.append(entry.name)
	return {"sites": sorted(sites), "count": len(sites)}


def _is_docker():
	"""Return True when this process is running inside a Docker container."""
	return os.path.exists("/.dockerenv")


def _docker_host_ip():
	"""Resolve the Docker host IP from the container's default gateway.

	Falls back to the BACKUP_SSH_HOST env-var, then 'host.docker.internal'.
	"""
	import socket
	import struct
	try:
		with open("/proc/net/route") as f:
			for line in f:
				fields = line.strip().split()
				if len(fields) >= 3 and fields[1] == "00000000":
					# Gateway field is little-endian hex
					return socket.inet_ntoa(struct.pack("<I", int(fields[2], 16)))
	except Exception:
		pass
	return os.environ.get("BACKUP_SSH_HOST", "host.docker.internal")


@frappe.whitelist()
def run_manual_backup():
	"""Run /opt/scripts/frappe_backup.sh.

	- Bare-metal: executes via sudo directly.
	- Docker: SSHes to the host server and runs the script there.

	Docker requirements:
	  • SSH key mounted into the container (default: /home/erpdev/.ssh/id_rsa).
	  • Host accepts the key for BACKUP_SSH_USER (default: erpdev).
	  • Optionally set BACKUP_SSH_HOST env-var to override auto-detected gateway IP.
	"""
	import subprocess

	script = os.environ.get("BACKUP_SCRIPT", "/opt/scripts/frappe_backup.sh")

	if _is_docker():
		host = os.environ.get("BACKUP_SSH_HOST") or _docker_host_ip()
		user = os.environ.get("BACKUP_SSH_USER", "erpdev")
		key  = os.environ.get("BACKUP_SSH_KEY",  "/home/erpdev/.ssh/id_rsa")
		cmd = [
			"ssh",
			"-i", key,
			"-o", "StrictHostKeyChecking=no",
			"-o", "ConnectTimeout=10",
			f"{user}@{host}",
			f"sudo {script}",
		]
	else:
		cmd = ["sudo", script]

	result = subprocess.run(cmd, capture_output=True, timeout=600)
	return {
		"success": result.returncode == 0,
		"stdout": result.stdout.decode(errors="replace").strip(),
		"stderr": result.stderr.decode(errors="replace").strip(),
		"returncode": result.returncode,
	}


@frappe.whitelist()
def get_billing_settings():
	"""Return SSPL Billing Settings; user_zoom and accounts are resolved for the current user."""
	settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
	user = frappe.session.user
	user_row = next((r for r in settings.user_series if r.user == user), None)

	# Fetch Mode of Payment to Account mappings
	mop_accounts = frappe.get_all("Mode of Payment Account", 
		filters={"company": "Sundaram and Sons Private Ltd"}, 
		fields=["parent", "default_account"])
	mop_map = {r.parent: r.default_account for r in mop_accounts}

	user_zoom = (user_row.zoom_value or "") if user_row else ""
	user_defaults = {
		"cash": (user_row.cash or "") if user_row else "",
		"card": (user_row.card or "") if user_row else "",
		"upi": (user_row.upi or "") if user_row else "",
		"bank": (user_row.bank or "") if user_row else "",
		"bank_account": (user_row.bank or "") if user_row else "",
		"warehouse": (user_row.warehouse or "") if user_row else "",
		"cost_center": (user_row.cost_center or "") if user_row else "",
		"income_account": (user_row.income_account or "") if user_row else "",
		"default_printer": (user_row.default_printer or "") if user_row else "",
	}

	return {
		"discount_account": settings.discount_account or "",
		"freight_account": settings.freight or "",
		"tax_paid_on_purchase": settings.tax_paid_on_purchase or "",
		"packing_charge": settings.packing_charge or "",
		"loading": settings.loading or "",
		"other_charges": settings.other_charges or "",
		"cipher_map": settings.cipher_map or "",
		"mop_map": mop_map,
		"user_zoom": user_zoom,
		"user_defaults": user_defaults,		"billing_series": [
			{
				"series": r.series or "",
				"price_list": r.price_list or "",
				"tax_template": r.tax_template or "",
				"print_format": r.print_format or "",
			}
			for r in settings.billing_series
		],
		"user_series": [
			{
				"user": r.user or "",
				"allowed_series": r.allowed_series_seperated_by_comma or "",
				"zoom_value": r.zoom_value or "",
				"cash": r.cash or "",
				"card": r.card or "",
				"upi": r.upi or "",
				"bank": r.bank or "",
				"bank_account": r.bank or "",
				"warehouse": r.warehouse or "",
				"cost_center": r.cost_center or "",
				"income_account": r.income_account or "",
				"admin": r.admin or 0,
				"cashier": r.cashier or 0,
				"biller": r.biller or 0,
				"accounts": r.accounts or 0,
				"default_printer": r.default_printer or "",
			}
			for r in settings.user_series
		],
		"printer_settings": [
			{
				"user": r.user or "",
				"printer": r.printer or "",
				"template": r.template or "",
			}
			for r in (settings.table_vycb or [])
		],
		"visible_accounts": [
			{
				"account": r.account or "",
				"label": r.label or "",
			}
			for r in (settings.visible_accounts or [])
		],
	}
