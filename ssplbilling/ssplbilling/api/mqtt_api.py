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
			t = threading.Thread(target=run_mqtt_daemon, daemon=True)
			t.start()

def run_mqtt_daemon():
	"""Main daemon loop running in a background thread."""
	frappe.cache().delete(LOCK_KEY)
	time.sleep(1)
	
	frappe.connect()
	try:
		settings = frappe.get_doc("MQTT Settings")
		if not settings.mqtt_server or not settings.port:
			frappe.cache().set_value(CONNECTED_KEY, 0)
			return
		
		mqtt_server = settings.mqtt_server
		port = int(settings.port)
		topics = [row.topic for row in settings.topics if row.topic]
	except Exception as e:
		print(f"[MQTT Daemon] Failed to load settings: {e}")
		frappe.cache().set_value(CONNECTED_KEY, 0)
		return
	finally:
		frappe.destroy_relations()
		frappe.close_connection()

	client = mqtt_client.Client(
		callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
	)
	
	def on_connect(client, userdata, flags, reason_code, properties):
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
		print(f"[MQTT Daemon] Disconnected: {reason_code}")
		frappe.cache().set_value(CONNECTED_KEY, 0)

	def on_message(client, userdata, msg):
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
				frappe.destroy_relations()
				frappe.close_connection()
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
		frappe.cache().set_value(CONNECTED_KEY, 0)
		return

	client.loop_start()
	
	try:
		while True:
			frappe.cache().set_value(PING_KEY, str(time.time()))
			if client.is_connected():
				frappe.cache().set_value(CONNECTED_KEY, 1)
			else:
				frappe.cache().set_value(CONNECTED_KEY, 0)
			time.sleep(10)
	except Exception as e:
		print(f"[MQTT Daemon] Loop error: {e}")
	finally:
		client.loop_stop()
		client.disconnect()
		frappe.cache().set_value(CONNECTED_KEY, 0)
