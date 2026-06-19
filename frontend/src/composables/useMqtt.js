import { ref } from 'vue'
import { io } from 'socket.io-client'
import { frappeGet } from '../api.js'

const isConnected = ref(false)
const serverInfo = ref({ server: '', port: '' })
const isConnecting = ref(false)
let socket = null
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
    if (socket) return

    const url = window.location.origin
    console.log(`[useMqtt] Connecting to Frappe Socket.io at ${url}...`)
    
    socket = io(url, { withCredentials: true })

    socket.on('connect', () => {
      console.log('[useMqtt] Socket.io connected.')
    })

    socket.on('disconnect', () => {
      console.log('[useMqtt] Socket.io disconnected.')
    })

    socket.on('events', (data) => {
      if (data && data.event === 'mqtt_payment_received') {
        console.log('[useMqtt] Realtime message received:', data.message)
        window.dispatchEvent(new CustomEvent('wb-mqtt-payment', { detail: data.message }))
      }
    })
  }

  function startStatusPolling() {
    if (statusInterval) return
    checkStatus()
    statusInterval = setInterval(checkStatus, 20000)
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
    if (socket) {
      socket.disconnect()
      socket = null
    }
  }

  return {
    isConnected,
    isConnecting,
    serverInfo,
    connectMqtt,
    disconnectMqtt,
    checkStatus
  }
}
