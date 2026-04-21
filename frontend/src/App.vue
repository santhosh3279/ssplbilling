<template>
  <div class="min-h-screen bg-[var(--color-bg)]">
    <router-view />
    <Calculator :show="showCalculator" @close="showCalculator = false" />
    <ErrorWindow :show="showError" :message="errorMessage" @close="showError = false" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useShortcuts } from './services/shortcutManager';
import { globalShortcuts } from './shortcuts/globalShortcuts';
import Calculator from './components/Calculator.vue';
import ErrorWindow from './components/ErrorWindow.vue';
import { useTheme } from './composables/useTheme';

const showCalculator = ref(false);
const showError = ref(false);
const errorMessage = ref('');
const { initTheme } = useTheme();

useShortcuts(globalShortcuts, 'global');

function toggleCalculator() {
  showCalculator.value = !showCalculator.value;
}

const _nativeAlert = window.alert.bind(window);

onMounted(() => {
  initTheme();
  window.addEventListener('wb-global-calculator-toggle', toggleCalculator);
  window.alert = (msg) => {
    errorMessage.value = String(msg ?? '')
    showError.value = true
  };
});

onUnmounted(() => {
  window.removeEventListener('wb-global-calculator-toggle', toggleCalculator);
  window.alert = _nativeAlert;
});
</script>
