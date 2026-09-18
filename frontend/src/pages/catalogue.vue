<template>
  <div class="h-screen flex flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] text-[13px] overflow-hidden catalogue-display-page">
    
    <!-- ── HEADER ────────────────────────────────────────────────── -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 shadow-sm shrink-0">
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <button
            @click="router.push('/catelogue')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition"
          >
            ← Catalogue
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-sm font-semibold text-[var(--color-text)]">
            Cataloge Mangement
          </h1>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="handleNewCatalogue"
            class="rounded bg-[var(--color-success)] px-4 py-1.5 text-xs font-bold text-white hover:bg-[var(--color-success)]/90 transition shadow-sm"
          >
            + New Catalogue List
          </button>
          <button
            @click="fetchCatalogues"
            :disabled="loading"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]/80 transition"
          >
            {{ loading ? 'Loading...' : '🔄 Refresh List' }}
          </button>
        </div>
      </div>
    </header>

    <!-- ── MAIN BODY: SPLIT VIEW ─────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">
      
      <!-- ── LEFT COLUMN: CATALOGUES LIST (17.5%) ── -->
      <aside class="w-[17.5%] flex flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
        <!-- Search bar -->
        <div class="p-3 border-b border-[var(--color-border)] shrink-0 bg-[var(--color-surface)]/50">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search catalogues by heading or address..."
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition"
          />
        </div>

        <!-- Catalogues List -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="loading && !catalogues.length" class="flex h-32 items-center justify-center">
            <span class="text-xs text-[var(--color-text-muted)] animate-pulse">Loading catalogue lists...</span>
          </div>
          <div v-else-if="!filteredCatalogues.length" class="flex h-32 items-center justify-center">
            <span class="text-xs italic text-[var(--color-text-muted)]">No catalogue lists found</span>
          </div>
          <div v-else class="divide-y divide-[var(--color-border)]/50">
            <div
              v-for="catalogue in filteredCatalogues"
              :key="catalogue.name"
              @click="selectCatalogue(catalogue.name)"
              class="p-4 cursor-pointer hover:bg-[var(--color-surface-raised)]/40 transition-colors flex flex-col gap-2 relative"
              :class="{
                'bg-[var(--color-info)]/10 border-l-4 border-[var(--color-info)]': selectedName === catalogue.name
              }"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="font-bold text-[14px] text-[var(--color-text)] truncate" :title="catalogue.heading">
                  {{ catalogue.heading }}
                </div>
              </div>

              <div class="text-[11px] text-[var(--color-text-muted)] flex flex-wrap items-center gap-x-2 gap-y-1">
                <span>Address: 
                  <a 
                    :href="`/catalogue/${catalogue.pageaddress}`"
                    target="_blank" 
                    class="text-[var(--color-info)] hover:underline font-mono"
                    @click.stop
                  >
                    /catalogue/{{ catalogue.pageaddress }}
                  </a>
                </span>
                <span>•</span>
                <span>ID: <span class="font-mono text-[var(--color-text-muted)]">{{ catalogue.name }}</span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer status -->
        <div class="p-3 border-t border-[var(--color-border)] shrink-0 bg-[var(--color-surface)] text-center text-xs text-[var(--color-text-muted)]">
          <strong>{{ filteredCatalogues.length }}</strong> lists shown (Total: {{ catalogues.length }})
        </div>
      </aside>

      <!-- ── RIGHT COLUMN: FORM / DETAILS (82.5%) ── -->
      <main class="w-[82.5%] flex flex-col bg-[var(--color-bg)] overflow-hidden">
        <!-- Loading overlay for details -->
        <div v-if="detailLoading" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <span class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent mb-2"></span>
            <div class="text-xs text-[var(--color-text-muted)]">Loading catalogue details...</div>
          </div>
        </div>

        <div v-else-if="!isFormActive" class="flex-1 flex flex-col items-center justify-center p-8 text-center text-[var(--color-text-muted)]">
          <span class="text-5xl mb-4">🏷️</span>
          <h2 class="text-base font-bold text-[var(--color-text)] mb-1">Catalogue Display Management</h2>
          <p class="max-w-md text-xs leading-relaxed mb-4">
            Select a catalogue list from the left panel to edit its details and items, or click the button below to create a new one.
          </p>
          <button
            @click="handleNewCatalogue"
            class="rounded bg-[var(--color-success)] px-5 py-2 text-xs font-bold text-white hover:bg-[var(--color-success)]/90 transition shadow-md"
          >
            + Create New Catalogue List
          </button>
        </div>

        <!-- FORM PANEL -->
        <div v-else class="flex-1 flex flex-col overflow-hidden">
          <!-- Form Header -->
          <div class="px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-between shrink-0">
            <div>
              <h2 class="text-[14px] font-bold text-[var(--color-text)]">
                {{ form.name ? 'Edit Catalogue List' : 'New Catalogue List' }}
              </h2>
              <p class="text-[10px] text-[var(--color-text-muted)] font-mono truncate max-w-sm mt-0.5">
                {{ form.name || 'Draft document' }}
              </p>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="form.name"
                @click="handleDeleteCatalogue"
                :disabled="saving"
                class="rounded border border-red-300 text-red-600 bg-red-50 px-3 py-1.5 text-xs font-bold hover:bg-red-100 disabled:opacity-50 transition"
              >
                🗑 Delete List
              </button>
              <button
                @click="closeForm"
                class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]/80 transition"
              >
                Cancel
              </button>
              <button
                @click="handleSave"
                :disabled="saving"
                class="rounded bg-[var(--color-info)] px-5 py-1.5 text-xs font-bold text-white hover:bg-[var(--color-info)]/90 disabled:opacity-50 transition shadow"
              >
                {{ saving ? 'Saving...' : 'Save Catalogue List' }}
              </button>
            </div>
          </div>

          <!-- Form Fields Wrapper -->
          <div class="flex-1 overflow-y-auto p-6 space-y-6">
            <!-- Basic Info Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm space-y-4">
              <h3 class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 pb-1.5">
                Catalogue Information
              </h3>
              
              <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <!-- Heading -->
                <div class="flex flex-col gap-1.5 md:col-span-1">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Heading <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <input
                    v-model="form.heading"
                    type="text"
                    placeholder="Enter catalogue display heading"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  />
                </div>

                <!-- Page Address -->
                <div class="flex flex-col gap-1.5 md:col-span-1">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Page Address <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <input
                    v-model="form.pageaddress"
                    type="text"
                    placeholder="Enter unique page address"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition font-mono"
                  />
                  <p class="text-[9px] text-[var(--color-text-muted)] mt-0.5" v-if="!form.name">
                    This will be used as the unique ID for this document.
                  </p>
                  <a
                    v-if="form.name"
                    :href="`/catalogue/${form.pageaddress}`"
                    target="_blank"
                    class="text-[10px] text-[var(--color-info)] hover:underline mt-1 font-mono inline-flex items-center gap-1 w-fit"
                  >
                    🔗 View Page: /catalogue/{{ form.pageaddress }}
                  </a>
                </div>

                <!-- Priority -->
                <div class="flex flex-col gap-1.5 md:col-span-1">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">Priority</label>
                  <input
                    v-model.number="form.priority"
                    type="number"
                    min="0"
                    step="1"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  />
                  <p class="text-[9px] text-[var(--color-text-muted)] mt-0.5">Lower numbers appear first in the catalogue viewer.</p>
                </div>

                <!-- Tile Grid -->
                <div class="flex flex-col gap-1.5 md:col-span-1">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Tile Grid <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <select
                    v-model="form.tile_grid"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  >
                    <option value="1">1 Column</option>
                    <option value="2">2 Columns</option>
                    <option value="4">4 Columns</option>
                    <option value="6">6 Columns</option>
                    <option value="9">9 Columns</option>
                  </select>
                </div>

                <!-- Timer -->
                <div class="flex flex-col gap-1.5 md:col-span-1">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)] block">
                    Timer (Seconds)
                  </label>
                  <input
                    v-model="form.timer"
                    type="number"
                    min="0"
                    placeholder="e.g. 30 (0 to disable auto-refresh)"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  />
                  <p class="text-[9px] text-[var(--color-text-muted)] mt-0.5">
                    Time in seconds to auto-refresh/reload catalogue details (0 to disable).
                  </p>
                </div>
              </div>
            </div>

            <!-- Price Lists Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm space-y-4">
              <div class="flex items-center justify-between border-b border-[var(--color-border)]/50 pb-1.5">
                <h3 class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                  Applies to Price Lists ({{ form.price_lists?.length || 0 }})
                </h3>
                <button
                  @click="addPriceListRow"
                  type="button"
                  class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1 text-[10px] font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]/80 transition"
                >
                  + Add Price List
                </button>
              </div>

              <!-- Price Lists Table/List -->
              <div v-if="form.price_lists && form.price_lists.length" class="space-y-2">
                <div 
                  v-for="(pl, idx) in form.price_lists" 
                  :key="idx" 
                  class="flex items-center gap-3"
                >
                  <span class="text-xs text-[var(--color-text-muted)] font-mono w-6 text-center">
                    {{ idx + 1 }}
                  </span>
                  
                  <select
                    v-model="pl.price_list"
                    class="flex-1 rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-1.5 text-xs outline-none focus:border-[var(--color-info)] transition"
                  >
                    <option value="" disabled>Select Price List...</option>
                    <option 
                      v-for="list in priceLists" 
                      :key="list.name" 
                      :value="list.name"
                    >
                      {{ list.name }}
                    </option>
                  </select>

                  <button
                    @click="removePriceListRow(idx)"
                    type="button"
                    class="text-red-500 hover:text-red-700 font-bold px-2 py-1 text-sm transition"
                    title="Remove price list"
                  >
                    ✕
                  </button>
                </div>
              </div>
              <div v-else class="text-xs text-[var(--color-text-muted)] italic text-center py-2">
                No price lists configured. This catalogue applies to all price lists by default.
              </div>
            </div>

            <!-- Items Table Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm space-y-4">
              <div class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-border)]/50 pb-2">
                <h3 class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                  Catalogue Items ({{ form.items.length }})
                </h3>
                <div class="flex items-center gap-2">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)] whitespace-nowrap">
                    Sort by:
                  </label>
                  <select
                    v-model="sortColumn"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2.5 py-1 text-xs text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition font-medium"
                    aria-label="Select column to sort"
                  >
                    <option value="itemcode">Item</option>
                    <option value="itemname">Item Name</option>
                    <option value="discount_rule">Discount Rule</option>
                  </select>
                  <button
                    type="button"
                    @click="handleSort"
                    class="flex items-center gap-1.5 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1 text-xs font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]/80 active:scale-95 transition shadow-sm"
                    :title="`Click to sort by ${sortColumnLabel} (${sortDirection === 'asc' ? 'ascending' : 'descending'})`"
                  >
                    <span class="text-[var(--color-info)] font-mono">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
                    <span>Sort {{ sortDirection === 'asc' ? 'Ascending' : 'Descending' }}</span>
                  </button>
                </div>
              </div>
              
                <div @mousedown.prevent>
                  <QuickItemSearch
                    ref="quickSearchRef"
                    :results="searchSuggestions"
                    :query="itemSearchQuery"
                    :excluded-item-codes="listedItemCodes"
                    show-excluded-items
                    search-type="Sales"
                    @select="selectSearchItem"
                    @close="closeItemSearch"
                    @refresh="handleItemSearch"
                  />
                </div>

              <!-- Invoice-style catalogue items -->
              <p id="catalogue-grid-help" class="text-[var(--color-text-muted)]">
                Enter an item code, name, or barcode in Item/Barcode. Selecting an item moves to the next row. Tab, Enter and ↑ / ↓ move between item boxes.
              </p>
              <div ref="itemsGrid" class="catalogue-grid" tabindex="0" aria-label="Catalogue items spreadsheet">
                <table class="catalogue-sheet" aria-describedby="catalogue-grid-help">
                  <thead>
                    <tr>
                      <th scope="col" class="sheet-handle-col" title="Arrange items"></th>
                      <th scope="col" class="sheet-row-number">#</th>
                      <th v-for="column in itemColumns" :key="column.key" scope="col" :class="'sheet-col-' + column.key">
                        {{ column.label }}
                      </th>
                      <th scope="col" class="sheet-discount-rule">Discount Rule</th>
                      <th scope="col" class="sheet-image">Image</th>
                      <th scope="col" class="sheet-status">Deactivate</th>
                      <th scope="col" class="sheet-action">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="!form.items.length">
                      <td colspan="8" class="sheet-empty">Type an item code, name, or barcode in the Item/Barcode column to begin.</td>
                    </tr>
                    <tr
                      v-for="(item, idx) in form.items"
                      :key="item._rowId || idx"
                      :class="{
                        'sheet-inactive': Number(item.disabled) === 1,
                        'sheet-dragging': draggedRowIndex === idx,
                        'sheet-drag-over': dragOverRowIndex === idx,
                      }"
                      @dragover.prevent="onRowDragOver($event, idx)"
                      @dragenter.prevent="onRowDragEnter($event, idx)"
                      @dragleave="onRowDragLeave($event, idx)"
                      @drop.prevent="onRowDrop($event, idx)"
                    >
                      <td class="sheet-handle-cell">
                        <div class="sheet-handle-wrapper">
                          <div
                            class="sheet-handle-grip"
                            draggable="true"
                            @dragstart="onHandleDragStart($event, idx)"
                            @dragend="onHandleDragEnd"
                            title="Drag to rearrange (or use Alt+↑ / Alt+↓)"
                          >
                            <svg class="sheet-grip-icon" viewBox="0 0 24 24" fill="currentColor">
                              <circle cx="8" cy="5" r="2" />
                              <circle cx="8" cy="12" r="2" />
                              <circle cx="8" cy="19" r="2" />
                              <circle cx="16" cy="5" r="2" />
                              <circle cx="16" cy="12" r="2" />
                              <circle cx="16" cy="19" r="2" />
                            </svg>
                          </div>
                          <div class="sheet-handle-buttons">
                            <button
                              type="button"
                              tabindex="-1"
                              :disabled="idx === 0"
                              @click.stop="moveItemUp(idx)"
                              class="sheet-move-btn"
                              title="Move up (Alt+↑)"
                            >▲</button>
                            <button
                              type="button"
                              tabindex="-1"
                              :disabled="idx === form.items.length - 1"
                              @click.stop="moveItemDown(idx)"
                              class="sheet-move-btn"
                              title="Move down (Alt+↓)"
                            >▼</button>
                          </div>
                        </div>
                      </td>
                      <th scope="row" class="sheet-row-number">{{ idx + 1 }}</th>
                      <td v-for="(column, columnIndex) in itemColumns" :key="column.key" class="sheet-cell">
                        <span v-if="column.key === 'itemname'" class="sheet-item-name">{{ item.itemname }}</span>
                        <input
                          v-else
                          :value="searchTargetRow === idx ? itemSearchQuery : item.itemcode"
                          @input="searchRowItem($event, idx)"
                          @blur="closeItemSearch()"
                          type="text"
                          :data-cell="`${idx}-${columnIndex}`"
                          :aria-label="`${column.label}, row ${idx + 1}`"
                          :class="{ 'sheet-mono': column.key !== 'itemname', 'sheet-code': column.key === 'itemcode' }"
                          @focus="$event.target.select()"
                          autocomplete="off"
                          @keydown="handleItemCellKeydown($event, idx, columnIndex)"
                        />
                      </td>
                      <td class="sheet-cell sheet-discount-rule-col">
                        <div v-if="discountRulesForItem(item.itemcode).length" class="sheet-discount-cell">
                          <div
                            v-for="r in discountRulesForItem(item.itemcode)"
                            :key="r.name"
                            class="sheet-discount-item"
                            :title="getRuleTooltip(r)"
                          >
                            <span class="sheet-discount-badge" :class="{ 'opacity-60': !r.isActiveDate }">
                              {{ r.rule_name }}
                            </span>
                            <span v-if="r.description && r.description !== r.rule_name" class="sheet-discount-desc">
                              {{ r.description }}
                            </span>
                          </div>
                        </div>
                        <span v-else-if="item.itemcode" class="sheet-discount-none">—</span>
                      </td>
                      <td class="sheet-image">
                        <button type="button" :disabled="!item.itemcode" :aria-label="`Manage image for ${item.itemname || item.itemcode}`" :class="['sheet-image-button', hasItemImage(item.itemcode) ? 'sheet-image-present' : 'sheet-image-missing']" @click="openItemImage(item)">Image</button>
                      </td>
                      <td class="sheet-status">
                        <input
                          v-model="item.disabled"
                          type="checkbox"
                          :true-value="1"
                          :false-value="0"
                          :aria-label="`Deactivate item in row ${idx + 1}`"
                          class="h-5 w-5 cursor-pointer accent-[var(--color-info)]"
                        />
                      </td>
                      <td class="sheet-action">
                        <button type="button" @click="removeItemRow(idx)" :aria-label="`Remove row ${idx + 1}`" title="Remove row" class="sheet-remove">×</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
    <div v-if="imageItemCode" class="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 p-4" @click.self="closeItemImage">
      <div role="dialog" aria-modal="true" aria-labelledby="item-image-title" class="w-full max-w-sm rounded-xl bg-[var(--color-surface)] p-5 shadow-xl">
        <div class="flex items-center justify-between gap-3">
          <h2 id="item-image-title" class="text-base font-semibold">Product image</h2>
          <button type="button" :disabled="imageUploading" aria-label="Close image window" @click="closeItemImage">×</button>
        </div>
        <p class="mt-1 text-xs text-[var(--color-text-muted)]">{{ imageItemName }} ({{ imageItemCode }})</p>
        <div class="mt-4 flex min-h-44 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-3">
          <span v-if="imageLoading" class="text-sm text-[var(--color-text-muted)]">Loading image...</span>
          <img v-else-if="imageUrl" :src="imageUrl" :alt="imageItemName" class="max-h-56 max-w-full object-contain" />
          <span v-else class="text-sm text-[var(--color-text-muted)]">No image uploaded</span>
        </div>
        <input ref="imageFileInput" type="file" accept="image/*" class="hidden" aria-label="Choose product image" @change="uploadItemImage" />
        <button type="button" :disabled="imageLoading || imageUploading" class="mt-4 w-full rounded bg-[var(--color-info)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" @click="imageFileInput?.click()">
          {{ imageUploading ? 'Uploading...' : imageUrl ? 'Replace image' : 'Upload photo' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import QuickItemSearch from '../components/QuickItemSearch.vue'
import { frappeGet, frappePost, uploadFile } from '../api.js'
import { useItemCache } from '../services/itemCache.js'

const router = useRouter()
const {
  items: cachedItems,
  refreshItemCache,
  discountRules,
  refreshDiscountRuleCache,
  lookupItemInCache,
} = useItemCache()

// State
const catalogues = ref([])
const loading = ref(false)
const searchQuery = ref('')
const selectedName = ref(null)
const detailLoading = ref(false)
const saving = ref(false)
const priceLists = ref([])
const imageItemCode = ref('')
const imageItemName = ref('')
const imageUrl = ref('')
const imageLoading = ref(false)
const imageUploading = ref(false)
const imageFileInput = ref(null)
const imageByCode = ref({})
const cachedImageByCode = computed(() => new Map(cachedItems.value.map(item => [item.item_code, item.image])))

function hasItemImage(code) {
  return Boolean(Object.hasOwn(imageByCode.value, code) ? imageByCode.value[code] : cachedImageByCode.value.get(code))
}

async function openItemImage(item) {
  if (!item.itemcode) return
  imageItemCode.value = item.itemcode
  imageItemName.value = item.itemname || item.itemcode
  imageUrl.value = ''
  imageLoading.value = true
  try {
    const product = await frappeGet('frappe.client.get_value', {
      doctype: 'Item', filters: { name: item.itemcode }, fieldname: 'image'
    })
    if (imageItemCode.value === item.itemcode) {
      imageUrl.value = product?.image || ''
      imageByCode.value[item.itemcode] = imageUrl.value
    }
  } catch (e) {
    alert(e.message || 'Failed to load product image')
  } finally {
    imageLoading.value = false
  }
}

function closeItemImage() {
  if (imageUploading.value) return
  imageItemCode.value = ''
  imageUrl.value = ''
}

async function uploadItemImage(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    alert('Please choose an image file.')
    event.target.value = ''
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    alert('File size exceeds 5MB limit.')
    event.target.value = ''
    return
  }
  imageUploading.value = true
  try {
    const uploaded = await uploadFile(file, { doctype: 'Item', docname: imageItemCode.value, fieldname: 'image' })
    await frappePost('frappe.client.set_value', {
      doctype: 'Item', name: imageItemCode.value, fieldname: 'image', value: uploaded.file_url
    }, { silent: true })
    imageUrl.value = uploaded.file_url
    imageByCode.value[imageItemCode.value] = uploaded.file_url
    const cached = cachedItems.value.find(item => item.item_code === imageItemCode.value)
    if (cached) cached.image = uploaded.file_url
  } catch (e) {
    alert(e.message || 'Failed to upload product image')
  } finally {
    imageUploading.value = false
    event.target.value = ''
  }
}

let _rowIdSeed = 0
function getRowId() {
  return 'row_' + (++_rowIdSeed)
}

const draggedRowIndex = ref(null)
const dragOverRowIndex = ref(null)

function onHandleDragStart(event, idx) {
  closeItemSearch()
  draggedRowIndex.value = idx
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', String(idx))
}

function onHandleDragEnd() {
  draggedRowIndex.value = null
  dragOverRowIndex.value = null
}

function onRowDragOver(event, idx) {
  event.preventDefault()
  if (draggedRowIndex.value === null) return
  event.dataTransfer.dropEffect = 'move'
  if (dragOverRowIndex.value !== idx) {
    dragOverRowIndex.value = idx
  }
}

function onRowDragEnter(event, idx) {
  event.preventDefault()
  if (draggedRowIndex.value !== null) {
    dragOverRowIndex.value = idx
  }
}

function onRowDragLeave(event, idx) {
  if (dragOverRowIndex.value === idx && !event.currentTarget.contains(event.relatedTarget)) {
    dragOverRowIndex.value = null
  }
}

function onRowDrop(event, targetIdx) {
  event.preventDefault()
  const fromIdx = draggedRowIndex.value
  if (fromIdx !== null && fromIdx !== undefined && fromIdx !== targetIdx) {
    const moved = form.value.items.splice(fromIdx, 1)[0]
    form.value.items.splice(targetIdx, 0, moved)
  }
  draggedRowIndex.value = null
  dragOverRowIndex.value = null
}

function moveItemUp(idx) {
  if (idx <= 0) return
  const item = form.value.items.splice(idx, 1)[0]
  form.value.items.splice(idx - 1, 0, item)
}

function moveItemDown(idx) {
  if (idx >= form.value.items.length - 1) return
  const item = form.value.items.splice(idx, 1)[0]
  form.value.items.splice(idx + 1, 0, item)
}

// Form structure
const emptyForm = () => ({
  name: null,
  modified: null,
  creation: null,
  owner: null,
  heading: '',
  pageaddress: '',
  priority: 0,
  tile_grid: '4',
  timer: 0,
  price_lists: [],
  items: [{ _rowId: getRowId(), itemcode: '', itemname: '', barcode: '', disabled: 0 }]
})

const form = ref(emptyForm())
const listedItemCodes = computed(() => form.value.items.map(item => item.itemcode))
const isFormActive = ref(false)

// Item autocomplete search state
const itemSearchQuery = ref('')
const searchSuggestions = ref([])
const quickSearchRef = ref(null)
const searchTargetRow = ref(null)

// Fetch all catalogue documents from the database
async function fetchCatalogues() {
  loading.value = true
  refreshDiscountRuleCache()
  try {
    const data = await frappeGet('frappe.client.get_list', {
      doctype: 'Offer-Items',
      fields: ['name', 'heading', 'pageaddress', 'modified'],
      order_by: 'modified desc',
      limit_page_length: 100
    })
    catalogues.value = data || []
  } catch (e) {
    alert(e.message || 'Failed to fetch catalogue lists')
  } finally {
    loading.value = false
  }
}

// Filter catalogue lists in sidebar
const filteredCatalogues = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return catalogues.value
  return catalogues.value.filter(o =>
    (o.heading || '').toLowerCase().includes(q) ||
    (o.pageaddress || '').toLowerCase().includes(q) ||
    (o.name || '').toLowerCase().includes(q)
  )
})

