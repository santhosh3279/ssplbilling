<template>
  <!-- Sub-folder catalogues linked to the open catalogue; card styling mirrors catalogueviewer.vue. -->
  <section v-if="folders.length" class="mb-8" aria-label="Sub folders">
    <div class="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      <button
        v-for="folder in folders"
        :key="folder.name"
        type="button"
        @click="$emit('open', folder.pageaddress)"
        class="catalogue-card group relative flex flex-col rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3.5 text-left shadow-md hover:shadow-2xl hover:border-[var(--color-info)]/60 cursor-pointer transition-all duration-300 transform hover:-translate-y-1"
      >
        <!-- Accent Light Border Top Glow -->
        <div class="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-t-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

        <div class="flex-1 w-full space-y-2">
          <!-- Icon and Active Items -->
          <div class="flex items-center justify-between">
            <span class="card-icon text-3xl">📁</span>
            <span class="card-item-count text-[10px] font-bold text-[var(--color-text-muted)]">
              {{ folder.item_count ?? 0 }} active {{ folder.item_count === 1 ? 'item' : 'items' }}
            </span>
          </div>

          <!-- Title -->
          <div class="space-y-1.5">
            <h3 class="card-heading text-lg font-black text-[var(--color-text)] group-hover:text-[var(--color-info)] transition-colors line-clamp-2">
              {{ folder.heading }}
            </h3>
          </div>
        </div>

        <!-- Bottom Action indicator -->
        <div class="card-action w-full mt-3.5 pt-2 border-t border-[var(--color-border)]/40 flex items-center justify-between text-xs font-bold text-[var(--color-info)] group-hover:translate-x-1 transition-transform duration-300">
          <span>View Items</span>
          <span>→</span>
        </div>
      </button>
    </div>
  </section>
</template>

<script setup>
defineProps({
  folders: { type: Array, default: () => [] },
})
defineEmits(['open'])
</script>

<style scoped>
.catalogue-card {
  font-size: 26px !important;
}
.catalogue-card .card-item-count {
  font-size: 20px !important;
}
.catalogue-card .card-heading {
  font-size: 27px !important;
}
.catalogue-card .card-action {
  font-size: 24px !important;
}
.catalogue-card .card-icon {
  font-size: 40px !important;
}
</style>
