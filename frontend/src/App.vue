<template>
  <div class="min-h-screen bg-[var(--color-bg)]">
    <router-view />
    <Calculator :show="showCalculator" @close="showCalculator = false" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useShortcuts } from './services/shortcutManager';
import { globalShortcuts } from './shortcuts/globalShortcuts';
import Calculator from './components/Calculator.vue';
import { useTheme } from './composables/useTheme';

const showCalculator = ref(false);
const { initTheme } = useTheme();

// Register application-wide shortcuts
useShortcuts(globalShortcuts, 'global');

function toggleCalculator() {
  showCalculator.value = !showCalculator.value;
}

onMounted(() => {
  initTheme(); // Apply saved theme class to <html> on boot
  window.addEventListener('wb-global-calculator-toggle', toggleCalculator);
});

onUnmounted(() => {
  window.removeEventListener('wb-global-calculator-toggle', toggleCalculator);
});
</script>