// Select a catalogue list and load it details including the items child table
async function selectCatalogue(name) {
  closeItemImage()
  selectedName.value = name
  detailLoading.value = true
  isFormActive.value = true
  closeItemSearch()
  
  try {
    const doc = await frappeGet('frappe.client.get', {
      doctype: 'Offer-Items',
      name: name
    })
    form.value = {
      name: doc.name,
      modified: doc.modified,
      creation: doc.creation,
      owner: doc.owner,
      heading: doc.heading || '',
      pageaddress: doc.pageaddress || '',
      priority: doc.priority ?? 0,
      tile_grid: doc.tile_grid || '4',
      timer: doc.timer || 0,
      price_lists: (doc.price_lists || []).map(p => ({
        name: p.name,
        price_list: p.price_list || ''
      })),
      items: (doc.items || []).map(i => ({
        _rowId: getRowId(),
        name: i.name,
        itemcode: i.itemcode || '',
        itemname: i.itemname || '',
        barcode: i.barcode || '',
        disabled: Number(i.disabled) === 1 ? 1 : 0
      }))
    }
    if (!form.value.items.length) addEmptyRow()
  } catch (e) {
    alert(e.message || 'Failed to load catalogue details')
    closeForm()
  } finally {
    detailLoading.value = false
  }
}

