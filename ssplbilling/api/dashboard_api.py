import json
import os
import frappe
import re

@frappe.whitelist()
def get_all_naming_series():
    """Return naming series and their current values for core DocTypes."""
    from frappe.model.naming import NamingSeries
    
    doctypes = ["Sales Invoice", "Purchase Invoice", "Quotation", "Sales Order", "Purchase Order"]
    result = {}

    def _get_series_details(dt):
        series_options = []
        try:
            prop_value = frappe.db.get_value(
                "Property Setter",
                {"doc_type": dt, "field_name": "naming_series", "property": "options"},
                "value",
            )
            if prop_value:
                series_options = [s.strip() for s in prop_value.split("\n") if s.strip()]
        except Exception:
            pass
            
        if not series_options:
            try:
                meta = frappe.get_meta(dt)
                sf = meta.get_field("naming_series")
                if sf and sf.options:
                    series_options = [s.strip() for s in sf.options.split("\n") if s.strip()]
            except Exception:
                pass
        
        details = []
        for s in series_options:
            current = 0
            try:
                ns = NamingSeries(s)
                current = ns.get_current_value()
            except Exception:
                pass
            
            details.append({
                "prefix": s,
                "current": int(current) + 1
            })
        return details

    for dt in doctypes:
        result[dt] = _get_series_details(dt)
    
    return result

@frappe.whitelist()
def update_naming_series(doctype, series_list):
    """Update naming series options for a DocType via Property Setter."""
    if isinstance(series_list, str):
        series_list = json.loads(series_list)
    
    # Extract prefixes from the list of objects
    prefixes = []
    for item in series_list:
        if isinstance(item, dict):
            prefixes.append(item.get("prefix"))
        else:
            prefixes.append(str(item))

    value = "\n".join([s.strip() for s in prefixes if s.strip()])
    
    # Create or update Property Setter
    ps_name = frappe.db.get_value("Property Setter", {"doc_type": doctype, "field_name": "naming_series", "property": "options"})
    
    if ps_name:
        frappe.db.set_value("Property Setter", ps_name, "value", value)
    else:
        frappe.get_doc({
            "doctype": "Property Setter",
            "doctype_or_field": "DocField",
            "doc_type": doctype,
            "field_name": "naming_series",
            "property": "options",
            "property_type": "Text",
            "value": value
        }).insert(ignore_permissions=True)
    
    # Also update counters if provided
    from frappe.model.naming import NamingSeries
    for item in series_list:
        if isinstance(item, dict) and "current" in item:
            try:
                ns = NamingSeries(item["prefix"])
                # Next value from UI - 1 = current value in DB
                new_val = max(0, int(item["current"]) - 1)
                ns.update_counter(new_val)
            except Exception:
                pass

    frappe.clear_cache(doctype=doctype)
    return {"status": "success"}

@frappe.whitelist()
def update_single_series_counter(prefix, current):
    """Update a single naming series counter in tabSeries."""
    from frappe.model.naming import NamingSeries
    try:
        ns = NamingSeries(prefix)
        new_val = max(0, int(current) - 1)
        ns.update_counter(new_val)
        return {"status": "success"}
    except Exception as e:
        frappe.throw(f"Failed to update counter: {str(e)}")

@frappe.whitelist()
def get_all_users():
    """Return a list of all users from SSPL Billing Settings -> User Series."""
    settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
    return [{"value": r.user, "label": r.user} for r in settings.user_series if r.user]

