<template>
  <div class="min-h-screen bg-gray-50">
    <router-view />
    <Calculator :show="showCalculator" @close="showCalculator = false" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useShortcuts } from './services/shortcutManager';
import { globalShortcuts } from './shortcuts/globalShortcuts';
import Calculator from './components/Calculator.vue';

const showCalculator = ref(false);

// Register application-wide shortcuts
useShortcuts(globalShortcuts, 'global');

function toggleCalculator() {
  showCalculator.value = !showCalculator.value;
}

onMounted(() => {
  window.addEventListener('wb-global-calculator-toggle', toggleCalculator);
});

onUnmounted(() => {
  window.removeEventListener('wb-global-calculator-toggle', toggleCalculator);
});
</script>
