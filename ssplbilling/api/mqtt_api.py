import time
import threading
import frappe
from paho.mqtt import client as mqtt_client

PING_KEY = "mqtt_client_last_ping"
CONNECTED_KEY = "mqtt_connected"
LOCK_KEY = "mqtt_client_lock"

@frappe.whitelist()
def get_mqtt_status():
	"""Return the MQTT connection status to the frontend and ensure the background thread is running."""
	ensure_mqtt_connected()
	
	connected = frappe.cache().get_value(CONNECTED_KEY)
	last_ping = frappe.cache().get_value(PING_KEY)
	
	is_active = False
	if last_ping:
		try:
			is_active = (time.time() - float(last_ping)) < 30
		except Exception:
			pass
			
	return {
		"connected": bool(connected) and is_active,
		"last_ping": last_ping
	}

ACTIVE_DAEMON_KEY = "mqtt_active_daemon_id"

@frappe.whitelist()
def ensure_mqtt_connected():
	"""Check if the background MQTT client daemon process is running. If not, start it."""
	last_ping = frappe.cache().get_value(PING_KEY)
	now = time.time()
	
	if not last_ping or (now - float(last_ping)) > 30:
		if frappe.cache().set(LOCK_KEY, "1", ex=20, nx=True):
			site_name = getattr(frappe.local, "site", None)
			if site_name:
				import os
				import sys
				import subprocess
				import uuid
				
				bench_path = frappe.utils.get_bench_path()
				sites_path = os.path.join(bench_path, "sites")
				log_path = os.path.join(bench_path, "logs", "mqtt_daemon.log")
				
				# Generate a new unique daemon ID and set it as active BEFORE spawning.
				daemon_id = str(uuid.uuid4())
				frappe.cache().set_value(ACTIVE_DAEMON_KEY, daemon_id)
				frappe.cache().delete("mqtt_exit_daemon")
				
				cmd = [
					sys.executable,
					"-m", "frappe.utils.bench_helper",
					"frappe",
					"--site", site_name,
					"execute",
					"ssplbilling.api.mqtt_api.run_mqtt_daemon"
				]
				
				try:
					log_file = open(log_path, "a", encoding="utf-8")
					subprocess.Popen(
						cmd,
						cwd=sites_path,
						stdout=log_file,
						stderr=log_file,
						start_new_session=True,
						env=dict(os.environ, MQTT_DAEMON_ID=daemon_id)
					)
					log_file.close()
				except Exception as e:
					t = threading.Thread(target=run_mqtt_daemon, args=(site_name, daemon_id), daemon=True)
					t.start()

