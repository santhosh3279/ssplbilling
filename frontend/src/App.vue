<template>
  <div class="min-h-screen bg-[var(--color-bg)] flex overflow-hidden">
    <!-- Main App Content -->
    <div 
      :class="[showKeyboardPanel ? (isSidebarCollapsed ? 'w-[70%]' : 'w-[80%]') : 'w-full']"
      class="relative h-screen overflow-hidden transform-gpu flex flex-col bg-[var(--color-bg)] transition-all duration-300 ease-in-out"
    >
      <router-view class="flex-1 overflow-hidden" />
      
      <!-- Global Components (Contained within this div's boundaries on tablet) -->
      <Calculator :show="showCalculator" @close="showCalculator = false" />
      <CommandLine :show="showCommandLine" @close="showCommandLine = false" @open="showCommandLine = true" />
      <GlobalModals />
      <ErrorWindow :show="showError" :message="errorMessage" @close="showError = false" />
    </div>

    <!-- Tablet Side Panel (Keyboard) -->
    <div 
      v-if="showKeyboardPanel" 
      :class="isSidebarCollapsed ? 'w-[30%]' : 'w-[20%]'"
      class="h-screen border-l border-[var(--color-border)] shadow-2xl z-50 overflow-hidden shrink-0 bg-[var(--color-surface)] transition-all duration-300 ease-in-out"
    >
      <Keyboard />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useShortcuts } from './services/shortcutManager';
import { globalShortcuts } from './shortcuts/globalShortcuts';
import Calculator from './components/Calculator.vue';
import CommandLine from './components/CommandLine.vue';
import Keyboard from './components/Keyboard.vue';
import GlobalModals from './components/GlobalModals.vue';
import ErrorWindow from './components/ErrorWindow.vue';
import { useTheme } from './composables/useTheme';
import { useDevice } from './composables/useDevice';
import { useLayout } from './composables/useLayout';
import { useMqtt } from './composables/useMqtt';

const showCalculator = ref(false);
const showCommandLine = ref(false);
const showError = ref(false);
const errorMessage = ref('');
const { initTheme } = useTheme();
const { isTablet } = useDevice();
const { isSidebarCollapsed } = useLayout();
const { connectMqtt } = useMqtt();

const route = useRoute();
const showKeyboardPanel = computed(() => {
  return isTablet.value && route.name !== 'OfferPage';
});

useShortcuts(globalShortcuts, 'global');

function toggleCalculator() {
  showCalculator.value = !showCalculator.value;
}

function toggleCommandLine() {
  showCommandLine.value = !showCommandLine.value;
}

const _nativeAlert = window.alert.bind(window);

// Global Keyboard Suppression for Tablet
function suppressKeyboard(e) {
  if (!isTablet.value) return;

  const target = e.target;
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') {
    // Force inputmode to none to prevent virtual keyboard
    target.setAttribute('inputmode', 'none');
    // Newer standard for chromium browsers
    target.setAttribute('virtualkeyboardpolicy', 'manual');
  }
}

let observer = null;

onMounted(() => {
  initTheme();
  connectMqtt();
  window.addEventListener('wb-global-calculator-toggle', toggleCalculator);

  window.addEventListener('wb-global-command-line-toggle', toggleCommandLine);

  // Initial scan and setup for tablet
  if (isTablet.value) {
    const applyToAll = () => {
      document.querySelectorAll('input, textarea, select').forEach(el => {
        el.setAttribute('inputmode', 'none');
        el.setAttribute('virtualkeyboardpolicy', 'manual');
      });
    };
    
    applyToAll();

    // Attach global focus listener for keyboard suppression
    document.addEventListener('focusin', suppressKeyboard, true);
    document.addEventListener('touchstart', suppressKeyboard, true);

    // Watch for dynamic inputs (modals, new rows, etc)
    observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1) { // Element
            if (node.tagName === 'INPUT' || node.tagName === 'TEXTAREA' || node.tagName === 'SELECT') {
              node.setAttribute('inputmode', 'none');
              node.setAttribute('virtualkeyboardpolicy', 'manual');
            }
            node.querySelectorAll?.('input, textarea, select').forEach(el => {
              el.setAttribute('inputmode', 'none');
              el.setAttribute('virtualkeyboardpolicy', 'manual');
            });
          }
        });
      });
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  window.alert = (msg) => {
    const messageStr = String(msg ?? '')
    const lower = messageStr.toLowerCase()
    
    // Check if it is a success message
    const isSuccess = (
      lower.includes('success') ||
      lower.includes('saved') ||
      lower.includes('updated') ||
      lower.includes('deleted') ||
      lower.includes('synced') ||
      lower.includes('created') ||
      lower.includes('completed')
    ) && !lower.includes('fail') && !lower.includes('error') && !lower.includes('required') && !lower.includes('invalid')

    if (isSuccess) {
      _nativeAlert(messageStr)
    } else {
      errorMessage.value = messageStr
      showError.value = true
    }
  };
});

onUnmounted(() => {
  window.removeEventListener('wb-global-calculator-toggle', toggleCalculator);
  window.removeEventListener('wb-global-command-line-toggle', toggleCommandLine);
  document.removeEventListener('focusin', suppressKeyboard, true);
  document.removeEventListener('touchstart', suppressKeyboard, true);
  if (observer) observer.disconnect();
  window.alert = _nativeAlert;
});
</script>