// Open clean form for creating new Catalogue List
function handleNewCatalogue() {
  closeItemImage()
  selectedName.value = null
  isFormActive.value = true
  form.value = emptyForm()
  closeItemSearch()
}

function closeForm() {
  closeItemImage()
  closeItemSearch()
  isFormActive.value = false
  selectedName.value = null
  form.value = emptyForm()
}

// QuickItemSearch filters the shared cache by item code, name, and barcode.
function handleItemSearch() {
  searchSuggestions.value = itemSearchQuery.value.length ? cachedItems.value.slice(0, 1) : []
}

function closeItemSearch() {
  searchSuggestions.value = []
  searchTargetRow.value = null
  itemSearchQuery.value = ''
}

function searchRowItem(event, row) {
  searchTargetRow.value = row
  itemSearchQuery.value = event.target.value
  handleItemSearch()
}

function handleSearchKeydown(event) {
  if (event.isComposing) return
  if (event.key === 'Escape') {
    event.preventDefault()
    closeItemSearch()
    return
  }
  if (searchSuggestions.value.length && ['ArrowDown', 'ArrowUp', 'Enter'].includes(event.key)) {
    event.preventDefault()
    quickSearchRef.value?.handleQuickSearchKeydown(event)
  }
}

function handleItemCellKeydown(event, row, column) {
  if (event.altKey && (event.key === 'ArrowUp' || event.key === 'ArrowDown')) {
    event.preventDefault()
    if (event.key === 'ArrowUp' && row > 0) {
      moveItemUp(row)
      nextTick(() => {
        const input = itemsGrid.value?.querySelector(`[data-cell="${row - 1}-${column}"]`)
        input?.focus()
        input?.select()
      })
    } else if (event.key === 'ArrowDown' && row < form.value.items.length - 1) {
      moveItemDown(row)
      nextTick(() => {
        const input = itemsGrid.value?.querySelector(`[data-cell="${row + 1}-${column}"]`)
        input?.focus()
        input?.select()
      })
    }
    return
  }
  if (column === 0 && searchTargetRow.value === row) {
    handleSearchKeydown(event)
    if (event.defaultPrevented || event.isComposing) return
    if (event.key === 'Tab') closeItemSearch()
  }
  handleCellKeydown(event, row, column)
}

