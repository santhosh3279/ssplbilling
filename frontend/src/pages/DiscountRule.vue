<template>
  <div class="h-screen flex flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] text-[13px] overflow-hidden discount-rule-page">
    <!-- HEADER -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 shadow-sm shrink-0">
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <button
            @click="router.push('/')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition"
          >
            ← Dashboard
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-sm font-semibold text-[var(--color-text)]">
            Discount Rules DocType Management
          </h1>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="handleNewRule"
            class="rounded bg-[var(--color-success)] px-4 py-1.5 text-xs font-bold text-white hover:bg-[var(--color-success)]/90 transition shadow-sm"
          >
            + New Discount Rule
          </button>
          <button
            @click="fetchRules"
            :disabled="loading"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]/80 transition"
          >
            {{ loading ? 'Loading...' : '🔄 Refresh List' }}
          </button>
        </div>
      </div>
    </header>

    <!-- MAIN BODY: SPLIT VIEW -->
    <div class="flex flex-1 overflow-hidden">
      <!-- LEFT COLUMN: RULES LIST (40%) -->
      <aside class="w-[40%] flex flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
        <!-- Search bar -->
        <div class="p-3 border-b border-[var(--color-border)] shrink-0 bg-[var(--color-surface)]/50">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search rules by name, item or group..."
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition"
          />
        </div>

        <!-- Rules List -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="loading && !rules.length" class="flex h-32 items-center justify-center">
            <span class="text-xs text-[var(--color-text-muted)] animate-pulse">Loading discount rules...</span>
          </div>
          <div v-else-if="!filteredRules.length" class="flex h-32 items-center justify-center">
            <span class="text-xs italic text-[var(--color-text-muted)]">No discount rules found</span>
          </div>
          <div v-else class="divide-y divide-[var(--color-border)]/50">
            <div
              v-for="rule in filteredRules"
              :key="rule.name"
              @click="selectRule(rule.name)"
              class="p-4 cursor-pointer hover:bg-[var(--color-surface-raised)]/40 transition-colors flex flex-col gap-2 relative"
              :class="{
                'bg-[var(--color-info)]/10 border-l-4 border-[var(--color-info)]': selectedName === rule.name,
                'opacity-65': !rule.enabled
              }"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="font-bold text-[14px] text-[var(--color-text)] truncate" :title="rule.rule_name">
                  {{ rule.rule_name }}
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <span class="rounded px-2 py-0.5 text-[9px] font-bold uppercase" :class="{
                    'bg-[var(--color-employee)]/20 text-[var(--color-employee)]': rule.discount_type === 'Product Discount',
                    'bg-[var(--color-warning)]/20 text-[var(--color-warning)]': rule.discount_type === 'Percentage Discount',
                    'bg-[var(--color-info)]/20 text-[var(--color-info)]': rule.discount_type === 'Custom Logic',
                  }">{{ rule.discount_type }}</span>

                  <!-- Status Toggle Switch -->
                  <button
                    @click.stop="toggleStatus(rule)"
                    class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                    :class="rule.enabled ? 'bg-[var(--color-success)]' : 'bg-gray-400'"
                  >
                    <span
                      class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                      :class="rule.enabled ? 'translate-x-4' : 'translate-x-0'"
                    />
                  </button>
                </div>
              </div>

              <!-- Scope & Info -->
              <div class="text-[11px] text-[var(--color-text-muted)] flex flex-wrap items-center gap-x-2 gap-y-1">
                <span>Price List: <strong class="text-[var(--color-text)]">{{ rule.price_list }}</strong></span>
                <span>•</span>
                <span v-if="rule.applies_to === 'Product Group'">
                  Group: <strong class="text-[var(--color-text)]">{{ rule.product_group }}</strong>
                </span>
                <span v-else>
                  Items: <strong class="text-[var(--color-text)]">{{ rule.items?.length || 0 }} pcs</strong>
                </span>
                <span v-if="rule.min_quantity">• Min Qty: <strong class="text-[var(--color-text)]">{{ rule.min_quantity }}</strong></span>
                <span v-if="rule.percentage_discount">• <strong class="text-[var(--color-warning)]">{{ rule.percentage_discount }}%</strong></span>
              </div>

              <!-- Date Range -->
              <div v-if="rule.start_date || rule.end_date" class="text-[10px] text-[var(--color-text-muted)] italic">
                📅 {{ rule.start_date || 'Any' }} to {{ rule.end_date || 'Any' }}
              </div>
            </div>
          </div>
        </div>

        <!-- Footer status -->
        <div class="p-3 border-t border-[var(--color-border)] shrink-0 bg-[var(--color-surface)] text-center text-xs text-[var(--color-text-muted)]">
          <strong>{{ filteredRules.length }}</strong> rules shown (Total: {{ rules.length }})
        </div>
      </aside>

      <!-- RIGHT COLUMN: FORM / DETAILS (60%) -->
      <main class="w-[60%] flex flex-col bg-[var(--color-bg)] overflow-hidden">
        <!-- Loading overlay for details -->
        <div v-if="detailLoading" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <span class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent mb-2"></span>
            <div class="text-xs text-[var(--color-text-muted)]">Loading discount rule details...</div>
          </div>
        </div>

        <div v-else-if="!isFormActive" class="flex-1 flex flex-col items-center justify-center p-8 text-center text-[var(--color-text-muted)]">
          <span class="text-5xl mb-4">🏷️</span>
          <h2 class="text-base font-bold text-[var(--color-text)] mb-1">Discount Rules Management</h2>
          <p class="max-w-md text-xs leading-relaxed mb-4">
            Select a rule from the left panel to edit its settings, scopes, and discount tiers, or create a brand new rule.
          </p>
          <button
            @click="handleNewRule"
            class="rounded bg-[var(--color-success)] px-5 py-2 text-xs font-bold text-white hover:bg-[var(--color-success)]/90 transition shadow-md"
          >
            + Create New Rule
          </button>
        </div>

        <!-- FORM PANEL -->
        <div v-else class="flex-1 flex flex-col overflow-hidden">
          <!-- Form Header -->
          <div class="px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-between shrink-0">
            <div>
              <h2 class="text-[14px] font-bold text-[var(--color-text)]">
                {{ form.name ? 'Edit Discount Rule' : 'New Discount Rule' }}
              </h2>
              <p class="text-[10px] text-[var(--color-text-muted)] font-mono truncate max-w-sm mt-0.5">
                {{ form.name || 'Draft document' }}
              </p>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="form.name"
                @click="handleDeleteRule"
                :disabled="saving"
                class="rounded border border-red-300 text-red-600 bg-red-50 px-3 py-1.5 text-xs font-bold hover:bg-red-100 disabled:opacity-50 transition"
              >
                🗑 Delete Rule
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
                {{ saving ? 'Saving...' : 'Save Rule' }}
              </button>
            </div>
          </div>

          <!-- Form Fields Wrapper -->
          <div class="flex-1 overflow-y-auto p-6 space-y-6">
            <!-- Basic Info Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm space-y-4">
              <h3 class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 pb-1.5">
                Basic Settings
              </h3>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- Rule Name -->
                <div class="flex flex-col gap-1.5">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Rule Name <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <input
                    v-model="form.rule_name"
                    type="text"
                    placeholder="Enter unique rule name"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  />
                </div>

                <!-- Enabled Check -->
                <div class="flex items-center gap-3 pt-6">
                  <input
                    id="form-enabled"
                    v-model="form.enabled"
                    type="checkbox"
                    class="h-4 w-4 rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-info)]"
                  />
                  <label for="form-enabled" class="text-[12px] font-bold text-[var(--color-text)] cursor-pointer select-none">
                    Enabled (Active)
                  </label>
                </div>

                <!-- Price List -->
                <div class="flex flex-col gap-1.5">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Price List <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <select
                    v-model="form.price_list"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  >
                    <option value="" disabled>Select Price List</option>
                    <option v-for="pl in priceLists" :key="pl" :value="pl">{{ pl }}</option>
                  </select>
                </div>

                <!-- Discount Type -->
                <div class="flex flex-col gap-1.5">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Discount Type <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <select
                    v-model="form.discount_type"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  >
                    <option value="Product Discount">Product Discount (Free Goods)</option>
                    <option value="Percentage Discount">Percentage Discount (%)</option>
                    <option value="Custom Logic">Custom Logic (Tiers)</option>
                  </select>
                </div>

                <!-- Start Date -->
                <div class="flex flex-col gap-1.5">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">Start Date</label>
                  <input
                    v-model="form.start_date"
                    type="date"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  />
                </div>

                <!-- End Date -->
                <div class="flex flex-col gap-1.5">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">End Date</label>
                  <input
                    v-model="form.end_date"
                    type="date"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  />
                </div>
              </div>
            </div>

            <!-- Scope / Applies To Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm space-y-4">
              <h3 class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 pb-1.5">
                Rule Scope (Applies To)
              </h3>
              
              <div class="flex flex-col gap-4">
                <div class="flex flex-col gap-1.5">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Applies To <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <select
                    v-model="form.applies_to"
                    class="w-full md:w-1/2 rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  >
                    <option value="Product Group">Product Group (Item Group)</option>
                    <option value="Item Code">Specific Item Codes</option>
                  </select>
                </div>

                <!-- Product Group Input -->
                <div v-if="form.applies_to === 'Product Group'" class="flex flex-col gap-1.5">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Product Group <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <select
                    v-model="form.product_group"
                    class="w-full md:w-1/2 rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  >
                    <option value="" disabled>Select Item Group</option>
                    <option v-for="ig in itemGroups" :key="ig" :value="ig">{{ ig }}</option>
                  </select>
                </div>

                <!-- Specific Items Table Editor -->
                <div v-else class="space-y-3">
                  <div class="flex items-center justify-between border-b border-[var(--color-border)]/30 pb-2">
                    <span class="text-[11px] font-bold text-[var(--color-text-muted)] uppercase">Item Scope List</span>
                    <span class="text-[10px] text-[var(--color-text-muted)] font-mono">{{ form.items.length }} items selected</span>
                  </div>

                  <!-- Autocomplete Item Search Box -->
                  <div class="relative max-w-md">
                    <input
                      v-model="itemSearchQuery"
                      @input="handleItemSearch"
                      @keydown.down.prevent="moveSearchSelection(1)"
                      @keydown.up.prevent="moveSearchSelection(-1)"
                      @keydown.enter.prevent="addSearchSelectedItem"
                      type="text"
                      placeholder="Type code or name to find item..."
                      class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                    />
                    
                    <!-- Search Results dropdown -->
                    <div
                      v-if="searchSuggestions.length"
                      class="absolute z-50 left-0 right-0 mt-1 max-h-60 overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg divide-y divide-[var(--color-border)]/50"
                    >
                      <div
                        v-for="(item, idx) in searchSuggestions"
                        :key="item.item_code"
                        @click="addItemToScope(item)"
                        class="p-2 cursor-pointer text-xs hover:bg-[var(--color-info)]/10 flex items-center justify-between"
                        :class="{'bg-[var(--color-info)]/15 font-bold': searchActiveIndex === idx}"
                      >
                        <div class="truncate pr-4">
                          <span class="font-mono font-bold text-[var(--color-info)]">{{ item.item_code }}</span>
                          <span class="text-[var(--color-text-muted)] ml-2">— {{ item.item_name }}</span>
                        </div>
                        <span class="text-[10px] text-gray-500 font-mono shrink-0">{{ item.uom || 'Nos' }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Item scope list view -->
                  <div class="border border-[var(--color-border)] rounded-lg overflow-hidden max-h-64 overflow-y-auto">
                    <table class="w-full text-left">
                      <thead>
                        <tr class="bg-[var(--color-surface-raised)] text-[10px] uppercase font-bold text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                          <th class="p-2 w-1/3">Item Code</th>
                          <th class="p-2 w-1/2">Item Name</th>
                          <th class="p-2 w-[10%]">UOM</th>
                          <th class="p-2 w-[10%] text-center">Action</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-[var(--color-border)]">
                        <tr v-if="!form.items.length">
                          <td colspan="4" class="p-4 text-center text-xs text-[var(--color-text-muted)] italic">
                            No items added to scope. Search above to add.
                          </td>
                        </tr>
                        <tr v-for="(item, idx) in form.items" :key="item.item_code" class="text-xs hover:bg-[var(--color-surface-raised)]/20">
                          <td class="p-2 font-mono font-bold">{{ item.item_code }}</td>
                          <td class="p-2 truncate max-w-[200px]" :title="item.item_name">{{ item.item_name }}</td>
                          <td class="p-2 text-gray-500 font-mono">{{ item.uom || '—' }}</td>
                          <td class="p-2 text-center">
                            <button
                              @click="removeItemFromScope(idx)"
                              class="text-red-500 hover:text-red-700 font-bold px-2 py-1 text-sm transition"
                              title="Remove item"
                            >
                              ✕
                            </button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>

            <!-- Discount Settings Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm space-y-4">
              <h3 class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 pb-1.5">
                Discount Settings — {{ form.discount_type }}
              </h3>

              <!-- PRODUCT DISCOUNT SETTINGS -->
              <div v-if="form.discount_type === 'Product Discount'" class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="flex flex-col gap-1.5">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">Min Purchase Quantity</label>
                  <input
                    v-model.number="form.min_quantity"
                    type="number"
                    min="0"
                    step="1"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  />
                </div>
                <div class="flex flex-col gap-1.5">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">Free Quantity Given</label>
                  <input
                    v-model.number="form.free_quantity"
                    type="number"
                    min="0"
                    step="1"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  />
                </div>
                <div class="flex items-center gap-3 pt-6">
                  <input
                    id="form-recursive"
                    v-model="form.recursive"
                    type="checkbox"
                    class="h-4 w-4 rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-info)]"
                  />
                  <label for="form-recursive" class="text-[12px] font-bold text-[var(--color-text)] cursor-pointer select-none">
                    Recursive (Multiply Free Qty by multiples of Min Qty)
                  </label>
                </div>
              </div>

              <!-- PERCENTAGE DISCOUNT SETTINGS -->
              <div v-else-if="form.discount_type === 'Percentage Discount'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="flex flex-col gap-1.5">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">Min Purchase Quantity</label>
                  <input
                    v-model.number="form.min_quantity"
                    type="number"
                    min="0"
                    step="1"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  />
                </div>
                <div class="flex flex-col gap-1.5">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">Discount Percentage (%)</label>
                  <input
                    v-model.number="form.percentage_discount"
                    type="number"
                    min="0"
                    max="100"
                    step="0.01"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition font-mono"
                  />
                </div>
              </div>

              <!-- CUSTOM LOGIC TIERED SETTINGS -->
              <div v-else class="space-y-4">
                <div class="flex flex-col gap-1.5 w-full md:w-1/2">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">Custom Logic Type</label>
                  <select
                    v-model="form.custom_logic_type"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  >
                    <option value="Product">Product Logic (Tiered Free Qty)</option>
                    <option value="Percentage">Percentage Logic (Tiered Disc %)</option>
                  </select>
                </div>

                <!-- Custom Logic Table Editor -->
                <div class="space-y-2">
                  <div class="flex items-center justify-between border-b border-[var(--color-border)]/30 pb-2">
                    <span class="text-[11px] font-bold text-[var(--color-text-muted)] uppercase">Custom Logic Threshold Tiers</span>
                    <button
                      @click="addCustomLogicRow"
                      type="button"
                      class="rounded bg-[var(--color-info)] px-3 py-1 text-[10px] font-bold text-white hover:bg-[var(--color-info)]/90 transition"
                    >
                      + Add Tier
                    </button>
                  </div>

                  <div class="border border-[var(--color-border)] rounded-lg overflow-hidden">
                    <table class="w-full text-left">
                      <thead>
                        <tr class="bg-[var(--color-surface-raised)] text-[10px] uppercase font-bold text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                          <th class="p-2 w-1/3">Min Quantity</th>
                          <th v-if="form.custom_logic_type === 'Product'" class="p-2 w-1/3">Nos (Free Qty)</th>
                          <th v-if="form.custom_logic_type === 'Percentage'" class="p-2 w-1/3">Percentage (%)</th>
                          <th class="p-2 w-[10%] text-center">Action</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-[var(--color-border)]">
                        <tr v-if="!form.custom_logic_table.length">
                          <td colspan="3" class="p-4 text-center text-xs text-[var(--color-text-muted)] italic">
                            No tiers added yet. Click "+ Add Tier" above to insert.
                          </td>
                        </tr>
                        <tr v-for="(row, idx) in form.custom_logic_table" :key="idx" class="text-xs hover:bg-[var(--color-surface-raised)]/20">
                          <td class="p-1.5">
                            <input
                              v-model.number="row.min_quantity"
                              type="number"
                              min="0"
                              step="1"
                              placeholder="e.g. 10"
                              class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 outline-none focus:border-[var(--color-info)] transition font-mono"
                            />
                          </td>
                          <td v-if="form.custom_logic_type === 'Product'" class="p-1.5">
                            <input
                              v-model.number="row.nos"
                              type="number"
                              min="0"
                              step="1"
                              placeholder="e.g. 1"
                              class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 outline-none focus:border-[var(--color-info)] transition font-mono"
                            />
                          </td>
                          <td v-if="form.custom_logic_type === 'Percentage'" class="p-1.5">
                            <input
                              v-model.number="row.percentage"
                              type="number"
                              min="0"
                              max="100"
                              step="0.01"
                              placeholder="e.g. 5"
                              class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 outline-none focus:border-[var(--color-info)] transition font-mono"
                            />
                          </td>
                          <td class="p-1.5 text-center">
                            <button
                              @click="removeCustomLogicRow(idx)"
                              class="text-red-500 hover:text-red-700 font-bold px-2 py-1 text-sm transition"
                              title="Delete Tier"
                            >
                              ✕
                            </button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import { useItemCache } from '../services/itemCache.js'

const router = useRouter()
const { searchItemsInCache } = useItemCache()

const API = 'ssplbilling.api.discount_rule_api'

// Metadata references
const priceLists = ref([])
const itemGroups = ref([])

// State
const rules = ref([])
const loading = ref(false)
const searchQuery = ref('')
const selectedName = ref(null)
const detailLoading = ref(false)
const saving = ref(false)

// Form structure
const emptyForm = () => ({
  name: null,
  rule_name: '',
  enabled: true,
  price_list: '',
  discount_type: 'Product Discount',
  applies_to: 'Product Group',
  product_group: '',
  start_date: '',
  end_date: '',
  min_quantity: 0,
  free_quantity: 0,
  recursive: false,
  percentage_discount: 0,
  custom_logic_type: 'Product',
  items: [],
  custom_logic_table: []
})

const form = ref(emptyForm())
const isFormActive = ref(false)

// Item search state inside specific items editor
const itemSearchQuery = ref('')
const searchSuggestions = ref([])
const searchActiveIndex = ref(-1)

// Fetch all rules from database
async function fetchRules() {
  loading.value = true
  try {
    const data = await frappePost(`${API}.get_discount_rules`)
    rules.value = data || []
  } catch (e) {
    alert(e.message || 'Failed to fetch rules')
  } finally {
    loading.value = false
  }
}

// Fetch lists of Price Lists and Item Groups
async function fetchMetadata() {
  try {
    const meta = await frappeGet(`${API}.get_discount_rule_metadata`)
    priceLists.value = meta.price_lists || []
    itemGroups.value = meta.item_groups || []
    
    // Set default price list to the first available if not empty
    if (priceLists.value.length && !form.value.price_list) {
      form.value.price_list = priceLists.value[0]
    }
  } catch (e) {
    console.warn('Metadata fetch failed:', e)
  }
}

// Filter rules list
const filteredRules = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return rules.value
  return rules.value.filter(r =>
    (r.rule_name || '').toLowerCase().includes(q) ||
    (r.product_group || '').toLowerCase().includes(q) ||
    (r.items || []).some(i => i.item_code.toLowerCase().includes(q) || (i.item_name || '').toLowerCase().includes(q))
  )
})