def run_mqtt_daemon(site_name=None, daemon_id=None):
	"""Main daemon loop running in a background thread or detached process."""
	import os
	import uuid
	
	if not daemon_id:
		daemon_id = os.environ.get("MQTT_DAEMON_ID") or str(uuid.uuid4())
		
	if not site_name:
		site_name = getattr(frappe.local, "site", None)

	if site_name:
		frappe.init(site_name)

	print(f"[MQTT Daemon] Starting daemon process. ID: {daemon_id}")

	# Set the ping immediately so ensure_mqtt_connected knows we are running
	frappe.cache().set_value(PING_KEY, str(time.time()))
	frappe.cache().delete(LOCK_KEY)
	time.sleep(1)
	
	frappe.connect()
	try:
		settings = frappe.get_doc("MQTT Settings")
		if not settings.mqtt_server:
			frappe.cache().set_value(CONNECTED_KEY, 0)
			return
		
		from urllib.parse import urlparse
		server_str = settings.mqtt_server.strip()
		if "://" not in server_str:
			parsed = urlparse("mqtt://" + server_str)
		else:
			parsed = urlparse(server_str)
		
		mqtt_server = parsed.hostname or parsed.path or server_str
		
		if parsed.port:
			port = int(parsed.port)
		else:
			port = int(settings.port) if settings.port else 1883
			
		topics = [row.topic for row in settings.topics if row.topic]
	except Exception as e:
		print(f"[MQTT Daemon] Failed to load settings: {e}")
		frappe.cache().set_value(CONNECTED_KEY, 0)
		return
	finally:
		if frappe.db:
			frappe.db.close()

	client = mqtt_client.Client(
		callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
	)
	
	def on_connect(client, userdata, flags, reason_code, properties):
		if site_name:
			frappe.init(site_name)
		if reason_code == 0:
			print("[MQTT Daemon] Connected successfully.")
			frappe.cache().set_value(CONNECTED_KEY, 1)
			for topic in topics:
				client.subscribe(topic)
				print(f"[MQTT Daemon] Subscribed to {topic}")
		else:
			print(f"[MQTT Daemon] Connect failed with code {reason_code}")
			frappe.cache().set_value(CONNECTED_KEY, 0)

	def on_disconnect(client, userdata, flags, reason_code, properties):
		if site_name:
			frappe.init(site_name)
		print(f"[MQTT Daemon] Disconnected: {reason_code}")
		frappe.cache().set_value(CONNECTED_KEY, 0)

	def on_message(client, userdata, msg):
		if site_name:
			frappe.init(site_name)
		try:
			payload = msg.payload.decode("utf-8")
			topic = msg.topic
			print(f"[MQTT Daemon] Received message on {topic}: {payload}")
			
			# Publish to frappe socketio/realtime
			frappe.connect()
			try:
				frappe.publish_realtime(
					event="mqtt_payment_received",
					message={"topic": topic, "payload": payload},
					after_commit=False
				)
			finally:
				frappe.destroy()
		except Exception as e:
			print(f"[MQTT Daemon] Error handling message: {e}")

	client.on_connect = on_connect
	client.on_disconnect = on_disconnect
	client.on_message = on_message

	print(f"[MQTT Daemon] Connecting to {mqtt_server}:{port}...")
	try:
		client.connect(mqtt_server, port, keepalive=60)
	except Exception as e:
		print(f"[MQTT Daemon] Connection error: {e}")
		if site_name:
			frappe.init(site_name)
		frappe.cache().set_value(CONNECTED_KEY, 0)
		return

	client.loop_start()
	
	try:
		while True:
			if site_name:
				frappe.init(site_name)
			
			# Exit if this daemon has been superseded by a newer one
			active_id = frappe.cache().get_value(ACTIVE_DAEMON_KEY)
			if active_id and active_id != daemon_id:
				print(f"[MQTT Daemon] Superseded by newer daemon (Active: {active_id}, Current: {daemon_id}). Exiting.")
				break
				
			if frappe.cache().get_value("mqtt_exit_daemon"):
				frappe.cache().delete("mqtt_exit_daemon")
				print("[MQTT Daemon] Exit requested via cache flag.")
				break
				
			frappe.cache().set_value(PING_KEY, str(time.time()))
			if client.is_connected():
				frappe.cache().set_value(CONNECTED_KEY, 1)
			else:
				frappe.cache().set_value(CONNECTED_KEY, 0)
			
			# Sleep for 10s total, checking every 1s
			exit_requested = False
			for _ in range(10):
				time.sleep(1)
				active_id = frappe.cache().get_value(ACTIVE_DAEMON_KEY)
				if active_id and active_id != daemon_id:
					exit_requested = True
					print(f"[MQTT Daemon] Superseded by newer daemon (Active: {active_id}, Current: {daemon_id}). Exiting.")
					break
				if frappe.cache().get_value("mqtt_exit_daemon"):
					exit_requested = True
					break
			if exit_requested:
				break
	except Exception as e:
		print(f"[MQTT Daemon] Loop error: {e}")
	finally:
		client.loop_stop()
		client.disconnect()
		if site_name:
			frappe.init(site_name)
		# Only clear connection status if we are still the active daemon
		active_id = frappe.cache().get_value(ACTIVE_DAEMON_KEY)
		if not active_id or active_id == daemon_id:
			frappe.cache().set_value(CONNECTED_KEY, 0)

@frappe.whitelist()
def refresh_mqtt_connection():
	"""Force restart the background MQTT daemon by terminating the current one and starting a new one."""
	# Invalidate the active daemon ID to force any running daemon to exit
	frappe.cache().set_value(ACTIVE_DAEMON_KEY, "restart")
	frappe.cache().set_value("mqtt_exit_daemon", 1)
	frappe.cache().delete(PING_KEY)
	frappe.cache().delete(LOCK_KEY)
	
	# Give the existing thread/process a moment to exit
	time.sleep(0.5)
	
	ensure_mqtt_connected()
	
	# Give the new subprocess a brief moment to boot and connect
	time.sleep(2.0)
	
	return get_mqtt_status()


@frappe.whitelist()
def publish_mqtt_message(topic, message):
	"""Publish an MQTT message to the specified topic."""
	try:
		settings = frappe.get_doc("MQTT Settings")
		if not settings.mqtt_server:
			frappe.throw("MQTT Server is not configured in MQTT Settings.")
			
		from urllib.parse import urlparse
		server_str = settings.mqtt_server.strip()
		if "://" not in server_str:
			parsed = urlparse("mqtt://" + server_str)
		else:
			parsed = urlparse(server_str)
		
		mqtt_server = parsed.hostname or parsed.path or server_str
		
		if parsed.port:
			port = int(parsed.port)
		else:
			port = int(settings.port) if settings.port else 1883
			
		client = mqtt_client.Client(
			callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
		)
		client.connect(mqtt_server, port, keepalive=60)
		info = client.publish(topic, message, qos=1)
		info.wait_for_publish()
		client.disconnect()
		return {"status": "success", "message": "Message published successfully"}
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback(), title="MQTT Publish Error")
		frappe.throw(f"Failed to publish MQTT message: {str(e)}")