async function selectSearchItem(item) {
  const row = searchTargetRow.value
  const values = {
    itemcode: item.item_code,
    itemname: item.item_name || '',
    barcode: item.barcodes_detailed?.[0]?.barcode || item.barcodes?.split(',')[0]?.trim() || '',
  }
  if (row !== null && form.value.items[row]) {
    Object.assign(form.value.items[row], values)
  } else {
    form.value.items.push({ _rowId: getRowId(), ...values, disabled: 0 })
  }
  closeItemSearch()
  const nextRow = row !== null ? row + 1 : form.value.items.length
  if (nextRow === form.value.items.length) addEmptyRow()
  await nextTick()
  const input = itemsGrid.value?.querySelector(`[data-cell="${nextRow}-0"]`)
  input?.focus()
  input?.select()
}

const itemsGrid = ref(null)
const itemColumns = [
  { key: 'itemcode', label: 'Item/Barcode' },
  { key: 'itemname', label: 'Item Name' },
]

async function handleCellKeydown(event, row, column) {
  if (event.isComposing || event.ctrlKey || event.metaKey || event.altKey) return
  let nextRow = row
  let nextColumn = column
  if (event.key === 'Enter') nextRow += event.shiftKey ? -1 : 1
  else if (event.key === 'ArrowDown') nextRow++
  else if (event.key === 'ArrowUp') nextRow--
  else if (event.key === 'Tab') {
    nextRow += event.shiftKey ? -1 : 1
    nextColumn = 0
  } else return
  if (event.key === 'Enter' && !event.shiftKey && nextRow === form.value.items.length) {
    addEmptyRow()
  }
  // Let Tab leave the grid at its boundaries; Enter stays in the current column.
  if (nextRow < 0 || nextRow >= form.value.items.length) {
    if (event.key !== 'Tab') event.preventDefault()
    return
  }
  event.preventDefault()
  await nextTick()
  const input = itemsGrid.value?.querySelector(`[data-cell="${nextRow}-${nextColumn}"]`)
  input?.focus()
  input?.select()
}