// Select a rule and load full document including child tables
async function selectRule(name) {
  selectedName.value = name
  detailLoading.value = true
  isFormActive.value = true
  itemSearchQuery.value = ''
  searchSuggestions.value = []
  
  try {
    const doc = await frappePost(`${API}.get_discount_rule`, { name })
    form.value = {
      name: doc.name,
      rule_name: doc.rule_name || '',
      enabled: doc.enabled === 1,
      price_list: doc.price_list || '',
      discount_type: doc.discount_type || 'Product Discount',
      applies_to: doc.applies_to || 'Product Group',
      product_group: doc.product_group || '',
      start_date: doc.start_date || '',
      end_date: doc.end_date || '',
      min_quantity: doc.min_quantity || 0,
      free_quantity: doc.free_quantity || 0,
      recursive: doc.recursive === 1,
      percentage_discount: doc.percentage_discount || 0,
      custom_logic_type: doc.custom_logic_type || 'Product',
      items: doc.items || [],
      custom_logic_table: doc.custom_logic_table || []
    }
  } catch (e) {
    alert(e.message || 'Failed to load discount rule details')
    closeForm()
  } finally {
    detailLoading.value = false
  }
}

// Open clean form for creating new rule
function handleNewRule() {
  selectedName.value = null
  isFormActive.value = true
  form.value = emptyForm()
  itemSearchQuery.value = ''
  searchSuggestions.value = []
  
  if (priceLists.value.length) {
    form.value.price_list = priceLists.value[0]
  }
}

