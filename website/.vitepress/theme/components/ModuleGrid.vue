<script setup>
// Single source of truth: the same list the licence uses to unlock pages.
import modules from '../../../../licensing_features_by_category.json'

const categories = Object.entries(modules).map(([name, items]) => ({ name, items }))
</script>

<template>
  <div class="module-grid">
    <div v-for="cat in categories" :key="cat.name" class="module">
      <h3>{{ cat.name }}</h3>
      <span class="count">{{ cat.items.length }} screens</span>
      <ul>
        <li v-for="item in cat.items" :key="item.id">{{ item.name }}</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-top: 16px;
}
.module {
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 18px 20px;
  background: var(--vp-c-bg-soft);
}
.module h3 {
  margin: 0;
  font-size: 17px;
  border: none;
  padding: 0;
}
.count {
  font-size: 12px;
  color: var(--vp-c-text-2);
}
.module ul {
  margin: 10px 0 0;
  padding-left: 18px;
  font-size: 14px;
  line-height: 1.7;
}
</style>
