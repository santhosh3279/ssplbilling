<script setup>
import { plans, extras, billingNote, formatPrice } from '../../data/plans.js'
import { withBase } from 'vitepress'

defineProps({
  showExtras: { type: Boolean, default: false },
})
</script>

<template>
  <div class="pricing">
    <div class="plans">
      <div v-for="plan in plans" :key="plan.id" class="plan" :class="{ featured: plan.featured }">
        <div v-if="plan.featured" class="badge">Most popular</div>
        <h3>{{ plan.name }}</h3>
        <p class="tagline">{{ plan.tagline }}</p>
        <div class="price">
          <span class="amount">{{ formatPrice(plan.price) }}</span>
          <span v-if="plan.price !== null" class="period">{{ plan.period }}</span>
        </div>
        <ul class="limits">
          <li>{{ plan.users }}</li>
          <li>{{ plan.stores }}</li>
        </ul>
        <ul class="highlights">
          <li v-for="h in plan.highlights" :key="h">{{ h }}</li>
        </ul>
        <a class="cta" :href="withBase('/contact')">{{ plan.cta }}</a>
      </div>
    </div>
    <p class="note">{{ billingNote }}</p>

    <table v-if="showExtras" class="extras">
      <thead>
        <tr><th>Optional service</th><th>Rate</th><th>Billed</th></tr>
      </thead>
      <tbody>
        <tr v-for="e in extras" :key="e.item">
          <td>{{ e.item }}</td>
          <td>{{ formatPrice(e.price) }}</td>
          <td>{{ e.unit }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.plans {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  margin-top: 16px;
}
.plan {
  position: relative;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--vp-c-divider);
  border-radius: 14px;
  padding: 24px;
  background: var(--vp-c-bg-soft);
}
.plan.featured {
  border: 2px solid var(--vp-c-brand-1);
}
.badge {
  position: absolute;
  top: -12px;
  right: 20px;
  background: var(--vp-c-brand-1);
  color: var(--vp-c-white);
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 999px;
}
.plan h3 {
  margin: 0;
  font-size: 20px;
  border: none;
  padding: 0;
}
.tagline {
  margin: 4px 0 16px;
  color: var(--vp-c-text-2);
  font-size: 14px;
  line-height: 1.5;
}
.price {
  margin-bottom: 12px;
}
.amount {
  font-size: 30px;
  font-weight: 700;
}
.period {
  color: var(--vp-c-text-2);
  margin-left: 4px;
}
.limits,
.highlights {
  list-style: none;
  padding: 0;
  margin: 0 0 12px;
  font-size: 14px;
}
.limits li {
  font-weight: 600;
  line-height: 1.8;
}
.highlights {
  flex: 1;
}
.highlights li {
  padding-left: 22px;
  position: relative;
  line-height: 1.6;
  margin: 4px 0;
}
.highlights li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: var(--vp-c-brand-1);
  font-weight: 700;
}
.cta {
  display: block;
  text-align: center;
  padding: 10px 16px;
  border-radius: 20px;
  font-weight: 600;
  text-decoration: none !important;
  border: 1px solid var(--vp-c-brand-1);
  color: var(--vp-c-brand-1) !important;
}
.featured .cta {
  background: var(--vp-c-brand-1);
  color: var(--vp-c-white) !important;
}
.note {
  font-size: 13px;
  color: var(--vp-c-text-2);
  margin-top: 12px;
}
.extras {
  margin-top: 24px;
  width: 100%;
  display: table;
}
</style>
