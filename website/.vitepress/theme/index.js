import DefaultTheme from 'vitepress/theme'
import PricingTable from './components/PricingTable.vue'
import ModuleGrid from './components/ModuleGrid.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('PricingTable', PricingTable)
    app.component('ModuleGrid', ModuleGrid)
  },
}