function closeForm() {
  isFormActive.value = false
  selectedName.value = null
  form.value = emptyForm()
}

// Toggle enabled status directly from left-side list
async function toggleStatus(rule) {
  const newStatus = !rule.enabled
  try {
    await frappePost(`${API}.toggle_discount_rule_enabled`, {
      name: rule.name,
      enabled: newStatus ? 1 : 0
    })
    rule.enabled = newStatus
  } catch (e) {
    alert(e.message || 'Failed to toggle status')
  }
}

// Item autocomplete search
function handleItemSearch() {
  const q = itemSearchQuery.value.trim()
  if (!q || q.length < 2) {
    searchSuggestions.value = []
    searchActiveIndex.value = -1
    return
  }
  
  // Quick search in local cached items index
  const found = searchItemsInCache(q, 10)
  
  // Filter out items already in the form's items list
  const existingCodes = form.value.items.map(i => i.item_code)
  searchSuggestions.value = found.filter(i => !existingCodes.includes(i.item_code))
  searchActiveIndex.value = searchSuggestions.value.length ? 0 : -1
}

function moveSearchSelection(dir) {
  if (!searchSuggestions.value.length) return
  const len = searchSuggestions.value.length
  searchActiveIndex.value = (searchActiveIndex.value + dir + len) % len
}

