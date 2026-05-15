<template>
  <div class="h-full flex flex-col bg-[var(--color-surface)] select-none">
    <!-- Header -->
    <div class="bg-[var(--color-highlight)] p-2 text-center shadow-md shrink-0">
      <div class="text-[var(--color-text-on-highlight)] font-black uppercase tracking-[0.1em] text-[10px]">
        Tablet Keyboard
      </div>
    </div>

    <!-- Scrollable Key Area -->
    <div class="flex-1 overflow-y-auto p-1 flex flex-col gap-1 custom-scrollbar">
      
      <!-- Function Keys Row -->
      <div class="grid grid-cols-6 gap-1 mb-1">
        <button v-for="n in 12" :key="'f'+n" 
                @mousedown.prevent="pressKey('F' + n)"
                class="key-btn text-[9px] font-bold py-2 bg-[var(--color-bg)] text-[var(--color-highlight)] border border-[var(--color-border)] rounded shadow-sm">
          F{{ n }}
        </button>
      </div>

      <!-- Special Utility Keys -->
      <div class="grid grid-cols-4 gap-1 mb-2">
        <button @mousedown.prevent="pressKey('Escape')" class="key-btn utility bg-[var(--color-danger)]/10 text-[var(--color-danger)] py-2 text-[10px] font-bold rounded border border-[var(--color-danger)]/20 shadow-sm">ESC</button>
        <button @mousedown.prevent="pressKey('End')" class="key-btn utility bg-[var(--color-info)]/10 text-[var(--color-info)] py-2 text-[10px] font-bold rounded border border-[var(--color-info)]/20 shadow-sm">END</button>
        <button @mousedown.prevent="pressShortcut('l', { ctrlKey: true })" class="key-btn utility bg-[var(--color-warning)]/10 text-[var(--color-warning)] py-2 text-[10px] font-bold rounded border border-[var(--color-warning)]/20 shadow-sm">C+L</button>
        <button @mousedown.prevent="pressShortcut('i', { ctrlKey: true })" class="key-btn utility bg-[var(--color-warning)]/10 text-[var(--color-warning)] py-2 text-[10px] font-bold rounded border border-[var(--color-warning)]/20 shadow-sm">C+I</button>
      </div>

      <!-- QWERTY Layout -->
      <div class="flex flex-col gap-1">
        <!-- Numbers Row -->
        <div class="flex gap-1">
          <button v-for="k in '1234567890'.split('')" :key="k" @mousedown.prevent="pressKey(k)" class="key-btn qwerty flex-1">{{ k }}</button>
        </div>

        <!-- Alpha Row 1 -->
        <div class="flex gap-1">
          <button v-for="k in 'QWERTYUIOP'.split('')" :key="k" @mousedown.prevent="pressKey(k)" class="key-btn qwerty flex-1">{{ k }}</button>
        </div>

        <!-- Alpha Row 2 -->
        <div class="flex gap-1 px-2">
          <button v-for="k in 'ASDFGHJKL'.split('')" :key="k" @mousedown.prevent="pressKey(k)" class="key-btn qwerty flex-1">{{ k }}</button>
        </div>

        <!-- Alpha Row 3 -->
        <div class="flex gap-1">
          <button v-for="k in 'ZXCVBNM'.split('')" :key="k" @mousedown.prevent="pressKey(k)" class="key-btn qwerty flex-1">{{ k }}</button>
          <button @mousedown.prevent="pressKey('Backspace')" class="key-btn qwerty flex-[1.5] text-[var(--color-danger)]">⌫</button>
        </div>

        <!-- Symbols / Misc Row 4 -->
        <div class="flex gap-1">
          <button @mousedown.prevent="pressKey('.')" class="key-btn qwerty flex-1">.</button>
          <button @mousedown.prevent="pressKey(',')" class="key-btn qwerty flex-1">,</button>
          <button @mousedown.prevent="pressKey(' ')" class="key-btn qwerty flex-[4] text-[10px]">SPACE</button>
          <button @mousedown.prevent="pressKey('-')" class="key-btn qwerty flex-1">-</button>
          <button @mousedown.prevent="pressKey('/')" class="key-btn qwerty flex-1">/</button>
        </div>
      </div>
    </div>

    <!-- Bottom Enter Key -->
    <div class="p-2 bg-[var(--color-surface-raised)] border-t border-[var(--color-border)] shrink-0">
      <button 
        @mousedown.prevent="pressKey('Enter')"
        class="w-full py-5 rounded-xl bg-[var(--color-success)] text-[var(--color-text-on-highlight)] font-black text-xl uppercase tracking-[0.2em] shadow-lg active:scale-95 transition-all"
      >
        Enter
      </button>
    </div>
  </div>
</template>

<script setup>
function pressKey(key) {
  const activeEl = document.activeElement;
  const isInput = activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA');

  // Handle standard characters vs special keys
  if (key.length === 1) {
    if (isInput) {
      const start = activeEl.selectionStart;
      const end = activeEl.selectionEnd;
      const val = activeEl.value;
      activeEl.value = val.substring(0, start) + key + val.substring(end);
      activeEl.selectionStart = activeEl.selectionEnd = start + 1;
      // Trigger input event for Vue/other listeners
      activeEl.dispatchEvent(new Event('input', { bubbles: true }));
    }
  } else {
    // Dispatch keyboard event for special keys (Enter, Esc, F-keys, etc.)
    const event = new KeyboardEvent('keydown', {
      key: key,
      code: key,
      bubbles: true,
      cancelable: true
    });
    
    if (isInput && key === 'Backspace') {
      const start = activeEl.selectionStart;
      const end = activeEl.selectionEnd;
      if (start === end && start > 0) {
        activeEl.value = activeEl.value.substring(0, start - 1) + activeEl.value.substring(end);
        activeEl.selectionStart = activeEl.selectionEnd = start - 1;
      } else {
        activeEl.value = activeEl.value.substring(0, start) + activeEl.value.substring(end);
        activeEl.selectionStart = activeEl.selectionEnd = start;
      }
      activeEl.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // Special case for Enter on buttons/inputs
    if (key === 'Enter' && activeEl) {
       // Also dispatch to the element specifically
       activeEl.dispatchEvent(event);
       if (activeEl.tagName === 'BUTTON') activeEl.click();
    } else {
       document.dispatchEvent(event);
    }
  }
}

function pressShortcut(key, mods = {}) {
  const event = new KeyboardEvent('keydown', {
    key: key,
    code: 'Key' + key.toUpperCase(),
    ctrlKey: !!mods.ctrlKey,
    altKey: !!mods.altKey,
    shiftKey: !!mods.shiftKey,
    bubbles: true,
    cancelable: true
  });
  document.dispatchEvent(event);
}
</script>

<style scoped>
.key-btn {
  @apply transition-all active:scale-90 active:brightness-90 flex items-center justify-center;
}
.qwerty {
  @apply py-3 bg-[var(--color-bg)] text-[var(--color-text)] font-bold text-xs border border-[var(--color-border)] rounded shadow-sm;
}
.utility {
  @apply flex items-center justify-center uppercase tracking-tighter;
}
/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 10px;
}
</style>
