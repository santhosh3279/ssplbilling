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
      <ErrorWindow :show="showError" :message="errorMessage" :type="errorType" :title="errorTitle" @close="showError = false" />
    </div>

    <!-- Tablet Side Panel (Keyboard) -->
    <div 
      v-if="showKeyboardPanel" 
      :class="isSidebarCollapsed ? 'w-[30%]' : 'w-[20%]'"
      class="h-screen border-l border-[var(--color-border)] shadow-2xl z-50 overflow-hidden shrink-0 bg-[var(--color-surface)] transition-all duration-300 ease-in-out"
    >
      <Keyboard />
    </div>
    <!-- Floating Keyboard Toggle Handle (Visible only when keyboard is hidden) -->
    <button
      v-if="!showKeyboardPanel && route.name !== 'OfferPage'"
      @click="toggleKeyboard"
      class="fixed right-0 top-2 z-[100] flex items-center justify-center h-10 w-6 rounded-l-xl bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] shadow-2xl hover:brightness-110 active:scale-95 transition-all focus:outline-none border-l border-t border-b border-[var(--color-border)] cursor-pointer"
      title="Open Keyboard"
    >
      <span class="text-xs font-bold font-mono">◀</span>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
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
import { initItemSync, destroyItemSync } from './composables/useItemSync';
import { initFrappeSocket } from './services/frappeSocket';

const showCalculator = ref(false);
const showCommandLine = ref(false);
const showError = ref(false);
const errorMessage = ref('');
const errorType = ref('error');
const errorTitle = ref('Error');
const { initTheme } = useTheme();
const { isTablet } = useDevice();
const { isSidebarCollapsed } = useLayout();
const { connectMqtt } = useMqtt();

const route = useRoute();
const forceKeyboard = ref(localStorage.getItem('wb-force-keyboard') === 'true');

const showKeyboardPanel = computed(() => {
  if (forceKeyboard.value) {
    return route.name !== 'OfferPage';
  }
  return isTablet.value && route.name !== 'OfferPage';
});

function toggleKeyboard() {
  forceKeyboard.value = !forceKeyboard.value;
  localStorage.setItem('wb-force-keyboard', forceKeyboard.value ? 'true' : 'false');
}

useShortcuts(globalShortcuts, 'global');

function toggleCalculator() {
  showCalculator.value = !showCalculator.value;
}

function toggleCommandLine() {
  showCommandLine.value = !showCommandLine.value;
}

const _nativeAlert = window.alert.bind(window);

// Global Keyboard Suppression for Tablet / Forced Keyboard
function suppressKeyboard(e) {
  if (!showKeyboardPanel.value) return;

  const target = e.target;
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') {
    target.setAttribute('inputmode', 'none');
    target.setAttribute('virtualkeyboardpolicy', 'manual');
  }
}

let observer = null;
let isObserverActive = false;

function setupKeyboardSuppression() {
  if (showKeyboardPanel.value) {
    if (isObserverActive) return;
    
    document.querySelectorAll('input, textarea, select').forEach(el => {
      el.setAttribute('inputmode', 'none');
      el.setAttribute('virtualkeyboardpolicy', 'manual');
    });

    document.addEventListener('focusin', suppressKeyboard, true);
    document.addEventListener('touchstart', suppressKeyboard, true);

    if (!observer) {
      observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1) {
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
    }
    observer.observe(document.body, { childList: true, subtree: true });
    isObserverActive = true;
  } else {
    if (!isObserverActive) return;
    
    document.querySelectorAll('input, textarea, select').forEach(el => {
      el.removeAttribute('inputmode');
      el.removeAttribute('virtualkeyboardpolicy');
    });

    document.removeEventListener('focusin', suppressKeyboard, true);
    document.removeEventListener('touchstart', suppressKeyboard, true);

    if (observer) {
      observer.disconnect();
    }
    isObserverActive = false;
  }
}

watch(showKeyboardPanel, () => {
  setupKeyboardSuppression();
});

onMounted(async () => {
  initTheme();
  await initFrappeSocket();
  connectMqtt();
  initItemSync();
  window.addEventListener('wb-global-calculator-toggle', toggleCalculator);
  window.addEventListener('wb-global-command-line-toggle', toggleCommandLine);
  window.addEventListener('wb-global-keyboard-toggle', toggleKeyboard);

  setupKeyboardSuppression();

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
      errorMessage.value = messageStr
      errorType.value = 'success'
      errorTitle.value = 'Success'
      showError.value = true
    } else {
      errorMessage.value = messageStr
      errorType.value = 'error'
      errorTitle.value = 'Error'
      showError.value = true
    }
  };
});

onUnmounted(() => {
  destroyItemSync();
  window.removeEventListener('wb-global-calculator-toggle', toggleCalculator);
  window.removeEventListener('wb-global-command-line-toggle', toggleCommandLine);
  window.removeEventListener('wb-global-keyboard-toggle', toggleKeyboard);
  document.removeEventListener('focusin', suppressKeyboard, true);
  document.removeEventListener('touchstart', suppressKeyboard, true);
  if (observer) observer.disconnect();
  window.alert = _nativeAlert;
});
</script>