@frappe.whitelist()
def get_allowed_series(doctype="Sales Invoice", user=None):
    """Return a list of naming series allowed for the current or specified user."""

    def get_alpha(s):
        return re.sub(r"[^A-Za-z]", "", s or "")

    def _fallback_series():
        """Read series from Property Setter or DocType meta as last resort."""
        try:
            prop_value = frappe.db.get_value(
                "Property Setter",
                {"doc_type": doctype, "field_name": "naming_series", "property": "options"},
                "value",
            )
            if prop_value:
                series = [s.strip() for s in prop_value.split("\n") if s.strip()]
                if series:
                    return series
        except Exception:
            pass
        try:
            meta = frappe.get_meta(doctype)
            sf = meta.get_field("naming_series")
            if sf and sf.options:
                series = [s.strip() for s in sf.options.split("\n") if s.strip()]
                if series:
                    return series
        except Exception:
            pass
        
        if doctype == "Sales Invoice":
            return ["SINV-.YY.-"]
        elif doctype == "Quotation":
            return ["SSPL-QT-.YYYY.-"]
        return []

    available = []
    user_series_rows = []
    try:
        settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
        
        if doctype == "Quotation":
            from ssplbilling.api.quotation_api import get_naming_series
            available = get_naming_series()
        else:
            # Get global billing series
            global_series = [r.series for r in settings.billing_series if r.series]
            # Get actual naming series options for this DocType from ERPNext/Frappe
            doctype_series_options = _fallback_series()
            
            # Filter global series to only include those that are valid for this DocType
            if global_series:
                available = [s for s in global_series if s in doctype_series_options]
            else:
                available = doctype_series_options
            
        user_series_rows = list(settings.user_series or [])
    except Exception:
        pass

    # If available list is empty, fall back to ERPNext naming series
    if not available:
        available = _fallback_series()

    current_user = frappe.session.user
    # Only Administrator/admin can request series for another user
    if user and current_user not in ["Administrator", "admin"]:
        user = current_user
    
    target_user = user or current_user

    # Administrator / admin gets everything
    if target_user in ["Administrator", "admin"]:
        return {"allowed_series": available, "user_allowed_string": "ALL"}

    # Find rows for this user
    user_rows = [r for r in user_series_rows if r.user == target_user]
    if not user_rows:
        # If user not found in SSPL settings, they get nothing unless they are admin
        return {"allowed_series": [], "user_allowed_string": ""}

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
        "allowed_series": result,
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
	import getpass
	import socket

	mem = psutil.virtual_memory()
	cpu = psutil.cpu_percent(interval=0.2)

	is_docker = _is_docker()
	if is_docker:
		user = os.environ.get("BACKUP_SSH_USER", "erpdev")
		host = "host"
	else:
		user = getpass.getuser()
		try:
			host = socket.gethostname()
		except Exception:
			host = "localhost"

	return {
		"ram_used_gb": round(mem.used / (1024 ** 3), 1),
		"ram_total_gb": round(mem.total / (1024 ** 3), 1),
		"ram_percent": round(mem.percent, 1),
		"cpu_percent": round(cpu, 1),
		"is_docker": is_docker,
		"terminal_user": user,
		"terminal_host": host,
	}



@frappe.whitelist()
def clear_ram_cache():
	"""Drop Linux page cache."""
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
def clear_and_rebuild_draft_invoice_cache():
	"""Clear the draft Sales Invoice quantities Redis cache and rebuild it from current draft Sales Invoices."""
	from ssplbilling.api.stock_utils import clear_draft_invoice_qtys_cache, get_draft_invoice_qtys_from_redis
	clear_draft_invoice_qtys_cache()
	new_qtys = get_draft_invoice_qtys_from_redis()
	return {"status": "success", "count": len(new_qtys)}


@frappe.whitelist()
def clear_and_rebuild_draft_purchase_cache():
	"""Clear the draft Purchase Invoice quantities Redis cache and rebuild it from current draft Purchase Invoices."""
	from ssplbilling.api.stock_utils import clear_draft_purchase_qtys_cache, get_draft_purchase_qtys_from_redis
	clear_draft_purchase_qtys_cache()
	new_qtys = get_draft_purchase_qtys_from_redis()
	return {"status": "success", "count": len(new_qtys)}


