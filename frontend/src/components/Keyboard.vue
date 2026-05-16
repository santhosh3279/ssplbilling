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
      <!-- Spacer to push content to bottom -->
      <div class="flex-1"></div>
      
      <!-- Function Keys Row -->
      <div class="grid grid-cols-6 gap-1 mb-1">
        <button v-for="n in 12" :key="'f'+n" 
                @pointerdown.prevent="pressKey('F' + n)"
                class="key-btn text-[18px] font-bold py-3 bg-[var(--color-bg)] text-[var(--color-highlight)] border border-[var(--color-border)] rounded shadow-sm">
          F{{ n }}
        </button>
      </div>

      <!-- Special Utility Keys -->
      <div class="grid grid-cols-4 gap-1 mb-1">
        <button @pointerdown.prevent="pressKey('Escape')" class="key-btn utility bg-[var(--color-danger)]/10 text-[var(--color-danger)] py-3 text-[20px] font-bold rounded border border-[var(--color-danger)]/20 shadow-sm">ESC</button>
        <button @pointerdown.prevent="pressKey('End')" class="key-btn utility bg-[var(--color-info)]/10 text-[var(--color-info)] py-3 text-[20px] font-bold rounded border border-[var(--color-info)]/20 shadow-sm">END</button>
        <button @pointerdown.prevent="pressShortcut('l', { ctrlKey: true })" class="key-btn utility bg-[var(--color-warning)]/10 text-[var(--color-warning)] py-3 text-[20px] font-bold rounded border border-[var(--color-warning)]/20 shadow-sm">C+L</button>
        <button @pointerdown.prevent="pressShortcut('i', { ctrlKey: true })" class="key-btn utility bg-[var(--color-warning)]/10 text-[var(--color-warning)] py-3 text-[20px] font-bold rounded border border-[var(--color-warning)]/20 shadow-sm">C+I</button>
      </div>

      <!-- QWERTY Layout -->
      <div v-if="currentLayout === 'qwerty'" class="flex flex-col gap-1">
        <!-- Full Width Backspace Row (Top of Numpad) -->
        <div class="flex mb-1">
          <button @pointerdown.prevent="pressKey('Backspace')" class="key-btn qwerty w-full text-[var(--color-danger)] font-black flex gap-4">
            <span>⌫</span>
            <span class="text-[20px] uppercase tracking-[0.2em]">Backspace</span>
          </button>
        </div>

        <!-- Number Row (Above QWERTY) -->
        <div class="flex gap-1 mb-1">
          <button v-for="k in '1234567890'.split('')" :key="k" @pointerdown.prevent="pressKey(k)" class="key-btn qwerty flex-1">{{ k }}</button>
        </div>

        <!-- Alpha Row 1 -->
        <div class="flex gap-1">
          <button v-for="k in 'QWERTYUIOP'.split('')" :key="k" @pointerdown.prevent="pressKey(k)" class="key-btn qwerty flex-1">{{ isCapsLock ? k : k.toLowerCase() }}</button>
        </div>

        <!-- Alpha Row 2 -->
        <div class="flex gap-1 px-2">
          <button v-for="k in 'ASDFGHJKL'.split('')" :key="k" @pointerdown.prevent="pressKey(k)" class="key-btn qwerty flex-1">{{ isCapsLock ? k : k.toLowerCase() }}</button>
        </div>

        <!-- Alpha Row 3 -->
        <div class="flex gap-1 px-4">
          <button v-for="k in 'ZXCVBNM'.split('')" :key="k" @pointerdown.prevent="pressKey(k)" class="key-btn qwerty flex-1">{{ isCapsLock ? k : k.toLowerCase() }}</button>
          <button @pointerdown.prevent="pressKey('Backspace')" class="key-btn qwerty flex-1 text-[var(--color-danger)] font-bold">⌫</button>
        </div>

        <!-- Symbols / Misc Row 4 -->
        <div class="flex gap-1">
          <button @pointerdown.prevent="toggleCapsLock" class="key-btn qwerty flex-1 text-[14px] leading-tight transition-all duration-200" :class="isCapsLock ? 'bg-[var(--color-focus)] text-[var(--color-text-on-focus)] ring-2 ring-[var(--color-focus)]/50 shadow-lg' : 'bg-[var(--color-bg)] text-[var(--color-text)]'">CAPS</button>
          <button @pointerdown.prevent="pressKey(',')" class="key-btn qwerty flex-1">,</button>
          <button @pointerdown.prevent="pressKey(' ')" class="key-btn qwerty flex-[4] text-[20px]">SPACE</button>
          <button @pointerdown.prevent="pressKey('-')" class="key-btn qwerty flex-1">-</button>
          <button @pointerdown.prevent="currentLayout = 'numpad'" class="key-btn qwerty flex-1 text-[16px] text-[var(--color-info)]">123</button>
        </div>
      </div>

      <!-- NUMPAD / SYMBOLS Layout -->
      <div v-else class="flex gap-1">
        <!-- Symbols Side (Left) -->
        <div class="flex-1 grid grid-cols-4 gap-1">
          <button v-for="s in symbols" :key="s" @pointerdown.prevent="pressKey(s)" class="key-btn qwerty text-[20px]">{{ s }}</button>
          <button @pointerdown.prevent="currentLayout = 'qwerty'" class="key-btn qwerty col-span-2 text-[var(--color-info)] text-[20px]">ABC</button>
          <button @pointerdown.prevent="pressKey(' ')" class="key-btn qwerty col-span-2 text-[16px]">SPACE</button>
        </div>

        <!-- Numpad Side (Right) -->
        <div class="w-[45%] flex flex-col gap-1 border-l border-[var(--color-border)] pl-1">
          <div class="grid grid-cols-3 gap-1">
            <button v-for="k in '789456123'.split('')" :key="k" @pointerdown.prevent="pressKey(k)" class="key-btn qwerty py-6 text-[32px]">{{ k }}</button>
            <button @pointerdown.prevent="pressKey('0')" class="key-btn qwerty col-span-2 py-6 text-[32px]">0</button>
            <button @pointerdown.prevent="pressKey('.')" class="key-btn qwerty py-6 text-[32px]">.</button>
          </div>
          <button @pointerdown.prevent="pressKey('Backspace')" class="key-btn qwerty w-full py-4 text-[var(--color-danger)] text-[24px]">⌫ Backspace</button>
        </div>
      </div>
    </div>

    <!-- Bottom Enter Key -->
    <div class="p-2 bg-[var(--color-surface-raised)] border-t border-[var(--color-border)] shrink-0">
      <button 
        @pointerdown.prevent="pressKey('Enter')"
        class="w-full py-[22px] rounded-xl bg-[var(--color-success)] text-[var(--color-text-on-highlight)] font-black text-[30px] uppercase tracking-[0.2em] shadow-lg active:scale-95 transition-all"
      >
        Enter
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const isCapsLock = ref(true);
const currentLayout = ref('qwerty');
const symbols = '@#$%&*()_+=[]{}|\\:;"\'<>?'.split('');
let lastActiveElement = null;

