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
      
      <!-- Global Toast Stack -->
      <div class="fixed bottom-6 right-6 z-[300] flex flex-col gap-3 pointer-events-none">
        <TransitionGroup name="toast-fade" tag="div" class="flex flex-col gap-3">
          <div 
            v-for="t in toasts" 
            :key="t.id"
            class="flex items-center gap-3 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-success)]/30 shadow-2xl px-6 py-4 min-w-[320px] pointer-events-auto transform-gpu"
          >
            <div class="h-8 w-8 rounded-full bg-[var(--color-success)]/20 flex items-center justify-center text-xl shrink-0">
              ✅
            </div>
            <div class="flex-1">
              <h4 class="text-lg font-bold text-[var(--color-success)] uppercase tracking-wider">Success</h4>
              <p class="text-base text-[var(--color-text)] font-medium leading-tight mt-0.5">{{ t.message }}</p>
            </div>
            <button 
              @click="toasts = toasts.filter(item => item.id !== t.id)"
              class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-xl font-bold ml-2 focus:outline-none"
            >
              &times;
            </button>
          </div>
        </TransitionGroup>
      </div>
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
import { initLedgerSync, destroyLedgerSync } from './composables/useLedgerSync';
import { initFrappeSocket } from './services/frappeSocket';

const showCalculator = ref(false);
const showCommandLine = ref(false);
const showError = ref(false);
const errorMessage = ref('');
const errorType = ref('error');
const errorTitle = ref('Error');

const toasts = ref([]);
function showToast(message, type = 'success', duration = 2000) {
  const id = Date.now() + Math.random().toString(36).substr(2, 9);
  toasts.value.push({ id, message, type });
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id);
  }, duration);
}
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
  initLedgerSync();
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
      showToast(messageStr, 'success', 2000)
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
  destroyLedgerSync();
  window.removeEventListener('wb-global-calculator-toggle', toggleCalculator);
  window.removeEventListener('wb-global-command-line-toggle', toggleCommandLine);
  window.removeEventListener('wb-global-keyboard-toggle', toggleKeyboard);
  document.removeEventListener('focusin', suppressKeyboard, true);
  document.removeEventListener('touchstart', suppressKeyboard, true);
  if (observer) observer.disconnect();
  window.alert = _nativeAlert;
});
</script>

<style>
.toast-fade-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.toast-fade-leave-active {
  transition: all 0.2s ease;
}
.toast-fade-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.9);
}
.toast-fade-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
.toast-fade-move {
  transition: transform 0.3s ease;
}
</style>