function addEmptyRow() {
  form.value.items.push({
    _rowId: getRowId(),
    itemcode: '',
    itemname: '',
    barcode: '',
    disabled: 0
  })
}

function removeItemRow(idx) {
  closeItemSearch()
  form.value.items.splice(idx, 1)
  if (!form.value.items.length) addEmptyRow()
}

function formatRuleDescription(rule) {
  if (!rule) return ''
  const type = rule.discount_type
  const rows = rule.custom_logic_rows || []

  if (type === 'Product Discount') {
    const minQ = Number(rule.min_quantity) || 0
    const freeQ = Number(rule.free_quantity) || 0
    return `Buy ${minQ} Get ${freeQ} Free`
  }

  if (type === 'Percentage Discount') {
    if (rows.length) {
      return rows.map(r => `Qty ${Number(r.min_quantity) || 0}+: ${Number(r.percentage) || 0}% Off`).join(' | ')
    }
    const pct = Number(rule.percentage_discount) || 0
    const minQ = Number(rule.min_quantity) || 0
    if (minQ > 0) {
      return `${pct}% Off (Min: ${minQ})`
    }
    return `${pct}% Off`
  }

  if (type === 'Custom Logic') {
    if (rows.length) {
      if (rule.custom_logic_type === 'Product') {
        return rows.map(r => `Buy ${Number(r.min_quantity) || 0} Get ${Number(r.nos) || 0} Free`).join(' | ')
      }
      return rows.map(r => `Qty ${Number(r.min_quantity) || 0}+: ${Number(r.percentage) || 0}% Off`).join(' | ')
    }
    return 'Offer'
  }

  if (type === 'X to Y product discount') {
    const xToY = (rule.x_to_y_table || [])[0]
    if (xToY) {
      const minQ = Number(xToY.min_quantity) || 1
      const freeQ = Number(xToY.free_item_quantity) || 1
      const freeName = xToY.free_item_name || xToY.free_item_code || 'Free Item'
      return `Buy ${minQ} Get ${freeQ} ${freeName} Free`
    }
    return 'X to Y Offer'
  }

  return ''
}