function addSearchSelectedItem() {
  if (searchActiveIndex.value >= 0 && searchActiveIndex.value < searchSuggestions.value.length) {
    addItemToScope(searchSuggestions.value[searchActiveIndex.value])
  }
}

function addItemToScope(item) {
  form.value.items.push({
    item_code: item.item_code,
    item_name: item.item_name || '',
    uom: item.uom || 'Nos'
  })
  
  // Reset search
  itemSearchQuery.value = ''
  searchSuggestions.value = []
  searchActiveIndex.value = -1
}

function removeItemFromScope(idx) {
  form.value.items.splice(idx, 1)
}

// Custom logic rows management
function addCustomLogicRow() {
  form.value.custom_logic_table.push({
    min_quantity: 0,
    nos: 0,
    percentage: 0
  })
}

function removeCustomLogicRow(idx) {
  form.value.custom_logic_table.splice(idx, 1)
}

// Validate inputs & Save
async function handleSave() {
  if (!form.value.rule_name.trim()) {
    alert('Please enter a Rule Name.')
    return
  }
  if (!form.value.price_list) {
    alert('Please select a Price List.')
    return
  }
  if (form.value.applies_to === 'Product Group' && !form.value.product_group) {
    alert('Please select a Product Group.')
    return
  }
  if (form.value.applies_to === 'Item Code' && !form.value.items.length) {
    alert('Please add at least one Item to the scope.')
    return
  }

  saving.value = true
  try {
    const method = form.value.name ? 'update_discount_rule' : 'create_discount_rule'
    const payload = {
      ...form.value,
      enabled: form.value.enabled ? 1 : 0,
      recursive: form.value.recursive ? 1 : 0
    }
    
    const res = await frappePost(`${API}.${method}`, { data: JSON.stringify(payload) })
    alert(`Discount Rule saved successfully!`)
    
    // Refresh list and select the saved document
    await fetchRules()
    if (res && res.name) {
      await selectRule(res.name)
    } else {
      closeForm()
    }
  } catch (e) {
    alert(e.message || 'Save operation failed')
  } finally {
    saving.value = false
  }
}