@frappe.whitelist()
def get_active_sessions():
	"""Return users currently active on this site."""
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
	"""Return all site names in this bench."""
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
	"""Resolve the Docker host IP."""
	import socket
	import struct
	try:
		with open("/proc/net/route") as f:
			for line in f:
				fields = line.strip().split()
				if len(fields) >= 3 and fields[1] == "00000000":
					return socket.inet_ntoa(struct.pack("<I", int(fields[2], 16)))
	except Exception:
		pass
	return os.environ.get("BACKUP_SSH_HOST", "host.docker.internal")


@frappe.whitelist()
def run_manual_backup():
	"""Run /opt/scripts/frappe_backup.sh."""
	import subprocess
	script = os.environ.get("BACKUP_SCRIPT", "/opt/scripts/frappe_backup.sh")
	if _is_docker():
		host = os.environ.get("BACKUP_SSH_HOST") or _docker_host_ip()
		user = os.environ.get("BACKUP_SSH_USER", "erpdev")
		key  = os.environ.get("BACKUP_SSH_KEY",  "/home/erpdev/.ssh/id_rsa")
		cmd = [
			"ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
			f"{user}@{host}", f"sudo {script}",
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
def run_terminal_command(command, cwd=None):
	"""Execute an arbitrary bash command inside the docker container/root container or SSH to host."""
	if frappe.session.user not in ["Administrator", "admin"] and "System Manager" not in frappe.get_roles():
		frappe.throw("Not permitted", frappe.PermissionError)

	import subprocess
	import os
	import shlex

	# Execute command in the specified directory if provided, otherwise default to bench path
	exec_cwd = cwd or frappe.utils.get_bench_path()

	if _is_docker():
		host = os.environ.get("BACKUP_SSH_HOST") or _docker_host_ip()
		user = os.environ.get("BACKUP_SSH_USER", "erpdev")
		key  = os.environ.get("BACKUP_SSH_KEY",  "/home/erpdev/.ssh/id_rsa")

		# Handle cd command via SSH to verify path exists on the host
		cmd_parts = command.strip().split()
		if cmd_parts and cmd_parts[0] == "cd":
			target_dir = cmd_parts[1] if len(cmd_parts) > 1 else exec_cwd
			remote_command = f"cd {shlex.quote(exec_cwd)} && cd {shlex.quote(target_dir)} && pwd"
			ssh_cmd = [
				"ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
				f"{user}@{host}", remote_command
			]
			try:
				result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
				if result.returncode == 0:
					return {
						"success": True,
						"stdout": "",
						"stderr": "",
						"returncode": 0,
						"cwd": result.stdout.strip()
					}
				else:
					return {
						"success": False,
						"stdout": "",
						"stderr": result.stderr.strip() or f"cd: {target_dir}: No such file or directory",
						"returncode": result.returncode,
						"cwd": exec_cwd
					}
			except Exception as e:
				return {
					"success": False,
					"stdout": "",
					"stderr": str(e),
					"returncode": -1,
					"cwd": exec_cwd
				}

		# Execute remote command
		remote_command = f"cd {shlex.quote(exec_cwd)} && {command}"
		ssh_cmd = [
			"ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
			f"{user}@{host}", remote_command
		]
		try:
			result = subprocess.run(
				ssh_cmd,
				capture_output=True,
				text=True,
				timeout=30
			)
			return {
				"success": result.returncode == 0,
				"stdout": result.stdout,
				"stderr": result.stderr,
				"returncode": result.returncode,
				"cwd": exec_cwd
			}
		except Exception as e:
			return {
				"success": False,
				"stdout": "",
				"stderr": str(e),
				"returncode": -1,
				"cwd": exec_cwd
			}
	else:
		# Bare-metal local terminal execution
		# Handle cd command
		cmd_parts = command.strip().split()
		if cmd_parts and cmd_parts[0] == "cd":
			target_dir = cmd_parts[1] if len(cmd_parts) > 1 else frappe.utils.get_bench_path()
			resolved_path = os.path.abspath(os.path.join(exec_cwd, target_dir))
			if os.path.exists(resolved_path) and os.path.isdir(resolved_path):
				return {
					"success": True,
					"stdout": "",
					"stderr": "",
					"returncode": 0,
					"cwd": resolved_path
				}
			else:
				return {
					"success": False,
					"stdout": "",
					"stderr": f"cd: {target_dir}: No such file or directory",
					"returncode": 1,
					"cwd": exec_cwd
				}

		try:
			result = subprocess.run(
				command,
				shell=True,
				cwd=exec_cwd,
				capture_output=True,
				text=True,
				timeout=30
			)
			return {
				"success": result.returncode == 0,
				"stdout": result.stdout,
				"stderr": result.stderr,
				"returncode": result.returncode,
				"cwd": exec_cwd
			}
		except Exception as e:
			return {
				"success": False,
				"stdout": "",
				"stderr": str(e),
				"returncode": -1,
				"cwd": exec_cwd
			}


@frappe.whitelist()
def get_billing_settings(user=None):
	"""Return SSPL Billing Settings; user_zoom and accounts are resolved for the current or specified user."""
	import ssplbilling
	from datetime import datetime
	app_path = frappe.get_app_path("ssplbilling")
	hooks_path = os.path.join(app_path, "hooks.py")
	last_updated = ""
	if os.path.exists(hooks_path):
		mtime = os.path.getmtime(hooks_path)
		last_updated = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

	settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
	current_user = frappe.session.user
	if user and current_user not in ["Administrator", "admin"]:
		user = current_user
	target_user = user or current_user
	user_row = next((r for r in settings.user_series if r.user == target_user), None)

	mop_accounts = frappe.get_all("Mode of Payment Account",
		filters={"company": "Sundaram and Sons Private Ltd"},
		fields=["parent", "default_account"])
	mop_map = {r.parent: r.default_account for r in mop_accounts}
	company_state = frappe.db.get_value("Address", {"is_your_company_address": 1}, "state") or ""

	automatic_entries = frappe.get_cached_doc("Automatic Entries", "Automatic Entries")

	user_zoom = (user_row.zoom_value or "") if user_row else ""
	user_theme = (user_row.theme or "Light") if user_row else "Light"
	user_defaults = {
		"cash": (user_row.cash or "") if user_row else "",
		"card": (user_row.card or "") if user_row else "",
		"upi": (user_row.upi or "") if user_row else "",
		"bank": (user_row.bank or "") if user_row else "",
		"bank_account": (user_row.bank or "") if user_row else "",
		"warehouse": (user_row.warehouse or "") if user_row else "",
		"cost_center": (user_row.cost_center or "") if user_row else "",
		"income_account": (user_row.income_account or "") if user_row else "",
		"company": (user_row.company or "") if user_row else "",
		"default_printer": (user_row.default_printer or "") if user_row else "",
		"theme": user_theme,
	}

	return {
		"app_version": ssplbilling.__version__,
		"last_updated": last_updated,
		"company_state": company_state,
		"discount_account": settings.discount_account or "",
		"freight_account": settings.freight or "",
		"tax_paid_on_purchase": settings.tax_paid_on_purchase or "",
		"packing_charge": settings.packing_charge or "",
		"loading": settings.loading or "",
		"other_charges": settings.other_charges or "",
		"round_off": settings.round_off or "",
		"cipher_map": settings.cipher_map or "",
		"mop_map": mop_map,
		"user_zoom": user_zoom,
		"wb_theme": user_theme,
		"user_defaults": user_defaults,
		"user_role": {
			"admin": user_row.admin if user_row else 0,
			"cashier": user_row.cashier if user_row else 0,
			"biller": user_row.biller if user_row else 0,
			"accounts": user_row.accounts if user_row else 0,
		},
		"billing_series": [
			{
				"series": r.series or "",
				"price_list": r.price_list or "",
				"tax_template": r.tax_template or "",
				"print_format": r.print_format or "",
				"tax_type_incl": r.tax_type_incl or 0,
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
				"company": r.company or "",
				"admin": r.admin or 0,
				"cashier": r.cashier or 0,
				"biller": r.biller or 0,
				"accounts": r.accounts or 0,
				"default_printer": r.default_printer or "",
				"theme": r.theme or "Light",
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
		"automatic_entries": {
			"alternative_company": automatic_entries.alternative_company or "",
			"warehouse": automatic_entries.warehouse or "",
			"payment_entry_naming_settings": automatic_entries.payment_entry_naming_settings or "",
			"series": [
				{
					"sales_invoice_series": r.sales_invoice_series or "",
					"purchase_invoice_series": r.purchase_invoice_series or "",
					"conversion_invoice_series": r.get("conversion_invoice_series") or "",
				}
				for r in (automatic_entries.series or [])
			],
			"accounts": [
				{
					"account": r.account or "",
				}
				for r in (automatic_entries.accounts or [])
			],
		},
	}


@frappe.whitelist()
def get_allowed_tiles(user=None):
	"""Return the dashboard tiles allowed via SSPL Dashboard Tile Access, resolved for
	the inherited/specified user (admin only) or the session user as fallback.

	Resolution: a user-level record wins outright; otherwise the union of all enabled
	group-level records for User Groups the user belongs to. Returns configured=False
	(tiles=None) when nothing applies, so the frontend falls back to role-based filtering.
	"""
	current_user = frappe.session.user
	# Only Administrator/admin can request tiles for another user
	if user and current_user not in ["Administrator", "admin"]:
		user = current_user
	target_user = user or current_user

	access_names = []
	user_record = frappe.db.get_value(
		"SSPL Dashboard Tile Access",
		{"applies_to": "User", "user": target_user, "enabled": 1},
		"name",
	)
	if user_record:
		access_names = [user_record]
	else:
		groups = frappe.get_all("User Group Member", filters={"user": target_user}, pluck="parent")
		if groups:
			access_names = frappe.get_all(
				"SSPL Dashboard Tile Access",
				filters={"applies_to": "User Group", "user_group": ["in", groups], "enabled": 1},
				pluck="name",
			)

	if not access_names:
		return {"configured": False, "tiles": None}

	# Preserve the child-table row order from the doctype (first occurrence wins
	# when multiple group records grant the same tile)
	tiles = []
	seen = set()
	for name in access_names:
		doc = frappe.get_cached_doc("SSPL Dashboard Tile Access", name)
		for row in doc.tiles:
			if row.tile and row.tile not in seen:
				seen.add(row.tile)
				tiles.append(row.tile)

	return {"configured": True, "tiles": tiles}


@frappe.whitelist(allow_guest=True)
def get_frappe_site_name():
	"""Return site name and socket.io port so the frontend can build the correct socket.io URL."""
	return {
		"site": frappe.local.site,
		"socketio_port": frappe.conf.get("socketio_port", 9000),
	}


@frappe.whitelist()
def get_ic_api_credits():
	"""Fetch India Compliance API credits from resilient.tech GSP service."""
	# Only allow users with System Manager role to check it
	if "System Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw("Not authorized", frappe.PermissionError)

	import requests
	from frappe.utils.password import get_decrypted_password

	try:
		api_secret = get_decrypted_password(
			"GST Settings",
			"GST Settings",
			fieldname="api_secret",
			raise_exception=False,
		)
		if not api_secret:
			api_secret = frappe.conf.get("ic_api_secret")

		if not api_secret:
			return {"success": False, "error": "API Secret not configured in GST Settings"}

		headers = {
			"Content-Type": "application/json",
			"x-api-key": api_secret
		}
		url = "https://asp.resilient.tech/v1/account.get_subscription_details"
		response = requests.get(url, headers=headers, timeout=10)
		if response.status_code == 200:
			data = response.json()
			# GSP APIs (Frappe whitelisted methods) return the result inside 'message'
			if "message" in data:
				return {"success": True, "data": data["message"]}
			elif "error" in data:
				return {"success": False, "error": data["error"]}
			else:
				return {"success": False, "error": "Unknown API response"}
		else:
			return {"success": False, "error": f"API HTTP Error {response.status_code}"}
	except Exception as e:
		return {"success": False, "error": str(e)}