function discountRulesForItem(itemCode) {
  if (!itemCode || !discountRules.value || !discountRules.value.length) return []
  const code = itemCode.trim().toLowerCase()
  const today = new Date().toISOString().slice(0, 10)

  const cataloguePriceLists = (form.value.price_lists || [])
    .map(p => p.price_list && p.price_list.trim())
    .filter(Boolean)

  const matches = []

  for (const rule of discountRules.value) {
    if (!rule.enabled) continue

    let matchesItem = false
    if (rule.discount_type === 'X to Y product discount') {
      const codes = (rule.x_to_y_table || []).map(i => (i.item_code || '').toLowerCase())
      matchesItem = codes.includes(code)
    } else if (rule.applies_to === 'Item Code') {
      const codes = (rule.items || []).map(i => (i.item_code || '').toLowerCase())
      matchesItem = codes.includes(code)
    } else if (rule.applies_to === 'Product Group') {
      const cached = lookupItemInCache(itemCode)
      if (cached?.item_group && rule.product_group) {
        matchesItem = cached.item_group.toLowerCase() === rule.product_group.toLowerCase()
      }
    }

    if (!matchesItem) continue

    let isActiveDate = true
    if (rule.start_date && today < rule.start_date) isActiveDate = false
    if (rule.end_date && today > rule.end_date) isActiveDate = false

    let matchesPriceList = false
    if (!cataloguePriceLists.length || !rule.price_list) {
      matchesPriceList = true
    } else if (cataloguePriceLists.includes(rule.price_list)) {
      matchesPriceList = true
    }

    matches.push({
      ...rule,
      isActiveDate,
      matchesPriceList,
      description: formatRuleDescription(rule)
    })
  }

  matches.sort((a, b) => {
    if (a.matchesPriceList !== b.matchesPriceList) return a.matchesPriceList ? -1 : 1
    if (a.isActiveDate !== b.isActiveDate) return a.isActiveDate ? -1 : 1
    return 0
  })

  return matches
}

function getRuleTooltip(rule) {
  const parts = [
    `Rule: ${rule.rule_name}`,
    `Type: ${rule.discount_type || '—'}`
  ]
  if (rule.description) parts.push(`Offer: ${rule.description}`)
  const pct = getRuleDiscountPercentage(rule)
  if (pct > 0) parts.push(`Effective Discount: ${pct.toFixed(2).replace(/\.00$/, '')}%`)
  if (rule.price_list) parts.push(`Price List: ${rule.price_list}`)
  if (rule.start_date || rule.end_date) {
    parts.push(`Validity: ${rule.start_date || '—'} to ${rule.end_date || '—'}`)
  }
  if (!rule.isActiveDate) parts.push('Status: Inactive/Expired')
  return parts.join('\n')
}

function getRuleDiscountPercentage(rule) {
  if (!rule) return 0

  const type = rule.discount_type

  if (type === 'Percentage Discount') {
    const rows = rule.custom_logic_rows || []
    if (rows.length) {
      const pcts = rows.map(r => Number(r.percentage) || 0).filter(p => p > 0)
      if (pcts.length) return Math.max(...pcts)
    }
    return Number(rule.percentage_discount) || 0
  }

  if (type === 'Product Discount') {
    const paid = Number(rule.min_quantity) || 0
    const free = Number(rule.free_quantity) || 0
    if (paid > 0 && free > 0) {
      return (free / (paid + free)) * 100
    }
    return 0
  }

  if (type === 'Custom Logic') {
    const rows = rule.custom_logic_rows || []
    if (rows.length) {
      if (rule.custom_logic_type === 'Product') {
        const pcts = rows.map(r => {
          const paid = Number(r.min_quantity) || 0
          const free = Number(r.nos) || 0
          return paid > 0 && free > 0 ? (free / (paid + free)) * 100 : 0
        })
        return Math.max(0, ...pcts)
      } else {
        const pcts = rows.map(r => Number(r.percentage) || 0).filter(p => p > 0)
        if (pcts.length) return Math.max(...pcts)
      }
    }
    return 0
  }

  if (type === 'X to Y product discount') {
    const rows = rule.x_to_y_table || []
    if (rows.length) {
      const pcts = rows.map(r => {
        const paid = Number(r.min_quantity) || 0
        const free = Number(r.free_item_quantity) || 0
        return paid > 0 && free > 0 ? (free / (paid + free)) * 100 : 0
      })
      return Math.max(0, ...pcts)
    }
    return 0
  }

  // Fallback: parse from rule description if available
  const desc = rule.description || ''
  const percentages = [...desc.matchAll(/(\d+(?:\.\d+)?)\s*%\s*Off/gi)].map(m => Number(m[1]))
  const freeOffers = [...desc.matchAll(/Buy\s+(\d+(?:\.\d+)?)\s+Get\s+(\d+(?:\.\d+)?)\s+Free/gi)].map(m => {
    const paid = Number(m[1])
    const free = Number(m[2])
    return paid > 0 && free > 0 ? (free / (paid + free)) * 100 : 0
  })

  return Math.max(0, ...percentages, ...freeOffers)
}

function getItemDiscountPercentage(item) {
  if (!item?.itemcode) return 0
  const rules = discountRulesForItem(item.itemcode)
  if (!rules.length) return 0
  const percentages = rules.map(r => getRuleDiscountPercentage(r))
  return Math.max(0, ...percentages)
}

// Sorting controls
const sortColumn = ref('itemcode')
const sortDirection = ref('asc')
const lastSorted = ref(null)

const sortColumnLabel = computed(() => {
  if (sortColumn.value === 'itemcode') return 'Item'
  if (sortColumn.value === 'itemname') return 'Item Name'
  if (sortColumn.value === 'discount_rule') return 'Discount Rule'
  return ''
})

watch(sortColumn, () => {
  sortDirection.value = 'asc'
})

function getItemSortValue(item, column) {
  if (column === 'itemcode') {
    return (item.itemcode || item.barcode || '').trim()
  }
  if (column === 'itemname') {
    return (item.itemname || '').trim()
  }
  if (column === 'discount_rule') {
    const rules = discountRulesForItem(item.itemcode)
    return rules.length ? (rules[0].rule_name || rules[0].description || '').trim() : ''
  }
  return ''
}