// Delete discount rule
async function handleDeleteRule() {
  if (!form.value.name) return
  if (!confirm(`Are you sure you want to delete the rule "${form.value.rule_name}"? This cannot be undone.`)) {
    return
  }

  saving.value = true
  try {
    await frappePost(`${API}.delete_discount_rule`, { name: form.value.name })
    alert('Discount Rule deleted.')
    closeForm()
    await fetchRules()
  } catch (e) {
    alert(e.message || 'Failed to delete rule')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchRules()
  fetchMetadata()
})
</script>

<style scoped>
.discount-rule-page {
  font-size: 19.5px !important;
}
.discount-rule-page :deep(.text-xs),
.discount-rule-page :deep(input.text-xs),
.discount-rule-page :deep(select.text-xs) {
  font-size: 18px !important;
}
.discount-rule-page :deep(.text-sm),
.discount-rule-page :deep(h1.text-sm),
.discount-rule-page :deep(h2.text-sm) {
  font-size: 21px !important;
}
.discount-rule-page :deep(.text-base) {
  font-size: 24px !important;
}
.discount-rule-page :deep(.text-lg) {
  font-size: 27px !important;
}
.discount-rule-page :deep(.text-xl) {
  font-size: 30px !important;
}
.discount-rule-page :deep(.text-2xl) {
  font-size: 36px !important;
}
.discount-rule-page :deep(.text-3xl) {
  font-size: 45px !important;
}
.discount-rule-page :deep(.text-\[13px\]) {
  font-size: 19.5px !important;
}
.discount-rule-page :deep(.text-\[11px\]) {
  font-size: 16.5px !important;
}
.discount-rule-page :deep(.text-\[10px\]) {
  font-size: 15px !important;
}
.discount-rule-page :deep(.text-\[12px\]) {
  font-size: 18px !important;
}
.discount-rule-page :deep(.text-\[14px\]) {
  font-size: 21px !important;
}
.discount-rule-page :deep(.text-\[9px\]) {
  font-size: 13.5px !important;
}
.discount-rule-page :deep(.text-5xl) {
  font-size: 72px !important;
}
</style>
