<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm px-4"
  >
    <div class="w-[90vw] bg-[var(--color-bg)] border border-[var(--color-border)] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="p-[12px] bg-[var(--color-surface)] border-b border-[var(--color-border)] flex justify-between items-center">
        <div class="flex items-baseline gap-4">
          <h3 class="text-5xl font-bold text-[var(--color-text)]">{{ isEditMode ? 'Edit Item' : 'Create New Item' }}</h3>
          <span class="text-[var(--color-text-muted)] text-2xl">|</span>
          <p class="text-2xl text-[var(--color-text-muted)]">{{ isEditMode ? 'Update item details' : 'Add a new item to the system' }}</p>
        </div>
        <div class="flex items-center gap-[16px]">
          <button
            v-if="isEditMode"
            type="button"
            @click="startNewFromCurrent"
            class="flex items-center gap-[10px] rounded-xl border border-[var(--color-info)] px-[16px] py-[10px] text-2xl font-bold uppercase tracking-wider text-[var(--color-info)] bg-[var(--color-info)]/10 hover:bg-[var(--color-info)]/20 transition-all active:scale-95"
            title="Create a new item copying these details (except name and print name)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
            <span>New Item</span>
          </button>
          <button
            v-if="isEditMode"
            type="button"
            @click="toggleItemDisabled"
            :disabled="isTogglingDisabled"
            class="flex items-center gap-[10px] rounded-xl border px-[16px] py-[10px] text-2xl font-bold uppercase tracking-wider transition-all active:scale-95 disabled:opacity-50"
            :class="itemDisabled
              ? 'border-[var(--color-success)] text-[var(--color-success)] bg-[var(--color-success)]/10 hover:bg-[var(--color-success)]/20'
              : 'border-[var(--color-danger)] text-[var(--color-danger)] bg-[var(--color-danger)]/10 hover:bg-[var(--color-danger)]/20'"
            :title="itemDisabled ? 'Item is disabled — click to enable it again' : 'Disable this item so it no longer appears in billing'"
          >
            <span v-if="isTogglingDisabled" class="h-6 w-6 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
            <span>{{ itemDisabled ? 'Enable Item' : 'Disable Item' }}</span>
          </button>
          <button
            type="button"
            @click="toggleRetainTaxFields"
            class="flex items-center gap-[10px] rounded-xl border px-[16px] py-[10px] text-2xl font-bold uppercase tracking-wider transition-all active:scale-95"
            :class="retainTaxFields
              ? 'border-[var(--color-success)] text-[var(--color-success)] bg-[var(--color-success)]/10'
              : 'border-[var(--color-border)] text-[var(--color-text-muted)] bg-[var(--color-surface-raised)]'"
            :title="retainTaxFields
              ? 'HSN & Tax Template are remembered for the next item'
              : 'HSN & Tax Template are cleared after saving'"
          >
            <span class="inline-block h-6 w-6 rounded-full" :class="retainTaxFields ? 'bg-[var(--color-success)]' : 'bg-[var(--color-text-muted)]'"></span>
            <span>Retain HSN &amp; Tax: {{ retainTaxFields ? 'On' : 'Off' }}</span>
          </button>
          <button
            @click="$emit('close')"
            class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors px-[20px] py-[12px] hover:bg-[var(--color-surface-raised)] rounded-full"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex gap-[8px] px-[20px] pt-[12px] bg-[var(--color-bg)] border-b border-[var(--color-border)]">
        <button
          v-for="tab in visibleTabs"
          :key="tab.id"
          type="button"
          @click="activeTab = tab.id"
          class="rounded-t-xl px-[24px] py-[10px] text-2xl font-bold uppercase tracking-wider transition-colors"
          :class="activeTab === tab.id
            ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]'
            : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
        >
          {{ tab.label }}
          <span v-if="tab.id === 'variants' && form.has_variants" class="ml-[6px] opacity-80">({{ form.attributes.length }})</span>
        </button>
      </div>

      <!-- Form Content -->
      <div class="flex-1 overflow-y-auto px-[20px] py-[12px]">
        <!-- Both tabs share one grid cell, so the window keeps the Details size and an
             inactive tab is only hidden (invisible), never collapsed -->
        <div class="grid">
        <div class="[grid-area:1/1] grid grid-cols-1 md:grid-cols-3 gap-[24px]" :class="{ invisible: activeTab !== 'details' }">
          <!-- Column 1: Names & Barcodes -->
          <div class="space-y-[16px]">
            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Item Name *</label>
              <input
                ref="itemNameInput"
                v-model="form.item_name"
                type="text"
                class="w-full rounded-xl border bg-[var(--color-surface)] px-[20px] py-[12px] text-4xl font-medium text-[var(--color-text)] outline-none transition-all"
                :class="duplicateItemName
                  ? 'border-[var(--color-danger)] border-2 bg-[var(--color-danger)]/10 focus:border-[var(--color-danger)]'
                  : 'border-[var(--color-border)] focus:border-[var(--color-info)]'"
                placeholder="Enter full item name..."
                @keydown.enter.prevent="itemPrintNameInput?.focus()"
              />
              <p v-if="duplicateItemName" class="px-[20px] text-2xl font-bold text-[var(--color-danger)]">
                Item name already exists ({{ duplicateItemName }})
              </p>
            </div>

            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Item Print Name</label>
              <input
                ref="itemPrintNameInput"
                v-model="form.item_print_name"
                type="text"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-4xl font-medium text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all"
                placeholder="Print name..."
                @keydown.enter.prevent="itemGroupInput?.focus()"
              />
            </div>

            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Barcode / Code</label>
              <div class="relative">
                <input
                  ref="barcodeInput"
                  v-model="form.barcode"
                  type="text"
                  class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] pl-[20px] pr-[30px] py-[12px] font-mono text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  placeholder="Barcode..."
                  @focus="e => e.target.select()"
                  @keydown.enter.prevent="itemGroupInput?.focus()"
                />
                <div v-if="isFetchingBarcode" class="absolute right-[8px] top-1/2 -translate-y-1/2">
                  <span class="h-8 w-8 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent inline-block"></span>
                </div>
              </div>
            </div>

            <!-- Extra Barcodes Table (Excel-style) -->
            <div class="space-y-[4px]">
              <div class="flex items-center justify-between px-[20px]">
                <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Additional Barcodes</label>
                <button type="button" @click="addBarcodeRow" class="text-xl font-bold text-[var(--color-info)] hover:text-[var(--color-info)] transition-colors">+ Add Barcode</button>
              </div>
              <div class="border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden shadow-sm">
                <table class="w-full border-collapse text-2xl">
                  <thead>
                    <tr class="divide-x divide-[var(--color-border)] border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]">
                      <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Barcode</th>
                      <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">UOM</th>
                      <th class="w-16"></th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[var(--color-border)]">
                    <tr v-for="(row, idx) in form.extra_barcodes" :key="idx" class="divide-x divide-[var(--color-border)] hover:bg-[var(--color-border)]/10 transition-colors">
                      <td class="p-0">
                        <input
                          :ref="el => { if (el) extraBarcodeInputs[idx] = el }"
                          v-model="row.barcode"
                          type="text"
                          class="w-full bg-transparent px-[10px] py-[6px] font-mono text-2xl text-[var(--color-text)] outline-none focus:bg-[var(--color-info)]/10"
                          placeholder="Barcode..."
                        />
                      </td>
                      <td class="p-0">
                        <select v-model="row.uom" class="w-full bg-transparent px-[10px] py-[6px] text-2xl text-[var(--color-text)] outline-none cursor-pointer focus:bg-[var(--color-info)]/10 appearance-none">
                          <option v-for="u in availableUoms" :key="u" :value="u" class="bg-[var(--color-surface)] text-[var(--color-text)]">{{ u }}</option>
                        </select>
                      </td>
                      <td class="p-0 text-center">
                        <button type="button" @click="removeBarcodeRow(idx)" class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors text-4xl font-bold leading-none w-full h-full py-[6px]">&times;</button>
                      </td>
                    </tr>
                    <tr v-if="!form.extra_barcodes.length">
                      <td colspan="3" class="px-[10px] py-[12px] text-center text-2xl text-[var(--color-text-muted)] italic">
                        No additional barcodes mapped
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Item Image -->
            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Item Image</label>
              <div class="border border-[var(--color-border)] bg-[var(--color-surface)] rounded-xl p-[16px] flex flex-col items-center justify-center gap-[12px] min-h-[160px] relative group overflow-hidden">
                <div v-if="isUploadingImage" class="absolute inset-0 bg-black/50 flex flex-col items-center justify-center gap-[8px] z-10">
                  <span class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-info)] border-t-transparent"></span>
                  <span class="text-2xl font-bold text-white">Uploading...</span>
                </div>

                <div v-if="form.image" class="relative w-full flex flex-col items-center gap-[8px]">
                  <img :src="form.image" class="max-h-[140px] max-w-full rounded-lg object-contain border border-[var(--color-border)] bg-black/5 shadow-sm" alt="Item Image" />
                  <button 
                    type="button" 
                    @click="removeImage"
                    class="text-xl font-bold text-[var(--color-danger)] hover:text-red-700 transition-colors flex items-center gap-1 mt-1"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                    Remove Image
                  </button>
                </div>

                <div v-else class="flex flex-col items-center justify-center text-center cursor-pointer w-full py-[16px]" @click="triggerFileInput">
                  <svg class="w-16 h-16 text-[var(--color-text-muted)] group-hover:text-[var(--color-info)] transition-colors mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375 0 11-.75 0 .375 0 01.75 0z" />
                  </svg>
                  <span class="text-2xl font-semibold text-[var(--color-text)] group-hover:text-[var(--color-info)] transition-colors">Click to Upload Image</span>
                  <span class="text-xl text-[var(--color-text-muted)] mt-1">PNG, JPG, JPEG up to 5MB</span>
                </div>

                <input 
                  ref="fileInput"
                  type="file" 
                  accept="image/*"
                  class="hidden"
                  @change="handleImageUpload"
                />
              </div>
            </div>
          </div>

          <!-- Column 2: Classification & Taxes -->
          <div class="space-y-[16px]">
            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Item Group *</label>
              <select
                ref="itemGroupInput"
                v-model="form.item_group"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all appearance-none"
                @keydown.enter.prevent="hsnInput?.focus()"
              >
                <option value="">Select Group...</option>
                <option v-for="g in metadata.item_groups" :key="g.name" :value="g.name">{{ g.name }}</option>
              </select>
            </div>

            <label class="flex items-center gap-[12px] px-[20px] py-[12px] text-2xl font-bold text-[var(--color-text)] cursor-pointer">
              <input
                v-model="form.custom_is_gst_item"
                type="checkbox"
                :true-value="1"
                :false-value="0"
                class="h-6 w-6 accent-[var(--color-info)]"
              />
              <span>GST Incl</span>
            </label>

            <label
              v-if="canToggleVariants"
              class="flex items-center gap-[12px] px-[20px] py-[12px] text-2xl font-bold text-[var(--color-text)] cursor-pointer"
              title="Template item — set attributes in the Variants tab"
            >
              <input
                v-model="form.has_variants"
                type="checkbox"
                :true-value="1"
                :false-value="0"
                class="h-6 w-6 accent-[var(--color-info)]"
              />
              <span>Has Variants</span>
            </label>

            <div class="space-y-[4px] relative">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">HSN/SAC Code</label>
              <input
                ref="hsnInput"
                v-model="form.hsn_sac"
                type="text"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all"
                placeholder="Search HSN..."
                @focus="showHSNDropdown = true"
                @blur="setTimeout(() => showHSNDropdown = false, 200)"
                @keydown.enter.prevent="onHSNEnter"
                @keydown.down.prevent="hsnHighlightIdx = (hsnHighlightIdx + 1) % filteredHSNCodes.length"
                @keydown.up.prevent="hsnHighlightIdx = (hsnHighlightIdx - 1 + filteredHSNCodes.length) % filteredHSNCodes.length"
              />
              <div v-if="showHSNDropdown && filteredHSNCodes.length > 0" class="absolute left-0 right-0 top-full z-10 mt-1 max-h-80 overflow-y-auto rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] px-[20px] py-[12px] shadow-xl">
                <button
                  v-for="(res, idx) in filteredHSNCodes"
                  :key="res.name"
                  class="w-full rounded-lg px-[20px] py-[12px] text-left transition-colors group flex flex-col gap-2"
                  :class="hsnHighlightIdx === idx ? 'bg-[var(--color-info)]' : 'hover:bg-[var(--color-info)]/20'"
                  @click="selectHSN(res.name)"
                >
                  <span class="text-2xl font-bold group-hover:text-[var(--color-info)]" :class="hsnHighlightIdx === idx ? 'text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)]'">{{ res.name }}</span>
                  <span v-if="res.description" class="text-base truncate line-clamp-1 italic" :class="hsnHighlightIdx === idx ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ res.description }}</span>
                </button>
              </div>
            </div>

            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Default UOM *</label>
              <select
                ref="uomInput"
                v-model="form.stock_uom"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all appearance-none"
                @keydown.enter.prevent="taxTemplateInput?.focus()"
              >
                <option v-for="u in metadata.uoms" :key="u.name" :value="u.name">{{ u.name }}</option>
              </select>
            </div>

            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Tax Template *</label>
              <select
                ref="taxTemplateInput"
                v-model="form.item_tax_template"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all appearance-none"
                @keydown.enter.prevent="competitiveItemInput?.focus()"
              >
                <option value=""></option>
                <option v-for="t in taxTemplateOptions" :key="t.name" :value="t.name">{{ t.name }}</option>
              </select>
            </div>

            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Competitive Item</label>
              <select
                ref="competitiveItemInput"
                v-model="form.custom_competitive_item"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all appearance-none"
                @keydown.enter.prevent="rateInput?.focus()"
              >
                <option value=""></option>
                <option v-for="c in competitiveItemOptions" :key="c.name" :value="c.name">{{ c.name }}</option>
              </select>
            </div>
          </div>

          <!-- Column 3: Conversions, Rates & Supplier -->
          <div class="space-y-[16px]">
            <!-- UOM Conversions Table (Excel-style) -->
            <div class="space-y-[4px]">
              <div class="flex items-center justify-between px-[20px]">
                <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider">UOM Conversions</label>
                <button type="button" @click="addUomRow" class="text-xl font-bold text-[var(--color-info)] hover:text-[var(--color-info)] transition-colors">+ Add UOM</button>
              </div>
              <div class="border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden shadow-sm">
                <table class="w-full border-collapse text-2xl">
                  <thead>
                    <tr class="divide-x divide-[var(--color-border)] border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]">
                      <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">UOM</th>
                      <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Factor</th>
                      <th class="w-16"></th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[var(--color-border)]">
                    <tr v-for="(row, idx) in form.uom_conversions" :key="idx" class="divide-x divide-[var(--color-border)] hover:bg-[var(--color-border)]/10 transition-colors">
                      <td class="p-0">
                        <select v-model="row.uom" class="w-full bg-transparent px-[10px] py-[6px] text-2xl text-[var(--color-text)] outline-none cursor-pointer focus:bg-[var(--color-info)]/10 appearance-none">
                          <option v-for="u in metadata.uoms" :key="u.name" :value="u.name" :disabled="u.name === form.stock_uom" class="bg-[var(--color-surface)] text-[var(--color-text)]">{{ u.name }}</option>
                        </select>
                      </td>
                      <td class="p-0">
                        <input
                          v-model.number="row.conversion_factor"
                          type="number"
                          step="0.001"
                          class="w-full bg-transparent px-[10px] py-[6px] font-mono text-2xl text-[var(--color-text)] outline-none focus:bg-[var(--color-info)]/10"
                          placeholder="Factor..."
                        />
                      </td>
                      <td class="p-0 text-center">
                        <button type="button" @click="removeUomRow(idx)" class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors text-4xl font-bold leading-none w-full h-full py-[6px]">&times;</button>
                      </td>
                    </tr>
                    <tr v-if="!form.uom_conversions.length">
                      <td colspan="3" class="px-[10px] py-[12px] text-center text-2xl text-[var(--color-text-muted)] italic">
                        No UOM conversions mapped
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-[8px]">
              <div class="space-y-[4px]">
                <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Standard Rate</label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 font-bold text-[var(--color-text-muted)] text-3xl">₹</span>
                  <input ref="rateInput" v-model.number="form.standard_rate" type="number" class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] pl-[40px] text-right font-mono text-4xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-success)] transition-all" placeholder="0.00" @keydown.enter.prevent="safetyStockInput?.focus()" />
                </div>
              </div>
              <div class="space-y-[4px]">
                <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Safety Stock</label>
                <input ref="safetyStockInput" v-model.number="form.safety_stock" type="number" class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-right font-mono text-4xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all placeholder:text-[var(--color-text-muted)]" placeholder="0" @keydown.enter.prevent="supplierInput?.focus()" />
              </div>
            </div>

            <!-- Suppliers Mapping Table (Excel-style) -->
            <div class="space-y-[4px]">
              <div class="flex items-center justify-between px-[20px]">
                <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Suppliers Mapping</label>
                <button type="button" @click="addSupplierRow" class="text-xl font-bold text-[var(--color-info)] hover:text-[var(--color-info)] transition-colors">+ Add Supplier</button>
              </div>
              <div class="border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm">
                <table class="w-full border-collapse text-2xl">
                  <thead>
                    <tr class="divide-x divide-[var(--color-border)] border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]">
                      <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Supplier</th>
                      <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Part No</th>
                      <th class="w-16"></th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[var(--color-border)]">
                    <tr v-for="(row, idx) in form.suppliers" :key="idx" class="divide-x divide-[var(--color-border)] hover:bg-[var(--color-border)]/10 transition-colors">
                      <td class="p-0 relative">
                        <input
                          type="text"
                          class="w-full bg-transparent px-[10px] py-[6px] text-2xl text-[var(--color-text)] outline-none focus:bg-[var(--color-info)]/10"
                          :class="row.supplier ? 'text-[var(--color-success)] font-semibold' : ''"
                          placeholder="Search supplier..."
                          autocomplete="off"
                          :value="row.supplier_label || ''"
                          @input="e => onSupplierRowInput(idx, e.target.value)"
                          @focus="activeSupplierRowIdx = idx"
                          @blur="onSupplierRowBlur"
                        />
                        <div
                          v-if="activeSupplierRowIdx === idx && supplierOptions.length"
                          class="absolute left-0 right-0 bottom-full z-10 mb-1 max-h-48 overflow-y-auto rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] px-[10px] py-[6px] shadow-xl"
                        >
                          <button
                            v-for="opt in supplierOptions"
                            :key="opt.name"
                            type="button"
                            class="w-full rounded-lg px-[10px] py-[6px] text-left hover:bg-[var(--color-info)]/20 transition-colors flex flex-col gap-0.5"
                            @mousedown.prevent="selectSupplierForRow(idx, opt)"
                          >
                            <span class="text-xl font-bold text-[var(--color-text)]">{{ opt.label }}</span>
                            <span class="text-sm text-[var(--color-text-muted)]">{{ opt.name }}</span>
                          </button>
                        </div>
                      </td>
                      <td class="p-0">
                        <input
                          v-model="row.supplier_part_no"
                          type="text"
                          class="w-full bg-transparent px-[10px] py-[6px] text-2xl text-[var(--color-text)] outline-none focus:bg-[var(--color-info)]/10"
                          placeholder="Part No (Optional)..."
                        />
                      </td>
                      <td class="p-0 text-center">
                        <button type="button" @click="removeSupplierRow(idx)" class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors text-4xl font-bold leading-none w-full h-full py-[6px]">&times;</button>
                      </td>
                    </tr>
                    <tr v-if="!form.suppliers.length">
                      <td colspan="3" class="px-[10px] py-[12px] text-center text-2xl text-[var(--color-text-muted)] italic">
                        No suppliers mapped
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- Variants: template attributes (ERPNext needs at least one when Has Variants is set) -->
        <div class="[grid-area:1/1] self-start space-y-[16px] max-w-[1200px]" :class="{ invisible: activeTab !== 'variants' }">
          <label
            v-if="canToggleVariants"
            class="flex items-center gap-[12px] px-[20px] py-[12px] text-2xl font-bold text-[var(--color-text)] cursor-pointer"
          >
            <input
              v-model="form.has_variants"
              type="checkbox"
              :true-value="1"
              :false-value="0"
              class="h-6 w-6 accent-[var(--color-info)]"
            />
            <span>Has Variants</span>
            <span class="text-xl font-normal text-[var(--color-text-muted)]">
              Makes this item a template — variants are created from it, it is not billed itself
            </span>
          </label>
          <p v-else class="px-[20px] py-[12px] text-2xl font-bold text-[var(--color-text)]">
            Template item <span class="text-xl font-normal text-[var(--color-text-muted)]">— Has Variants cannot be changed: {{ variantsLock }}</span>
          </p>

          <div v-if="form.has_variants" class="space-y-[4px]">
            <div class="flex items-center justify-between px-[20px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Attributes *</label>
              <button type="button" @click="addAttributeRow" class="text-xl font-bold text-[var(--color-info)] hover:text-[var(--color-info)] transition-colors">+ Add Attribute</button>
            </div>
            <div class="border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden shadow-sm">
              <table class="w-full border-collapse text-2xl">
                <thead>
                  <tr class="divide-x divide-[var(--color-border)] border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]">
                    <th class="w-1/3 px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Attribute</th>
                    <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Values</th>
                    <th class="w-16"></th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--color-border)]">
                  <tr v-for="(row, idx) in form.attributes" :key="idx" class="divide-x divide-[var(--color-border)] hover:bg-[var(--color-border)]/10 transition-colors">
                    <td class="p-0">
                      <select v-model="row.attribute" class="w-full bg-transparent px-[10px] py-[6px] text-2xl text-[var(--color-text)] outline-none cursor-pointer focus:bg-[var(--color-info)]/10 appearance-none">
                        <option value="" class="bg-[var(--color-surface)] text-[var(--color-text)]">Select Attribute...</option>
                        <option
                          v-for="a in itemAttributes"
                          :key="a.name"
                          :value="a.name"
                          :disabled="a.name !== row.attribute && form.attributes.some(r => r.attribute === a.name)"
                          class="bg-[var(--color-surface)] text-[var(--color-text)]"
                        >{{ a.name }}</option>
                      </select>
                    </td>
                    <td class="px-[10px] py-[6px] text-xl text-[var(--color-text-muted)]">{{ attributeValuesLabel(row.attribute) }}</td>
                    <td class="p-0 text-center">
                      <button type="button" @click="removeAttributeRow(idx)" class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors text-4xl font-bold leading-none w-full h-full py-[6px]">&times;</button>
                    </td>
                  </tr>
                  <tr v-if="!form.attributes.length">
                    <td colspan="3" class="px-[10px] py-[12px] text-center text-2xl text-[var(--color-danger)] italic">
                      Add at least one attribute
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Variants of the saved template: list + create from attribute value combinations -->
          <div v-if="canManageVariants" class="space-y-[4px]">
            <div class="flex items-center justify-between px-[20px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Variants ({{ variants.length }})</label>
              <button
                type="button"
                @click="toggleVariantCreate"
                class="text-xl font-bold text-[var(--color-info)] hover:text-[var(--color-info)] transition-colors"
              >{{ showVariantCreate ? '− Cancel' : '+ Create Variants' }}</button>
            </div>

            <div v-if="showVariantCreate" class="border border-[var(--color-info)]/40 bg-[var(--color-info)]/5 p-[12px] space-y-[10px]">
              <div v-for="attr in savedAttributes" :key="attr" class="flex items-start gap-[12px]">
                <span class="w-48 shrink-0 pt-[4px] text-2xl font-bold text-[var(--color-text)]">{{ attr }}</span>
                <div class="flex flex-wrap gap-[6px]">
                  <button
                    v-for="val in attributeValueOptions(attr)"
                    :key="val"
                    type="button"
                    @click="toggleVariantValue(attr, val)"
                    class="rounded-lg border px-[10px] py-[4px] text-xl transition-colors"
                    :class="(variantSelection[attr] || []).includes(val)
                      ? 'border-[var(--color-info)] bg-[var(--color-info)] text-[var(--color-text-on-highlight)] font-bold'
                      : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] hover:bg-[var(--color-info)]/10'"
                  >{{ val }}</button>
                  <span v-if="!attributeValueOptions(attr).length" class="text-xl italic text-[var(--color-danger)]">No values defined</span>
                </div>
              </div>
              <div class="flex items-center justify-end gap-[12px]">
                <span class="text-xl text-[var(--color-text-muted)]">
                  {{ variantComboCount }} combination(s){{ variantComboCount > MAX_VARIANTS_PER_CREATE ? ` — max ${MAX_VARIANTS_PER_CREATE} at a time` : '' }}, existing ones are skipped
                </span>
                <button
                  type="button"
                  @click="submitVariants"
                  :disabled="!canCreateVariants || isCreatingVariants"
                  class="rounded-lg bg-[var(--color-info)] px-[16px] py-[6px] text-xl font-bold uppercase text-[var(--color-text-on-highlight)] transition-colors hover:bg-[var(--color-info)]/80 disabled:opacity-50 disabled:pointer-events-none"
                >{{ isCreatingVariants ? 'Creating…' : 'Create' }}</button>
              </div>
            </div>

            <div class="max-h-[40vh] overflow-y-auto border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm">
              <table class="w-full border-collapse text-2xl">
                <thead class="sticky top-0">
                  <tr class="divide-x divide-[var(--color-border)] border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]">
                    <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Item Code</th>
                    <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Item Name</th>
                    <th v-for="attr in savedAttributes" :key="attr" class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">{{ attr }}</th>
                    <th class="w-32 px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Status</th>
                    <th class="w-40"></th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--color-border)]">
                  <tr
                    v-for="v in variants"
                    :key="v.item_code"
                    @click="editingVariant !== v.item_code && openVariant(v.item_code)"
                    class="cursor-pointer divide-x divide-[var(--color-border)] hover:bg-[var(--color-info)]/10 transition-colors"
                    title="Open variant"
                  >
                    <td class="px-[10px] py-[6px] font-mono text-[var(--color-text)]">{{ v.item_code }}</td>
                    <td class="px-[10px] py-[6px] text-[var(--color-text)]">{{ v.item_name }}</td>
                    <td v-for="attr in savedAttributes" :key="attr" class="px-[10px] py-[6px] text-[var(--color-text-muted)]" :class="{ 'p-0': editingVariant === v.item_code }">
                      <select
                        v-if="editingVariant === v.item_code"
                        v-model="variantDraft[attr]"
                        @click.stop
                        :aria-label="`${attr} for ${v.item_code}`"
                        class="w-full bg-[var(--color-info)]/10 px-[10px] py-[6px] text-2xl text-[var(--color-text)] outline-none cursor-pointer"
                      >
                        <option v-for="val in attributeValueOptions(attr)" :key="val" :value="val" class="bg-[var(--color-surface)] text-[var(--color-text)]">{{ val }}</option>
                        <option v-if="variantDraft[attr] && !attributeValueOptions(attr).includes(variantDraft[attr])" :value="variantDraft[attr]" class="bg-[var(--color-surface)] text-[var(--color-text)]">{{ variantDraft[attr] }}</option>
                      </select>
                      <template v-else>{{ v.attributes[attr] || '--' }}</template>
                    </td>
                    <td v-if="editingVariant === v.item_code" class="p-0">
                      <select
                        v-model="variantDraftDisabled"
                        @click.stop
                        :aria-label="`Status of ${v.item_code}`"
                        class="w-full bg-[var(--color-info)]/10 px-[10px] py-[6px] text-xl font-bold outline-none cursor-pointer"
                        :class="variantDraftDisabled ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'"
                      >
                        <option :value="0" class="bg-[var(--color-surface)] text-[var(--color-text)]">Enabled</option>
                        <option :value="1" class="bg-[var(--color-surface)] text-[var(--color-text)]">Disabled</option>
                      </select>
                    </td>
                    <td v-else class="px-[10px] py-[6px] text-xl font-bold" :class="Number(v.disabled) ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                      {{ Number(v.disabled) ? 'Disabled' : 'Enabled' }}
                    </td>
                    <td class="px-[10px] py-[6px] text-right whitespace-nowrap" @click.stop>
                      <template v-if="editingVariant === v.item_code">
                        <button type="button" @click="saveVariantAttributes(v)" :disabled="isSavingVariant" class="text-xl font-bold text-[var(--color-success)] disabled:opacity-50">{{ isSavingVariant ? 'Saving…' : 'Save' }}</button>
                        <button type="button" @click="cancelVariantEdit" :disabled="isSavingVariant" class="ml-[12px] text-xl font-bold text-[var(--color-text-muted)] disabled:opacity-50">Cancel</button>
                      </template>
                      <button v-else type="button" @click="startVariantEdit(v)" class="text-xl font-bold text-[var(--color-info)]" :aria-label="`Edit attributes of ${v.item_code}`">Edit</button>
                    </td>
                  </tr>
                  <tr v-if="!variants.length">
                    <td :colspan="savedAttributes.length + 4" class="px-[10px] py-[12px] text-center text-2xl italic text-[var(--color-text-muted)]">
                      {{ variantsLoading ? 'Loading variants…' : 'No variants yet' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="px-[20px] py-[12px] bg-[var(--color-surface)] border-t border-[var(--color-border)] flex gap-[8px]">
        <button
          @click="gotoERPNext"
          class="flex-1 rounded-xl py-[12px] text-2xl font-bold uppercase tracking-widest text-[var(--color-info)] border border-[var(--color-info)] hover:bg-[var(--color-info)]/10 transition-all active:scale-95 flex items-center justify-center gap-[8px]"
        >
          <span>ERPNext</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        </button>
        <button
          @click="$emit('close')"
          class="flex-1 rounded-xl py-[12px] text-2xl font-bold uppercase tracking-widest text-[var(--color-text-muted)] bg-[var(--color-surface-raised)] border border-[var(--color-border)] hover:bg-[var(--color-midlight)] transition-all active:scale-95"
        >
          Cancel
        </button>
        <button
          @click="handleSubmit"
          :disabled="isSubmitting || !canSubmit"
          class="flex-[2] rounded-xl py-[12px] text-2xl font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none shadow-lg flex items-center justify-center gap-[8px]"
          :class="canSubmit ? 'bg-[var(--color-info)] hover:bg-[var(--color-info)]/80' : 'bg-[var(--color-surface-raised)]'"
        >
          <span v-if="isSubmitting" class="h-8 w-8 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
          <span v-else>{{ isEditMode ? 'Update Item' : 'Create Item' }} <kbd class="ml-1 rounded border border-current px-1.5 py-0.5 font-mono text-xl opacity-70">End</kbd></span>
          <svg v-if="!isSubmitting" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
        </button>
      </div>
    </div>

    <!-- A variant from the Variants tab, edited in a stacked copy of this window -->
    <ItemCreation
      v-if="showVariantEdit"
      :show="showVariantEdit"
      :edit-item-code="variantEditCode"
      @close="closeVariant"
      @created="onVariantSaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { fetchItemCreationMetadata, getNextBarcode, createItem, updateItem, getItemForEdit, setItemDisabled, getItemVariants, createItemVariants, updateVariantAttributes, frappeGet, uploadFile } from '../api.js'
import { useSubwindowWatcher } from '../services/shortcutManager'
import { useItemAttributeCache } from '../services/itemAttributeCache.js'

const props = defineProps({
  show: Boolean,
  editItemCode: { type: String, default: '' },  // when set → edit mode
})

const emit = defineEmits(['close', 'created', 'disabled-changed'])

useSubwindowWatcher(computed(() => props.show), {
  ESCAPE: () => emit('close'),
  END: () => handleSubmit(),   // save from any field
})

// Set by "New Item" while editing: the window switches to create mode even
// though the parent still passes editItemCode. Cleared each time it opens.
const forceCreate = ref(false)

const isEditMode = computed(() => !!props.editItemCode && !forceCreate.value)

function gotoERPNext() {
  const url = isEditMode.value
    ? `/app/item/${encodeURIComponent(props.editItemCode)}`
    : '/app/item'
  window.open(url, '_blank')
}

// ── Field cache (item_group, hsn_sac, stock_uom, item_tax_template, supplier) ─
const CACHE_KEY = 'ic-field-cache'
const RETAIN_KEY = 'ic-retain-tax-fields'

// When off, HSN/SAC and Tax Template are wiped after every save instead of
// being carried over to the next item. Defaults to off.
function loadRetainTaxFields() {
  try { return localStorage.getItem(RETAIN_KEY) === '1' } catch { return false }
}

const retainTaxFields = ref(loadRetainTaxFields())

function toggleRetainTaxFields() {
  retainTaxFields.value = !retainTaxFields.value
  try { localStorage.setItem(RETAIN_KEY, retainTaxFields.value ? '1' : '0') } catch { /* ignore */ }
  if (!retainTaxFields.value) {
    // Drop anything already cached so the next reset cannot resurrect it.
    const c = loadCache()
    c.hsn_sac = ''
    c.item_tax_template = ''
    try { localStorage.setItem(CACHE_KEY, JSON.stringify(c)) } catch { /* ignore */ }
  }
}

function loadCache() {
  try { return JSON.parse(localStorage.getItem(CACHE_KEY) || '{}') } catch { return {} }
}

function saveCache() {
  const c = {
    item_group:        form.value.item_group,
    hsn_sac:           retainTaxFields.value ? form.value.hsn_sac : '',
    stock_uom:         form.value.stock_uom,
    item_tax_template: retainTaxFields.value ? form.value.item_tax_template : '',
    suppliers:         form.value.suppliers,
  }
  localStorage.setItem(CACHE_KEY, JSON.stringify(c))
}

function _applyItemData(data, itemCode) {
  form.value.item_name        = data.item_name        || ''
  form.value.item_print_name  = data.item_print_name  || ''
  form.value.image            = data.image            || ''
  form.value.barcode           = data.barcode || itemCode
  form.value.item_group        = data.item_group        || ''
  form.value.custom_is_gst_item = Number(data.custom_is_gst_item) === 1 ? 1 : 0
  form.value.hsn_sac           = data.hsn_sac           || ''
  form.value.stock_uom         = data.stock_uom || 'Nos'
  form.value.item_tax_template = data.item_tax_template || ''
  form.value.custom_competitive_item = data.custom_competitive_item || ''
  form.value.standard_rate     = data.standard_rate || 0
  form.value.safety_stock      = data.safety_stock      || 0
  form.value.suppliers         = (data.suppliers || []).map(s => {
    const sup = typeof s === 'string' ? s : s.supplier
    const pno = typeof s === 'string' ? '' : (s.supplier_part_no || '')
    return { supplier: sup, supplier_part_no: pno, supplier_label: sup }
  })
  form.value.uom_conversions = data.uom_conversions || []
  form.value.extra_barcodes  = data.extra_barcodes  || []
  form.value.has_variants    = Number(data.has_variants) === 1 ? 1 : 0
  form.value.variant_of      = data.variant_of || ''
  form.value.attributes      = (data.attributes || []).map(a => ({ attribute: a.attribute }))
  variantsLock.value         = data.has_variants_lock || ''
  savedTemplate.value        = Number(data.has_variants) === 1 && !data.variant_of
  savedAttributes.value      = (data.attributes || []).map(a => a.attribute).filter(Boolean)
  itemDisabled.value = Number(data.disabled) === 1
  autoBarcode.value = ''
  isBarcodeManual.value = true
}

// Disabled state of the item being edited; saved straight away, not with Update Item.
const itemDisabled = ref(false)
const isTogglingDisabled = ref(false)

async function toggleItemDisabled() {
  if (!isEditMode.value || isTogglingDisabled.value) return
  const disable = !itemDisabled.value
  if (!confirm(`${disable ? 'Disable' : 'Enable'} item ${props.editItemCode}?`)) return
  isTogglingDisabled.value = true
  try {
    const res = await setItemDisabled(props.editItemCode, disable)
    itemDisabled.value = Number(res?.disabled) === 1
    emit('disabled-changed', { item_code: props.editItemCode, disabled: itemDisabled.value })
  } catch (e) {
    alert(`Failed to ${disable ? 'disable' : 'enable'} item: ` + e.message)
  } finally {
    isTogglingDisabled.value = false
  }
}

async function loadForEdit(itemCode) {
  try {
    // The edit API reads the tax template from the first Item Taxes child row.
    const data = await getItemForEdit(itemCode)
    _applyItemData(data, itemCode)
    variants.value = []
    cancelVariantEdit()
    showVariantCreate.value = false
    if (savedTemplate.value) loadVariants()
  } catch (e) {
    console.error('[ItemCreation] loadForEdit failed:', e)
  }
}

const itemNameInput = ref(null)
const itemPrintNameInput = ref(null)
const barcodeInput = ref(null)
const itemGroupInput = ref(null)
const hsnInput = ref(null)
const uomInput = ref(null)
const rateInput = ref(null)
const safetyStockInput = ref(null)
const taxTemplateInput = ref(null)
const competitiveItemInput = ref(null)

const isSubmitting = ref(false)
const isFetchingBarcode = ref(false)
const isBarcodeManual = ref(false)
const autoBarcode = ref('')
const selectedSeries = ref('')
const showHSNDropdown = ref(false)
const hsnHighlightIdx = ref(0)

const form = ref({
  item_name: '',
  item_print_name: '',
  barcode: '',
  image: '',
  item_group: '',
  custom_is_gst_item: 0,
  hsn_sac: '',
  stock_uom: 'Nos',
  standard_rate: 0,
  safety_stock: 0,
  item_tax_template: '',
  custom_competitive_item: '',
  suppliers: [],
  uom_conversions: [],
  extra_barcodes: [],
  has_variants: 0,
  variant_of: '',
  attributes: [],
})

// Why Has Variants cannot be toggled on the item being edited ('' = eligible). Always
// eligible in create mode — ERPNext's limits only apply to saved items.
const variantsLock = ref('')
const canToggleVariants = computed(() => !isEditMode.value || !variantsLock.value)

const tabs = [
  { id: 'details', label: 'Details' },
  { id: 'variants', label: 'Variants' },
]
// Variants tab only when the box can be ticked, or the item already is a template
const visibleTabs = computed(() =>
  tabs.filter(t => t.id !== 'variants' || canToggleVariants.value || form.value.has_variants))
const activeTab = ref('details')

const fileInput = ref(null)
const isUploadingImage = ref(false)

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleImageUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return

  // Validate file size (max 5MB)
  if (file.size > 5 * 1024 * 1024) {
    alert('File size exceeds 5MB limit.')
    return
  }

  isUploadingImage.value = true
  try {
    const uploadArgs = {}
    if (isEditMode.value) {
      uploadArgs.doctype = 'Item'
      uploadArgs.docname = props.editItemCode
      uploadArgs.fieldname = 'image'
    }
    const res = await uploadFile(file, uploadArgs)
    form.value.image = res.file_url
  } catch (err) {
    console.error('Image upload failed:', err)
    alert('Failed to upload image: ' + err.message)
  } finally {
    isUploadingImage.value = false
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  }
}

function removeImage() {
  form.value.image = ''
}

const extraBarcodeInputs = ref([])

function addBarcodeRow() {
  const newIdx = form.value.extra_barcodes.length
  form.value.extra_barcodes.push({ barcode: '', uom: form.value.stock_uom })
  nextTick(() => {
    const el = extraBarcodeInputs.value[newIdx]
    if (el) {
      el.focus()
      el.select()
    }
  })
}

function removeBarcodeRow(idx) {
  form.value.extra_barcodes.splice(idx, 1)
  extraBarcodeInputs.value.splice(idx, 1)
}

function addUomRow() {
  form.value.uom_conversions.push({ uom: '', conversion_factor: 1 })
}

function removeUomRow(idx) {
  form.value.uom_conversions.splice(idx, 1)
}

// Served from IndexedDB, kept current by item_attribute_update socket events
const { itemAttributes, ensureItemAttributeCache } = useItemAttributeCache()

function addAttributeRow() {
  form.value.attributes.push({ attribute: '' })
}

function removeAttributeRow(idx) {
  form.value.attributes.splice(idx, 1)
}

function attributeValuesLabel(name) {
  const a = itemAttributes.value.find(x => x.name === name)
  if (!a) return ''
  if (Number(a.numeric_values) === 1) return `${a.from_range} to ${a.to_range}, step ${a.increment}`
  return a.values.join(', ') || 'No values defined'
}

// ─── Variants of a saved template ────────────────────────────────────────────
// Only for a template already saved: variants are built from its saved attributes, so
// unsaved attribute edits in the table above do not apply until Update Item.
const MAX_VARIANTS_PER_CREATE = 100 // matches _MAX_VARIANTS_PER_CREATE in item_api.py
const savedTemplate = ref(false)
const savedAttributes = ref([])
const variants = ref([])
const variantsLoading = ref(false)
const showVariantCreate = ref(false)
const variantSelection = ref({}) // { attribute: [values] }
const isCreatingVariants = ref(false)

const canManageVariants = computed(() => isEditMode.value && savedTemplate.value && savedAttributes.value.length > 0)

// Stacked window for one variant; the list reloads on close since name/disabled may have changed
const showVariantEdit = ref(false)
const variantEditCode = ref('')

function openVariant(itemCode) {
  variantEditCode.value = itemCode
  showVariantEdit.value = true
}

function closeVariant() {
  showVariantEdit.value = false
  loadVariants()
}

function onVariantSaved(item) {
  // "New Item" from the variant window creates a fresh item — keep the window open
  if (item?.is_new) return
  closeVariant()
}

// Inline edit of one variant's attribute values and status; the item code is kept
const editingVariant = ref('')
const variantDraft = ref({})
const variantDraftDisabled = ref(0)
const isSavingVariant = ref(false)

function startVariantEdit(v) {
  editingVariant.value = v.item_code
  variantDraft.value = Object.fromEntries(savedAttributes.value.map(attr => [attr, v.attributes[attr] || '']))
  variantDraftDisabled.value = Number(v.disabled) ? 1 : 0
}

function cancelVariantEdit() {
  editingVariant.value = ''
  variantDraft.value = {}
}

async function saveVariantAttributes(v) {
  if (isSavingVariant.value) return
  if (savedAttributes.value.some(attr => !variantDraft.value[attr])) {
    alert('Every attribute needs a value')
    return
  }
  isSavingVariant.value = true
  try {
    await updateVariantAttributes(v.item_code, variantDraft.value, variantDraftDisabled.value)
    cancelVariantEdit()
    await loadVariants()
  } catch (e) {
    alert('Failed to update variant: ' + e.message)
  } finally {
    isSavingVariant.value = false
  }
}

async function loadVariants() {
  variantsLoading.value = true
  try {
    variants.value = (await getItemVariants(props.editItemCode)) || []
  } catch (e) {
    console.error('[ItemCreation] loadVariants failed:', e)
  } finally {
    variantsLoading.value = false
  }
}

// Text values as defined; numeric attributes expand their range (capped so a fine step cannot flood the panel)
function attributeValueOptions(name) {
  const a = itemAttributes.value.find(x => x.name === name)
  if (!a) return []
  if (Number(a.numeric_values) !== 1) return a.values || []
  const from = Number(a.from_range), to = Number(a.to_range), step = Number(a.increment)
  if (!(step > 0) || to < from) return []
  const out = []
  for (let v = from; v <= to + 1e-9 && out.length < 200; v += step) out.push(String(parseFloat(v.toFixed(6))))
  return out
}

function toggleVariantCreate() {
  showVariantCreate.value = !showVariantCreate.value
  variantSelection.value = {}
}

function toggleVariantValue(attr, val) {
  const list = variantSelection.value[attr] || []
  variantSelection.value = {
    ...variantSelection.value,
    [attr]: list.includes(val) ? list.filter(v => v !== val) : [...list, val],
  }
}

const variantComboCount = computed(() => {
  if (!savedAttributes.value.length) return 0
  return savedAttributes.value.reduce((n, attr) => n * (variantSelection.value[attr]?.length || 0), 1)
})

// Every template attribute needs a value: ERPNext rejects a variant missing one
const canCreateVariants = computed(() => variantComboCount.value > 0 && variantComboCount.value <= MAX_VARIANTS_PER_CREATE)

async function submitVariants() {
  if (!canCreateVariants.value || isCreatingVariants.value) return
  isCreatingVariants.value = true
  try {
    const res = await createItemVariants(props.editItemCode, variantSelection.value)
    const created = Number(res?.created || 0)
    const skipped = variantComboCount.value - created
    alert(`${created} variant(s) created${skipped ? `, ${skipped} already existed` : ''}`)
    // Same rule as _has_variants_lock: a template with variants can no longer drop Has Variants
    if (created && !variantsLock.value) variantsLock.value = 'Variants already created from this template'
    showVariantCreate.value = false
    variantSelection.value = {}
    await loadVariants()
  } catch (e) {
    alert('Failed to create variants: ' + e.message)
  } finally {
    isCreatingVariants.value = false
  }
}

// A template needs at least one attribute row, so ticking the box seeds an empty one
watch(() => form.value.has_variants, (on) => {
  if (on && !form.value.attributes.length) addAttributeRow()
})

// ── Supplier search state ──────────────────────────────────────────────────
const supplierOptions = ref([])
const activeSupplierRowIdx = ref(-1)
let supplierSearchTimeout = null

function addSupplierRow() {
  form.value.suppliers.push({ supplier: '', supplier_part_no: '', supplier_label: '' })
}

function removeSupplierRow(idx) {
  form.value.suppliers.splice(idx, 1)
}

async function onSupplierRowInput(idx, q) {
  const row = form.value.suppliers[idx]
  row.supplier_label = q
  row.supplier = ''             // clear until a match is selected
  clearTimeout(supplierSearchTimeout)
  if (!q.trim()) { supplierOptions.value = []; return }
  supplierSearchTimeout = setTimeout(async () => {
    try {
      supplierOptions.value = await frappeGet('ssplbilling.api.item_api.search_suppliers', { query: q, limit: 15 })
    } catch (_) { supplierOptions.value = [] }
  }, 250)
}

function selectSupplierForRow(idx, opt) {
  const row = form.value.suppliers[idx]
  row.supplier = opt.name
  row.supplier_label = opt.label
  supplierOptions.value = []
  activeSupplierRowIdx.value = -1
}

function onSupplierRowBlur() {
  setTimeout(() => {
    activeSupplierRowIdx.value = -1
  }, 200)
}

// Sync Item Print Name from Item Name by default (only if empty or matching)
watch(() => form.value.item_name, (newVal) => {
  if (!isEditMode.value) {
    form.value.item_print_name = newVal
  }
})

// ── Live duplicate item-name check (print name may repeat) ──────────────────
// Holds the existing item code when the typed name is taken, else ''.
const duplicateItemName = ref('')
const isCheckingItemName = ref(false)
let itemNameCheckTimeout = null
let itemNameCheckSeq = 0

watch([() => form.value.item_name, isEditMode], ([name]) => {
  clearTimeout(itemNameCheckTimeout)
  const seq = ++itemNameCheckSeq
  duplicateItemName.value = ''
  const q = (name || '').trim()
  if (!q) { isCheckingItemName.value = false; return }
  isCheckingItemName.value = true
  itemNameCheckTimeout = setTimeout(async () => {
    try {
      const existing = await frappeGet('ssplbilling.api.item_api.check_item_name_exists', {
        item_name: q,
        exclude_item: isEditMode.value ? props.editItemCode : '',
      })
      if (seq === itemNameCheckSeq) duplicateItemName.value = existing || ''
    } catch (_) {
      // Server-side check on save still guards against duplicates.
    } finally {
      if (seq === itemNameCheckSeq) isCheckingItemName.value = false
    }
  }, 300)
})

// Track manual changes — strip all leading zeros on every change
watch(() => form.value.barcode, (newVal, oldVal) => {
  if (newVal && /^0/.test(newVal)) {
    form.value.barcode = stripLeadingZeros(newVal)
    return
  }
  if (oldVal !== undefined && !isFetchingBarcode.value) {
    isBarcodeManual.value = newVal !== autoBarcode.value
  }
})

const metadata = ref({
  item_groups: [],
  uoms: [],
  tax_templates: [],
  hsn_codes: [],
  competitive_items: [],
  naming_series: []
})

const filteredHSNCodes = computed(() => {
  const q = (form.value.hsn_sac || '').toLowerCase().trim()
  if (!q) return metadata.value.hsn_codes.slice(0, 50)
  return metadata.value.hsn_codes
    .filter(h => h.name.toLowerCase().includes(q) || (h.description || '').toLowerCase().includes(q))
    .slice(0, 50)
})

// metadata.tax_templates is already filtered to wb-company server-side. An item
// being edited may carry a template from another company — keep it in the list so
// opening the form does not silently blank it on save.
const taxTemplateOptions = computed(() => {
  const list = metadata.value.tax_templates || []
  const current = form.value.item_tax_template
  if (current && !list.some(t => t.name === current)) {
    return [...list, { name: current }]
  }
  return list
})

// Keep an edited item's competitive item selectable even if metadata has not loaded it
const competitiveItemOptions = computed(() => {
  const list = metadata.value.competitive_items || []
  const current = form.value.custom_competitive_item
  if (current && !list.some(c => c.name === current)) {
    return [...list, { name: current }]
  }
  return list
})

const availableUoms = computed(() => {
  const list = [form.value.stock_uom]
  form.value.uom_conversions.forEach(c => {
    if (c.uom && !list.includes(c.uom)) list.push(c.uom)
  })
  return list
})

const canSubmit = computed(() => {
  return form.value.item_name.trim() && form.value.item_group && form.value.stock_uom && form.value.item_tax_template
    && !duplicateItemName.value && !isCheckingItemName.value
    && (!form.value.has_variants || form.value.attributes.some(a => a.attribute))
})

async function loadMetadata() {
  try {
    const data = await fetchItemCreationMetadata()
    metadata.value = data

    if (data.naming_series?.length) {
      selectedSeries.value = data.naming_series[0]
      if (!isEditMode.value) generateBarcode()
    }
  } catch (e) {
    console.warn('Failed to load item metadata', e)
  }
}

function stripLeadingZeros(val) {
  const s = String(val || '').replace(/^0+/, '')
  return s || '0'
}

async function generateBarcode() {
  const series = selectedSeries.value || metadata.value.naming_series[0]
  if (!series) return

  isFetchingBarcode.value = true
  try {
    const res = await getNextBarcode(series)
    const stripped = stripLeadingZeros(res)
    form.value.barcode = stripped
    autoBarcode.value = stripped
    nextTick(() => { isBarcodeManual.value = false })
  } catch (e) {
    console.error('Failed to generate barcode', e)
  } finally {
    isFetchingBarcode.value = false
  }
}

function selectHSN(name) {
  form.value.hsn_sac = name
  showHSNDropdown.value = false
  hsnHighlightIdx.value = 0
  nextTick(() => uomInput.value?.focus())
}

function onHSNEnter() {
  if (showHSNDropdown.value && filteredHSNCodes.value.length > 0) {
    selectHSN(filteredHSNCodes.value[hsnHighlightIdx.value].name)
  } else {
    uomInput.value?.focus()
  }
}

watch(filteredHSNCodes, () => {
  hsnHighlightIdx.value = 0
})

async function handleSubmit() {
  if (!canSubmit.value || isSubmitting.value) return

  // Strip all leading zeros from primary barcode and any additional barcodes before saving
  form.value.barcode = stripLeadingZeros(form.value.barcode)
  form.value.extra_barcodes = form.value.extra_barcodes.map(r => ({
    ...r,
    barcode: stripLeadingZeros(r.barcode),
  }))

  isSubmitting.value = true
  try {
    if (isEditMode.value) {
      const res = await updateItem({
        ...form.value,
        item_code: props.editItemCode,
      })
      saveCache()
      alert('Item updated successfully!')
      emit('created', {
        item_code: res.item_code,
        item_name: res.item_name,
        price: form.value.standard_rate,
        uom: form.value.stock_uom,
        tax_rate: 0
      })
    } else {
      const res = await createItem({
        ...form.value,
        is_manual_barcode: isBarcodeManual.value,
        naming_series: selectedSeries.value,
      })
      saveCache()
      alert(`Item ${res.name} created successfully!`)
      emit('created', {
        item_code: res.item_code,
        item_name: form.value.item_name,
        price: form.value.standard_rate,
        uom: form.value.stock_uom,
        tax_rate: 0,
        is_new: true,
      })
      resetForm()
      nextTick(() => {
        itemNameInput.value?.focus()
      })
    }
  } catch (e) {
    alert(`Failed to ${isEditMode.value ? 'update' : 'create'} item: ` + e.message)
  } finally {
    isSubmitting.value = false
  }
}

// blank=true (window just opened, e.g. via F2) ignores the field cache so every
// field starts empty; after a save the cache carries values over to the next item.
function resetForm(blank = false) {
  const cache = blank ? {} : loadCache()
  form.value = {
    item_name: '',
    item_print_name: '',
    barcode: '',
    image: '',
    item_group:        blank ? '' : (cache.item_group || metadata.value.item_groups[0]?.name || ''),
    custom_is_gst_item: 0,
    hsn_sac:           (retainTaxFields.value && cache.hsn_sac)           || '',
    stock_uom:         cache.stock_uom         || 'Nos',
    item_tax_template: (retainTaxFields.value && cache.item_tax_template) || '',
    custom_competitive_item: '',
    standard_rate: 0,
    safety_stock: 0,
    suppliers:         cache.suppliers         || [],
    uom_conversions: [],
    extra_barcodes: [],
    has_variants: 0,
    variant_of: '',
    attributes: [],
  }
  startFreshBarcode()
}

function startFreshBarcode() {
  supplierOptions.value = []
  isBarcodeManual.value = false
  autoBarcode.value = ''
  if (selectedSeries.value) generateBarcode()
}

// Switch from edit to create, keeping every field except the names. Barcodes are
// cleared too — they are unique per item, so a fresh one is generated instead.
function startNewFromCurrent() {
  forceCreate.value = true
  itemDisabled.value = false
  form.value.item_name = ''
  form.value.item_print_name = ''
  form.value.barcode = ''
  form.value.extra_barcodes = []
  form.value.variant_of = ''
  savedTemplate.value = false
  variants.value = []
  cancelVariantEdit()
  showVariantCreate.value = false
  startFreshBarcode()
  nextTick(() => itemNameInput.value?.focus())
}

watch(() => props.show, async (newVal) => {
  if (newVal) {
    forceCreate.value = false
    activeTab.value = 'details'
    variantsLock.value = ''
    savedTemplate.value = false
    savedAttributes.value = []
    variants.value = []
    cancelVariantEdit()
    showVariantCreate.value = false
    showVariantEdit.value = false
    ensureItemAttributeCache()
    if (!isEditMode.value) {
      resetForm(true)
      await loadMetadata()
    } else {
      await loadMetadata()
      await loadForEdit(props.editItemCode)
    }
    nextTick(() => itemNameInput.value?.focus())
  }
})

onMounted(async () => {
  if (props.show) {
    ensureItemAttributeCache()
    if (!isEditMode.value) resetForm(true)
    await loadMetadata()
    if (isEditMode.value) {
      await loadForEdit(props.editItemCode)
    }
    nextTick(() => itemNameInput.value?.focus())
  }
})
</script>
