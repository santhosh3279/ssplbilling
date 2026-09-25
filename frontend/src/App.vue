<template>
  <div class="min-h-screen bg-[var(--color-bg)] flex overflow-hidden">
    <!-- Main App Content -->
    <div class="relative h-screen w-full overflow-hidden transform-gpu flex flex-col bg-[var(--color-bg)]">
      <!-- Company Indicator Top Bar -->
      <div 
        v-if="showCompanyBar" 
        class="bg-blue-600 text-white text-center py-2.5 px-4 font-black text-xs uppercase tracking-widest select-none border-b border-black/10 shrink-0 shadow-sm flex items-center justify-center gap-2"
      >
        🏢 {{ alternativeCompany }}
      </div>

      <router-view class="flex-1 overflow-hidden" />
      
      <!-- Global Components (Contained within this div's boundaries on tablet) -->
      <Calculator :show="showCalculator" @close="showCalculator = false" />
      <CommandLine :show="showCommandLine" @close="showCommandLine = false" @open="showCommandLine = true" />
      <GlobalModals />
      <ErrorWindow :show="showError" :message="errorMessage" :type="errorType" :title="errorTitle" @close="showError = false" />
      
      <!-- Global Toast Stack (top-center for visibility) -->
      <div class="fixed top-6 left-1/2 -translate-x-1/2 z-[300] flex flex-col items-center gap-3 pointer-events-none">
        <TransitionGroup name="toast-fade" tag="div" class="flex flex-col items-center gap-3">
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

    <!-- Tab Limit Block Overlay (root-level: the content div has transform-gpu, -->
    <!-- which would make `fixed` children scope to it instead of the viewport) -->
    <div
      v-if="tabLimitBlocked"
      class="fixed inset-0 z-[400] flex items-center justify-center bg-black/70 backdrop-blur-sm"
    >
      <div class="max-w-md mx-4 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] shadow-2xl p-8 text-center">
        <h2 class="text-xl font-bold text-[var(--color-error)] mb-2">Too Many Tabs Open</h2>
        <p class="text-[var(--color-text)] mb-1">
          This license allows {{ tabLimitInfo.max_tabs }} concurrent tab{{ tabLimitInfo.max_tabs === 1 ? '' : 's' }}.
        </p>
        <p class="text-[var(--color-text-muted)] text-sm">
          Close another open tab of this app to free a slot. This will unlock automatically once one is available.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useShortcuts } from './services/shortcutManager';
import { globalShortcuts } from './shortcuts/globalShortcuts';
import Calculator from './components/Calculator.vue';
import CommandLine from './components/CommandLine.vue';
import GlobalModals from './components/GlobalModals.vue';
import ErrorWindow from './components/ErrorWindow.vue';
import { useTheme } from './composables/useTheme';
import { useMqtt } from './composables/useMqtt';
import { initItemSync, destroyItemSync } from './composables/useItemSync';
import { initLedgerSync, destroyLedgerSync } from './composables/useLedgerSync';
import { initBillPanelSync, destroyBillPanelSync } from './composables/useBillPanelSync';
import { initFrappeSocket } from './services/frappeSocket';
import { tabLimitBlocked, tabLimitInfo } from './services/tabSession';

const showCalculator = ref(false);
const showCommandLine = ref(false);
const showError = ref(false);
const errorMessage = ref('');
const errorType = ref('error');
const errorTitle = ref('Error');

const toasts = ref([]);

const wbCompany = ref('');
const alternativeCompany = ref('');
let companiesInterval = null;

const showCompanyBar = computed(() => {
  const wb = (wbCompany.value || '').trim().toLowerCase();
  const ae = (alternativeCompany.value || '').trim().toLowerCase();
  return wb && ae && wb === ae;
});

function updateCompanies() {
  wbCompany.value = localStorage.getItem('wb-company') || '';
  alternativeCompany.value = localStorage.getItem('ae-alternative_company') || '';
}
function showToast(message, type = 'success', duration = 2000) {
  const id = Date.now() + Math.random().toString(36).substr(2, 9);
  toasts.value.push({ id, message, type });
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id);
  }, duration);
}
const { initTheme } = useTheme();
const { connectMqtt } = useMqtt();

useShortcuts(globalShortcuts, 'global');

function toggleCalculator() {
  showCalculator.value = !showCalculator.value;
}

function toggleCommandLine() {
  showCommandLine.value = !showCommandLine.value;
}

const _nativeAlert = window.alert.bind(window);

onMounted(async () => {
  updateCompanies();
  window.addEventListener('storage', updateCompanies);
  companiesInterval = setInterval(updateCompanies, 1000);

  initTheme();
  await initFrappeSocket();
  connectMqtt();
  initItemSync();
  initLedgerSync();
  initBillPanelSync();
  window.addEventListener('wb-global-calculator-toggle', toggleCalculator);
  window.addEventListener('wb-global-command-line-toggle', toggleCommandLine);
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
  window.removeEventListener('storage', updateCompanies);
  if (companiesInterval) {
    clearInterval(companiesInterval);
  }

  destroyItemSync();
  destroyLedgerSync();
  destroyBillPanelSync();
  window.removeEventListener('wb-global-calculator-toggle', toggleCalculator);
  window.removeEventListener('wb-global-command-line-toggle', toggleCommandLine);
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
  transform: translateY(-20px) scale(0.9);
}
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-40px);
}
.toast-fade-move {
  transition: transform 0.3s ease;
}
</style>
