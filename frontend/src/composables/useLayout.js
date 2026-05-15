import { ref } from 'vue'

const isSidebarCollapsed = ref(false)

export function useLayout() {
  return {
    isSidebarCollapsed
  }
}