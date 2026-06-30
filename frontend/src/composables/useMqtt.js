import { ref } from 'vue'
import { frappeGet } from '../api.js'
import { getFrappeSocket } from '../services/frappeSocket.js'

const isConnected = ref(false)
const serverInfo = ref({ server: '', port: '' })
const isConnecting = ref(false)
let statusInterval = null

export function useMqtt() {
  async function checkStatus() {
    isConnecting.value = true
    try {
      const res = await frappeGet('ssplbilling.api.mqtt_api.get_mqtt_status')
      isConnected.value = res.connected || false
      
      const settings = await frappeGet('frappe.client.get', {
        doctype: 'MQTT Settings',
        name: 'MQTT Settings'
      })
      if (settings) {
        serverInfo.value = {
          server: settings.mqtt_server || '',
          port: settings.port || ''
        }
      }
    } catch (e) {
      console.warn('[useMqtt] failed to get status:', e)
      isConnected.value = false
    } finally {
      isConnecting.value = false
    }
  }

  function initSocketConnection() {
    const socket = getFrappeSocket()
    socket.on('mqtt_payment_received', (data) => {
      console.log('[useMqtt] mqtt_payment_received:', data)
      window.dispatchEvent(new CustomEvent('wb-mqtt-payment', { detail: data }))
    })
  }

  function startStatusPolling() {
    checkStatus()
    // Automatic 20-second polling disabled as per user request to use manual refresh instead
    // if (statusInterval) return
    // checkStatus()
    // statusInterval = setInterval(checkStatus, 20000)
  }

  function stopStatusPolling() {
    if (statusInterval) {
      clearInterval(statusInterval)
      statusInterval = null
    }
  }

  async function connectMqtt() {
    initSocketConnection()
    startStatusPolling()
  }

  function disconnectMqtt() {
    stopStatusPolling()
  }

  async function refreshConnection() {
    isConnecting.value = true
    try {
      const res = await frappeGet('ssplbilling.api.mqtt_api.refresh_mqtt_connection')
      isConnected.value = res.connected || false
      
      const settings = await frappeGet('frappe.client.get', {
        doctype: 'MQTT Settings',
        name: 'MQTT Settings'
      })
      if (settings) {
        serverInfo.value = {
          server: settings.mqtt_server || '',
          port: settings.port || ''
        }
      }
    } catch (e) {
      console.warn('[useMqtt] failed to refresh connection:', e)
      isConnected.value = false
    } finally {
      isConnecting.value = false
    }
  }

  return {
    isConnected,
    isConnecting,
    serverInfo,
    connectMqtt,
    disconnectMqtt,
    checkStatus,
    refreshConnection
  }
}