function handleSort() {
  const col = sortColumn.value
  const dir = sortDirection.value

  const populated = []
  const empty = []

  for (const item of form.value.items) {
    if ((item.itemcode || '').trim() || (item.itemname || '').trim() || (item.barcode || '').trim()) {
      populated.push(item)
    } else {
      empty.push(item)
    }
  }

  if (!populated.length) return

  populated.sort((a, b) => {
    if (col === 'discount_rule') {
      const pctA = getItemDiscountPercentage(a)
      const pctB = getItemDiscountPercentage(b)

      // Rows without any discount rule (pct === 0) stay at the end
      if (pctA === 0 && pctB === 0) {
        const nameA = (a.itemname || a.itemcode || '').trim()
        const nameB = (b.itemname || b.itemcode || '').trim()
        return nameA.localeCompare(nameB, undefined, { numeric: true, sensitivity: 'base' })
      }
      if (pctA === 0) return 1
      if (pctB === 0) return -1

      const diff = dir === 'asc' ? pctA - pctB : pctB - pctA
      if (Math.abs(diff) > 0.0001) {
        return diff
      }

      // Secondary sort by itemname, then itemcode
      const nameA = (a.itemname || '').trim()
      const nameB = (b.itemname || '').trim()
      const nameCmp = nameA.localeCompare(nameB, undefined, { numeric: true, sensitivity: 'base' })
      if (nameCmp !== 0) return nameCmp

      const codeA = (a.itemcode || '').trim()
      const codeB = (b.itemcode || '').trim()
      return codeA.localeCompare(codeB, undefined, { numeric: true, sensitivity: 'base' })
    }

    // Default alphanumeric sort for itemcode and itemname
    const valA = getItemSortValue(a, col)
    const valB = getItemSortValue(b, col)

    // Rows with values come before empty rows
    if (!valA && !valB) return 0
    if (!valA) return 1
    if (!valB) return -1

    const cmp = valA.localeCompare(valB, undefined, { numeric: true, sensitivity: 'base' })
    if (cmp !== 0) {
      return dir === 'asc' ? cmp : -cmp
    }

    // Secondary sort by itemname, then itemcode
    const nameA = (a.itemname || '').trim()
    const nameB = (b.itemname || '').trim()
    const nameCmp = nameA.localeCompare(nameB, undefined, { numeric: true, sensitivity: 'base' })
    if (nameCmp !== 0) return nameCmp

    const codeA = (a.itemcode || '').trim()
    const codeB = (b.itemcode || '').trim()
    return codeA.localeCompare(codeB, undefined, { numeric: true, sensitivity: 'base' })
  })

  form.value.items = [...populated, ...empty]
  lastSorted.value = { column: col, direction: dir }

  // Toggle direction for next click
  sortDirection.value = dir === 'asc' ? 'desc' : 'asc'
}

// Save the catalogue document
async function handleSave() {
  if (!form.value.heading.trim()) {
    alert('Please enter a Heading.')
    return
  }
  if (!form.value.pageaddress.trim()) {
    alert('Please enter a Page Address.')
    return
  }
  if (!Number.isInteger(Number(form.value.priority)) || Number(form.value.priority) < 0) {
    alert('Priority must be a non-negative whole number.')
    return
  }
  const itemRows = form.value.items
    .map((item, index) => ({ item, rowNumber: index + 1 }))
    .filter(({ item }) => [item.itemcode, item.itemname, item.barcode].some(value => value.trim()))

  if (!itemRows.length) {
    alert('Please add at least one Item to the catalogue list.')
    return
  }

  // Validate nonempty rows using their visible row numbers.
  for (const { item, rowNumber } of itemRows) {
    if (!item.itemcode.trim()) {
      alert(`Row ${rowNumber}: Item Code is required.`)
      return
    }
  }

  saving.value = true
  try {
    let res
    const isNew = !form.value.name
    
    const docPayload = {
      doctype: 'Offer-Items',
      heading: form.value.heading.trim(),
      pageaddress: form.value.pageaddress.trim(),
      priority: Number(form.value.priority),
      tile_grid: form.value.tile_grid,
      timer: parseInt(form.value.timer) || 0,
      ...(form.value.modified && { modified: form.value.modified }),
      ...(form.value.creation && { creation: form.value.creation }),
      ...(form.value.owner && { owner: form.value.owner }),
      price_lists: (form.value.price_lists || []).filter(p => p.price_list && p.price_list.trim()).map(p => ({
        ...(p.name && { name: p.name }),
        doctype: 'Offer-Pricelist',
        price_list: p.price_list.trim()
      })),
      items: itemRows.map(({ item: i }) => ({
        ...(i.name && { name: i.name }),
        doctype: 'Offer-Item',
        itemcode: i.itemcode.trim(),
        itemname: i.itemname.trim(),
        barcode: i.barcode.trim(),
        disabled: Number(i.disabled) === 1 ? 1 : 0
      }))
    }

    if (isNew) {
      // Set name to pageaddress if autonamed by pageaddress or name field
      docPayload.name = form.value.pageaddress.trim()
      res = await frappePost('frappe.client.insert', { doc: docPayload })
    } else {
      docPayload.name = form.value.name
      res = await frappePost('frappe.client.save', { doc: docPayload })
    }

    alert('Catalogue list saved successfully!')
    await fetchCatalogues()
    if (res && res.name) {
      await selectCatalogue(res.name)
    } else {
      closeForm()
    }
  } catch (e) {
    alert(e.message || 'Failed to save catalogue list')
  } finally {
    saving.value = false
  }
}

// Delete the selected Catalogue List
async function handleDeleteCatalogue() {
  if (!form.value.name) return
  if (!confirm(`Are you sure you want to delete catalogue list "${form.value.heading}"?`)) return

  saving.value = true
  try {
    await frappePost('frappe.client.delete', {
      doctype: 'Offer-Items',
      name: form.value.name
    })
    alert('Catalogue list deleted successfully!')
    closeForm()
    await fetchCatalogues()
  } catch (e) {
    alert(e.message || 'Failed to delete catalogue list')
  } finally {
    saving.value = false
  }
}

function addPriceListRow() {
  if (!form.value.price_lists) {
    form.value.price_lists = []
  }
  form.value.price_lists.push({
    price_list: ''
  })
}

function removePriceListRow(idx) {
  form.value.price_lists.splice(idx, 1)
}

async function fetchPriceLists() {
  try {
    const data = await frappeGet('frappe.client.get_list', {
      doctype: 'Price List',
      fields: ['name'],
      order_by: 'name asc',
      limit_page_length: 200
    })
    priceLists.value = data || []
  } catch (e) {
    console.error('Failed to fetch price lists:', e)
  }
}

onMounted(() => {
  fetchCatalogues()
  fetchPriceLists()
  refreshDiscountRuleCache()
  if (!cachedItems.value.length) {
    refreshItemCache('Sales')
  }
})
</script>

<style scoped>
.catalogue-grid {
  max-height: 60vh;
  overflow: auto;
  border: 1px solid var(--color-border);
}
.catalogue-sheet {
  width: 100%;
  min-width: 1000px;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 27px;
  line-height: 30px;
}
.catalogue-sheet th,
.catalogue-sheet td {
  border-right: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}
