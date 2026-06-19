import { ref } from 'vue'
import mqtt from 'mqtt'
import { frappeGet } from '../api.js'

const isConnected = ref(false)
const client = ref(null)
const serverInfo = ref({ server: '', port: '' })
const isConnecting = ref(false)

export function useMqtt() {
  async function connectMqtt() {
    if (client.value && (client.value.connected || isConnecting.value)) {
      return
    }

    isConnecting.value = true
    try {
      const settings = await frappeGet('frappe.client.get', {
        doctype: 'MQTT Settings',
        name: 'MQTT Settings'
      })

      if (!settings || !settings.mqtt_server || !settings.port) {
        console.warn('MQTT Settings not configured or missing server/port.')
        isConnecting.value = false
        return
      }

      serverInfo.value = {
        server: settings.mqtt_server,
        port: settings.port
      }

      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const connectionUrl = `${protocol}://${settings.mqtt_server}:${settings.port}/mqtt`

      console.log(`Connecting to MQTT broker at ${connectionUrl}...`)

      if (client.value) {
        try {
          client.value.end()
        } catch (e) {
          console.error('Error closing existing client:', e)
        }
      }

      const options = {
        connectTimeout: 5000,
        reconnectPeriod: 5000,
        clean: true,
      }

      const mqttClient = mqtt.connect(connectionUrl, options)

      mqttClient.on('connect', () => {
        console.log('Successfully connected to MQTT broker.')
        isConnected.value = true
        isConnecting.value = false
      })

      mqttClient.on('close', () => {
        console.log('MQTT connection closed.')
        isConnected.value = false
        isConnecting.value = false
      })

      mqttClient.on('error', (err) => {
        console.error('MQTT error:', err)
        isConnected.value = false
        isConnecting.value = false
      })

      client.value = mqttClient

    } catch (e) {
      console.error('Failed to initialize MQTT connection:', e)
      isConnecting.value = false
    }
  }

  function disconnectMqtt() {
    if (client.value) {
      try {
        client.value.end()
      } catch (e) {
        console.error('Error during disconnect:', e)
      }
      client.value = null
      isConnected.value = false
    }
  }

  return {
    isConnected,
    isConnecting,
    client,
    serverInfo,
    connectMqtt,
    disconnectMqtt
  }
}