const toggleCapsLock = () => {
  isCapsLock.value = !isCapsLock.value;
};

const handleFocusIn = (e) => {
  const target = e.target;
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
    lastActiveElement = target;
  }
};

onMounted(() => {
  window.addEventListener('focusin', handleFocusIn);
});

onUnmounted(() => {
  window.removeEventListener('focusin', handleFocusIn);
});

function pressKey(key) {
  // Use current active element if it's not the body, otherwise fallback to last known input
  let activeEl = document.activeElement;
  if (!activeEl || activeEl === document.body) {
    activeEl = lastActiveElement;
  }

  if (!activeEl) return;

  const isInput = activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA';

  if (key.length === 1) {
    if (isInput) {
      // Ensure element is focused before typing
      activeEl.focus();
      
      let char = key;
      if (/[a-zA-Z]/.test(key)) {
        char = isCapsLock.value ? key.toUpperCase() : key.toLowerCase();
      }

      const success = document.execCommand('insertText', false, char);
      
      if (!success) {
        const start = activeEl.selectionStart;
        const end = activeEl.selectionEnd;
        const val = activeEl.value;
        activeEl.value = val.substring(0, start) + char + val.substring(end);
        activeEl.selectionStart = activeEl.selectionEnd = start + 1;
        activeEl.dispatchEvent(new Event('input', { bubbles: true }));
        activeEl.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
  } else {
    // Dispatch keyboard event for special keys
    const eventInit = {
      key: key,
      code: key,
      bubbles: true,
      cancelable: true,
      keyCode: key === 'Enter' ? 13 : (key === 'Backspace' ? 8 : 0),
      which: key === 'Enter' ? 13 : (key === 'Backspace' ? 8 : 0)
    };

    const keydownEvent = new KeyboardEvent('keydown', eventInit);
    const keyupEvent = new KeyboardEvent('keyup', eventInit);
    
    if (isInput && key === 'Backspace') {
      activeEl.focus();
      const start = activeEl.selectionStart;
      const end = activeEl.selectionEnd;
      if (start === end && start > 0) {
        activeEl.value = activeEl.value.substring(0, start - 1) + activeEl.value.substring(end);
        activeEl.selectionStart = activeEl.selectionEnd = start - 1;
      } else if (start !== end) {
        activeEl.value = activeEl.value.substring(0, start) + activeEl.value.substring(end);
        activeEl.selectionStart = activeEl.selectionEnd = start;
      }
      activeEl.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // Dispatch events
    activeEl.dispatchEvent(keydownEvent);

    if (key === 'Enter') {
       if (activeEl.tagName === 'BUTTON') activeEl.click();
       // Only dispatch to document if activeEl is not in the document to avoid double bubbling
       if (!document.contains(activeEl)) {
         document.dispatchEvent(keydownEvent);
       }
    } else {
       if (!document.contains(activeEl)) {
         document.dispatchEvent(keydownEvent);
       }
    }
    
    activeEl.dispatchEvent(keyupEvent);
    if (!document.contains(activeEl)) {
      document.dispatchEvent(keyupEvent);
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
  @apply transition-all active:scale-90 active:brightness-90 flex items-center justify-center touch-none;
}
.qwerty {
  @apply py-[18px] bg-[var(--color-bg)] text-[var(--color-text)] font-bold text-[24px] border border-[var(--color-border)] rounded shadow-sm;
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
