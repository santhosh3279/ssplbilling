<template>
  <div class="min-h-screen bg-[var(--color-bg)]">
    <router-view />
    <Calculator :show="showCalculator" @close="showCalculator = false" />
    <CommandLine :show="showCommandLine" @close="showCommandLine = false" @open="showCommandLine = true" />
    <GeneralLedger v-if="showGeneralLedger" :is-sub-window="true" @close="showGeneralLedger = false" />
    <ErrorWindow :show="showError" :message="errorMessage" @close="showError = false" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useShortcuts } from './services/shortcutManager';
import { globalShortcuts } from './shortcuts/globalShortcuts';
import Calculator from './components/Calculator.vue';
import CommandLine from './components/CommandLine.vue';
import GeneralLedger from './pages/GeneralLedger.vue';
import ErrorWindow from './components/ErrorWindow.vue';
import { useTheme } from './composables/useTheme';

const showCalculator = ref(false);
const showCommandLine = ref(false);
const showGeneralLedger = ref(false);
const showError = ref(false);
const errorMessage = ref('');
const { initTheme } = useTheme();

useShortcuts(globalShortcuts, 'global');

function toggleCalculator() {
  showCalculator.value = !showCalculator.value;
}

function toggleCommandLine() {
  showCommandLine.value = !showCommandLine.value;
}

function toggleGeneralLedger() {
  showGeneralLedger.value = !showGeneralLedger.value;
}

const _nativeAlert = window.alert.bind(window);

onMounted(() => {
  initTheme();
  window.addEventListener('wb-global-calculator-toggle', toggleCalculator);
  window.addEventListener('wb-global-command-line-toggle', toggleCommandLine);
  window.addEventListener('wb-global-general-ledger-toggle', toggleGeneralLedger);
  window.alert = (msg) => {
    errorMessage.value = String(msg ?? '')
    showError.value = true
  };
});

onUnmounted(() => {
  window.removeEventListener('wb-global-calculator-toggle', toggleCalculator);
  window.removeEventListener('wb-global-command-line-toggle', toggleCommandLine);
  window.removeEventListener('wb-global-general-ledger-toggle', toggleGeneralLedger);
  window.alert = _nativeAlert;
});
</script>
