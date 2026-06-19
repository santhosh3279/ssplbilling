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

@frappe.whitelist()
def ensure_mqtt_connected():
	"""Check if the background MQTT client thread is running. If not, start it."""
	last_ping = frappe.cache().get_value(PING_KEY)
	now = time.time()
	
	if not last_ping or (now - float(last_ping)) > 30:
		if frappe.cache().set(LOCK_KEY, "1", ex=20, nx=True):
			site_name = frappe.local.site
			t = threading.Thread(target=run_mqtt_daemon, args=(site_name,), daemon=True)
			t.start()

def run_mqtt_daemon(site_name=None):
	"""Main daemon loop running in a background thread."""
	if not site_name:
		site_name = getattr(frappe.local, "site", None)

	if site_name:
		frappe.init(site_name)

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
			
			if frappe.cache().get_value("mqtt_exit_daemon"):
				frappe.cache().delete("mqtt_exit_daemon")
				print("[MQTT Daemon] Exit requested via cache flag.")
				break
				
			frappe.cache().set_value(PING_KEY, str(time.time()))
			if client.is_connected():
				frappe.cache().set_value(CONNECTED_KEY, 1)
			else:
				frappe.cache().set_value(CONNECTED_KEY, 0)
			
			# Sleep for 10s total, checking for exit request every 1s
			exit_requested = False
			for _ in range(10):
				time.sleep(1)
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
		frappe.cache().set_value(CONNECTED_KEY, 0)


@frappe.whitelist()
def refresh_mqtt_connection():
	"""Force restart the background MQTT daemon by terminating the current one and starting a new one."""
	frappe.cache().set_value("mqtt_exit_daemon", 1)
	frappe.cache().delete(PING_KEY)
	frappe.cache().delete(LOCK_KEY)
	
	# Give the existing thread a moment to exit and release the lock/client
	time.sleep(1.2)
	
	ensure_mqtt_connected()
	
	# Give it a moment to connect and update the status
	time.sleep(1.0)
	
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