.catalogue-sheet thead th {
  font-size: 18.9px;
  line-height: 21px;
  position: sticky;
  top: 0;
  z-index: 2;
  padding: 8px 6px;
  text-align: left;
  background: var(--color-lowlight);
  color: var(--color-text);
  font-weight: 400;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.catalogue-sheet .sheet-handle-col {
  width: 50px;
  text-align: center;
  padding: 0;
}
.catalogue-sheet .sheet-row-number {
  width: 54px;
  text-align: center;
}
.catalogue-sheet tbody .sheet-row-number {
  color: var(--color-text-muted);
  font-family: monospace;
  font-size: 22.5px;
  font-weight: 400;
}
.catalogue-sheet .sheet-col-itemcode { width: 25%; }
.catalogue-sheet .sheet-discount-rule { width: 22%; }
.catalogue-sheet .sheet-image { width: 90px; text-align: center; }
.sheet-image-button { padding: 3px 8px; border-radius: 4px; color: white; font-weight: 600; }
.sheet-image-present { background: #16a34a; }
.sheet-image-missing { background: #dc2626; }
.sheet-image-button:hover:not(:disabled) { filter: brightness(0.9); }
.sheet-image-button:disabled { opacity: 0.4; cursor: not-allowed; }
.catalogue-sheet .sheet-status { width: 130px; text-align: center; }
.catalogue-sheet .sheet-action { width: 72px; text-align: center; }
.catalogue-sheet thead .sheet-action { font-size: 7.35px; }
.catalogue-sheet tbody tr { transition: background-color 120ms; }
.catalogue-sheet tbody tr:hover { background: var(--color-surface-raised); }
.catalogue-sheet tbody tr:focus-within {
  background: var(--color-focus);
  color: var(--color-text-on-focus);
  font-weight: 700;
  box-shadow: inset 2px 0 var(--color-focus);
}
.catalogue-sheet tbody tr.sheet-dragging {
  opacity: 0.4;
  background-color: var(--color-surface-raised) !important;
}
.catalogue-sheet tbody tr.sheet-drag-over {
  box-shadow: inset 0 3px 0 0 var(--color-info), inset 0 -3px 0 0 var(--color-info);
  background-color: rgba(59, 130, 246, 0.08) !important;
}
.sheet-handle-cell {
  width: 50px;
  padding: 2px 4px;
  text-align: center;
  vertical-align: middle;
  user-select: none;
}
.sheet-handle-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  height: 100%;
}
.sheet-handle-grip {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 28px;
  border-radius: 4px;
  cursor: grab;
  color: var(--color-text-muted);
  transition: color 120ms, background-color 120ms;
}
.sheet-handle-grip:hover {
  color: var(--color-text);
  background-color: var(--color-surface-raised);
}
.sheet-handle-grip:active {
  cursor: grabbing;
}
.sheet-grip-icon {
  width: 14px;
  height: 18px;
}
.sheet-handle-buttons {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 1px;
}
.sheet-move-btn {
  font-size: 8px;
  line-height: 9px;
  padding: 1px 3px;
  color: var(--color-text-muted);
  border-radius: 2px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all 100ms;
}
.sheet-move-btn:hover:not(:disabled) {
  color: var(--color-info);
  background: var(--color-surface-raised);
}
.sheet-move-btn:disabled {
  opacity: 0.2;
  cursor: not-allowed;
}
.catalogue-sheet tbody tr:focus-within .sheet-handle-grip {
  color: var(--color-text-on-focus);
}
.catalogue-sheet tbody tr:focus-within .sheet-move-btn {
  color: var(--color-text-on-focus);
}
.sheet-cell { padding: 0; }
.sheet-discount-rule-col {
  vertical-align: middle;
}
.sheet-discount-cell {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  padding: 4px 8px;
}
.sheet-discount-item {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
}
.sheet-discount-badge {
  font-family: monospace;
  font-size: 20px;
  font-weight: 700;
  color: var(--color-warning);
  white-space: nowrap;
  flex-shrink: 0;
}
.sheet-discount-desc {
  font-size: 15px;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sheet-discount-none {
  display: block;
  padding: 4px 8px;
  color: var(--color-text-muted);
  text-align: center;
  font-size: 22px;
}
.catalogue-sheet tbody tr:focus-within .sheet-discount-badge {
  color: var(--color-text-on-focus);
}
.catalogue-sheet tbody tr:focus-within .sheet-discount-desc {
  color: var(--color-text-on-focus);
  opacity: 0.9;
}
.catalogue-sheet tbody tr:focus-within .sheet-discount-none {
  color: var(--color-text-on-focus);
}
.catalogue-sheet .sheet-inactive .sheet-discount-rule-col {
  opacity: 0.5;
}
.sheet-item-name {
  display: block;
  padding: 4px 8px;
  user-select: none;
}
.sheet-cell input {
  display: block;
  width: 100%;
  min-width: 0;
  padding: 4px 8px;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: var(--color-text);
  font: inherit;
  font-weight: 500;
}
.catalogue-sheet .sheet-inactive .sheet-item-name,
.catalogue-sheet .sheet-inactive .sheet-cell input {
  text-decoration: line-through;
}
.sheet-cell input.sheet-mono { font-family: monospace; }
.sheet-cell input.sheet-code { color: var(--color-highlight); }
.sheet-cell input:focus {
  outline: 2px solid var(--color-text-on-focus);
  outline-offset: -2px;
}
.catalogue-sheet tbody tr:focus-within input,
.catalogue-sheet tbody tr:focus-within .sheet-row-number {
  color: var(--color-text-on-focus);
  font-weight: 700;
}
.sheet-remove {
  padding: 2px 4px;
  border-radius: 4px;
  color: var(--color-text-muted);
}
.catalogue-sheet tr:focus-within .sheet-remove { color: var(--color-text-on-focus); }
.catalogue-sheet .sheet-remove:hover,
.catalogue-sheet .sheet-remove:focus-visible {
  background: var(--color-surface-raised);
  color: var(--color-danger);
}
.sheet-empty {
  padding: 24px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 13.5px;
  line-height: 21px;
}

.catalogue-display-page {
  font-size: 19.5px !important; /* 13px * 1.5 */
}
.catalogue-display-page :deep(.text-xs),
.catalogue-display-page :deep(input.text-xs),
.catalogue-display-page :deep(select.text-xs),
.catalogue-display-page :deep(button.text-xs),
.catalogue-display-page :deep(textarea.text-xs) {
  font-size: 18px !important; /* 12px * 1.5 */
}
.catalogue-display-page :deep(.text-sm) {
  font-size: 21px !important; /* 14px * 1.5 */
}
.catalogue-display-page :deep(.text-base) {
  font-size: 24px !important; /* 16px * 1.5 */
}
.catalogue-display-page :deep(.text-5xl) {
  font-size: 72px !important; /* 48px * 1.5 */
}
.catalogue-display-page :deep(.text-\[14px\]) {
  font-size: 21px !important; /* 14px * 1.5 */
}
.catalogue-display-page :deep(.text-\[11px\]) {
  font-size: 16.5px !important; /* 11px * 1.5 */
}
.catalogue-display-page :deep(.text-\[10px\]) {
  font-size: 15px !important; /* 10px * 1.5 */
}
.catalogue-display-page :deep(.text-\[9px\]) {
  font-size: 13.5px !important; /* 9px * 1.5 */
}
</style>
