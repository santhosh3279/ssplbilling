<template>
  <div class="flex h-full overflow-hidden bg-[var(--color-bg)]">

    <!-- ===================== SIDEBAR ===================== -->
    <aside class="flex w-64 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
      <!-- Logo -->
      <div class="border-b border-[var(--color-border)] px-4 py-4">
        <div class="text-lg font-bold text-[var(--color-text)]">Wholesale<span class="font-light text-[var(--color-text-muted)]">Billing</span> <span class="text-[15px] font-mono font-normal text-[var(--color-text-muted)] opacity-80">V:{{ appVersion }}</span></div>
        <div class="mt-0.5 text-xs text-[var(--color-text-muted)]">Fast Billing System <span class="font-mono opacity-70">{{ appUpdated }}</span></div>
      </div>

      <!-- User -->
      <div class="border-b border-[var(--color-border)] px-4 py-3">
        <div class="flex items-center gap-2">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-highlight)] text-sm font-bold text-[var(--color-text-on-highlight)]">
            {{ userInitials }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="truncate text-base font-semibold text-[var(--color-text)]">
              {{ session.fullName.value || 'User' }}
              <span v-if="selectedUser !== session.user.value" class="text-xs font-normal text-[var(--color-text-muted)]"> ({{ selectedUserDisplayName }})</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="truncate text-xs text-[var(--color-text-muted)]">{{ session.user.value }}</span>
              <span class="shrink-0 rounded px-1 py-0.5 text-[10px] font-bold uppercase tracking-wider"
                :class="{
                  'bg-[var(--color-warning)]/20 text-[var(--color-warning)]': userRole === 'admin',
                  'bg-[var(--color-info)]/20 text-[var(--color-info)]': userRole === 'cashier',
                  'bg-[var(--color-success)]/20 text-[var(--color-success)]': userRole === 'biller',
                }"
              >{{ userRole }}</span>
            </div>
          </div>
          <button
            @click="handleFullSync"
            :disabled="isSyncing"
            class="flex items-center justify-center rounded bg-[var(--color-surface-raised)] p-1.5 text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)] transition-colors disabled:opacity-50"
            title="Sync Settings"
          >
            <svg class="h-4 w-4" :class="{'animate-spin text-[var(--color-info)]': isSyncing}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-3 overflow-y-auto">
        <!-- Admin: Inherit User Settings -->
        <div v-if="isActualAdmin" class="mb-6 px-2">
          <label class="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
            Inherit Settings
          </label>
          <div class="relative" ref="inheritDropdownRef">
            <button
              ref="inheritSettingsSelectRef"
              type="button"
              @click="toggleInheritDropdown"
              class="flex w-full items-center justify-between rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-[9px] py-[6px] text-left text-[16.8px] text-[var(--color-text)] focus:border-[var(--color-highlight)] focus:outline-none focus:ring-1 focus:ring-[var(--color-highlight)] transition-all hover:bg-[var(--color-midlight)]"
            >
              <span class="truncate">{{ selectedUserLabel }}</span>
              <svg class="h-6 w-6 shrink-0 text-[var(--color-text-muted)] transition-transform duration-200" :class="{ 'rotate-180': isInheritDropdownOpen }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            <!-- Dropdown List -->
            <div
              v-if="isInheritDropdownOpen"
              class="absolute left-0 right-0 z-50 mt-1 max-h-60 overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] py-1 shadow-lg"
            >
              <div
                v-for="(u, index) in inheritUsersOptions"
                :key="u.value"
                :id="'wb-user-opt-' + index"
                :class="[
                  'cursor-pointer px-[9px] py-[6px] text-[16.8px] text-[var(--color-text)] transition-colors',
                  index === focusedUserIndex ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] font-semibold' : 'hover:bg-[var(--color-midlight)]'
                ]"
                @click="selectUserOption(u.value)"
                @mouseenter="focusedUserIndex = index"
              >
                {{ u.label }}
              </div>
            </div>
          </div>
          <div v-if="selectedUser !== session.user.value" class="mt-1.5 flex items-center gap-1.5 px-1">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-warning)] opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-warning)]"></span>
            </span>
            <span class="text-xs font-medium text-[var(--color-warning)]/90 italic">Previewing User Mode</span>
          </div>
        </div>

        <div class="mb-2 px-2 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Menu</div>
        <button
          @click="currentTab = 'dashboard'"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base font-semibold transition-colors"
          :class="currentTab === 'dashboard' ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)] hover:bg-[var(--color-midlight)]'"
        >
          🏠 Dashboard
        </button>
        <button
          v-if="userRole === 'admin'"
          @click="currentTab = 'locked-bills'"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base font-semibold transition-colors"
          :class="currentTab === 'locked-bills' ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)] hover:bg-[var(--color-midlight)]'"
        >
          🔐 Locked Bills
        </button>
      </nav>

      <!-- Settings section -->
      <div class="border-t border-[var(--color-border)] px-3 py-3">
        <div class="mb-2 px-2 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Settings</div>

        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-text)] hover:bg-[var(--color-midlight)]"
          @click="showLicenseDetails = true"
        >
          🪪 License Details
        </button>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-text)] hover:bg-[var(--color-midlight)]"
          @click="handleToggleTheme"
        >
          <span v-if="theme === 'light'">☀️</span>
          <span v-else>🌙</span>
          <span>Toggle Theme</span>
        </button>

        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-text)] hover:bg-[var(--color-midlight)]"
          @click="handleOpenGstValidator"
        >
          🔍 GST Validation
        </button>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-text)] hover:bg-[var(--color-midlight)]"
          @click="showSystemPerformance = true"
        >
          📊 System Performance
        </button>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-text)] hover:bg-[var(--color-midlight)]"
          @click="showGeneralSettings = true"
        >
          ⚙️ General
        </button>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-text)] hover:bg-[var(--color-midlight)] disabled:opacity-50 transition-colors"
          @click="handleClearRedisCache"
          :disabled="isClearingRedis"
        >
          <span :class="{'animate-spin inline-block': isClearingRedis}">🧹</span>
          <span>{{ isClearingRedis ? 'Clearing Cache...' : 'Clear Redis Cache' }}</span>
        </button>
        <button
          v-if="userRole === 'admin'"
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-text)] hover:bg-[var(--color-midlight)]"
          @click="router.push('/ssplbillingsettings')"
        >
          ⚙️ SSPL Settings
        </button>
        <button
          class="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-base text-[var(--color-danger)] hover:bg-[var(--color-midlight)]"
          @click="handleLogout"
        >
          🚪 Logout
        </button>
      </div>
    </aside>

    <!-- ===================== MAIN CONTENT ===================== -->
    <main class="flex-1 overflow-y-auto">
      <!-- Top Bar -->
      <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-lg font-bold text-[var(--color-text)]">
              {{ (currentTab === 'locked-bills' && userRole === 'admin') ? 'Locked Bills' : 'Dashboard' }}
              <span v-if="licenseStatusText" class="text-[15px] font-mono font-normal ml-1" :class="daysRemaining !== null && daysRemaining < 30 ? 'text-[var(--color-warning)] font-bold' : 'text-[var(--color-text-muted)]'">
                License: {{ licenseStatusText }}
              </span>
            </h1>
            <p class="text-[10px] text-[var(--color-text-muted)] font-medium uppercase tracking-wider">{{ todayDate }} | {{ todayDay }}</p>
          </div>
          
          <div class="flex items-center gap-4">
            <span class="text-[var(--color-info)] font-bold uppercase tracking-widest text-lg">
              👤 {{ session.fullName.value || session.user.value }}
              <span v-if="selectedUser !== session.user.value" class="normal-case font-normal text-[var(--color-text-muted)] text-sm"> ({{ selectedUserDisplayName }})</span>
            </span>
            <!-- Fullscreen button -->
            <button
              @click="toggleFullscreen"
              class="flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-midlight)] transition shadow-sm active:scale-95 focus:outline-none"
              title="Toggle Fullscreen"
            >
              <span>{{ isFullscreen ? '📴 Exit Fullscreen' : '📺 Fullscreen' }}</span>
            </button>
          </div>
        </div>
      </header>

      <div v-if="currentTab === 'dashboard'" class="flex flex-col px-10 py-8 gap-6">
        <!-- Top bar with Search & Licensed To Widget -->
        <div class="flex items-center justify-between gap-6 w-full">
          <!-- Search bar -->
          <div class="relative w-full max-w-lg group">
            <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <svg class="h-5 w-5 text-[var(--color-text-muted)] group-focus-within:text-[var(--color-highlight)] transition-colors duration-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              ref="searchInputRef"
              v-model="searchQuery"
              type="text"
              placeholder="Search tiles... (Arrow keys to navigate, Enter to open)"
              class="w-full pl-11 pr-12 py-3 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] font-semibold placeholder-[var(--color-text-muted)] transition-all duration-300 focus:outline-none focus:border-[var(--color-highlight)] focus:ring-4 focus:ring-[var(--color-highlight)]/15 shadow-sm hover:border-[var(--color-border)]/80"
            />
            <div class="absolute inset-y-0 right-0 pr-4 flex items-center gap-2">
              <span v-if="!searchQuery" class="text-[10px] font-bold text-[var(--color-text-muted)] bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-1.5 py-0.5 rounded shadow-sm">/</span>
              <button
                v-else
                @click="searchQuery = ''; focusSearch()"
                class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors p-1 rounded-full hover:bg-[var(--color-border)]/30"
                title="Clear search"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Licensed Customer Widget -->
          <div
            v-if="licenseInfo?.customer_name"
            class="flex flex-col items-center justify-center bg-[var(--color-surface)] px-5 py-[5px] rounded-2xl border border-[var(--color-border)] shadow-sm shrink-0 w-[280px] text-center"
          >
            <div class="text-[13px] font-bold text-[var(--color-text-muted)] uppercase tracking-[0.2em] leading-none mb-1">Licensed To</div>
            <div class="text-xl font-black text-[var(--color-text)] truncate max-w-[240px] leading-tight">{{ licenseInfo.customer_name }}</div>
          </div>
        </div>

        <!-- Main content: Tiles and widgets -->
        <div class="flex flex-row items-start justify-between gap-8 w-full">
          <!-- Left: Bucketed Tiles -->
          <div class="flex-shrink-0 space-y-4">
            <!-- Column table (no buckets) when tiles come from SSPL Dashboard Tile Access;
                 10 tiles per column, overflow flows into the next column; ↑/↓ + Enter to navigate -->
            <div v-if="isTileAccessMode" class="flex flex-row items-start gap-4">
              <div v-for="(col, colIdx) in tileColumns" :key="colIdx" class="flex flex-col gap-2">
                <div
                  v-for="(tile, rowIdx) in col"
                  :key="tile.id"
                  :id="'wb-tile-' + (colIdx * TILES_PER_COLUMN + rowIdx)"
                  class="group relative cursor-pointer flex items-center gap-3 rounded-lg px-3 transition-all duration-200 hover:translate-x-1 hover:shadow-md hover:brightness-110 bg-[var(--color-midlight)]"
                  :class="colIdx * TILES_PER_COLUMN + rowIdx === focusedTileIndex ? 'ring-4 ring-[var(--color-info)] translate-x-1 shadow-md' : ''"
                  :style="{ width: '70mm', height: '15mm' }"
                  @click="focusedTileIndex = colIdx * TILES_PER_COLUMN + rowIdx; openModule(tile.id)"
                >
                  <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-black/5 text-lg">
                    {{ tile.icon }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="text-2xl font-normal truncate text-[var(--color-text)]">{{ tile.name }}</div>
                    <div class="text-[9px] truncate text-[var(--color-text)] opacity-60">{{ tile.desc }}</div>
                  </div>
                </div>
              </div>
            </div>
            <template v-for="bucket in BUCKETS" :key="bucket.id">
              <div v-if="!isTileAccessMode && tilesInBucket(bucket.id).length > 0">
                <!-- Bucket Label -->
                <div class="mb-1.5 flex items-center gap-2">
                  <span class="text-[9px] font-black uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{{ bucket.label }}</span>
                  <div class="h-px flex-1 bg-[var(--color-border)]"></div>
                </div>
                <!-- Tile Grid -->
                <div class="grid grid-cols-3 gap-2">
                  <div
                    v-for="tile in tilesInBucket(bucket.id)"
                    :key="tile.id"
                    :id="'wb-tile-' + getTileIndex(tile.id)"
                    class="group relative cursor-pointer flex items-center gap-3 rounded-lg px-3 transition-all duration-200 hover:translate-x-1 hover:shadow-md hover:brightness-110 bg-[var(--color-midlight)]"
                    :class="getTileIndex(tile.id) === focusedTileIndex ? 'ring-4 ring-[var(--color-info)] translate-x-1 shadow-md' : ''"
                    :style="{ width: '70mm', height: '15mm' }"
                    @click="focusedTileIndex = getTileIndex(tile.id); openModule(tile.id)"
                  >
                    <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-black/5 text-lg">
                      {{ tile.icon }}
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="text-2xl font-normal truncate text-[var(--color-text)]">{{ tile.name }}</div>
                      <div class="text-[9px] truncate text-[var(--color-text)] opacity-60">{{ tile.desc }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </template>
            <div v-if="filteredTiles.length === 0" class="flex flex-col items-center justify-center py-16 text-center w-[70mm] md:w-[144mm] lg:w-[218mm] bg-[var(--color-surface-raised)] rounded-3xl border border-[var(--color-border)] shadow-md">
              <div class="text-4xl mb-3">🔍</div>
              <h3 class="text-base font-bold text-[var(--color-text)]">No Matching Tiles</h3>
              <p class="mt-1 text-xs text-[var(--color-text-muted)] max-w-xs">No tiles match "{{ searchQuery }}". Try another search.</p>
            </div>
          </div>

        <!-- Right Column: Clock & MQTT Widgets -->
        <div class="flex-shrink-0 flex flex-col gap-4 w-[280px]">

          <!-- Clock -->
          <div class="flex flex-col items-center gap-1 pt-2 bg-[var(--color-surface)] p-6 rounded-3xl border border-[var(--color-border)] backdrop-blur-sm shadow-xl">
            <div class="text-[15px] font-bold text-[var(--color-text-muted)] uppercase tracking-[0.2em]">{{ todayDate }}</div>
            <div class="text-lg font-black text-[var(--color-text)] uppercase tracking-wider mb-2 drop-shadow-sm">{{ todayDay }}</div>
            <AnalogueClock :abbr="customerAbbr" />
          </div>

          <!-- India Compliance API Credits Card -->
          <div v-if="isActualAdmin" class="bg-[var(--color-surface)] p-5 rounded-3xl border border-[var(--color-border)] shadow-xl flex flex-col gap-3">
            <div class="flex items-center justify-between border-b border-[var(--color-border)]/50 pb-2">
              <span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-[0.15em]">GST API Credits</span>
              <button
                @click.stop="fetchICCredits"
                :disabled="icCreditsLoading"
                class="rounded bg-[var(--color-surface-raised)] p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)] transition-colors disabled:opacity-50"
                title="Refresh Credits"
              >
                <svg class="h-3.5 w-3.5" :class="{'animate-spin text-[var(--color-info)]': icCreditsLoading}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </div>

            <div v-if="icCreditsLoading" class="py-4 flex flex-col items-center justify-center gap-1.5">
              <span class="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent inline-block"></span>
              <span class="text-xs text-[var(--color-text-muted)] font-medium">Loading credits...</span>
            </div>
            <div v-else-if="icCreditsError" class="py-2 text-center">
              <p class="text-xs font-bold text-[var(--color-danger)] leading-snug" :title="icCreditsError">{{ icCreditsError }}</p>
              <button @click="fetchICCredits" class="mt-1 text-[10px] font-bold text-[var(--color-info)] hover:underline">Try Again</button>
            </div>
            <div v-else class="text-xs space-y-1.5">
              <div class="flex justify-between items-baseline">
                <span class="text-[var(--color-text-muted)]">Available:</span>
                <span class="text-lg font-black text-[var(--color-info)] tracking-wide">{{ icCreditsBalance }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Used:</span>
                <span class="font-mono font-bold text-[var(--color-text)]">{{ icCreditsUsed }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Expiry:</span>
                <span class="font-bold text-[var(--color-text)]">{{ icCreditsExpiry || '—' }}</span>
              </div>
            </div>
          </div>

          <!-- MQTT Server Status -->
          <div class="bg-[var(--color-surface)] p-5 rounded-3xl border border-[var(--color-border)] shadow-xl flex flex-col gap-3">
            <div class="flex items-center justify-between border-b border-[var(--color-border)]/50 pb-2">
              <span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-[0.15em]">MQTT Server</span>
              <span class="flex items-center gap-1.5 text-xs font-bold">
                <span
                  class="h-2.5 w-2.5 rounded-full"
                  :class="isConnected ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)] animate-pulse' : 'bg-rose-500'"
                ></span>
                <span :class="isConnected ? 'text-emerald-500' : 'text-rose-500'">
                  {{ isConnected ? 'Connected' : 'Disconnected' }}
                </span>
              </span>
            </div>

            <div class="text-xs space-y-1">
              <div class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Broker:</span>
                <span class="font-mono font-bold text-[var(--color-text)] truncate max-w-[160px] text-right" :title="serverInfo.server">{{ serverInfo.server || 'N/A' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Port:</span>
                <span class="font-mono font-bold text-[var(--color-text)]">{{ serverInfo.port || 'N/A' }}</span>
              </div>
            </div>

            <!-- Manual reconnect button -->
            <button
              v-if="!isConnected"
              @click="handleMqttRefresh"
              :disabled="isConnecting"
              class="w-full flex items-center justify-center gap-2 rounded-xl bg-amber-600 hover:bg-amber-700 disabled:opacity-50 px-4 py-2.5 text-xs font-bold text-white transition active:scale-95 border border-amber-500 shadow-md focus:outline-none"
            >
              <span>{{ isConnecting ? '⏳ Connecting...' : '🔄 Reconnect MQTT' }}</span>
            </button>
          </div>

          <!-- Live Sync Status -->
          <div
            class="bg-[var(--color-surface)] p-5 rounded-3xl border shadow-xl flex flex-col gap-3 transition-all duration-500"
            :class="syncFlash ? 'border-emerald-500 shadow-emerald-500/20' : 'border-[var(--color-border)]'"
          >
            <div class="flex items-center justify-between border-b border-[var(--color-border)]/50 pb-2">
              <span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-[0.15em]">Live Sync</span>
              <span class="flex items-center gap-1.5 text-xs font-bold">
                <span
                  class="h-2.5 w-2.5 rounded-full"
                  :class="socketConnected ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)] animate-pulse' : 'bg-rose-500'"
                ></span>
                <span :class="socketConnected ? 'text-emerald-500' : 'text-rose-500'">
                  {{ socketConnected ? 'Connected' : 'Offline' }}
                </span>
              </span>
            </div>

            <div class="text-xs space-y-1.5">
              <div class="flex justify-between items-center">
                <span class="text-[var(--color-text-muted)]">Channel:</span>
                <span class="font-mono text-[var(--color-text)] font-bold">Item Cache</span>
              </div>
              <div class="flex justify-between items-start gap-2">
                <span class="text-[var(--color-text-muted)] shrink-0">Last Update:</span>
                <span class="font-mono text-right text-[var(--color-text)]">
                  {{ lastSyncTime || '—' }}
                </span>
              </div>
            </div>

            <!-- Flash banner on update -->
            <div
              v-if="syncFlash"
              class="flex items-center gap-2 rounded-xl bg-emerald-500/15 border border-emerald-500/30 px-3 py-2 text-xs font-bold text-emerald-500"
            >
              <span class="animate-bounce">↻</span>
              Items refreshed
            </div>
          </div>
        </div>
      </div>
    </div>

      <div v-else-if="currentTab === 'locked-bills' && userRole === 'admin'" class="px-10 py-8">
        <div class="mb-6 flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-[var(--color-text)]">Locked Bills</h2>
            <p class="text-xs text-[var(--color-text-muted)]">Manage sales invoices currently being edited by users</p>
          </div>
          <button
            @click="fetchLockedBills"
            :disabled="isLoadingLocked"
            class="flex items-center gap-2 rounded-xl bg-[var(--color-highlight)] hover:bg-[var(--color-highlight)]/90 px-4 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] transition active:scale-95 shadow-md disabled:opacity-50"
          >
            <span :class="{'animate-spin inline-block': isLoadingLocked}">🔄</span>
            <span>Refresh</span>
          </button>
        </div>

        <!-- Table Card -->
        <div class="overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl">
          <div v-if="isLoadingLocked" class="flex flex-col items-center justify-center py-16 gap-3">
            <div class="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-highlight)] border-t-transparent"></div>
            <div class="text-sm text-[var(--color-text-muted)] font-medium">Fetching locked bills...</div>
          </div>
          
          <div v-else-if="lockedBills.length === 0" class="flex flex-col items-center justify-center py-20 text-center">
            <div class="text-5xl mb-4">🔓</div>
            <h3 class="text-lg font-bold text-[var(--color-text)]">No Locked Bills</h3>
            <p class="mt-1 text-sm text-[var(--color-text-muted)] max-w-sm">There are no invoices currently locked for editing by any user.</p>
          </div>

          <div v-else class="overflow-x-auto">
            <table class="w-full border-collapse text-left text-sm text-[var(--color-text)]">
              <thead>
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-6 py-4">Bill No</th>
                  <th class="px-6 py-4">Username</th>
                  <th class="px-6 py-4">Full Name</th>
                  <th class="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr
                  v-for="bill in lockedBills"
                  :key="bill.bill_no"
                  class="hover:bg-[var(--color-midlight)]/40 transition-colors"
                >
                  <td class="whitespace-nowrap px-6 py-4 font-mono font-bold text-[var(--color-highlight)] text-base">
                    {{ bill.bill_no }}
                  </td>
                  <td class="whitespace-nowrap px-6 py-4">
                    <span class="rounded bg-[var(--color-surface-raised)] px-2.5 py-1 text-xs font-mono text-[var(--color-text-muted)] border border-[var(--color-border)]">
                      {{ bill.username }}
                    </span>
                  </td>
                  <td class="whitespace-nowrap px-6 py-4 font-medium text-[var(--color-text)]">
                    {{ bill.fullname }}
                  </td>
                  <td class="whitespace-nowrap px-6 py-4 text-right">
                    <button
                      @click="handleForceUnlock(bill.bill_no)"
                      class="inline-flex items-center gap-1.5 rounded-xl border border-[var(--color-danger)]/30 bg-[var(--color-danger)]/10 px-3 py-1.5 text-xs font-bold text-[var(--color-danger)] hover:bg-[var(--color-danger)] hover:text-white transition active:scale-95 shadow-sm"
                    >
                      🔓 Force Unlock
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="mx-auto max-w-4xl px-6 pb-12">
      </div>
    </main>

    <!-- ===================== GENERAL SETTINGS DIALOG ===================== -->
    <GeneralSettings
      ref="generalSettingsRef"
      :show="showGeneralSettings"
      @close="showGeneralSettings = false"
    />

    <!-- SYSTEM PERFORMANCE -->
    <SystemPerformance
      :show="showSystemPerformance"
      @close="showSystemPerformance = false"
    />

    <!-- LICENSE DETAILS -->
    <LicenseDetails
      :show="showLicenseDetails"
      @close="showLicenseDetails = false"
    />



    <!-- SUCCESS POPUP -->
     
    <!-- ===================== LICENSE OVERLAY ===================== -->
    <div
      v-if="isLicenseInvalid"
      class="fixed inset-0 z-[9999] flex items-center justify-center bg-[var(--color-bg)]/95 backdrop-blur-md px-6"
    >
      <div class="w-full max-w-md rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-2xl space-y-6">
        <div class="flex flex-col items-center text-center space-y-2">
          <div class="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-danger)]/10 text-3xl text-[var(--color-danger)]">
            🔒
          </div>
          <h2 class="text-xl font-bold text-[var(--color-text)]">
            {{ licenseInfo?.days_remaining < 0 ? 'Software License Expired' : 'License Activation Required' }}
          </h2>
          <p class="text-xs text-[var(--color-text-muted)] max-w-sm">
            {{ licenseInfo?.message || 'A valid license file is required to use this software features.' }}
          </p>
        </div>

        <!-- License Details Card -->
        <div v-if="licenseInfo && licenseInfo.site" class="rounded-xl bg-[var(--color-surface-raised)] p-4 text-xs space-y-2">
          <div class="flex justify-between">
            <span class="text-[var(--color-text-muted)]">Licensed Site</span>
            <span class="font-bold text-[var(--color-text)] text-right">{{ licenseInfo.site }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-[var(--color-text-muted)]">Expiry Date</span>
            <span class="font-semibold text-[var(--color-text)]">{{ licenseInfo.expiry_date }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-[var(--color-text-muted)]">Remaining Days</span>
            <span class="font-bold" :class="licenseInfo.days_remaining < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-warning)]'">
              {{ licenseInfo.days_remaining }} days
            </span>
          </div>
        </div>

        <!-- Instructions -->
        <div class="text-[11px] text-[var(--color-text-muted)] leading-relaxed bg-[var(--color-surface-raised)]/50 p-3 rounded-lg border border-[var(--color-border)]/50">
          <span class="font-bold text-[var(--color-text)]">Deployment Instructions:</span>
          <ol class="list-decimal pl-4 mt-1 space-y-1">
            <li>Generate a valid signed <code class="bg-[var(--color-surface-raised)] px-1 rounded">license.json</code> file.</li>
            <li>Place the file on the server in your site directory:<br/><code class="bg-[var(--color-surface-raised)] px-1 rounded block mt-0.5 truncate font-mono">sites/{{ licenseInfo?.site ? licenseInfo.site : '"site name"' }}/license.json</code></li>
            <li>Click "Re-verify License" below.</li>
          </ol>
        </div>

        <div class="flex gap-3">
          <button
            @click="handleLogout"
            class="flex-1 rounded-xl bg-[var(--color-surface-raised)] hover:bg-[var(--color-midlight)] border border-[var(--color-border)] py-2.5 text-sm font-semibold text-[var(--color-text)] transition active:scale-95 cursor-pointer"
          >
            Logout
          </button>
          <button
            @click="syncSettings"
            class="flex-1 rounded-xl bg-[var(--color-highlight)] hover:bg-[var(--color-highlight)]/90 py-2.5 text-sm font-semibold text-[var(--color-text-on-highlight)] transition active:scale-95 shadow-lg shadow-[var(--color-highlight)]/15 cursor-pointer"
          >
            Re-verify License
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { session } from '../session'
import { dashboardApi } from '../services/dashboard'
import GeneralSettings from '../components/GeneralSettings.vue'
import SystemPerformance from '../components/SystemPerformance.vue'
import LicenseDetails from '../components/LicenseDetails.vue'
import AnalogueClock from '../components/AnalogueClock.vue'

import { fetchAllowedTiles, frappeGet, frappePost } from '../api.js'
import { useItemCache } from '../services/itemCache.js'
import { syncNamingSeries } from '../services/seriesCache.js'
import { useLedgerCache } from '../services/ledgerCache.js'
import { useShortcuts, isSubwindowActive } from '../services/shortcutManager'
import { canAccessTile, canAccessRoute, getUserRole } from '../composables/usePermission'
import { dashboardShortcuts } from '../shortcuts/dashboardShortcuts'
import { useTheme } from '../composables/useTheme'
import { useMqtt } from '../composables/useMqtt'
import { getFrappeSocket } from '../services/frappeSocket'
import { APP_VERSION, APP_UPDATED } from '../version'

const router = useRouter()

const { isConnected, isConnecting, serverInfo, refreshConnection, checkStatus } = useMqtt()

async function handleMqttRefresh() {
  await refreshConnection()
}

// ==================== LIVE SYNC INDICATOR ====================
const socketConnected = ref(false)
const lastSyncTime = ref('')
const syncFlash = ref(false)
let _flashTimer = null

function _onSocketConnect() { socketConnected.value = true }
function _onSocketDisconnect() { socketConnected.value = false }
function _onItemCacheUpdated() {
  lastSyncTime.value = new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit' })
  syncFlash.value = true
  clearTimeout(_flashTimer)
  _flashTimer = setTimeout(() => { syncFlash.value = false }, 3000)
}

const isFullscreen = ref(false)

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
      .then(() => {
        isFullscreen.value = true
      })
      .catch((err) => {
        console.error(`Error enabling fullscreen: ${err.message}`)
      })
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}




const { items: cachedItems, lastSync: itemsLastSync, refreshItemCache, refreshDiscountRuleCache } = useItemCache()
const { ledgers: cachedLedgers, lastSync: ledgersLastSync, refreshLedgerCache } = useLedgerCache()

// ==================== PERMISSIONS & ROLES ====================
const permissionTrigger = ref(0)
const userRole = computed(() => {
  permissionTrigger.value
  return getUserRole()
})
const isActualAdmin = computed(() => ['Administrator', 'admin'].includes(session.user.value))

// ==================== THEME ====================
const { theme, toggleTheme } = useTheme()

function handleToggleTheme() {
  toggleTheme()
}

function handleOpenGstValidator() {
  window.dispatchEvent(new CustomEvent('wb-open-gst-validator'))
}

// ==================== INDIA COMPLIANCE API CREDITS ====================
const icCreditsLoading = ref(false)
const icCreditsError = ref('')
const icCreditsBalance = ref('')
const icCreditsUsed = ref('0')
const icCreditsExpiry = ref('')

async function fetchICCredits() {
  if (!isActualAdmin.value) return
  icCreditsLoading.value = true
  icCreditsError.value = ''
  try {
    const res = await frappeGet('ssplbilling.api.dashboard_api.get_ic_api_credits')
    if (res && res.success && res.data) {
      const data = res.data
      if (data.total_credits === -1) {
        icCreditsBalance.value = 'Unlimited'
      } else {
        const bal = data.balance_credits ?? 0
        icCreditsBalance.value = bal.toLocaleString('en-IN')
      }
      const used = data.used_credits ?? 0
      icCreditsUsed.value = used.toLocaleString('en-IN')

      if (data.expiry_date) {
        try {
          const parts = data.expiry_date.split('-')
          if (parts.length === 3) {
            icCreditsExpiry.value = `${parts[2]}-${parts[1]}-${parts[0]}`
          } else {
            icCreditsExpiry.value = data.expiry_date
          }
        } catch (_) {
          icCreditsExpiry.value = data.expiry_date
        }
      } else {
        icCreditsExpiry.value = ''
      }
    } else {
      icCreditsError.value = res?.error || 'Failed to fetch credits'
    }
  } catch (err) {
    icCreditsError.value = err.message || 'Error fetching credits'
  } finally {
    icCreditsLoading.value = false
  }
}

// ==================== USER ====================
const userInitials = computed(() => {
  const name = String(session.fullName.value || session.user.value || 'U')
  return name.split(' ').map(w => w[0] || '').join('').toUpperCase().slice(0, 2) || 'U'
})

const selectedUser = ref(localStorage.getItem('wb-inherited-user') || session.user.value)
const allUsers = ref([])
const inheritSettingsSelectRef = ref(null)
const isInheritDropdownOpen = ref(false)
const focusedUserIndex = ref(-1)
const inheritDropdownRef = ref(null)

const inheritUsersOptions = computed(() => {
  const options = [{ value: session.user.value, label: `Me (${session.fullName.value || session.user.value})` }]
  if (Array.isArray(allUsers.value)) {
    allUsers.value.forEach(u => {
      if (u.value !== session.user.value) {
        options.push(u)
      }
    })
  }
  return options
})

const selectedUserLabel = computed(() => {
  const match = inheritUsersOptions.value.find(u => u.value === selectedUser.value)
  return match ? match.label : selectedUser.value
})

const selectedUserDisplayName = computed(() => {
  if (selectedUser.value === session.user.value) {
    return session.fullName.value || session.user.value
  }
  const match = inheritUsersOptions.value.find(u => u.value === selectedUser.value)
  return match ? match.label : selectedUser.value
})

function toggleInheritDropdown() {
  if (isInheritDropdownOpen.value) {
    closeInheritDropdown()
  } else {
    isInheritDropdownOpen.value = true
    const idx = inheritUsersOptions.value.findIndex(o => o.value === selectedUser.value)
    focusedUserIndex.value = idx >= 0 ? idx : 0
    scrollToFocusedUser()
  }
}

function closeInheritDropdown() {
  isInheritDropdownOpen.value = false
}

function selectUserOption(val) {
  selectedUser.value = val
  closeInheritDropdown()
  handleUserChange()
}

function scrollToFocusedUser() {
  nextTick(() => {
    const el = document.getElementById('wb-user-opt-' + focusedUserIndex.value)
    if (el) {
      el.scrollIntoView({ block: 'nearest' })
    }
  })
}

function handleClickOutside(e) {
  if (inheritDropdownRef.value && !inheritDropdownRef.value.contains(e.target)) {
    closeInheritDropdown()
  }
}

async function handleUserChange() {
  if (selectedUser.value === session.user.value) {
    localStorage.removeItem('wb-inherited-user')
  } else {
    localStorage.setItem('wb-inherited-user', selectedUser.value)
  }
  await syncSettings()
  permissionTrigger.value++
  window.location.reload()
}

async function handleLogout() {
  localStorage.removeItem('wb-inherited-user')
  localStorage.removeItem(TILE_CACHE_KEY)
  await session.logout()
  router.push('/login')
}

// ==================== DATE ====================
const now = ref(new Date())
let timeInterval = null

const todayDate = computed(() => {
  return now.value.toLocaleDateString('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  })
})

const todayDay = computed(() => {
  return now.value.toLocaleDateString('en-IN', {
    timeZone: 'Asia/Kolkata',
    weekday: 'long'
  })
})


// ==================== TILES ====================

const BUCKETS = [
  { id: 'sale',     label: 'Sale' },
  { id: 'purchase', label: 'Purchase' },
  { id: 'stock',    label: 'Stock' },
  { id: 'accounts', label: 'Accounts' },
  { id: 'ledger',   label: 'Ledger View' },
  { id: 'sspl',     label: 'SSPL Special' },
  { id: 'report',   label: 'Report' },
]

const allTiles = [
  // ── Sale ──
  { id: 'sales',              bucket: 'sale',     name: 'Sales Invoice',         desc: 'Create sales invoices',                    icon: '🧾', shortcut: ''  },
  { id: 'quotation',          bucket: 'sale',     name: 'Quotation',             desc: 'Create quotations',                        icon: '📄', shortcut: 'Shift+F10' },
  { id: 'cashier',            bucket: 'sale',     name: 'Cashier Desk',          desc: 'Modern payment desk',                      icon: '🏧', shortcut: 'Shift+F5'  },
  { id: 'sales-order',        bucket: 'sale',     name: 'Sales Order',           desc: 'Create & manage sales orders',             icon: '📝', shortcut: ''    },
  { id: 'Cashier-Management', bucket: 'sale',     name: 'Cashier Management',    desc: 'Daily reconciliation & denominations',     icon: '📓', shortcut: ''    },
  { id: 'cancellation',       bucket: 'sale',     name: 'Cancellation',          desc: 'Cancel & amend submitted bills',           icon: '🚫', shortcut: ''    },
  // ── Purchase ──
  { id: 'purchase-invoice',   bucket: 'purchase', name: 'Purchase Invoice',      desc: 'Fast purchase invoice entry',              icon: '🧾', shortcut: ''    },
  { id: 'purchase-order',     bucket: 'purchase', name: 'Purchase Order',        desc: 'Create & manage purchase orders',          icon: '📋', shortcut: 'Shift+F7'  },
  { id: 'purchase-submit',    bucket: 'purchase', name: 'Purchase Desk',         desc: 'Confirm & submit purchases',               icon: '📥', shortcut: 'Shift+F4'  },
  // ── Stock ──
  { id: 'stock-reconciliation', bucket: 'stock',  name: 'Stock Reconciliation',  desc: 'Adjust stock levels',                      icon: '⚖️', shortcut: ''    },
  { id: 'store-transfer',     bucket: 'stock',  name: 'Store Transfer',        desc: 'Transfer stock between warehouses',        icon: '🔄', shortcut: 'Shift+F9'  },
  { id: 'repack',             bucket: 'stock',  name: 'Repack Entry',          desc: 'Repack raw items into finished goods',     icon: '📦', shortcut: ''    },
  { id: 'land-cost-voucher',  bucket: 'stock',  name: 'Landed Cost Voucher',   desc: 'Distribute landed/transport charges to items', icon: '⚓', shortcut: ''    },
  // ── Accounts ──
  { id: 'expense',            bucket: 'accounts', name: 'Cash Box Entry',        desc: 'Manage company expenses',                  icon: '💸', shortcut: ''  },
  { id: 'single-entry',       bucket: 'accounts', name: 'Single Entry',          desc: 'Manage single payment entries',            icon: '🧾', shortcut: ''    },
  { id: 'payment',            bucket: 'accounts', name: 'Payment Receipt',       desc: 'Accounts payment & receipt entry',         icon: '💸', shortcut: 'Shift+F3'  },
  { id: 'unreconciled',       bucket: 'accounts', name: 'Unreconciled Entries',  desc: 'View and reconcile ledger entries',        icon: '🔗', shortcut: ''    },
  { id: 'payment-reconciliation', bucket: 'accounts', name: 'Payment Reconciliation', desc: 'Link payments to invoices', icon: '🤝', shortcut: '' },
  { id: 'journal-contra',     bucket: 'accounts', name: 'Journal Contra',        desc: 'General ledger entries',                   icon: '📒', shortcut: 'Shift+F8'  },
  { id: 'cheques',            bucket: 'accounts', name: 'Cheque Register',       desc: 'Track & settle cheques on clearance',      icon: '🏦', shortcut: ''    },
  { id: 'outstanding-bills',  bucket: 'accounts', name: 'Outstanding',           desc: 'View party outstanding bills',             icon: '📋', shortcut: ''    },
  { id: 'account-tree',       bucket: 'accounts', name: 'Chart of Accounts',     desc: 'Browse the account tree',                  icon: '🌳', shortcut: ''    },
  // ── Ledger View ──
  { id: 'stock-ledger',       bucket: 'ledger',   name: 'Stock',                 desc: 'View stock movement by item',              icon: '📦', shortcut: ''    },
  { id: 'ledger',             bucket: 'ledger',   name: 'Customer Ledger',       desc: 'View customer account history',            icon: '📋', shortcut: 'Shift+F6'  },
  { id: 'gst-ledger',         bucket: 'ledger',   name: 'GST Ledger',            desc: 'View GST Quotation ledger',                icon: '📜', shortcut: ''    },
  { id: 'incentive-ledger',   bucket: 'ledger',   name: 'Incentive Ledger',      desc: 'View employee incentives',                 icon: '🏆', shortcut: ''    },
  { id: 'incentive-redeem',   bucket: 'accounts', name: 'Incentive Redeem',      desc: 'Redeem points for cash',                   icon: '🎁', shortcut: ''    },
  { id: 'incentive-entry',    bucket: 'accounts', name: 'Incentive Entry',       desc: 'Create invoice incentive entries',         icon: '🏆', shortcut: ''    },
  { id: 'general-ledger',    bucket: 'ledger',   name: 'General Ledger',        desc: 'GL ledger via ERPNext report engine',       icon: '📒', shortcut: ''    },
  // ── SSPL Special ──
  { id: 'loading-receipt',    bucket: 'sspl',     name: 'Loading Receipt',       desc: 'Generate loading receipts',                icon: '🚚', shortcut: ''    },
  { id: 'customer-enquiry',   bucket: 'sspl',     name: 'Customer Enquiry',      desc: 'Track customer item enquiries',            icon: '📞', shortcut: ''    },
  { id: 'parcel-address',     bucket: 'sspl',     name: 'Parcel Address',        desc: 'Manage parcel addresses',                  icon: '📦', shortcut: ''    },
  { id: 'gst-dummy-ledger',   bucket: 'sspl',     name: 'WGB PAYMENTS',          desc: 'Manage WGB payment entries',               icon: '📖', shortcut: ''    },
  { id: 'pricing-rules',      bucket: 'sspl',     name: 'Discount Rules',        desc: 'Manage discount rules and tiers',          icon: '🏷️', shortcut: ''    },
  { id: 'naming-settings',    bucket: 'sspl',   name: 'Naming Settings',       desc: 'Configure document series',                icon: '🔢', shortcut: ''    },
  { id: 'barcode-print',      bucket: 'sspl',   name: 'Print Barcodes',        desc: 'Print item barcodes',                      icon: '🔖', shortcut: ''    },
  { id: 'catelogue',          bucket: 'sspl',   name: 'Catalogues',            desc: 'View published catalogues',                icon: '📖', shortcut: ''    },

  // ── Report ──
  { id: 'daily-report',       bucket: 'report',   name: 'Daily Report',          desc: 'Daily operations summary',                 icon: '📊', shortcut: ''    },
  { id: 'reports',            bucket: 'report',   name: 'Reports',               desc: 'Business reports and analytics',           icon: '📈', shortcut: ''    },
]

// Per-user/group tile selection from SSPL Dashboard Tile Access.
// null = no record configured → fall back to role-based canAccessTile.
// Cached in localStorage with TTL (same policy as billing settings) so login /
// dashboard reloads within the window don't refetch. Cache is keyed to the
// resolved user, so switching the inherited user invalidates it automatically.
// v3: v2 caches hold the pre-ordering (alphabetical) tile list — key bump forces a refetch
const TILE_CACHE_KEY = 'wb-allowed-tiles-v3'
const TILE_CACHE_TTL = 30 * 60 * 1000 // 30 mins

function readTileCache() {
  try { return JSON.parse(localStorage.getItem(TILE_CACHE_KEY) || 'null') } catch { return null }
}

localStorage.removeItem('wb-allowed-tiles')    // drop pre-TTL cache key
localStorage.removeItem('wb-allowed-tiles-v2') // drop pre-ordering cache key
const _tileCache = readTileCache()
const allowedTileIds = ref(_tileCache && _tileCache.user === selectedUser.value ? _tileCache.tiles : null)

async function loadAllowedTiles(user = null, force = false) {
  const cacheUser = user || session.user.value
  const cached = readTileCache()
  if (!force && cached && cached.user === cacheUser && (Date.now() - cached.ts) < TILE_CACHE_TTL) {
    allowedTileIds.value = cached.tiles
    return
  }
  try {
    // Resolve for the inherited user; server falls back to the logged-in user
    const res = await fetchAllowedTiles(user)
    allowedTileIds.value = res?.configured ? res.tiles : null
    localStorage.setItem(TILE_CACHE_KEY, JSON.stringify({ user: cacheUser, tiles: allowedTileIds.value, ts: Date.now() }))
  } catch (e) {
    console.warn('[Dashboard] fetchAllowedTiles failed:', e)
  }
}

const tiles = computed(() => {
  permissionTrigger.value
  if (Array.isArray(allowedTileIds.value)) {
    // Render in the order configured in SSPL Dashboard Tile Access
    const byId = new Map(allTiles.map(t => [t.id, t]))
    const unknown = allowedTileIds.value.filter(id => !byId.has(id))
    if (unknown.length) {
      console.warn(
        '[Dashboard] SSPL Dashboard Tile Access grants tile ids unknown to this build '
        + '(check tile_id spelling/case, or the deployed frontend is outdated):', unknown
      )
    }
    return allowedTileIds.value.map(id => byId.get(id)).filter(Boolean)
  }
  return allTiles.filter(t => canAccessTile(t.id))
})

// ── Column tile table + ↑/↓/Enter navigation (only when tiles are doctype-configured) ──
const isTileAccessMode = computed(() => Array.isArray(allowedTileIds.value))
const focusedTileIndex = ref(0)

const searchInputRef = ref(null)
const searchQuery = ref('')

const filteredTiles = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) {
    return tiles.value
  }
  const terms = query.split(/[^a-z0-9]+/).filter(Boolean)
  if (terms.length === 0) {
    return tiles.value
  }
  return tiles.value.filter(tile => {
    const nameWords = tile.name.toLowerCase().split(/[^a-z0-9]+/).filter(Boolean)
    const descWords = tile.desc.toLowerCase().split(/[^a-z0-9]+/).filter(Boolean)
    const allWords = [...nameWords, ...descWords]
    return terms.every(term => allWords.some(word => word.startsWith(term)))
  })
})

function getTileIndex(tileId) {
  return filteredTiles.value.findIndex(t => t.id === tileId)
}

function focusSearch() {
  nextTick(() => {
    if (searchInputRef.value) {
      searchInputRef.value.focus()
      searchInputRef.value.select()
    }
  })
}

watch(searchQuery, () => {
  focusedTileIndex.value = 0
})

// 10 tiles per column; overflow flows into the next column
const TILES_PER_COLUMN = 10
const tileColumns = computed(() => {
  const cols = []
  for (let i = 0; i < filteredTiles.value.length; i += TILES_PER_COLUMN) {
    cols.push(filteredTiles.value.slice(i, i + TILES_PER_COLUMN))
  }
  return cols
})

function handleTileKeyNav(e) {
  if (currentTab.value !== 'dashboard' || showGeneralSettings.value || showSystemPerformance.value) return
  // This is a raw window listener the shortcut manager can't suppress — bail out
  // whenever a subwindow overlay (global item search, price update, etc.) is open,
  // otherwise its Enter/F4 handling operates the tile grid / inherit dropdown blind
  if (isSubwindowActive()) return

  if (e.key === 'F4' && !e.shiftKey) {
    if (isActualAdmin.value) {
      e.preventDefault()
      toggleInheritDropdown()
      return
    }
  }

  if (isInheritDropdownOpen.value) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      focusedUserIndex.value = (focusedUserIndex.value + 1) % inheritUsersOptions.value.length
      scrollToFocusedUser()
      return
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      focusedUserIndex.value = (focusedUserIndex.value - 1 + inheritUsersOptions.value.length) % inheritUsersOptions.value.length
      scrollToFocusedUser()
      return
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const opt = inheritUsersOptions.value[focusedUserIndex.value]
      if (opt) {
        selectUserOption(opt.value)
      }
      return
    } else if (e.key === 'Escape') {
      e.preventDefault()
      closeInheritDropdown()
      return
    }
    // Block standard keys when dropdown is open
    const tag = e.target?.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || e.target?.isContentEditable) return
    if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault()
      return
    }
  }
  
  const tag = e.target?.tagName
  const isSearchInput = e.target === searchInputRef.value
  
  if (!isSearchInput && (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || e.target?.isContentEditable)) return
  
  // If the user types a character key anywhere, focus search box and type it
  if (!isSearchInput && e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey && e.key !== '/') {
    e.preventDefault()
    searchQuery.value += e.key
    nextTick(() => {
      if (searchInputRef.value) {
        searchInputRef.value.focus()
        const len = searchQuery.value.length
        searchInputRef.value.setSelectionRange(len, len)
      }
    })
    return
  }

  // Handle global search control keys before checking count/matches
  if (e.key === 'Escape') {
    if (isSearchInput && searchQuery.value) {
      e.preventDefault()
      searchQuery.value = ''
      return
    }
  } else if (e.key === 'Delete' || (e.key === 'Backspace' && !isSearchInput)) {
    if (searchQuery.value) {
      e.preventDefault()
      searchQuery.value = ''
      focusSearch()
      return
    }
  } else if (e.key === '/') {
    if (!isSearchInput) {
      e.preventDefault()
      focusSearch()
      return
    }
  }

  const count = filteredTiles.value.length
  if (!count) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    focusedTileIndex.value = (focusedTileIndex.value + 1) % count
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    focusedTileIndex.value = (focusedTileIndex.value - 1 + count) % count
  } else if (e.key === 'ArrowRight') {
    if (!isSearchInput) {
      e.preventDefault()
      if (isTileAccessMode.value) {
        if (focusedTileIndex.value + TILES_PER_COLUMN < count) {
          focusedTileIndex.value += TILES_PER_COLUMN
        }
      } else {
        focusedTileIndex.value = (focusedTileIndex.value + 1) % count
      }
    }
  } else if (e.key === 'ArrowLeft') {
    if (!isSearchInput) {
      e.preventDefault()
      if (isTileAccessMode.value) {
        if (focusedTileIndex.value - TILES_PER_COLUMN >= 0) {
          focusedTileIndex.value -= TILES_PER_COLUMN
        }
      } else {
        focusedTileIndex.value = (focusedTileIndex.value - 1 + count) % count
      }
    }
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const tile = filteredTiles.value[focusedTileIndex.value]
    if (tile) openModule(tile.id)
  }
}

watch(focusedTileIndex, (idx) => {
  nextTick(() => document.getElementById('wb-tile-' + idx)?.scrollIntoView({ block: 'nearest' }))
})
watch(() => filteredTiles.value.length, (count) => {
  if (focusedTileIndex.value >= count) focusedTileIndex.value = 0
})

function tilesInBucket(bucketId) {
  return filteredTiles.value.filter(t => t.bucket === bucketId)
}

const readyModules = ['sales', 'quotation', 'purchase-invoice', 'cashier', 'purchase-submit', 'ledger', 'purchase-order', 'sales-order', 'journal-contra', 'stock-reconciliation', 'reports', 'gst-dummy-ledger', 'gst-ledger', 'pricing-rules', 'barcode-print', 'incentive-ledger', 'incentive-redeem', 'incentive-entry', 'loading-receipt', 'daily-report', 'parcel-address', 'stock-ledger', 'general-ledger', 'single-entry', 'cancellation', 'naming-settings', 'expense', 'payment-reconciliation', 'repack', 'offer-display', 'catelogue', 'unreconciled', 'cheques', 'land-cost-voucher', 'account-tree']

// payment/receipt/journal/contra are aliases into the PaymentReceiptEntry page
const routeAliases = {
  sales: '/sales',
  quotation: '/quotation',
  repack: '/repack',
  'land-cost-voucher': '/land-cost-voucher',
  'offer-display': '/offer-display',
  'purchase-invoice': '/purchase-invoice',
  payment: '/payment',
  expense: '/expense',
  'purchase-order': '/purchase-order',
  'sales-order': '/sales-order',
  'journal-contra': '/journal-contra',
  'stock-reconciliation': '/stock-reconciliation',
  'gst-dummy-ledger': '/gst-dummy-ledger',
  'gst-ledger': '/gst-ledger',
  'Cashier-Management': '/Cashier-Management',
  'pricing-rules': '/discount-rules',
  'barcode-print': '/barcode-print',
  'incentive-ledger': '/incentive-ledger',
  'incentive-redeem': '/incentive-redeem',
  'incentive-entry': '/incentive-entry',
  'loading-receipt': '/loading-receipt',
  'customer-enquiry': '/customer-enquiry',
  'daily-report': '/daily-report',
  'parcel-address': '/parcel-address',
  'store-transfer': '/store-transfer',
  'general-ledger': '/general-ledger',
  reports: '/reports',
  cancellation: '/cancellation',
  'naming-settings': '/naming-settings',
  catelogue: '/catelogue',
}

function openModule(id) {

  if (id === 'payment-reconciliation') {
    window.open('/app/payment-reconciliation', '_blank')
    return
  }
  if (id === 'stock-ledger') {
    window.dispatchEvent(new CustomEvent('wb-global-item-search'))
    return
  }
  if (id === 'outstanding-bills') {
    window.dispatchEvent(new CustomEvent('wb-global-ledger-search', { detail: { purpose: 'outstanding' } }))
    return
  }
  if (id === 'ledger') {
    window.dispatchEvent(new CustomEvent('wb-global-ledger-search', { detail: { purpose: 'ledger' } }))
    return
  }
  if (routeAliases[id]) {
    router.push(routeAliases[id])
  } else if (readyModules.includes(id)) {
    router.push('/' + id)
  } else {
    alert('Coming soon: ' + id)
  }
}

// ==================== KEYBOARD SHORTCUTS ====================
useShortcuts(dashboardShortcuts({
  openModule,
  handleEscape: () => {
    if (showGeneralSettings.value) { showGeneralSettings.value = false; return }

  }
}))

const availableSeries = ref([])
const userAllowedString = ref('')
const systemSettings = ref(null)

const SETTINGS_CACHE_KEY = 'wb-settings-v2'
const BILLING_SETTINGS_TTL = 30 * 60 * 1000 // 30 mins
const ALLOWED_SERIES_CACHE_KEY = 'wb-allowed-series-v1'
const OPENING_CASH_DATE_KEY = 'wb-opening-box-cash-date'
const GENERIC_CACHE_TTL = 30 * 60 * 1000 // 30 mins — series / naming series
const ITEM_CACHE_TTL = 5 * 60 * 1000 // 5 mins — items / ledgers freshness window



// ==================== SYSTEM PERFORMANCE ====================
const showSystemPerformance = ref(false)

// ==================== LICENSE DETAILS ====================
const showLicenseDetails = ref(false)

// ==================== GENERAL SETTINGS ====================
const showGeneralSettings = ref(false)
const generalSettingsRef = ref(null)
const isSyncing = ref(false)

// ==================== LOCKED BILLS MANAGEMENT ====================
const currentTab = ref('dashboard')
const lockedBills = ref([])
const isLoadingLocked = ref(false)

async function fetchLockedBills() {
  isLoadingLocked.value = true
  try {
    const res = await frappeGet('ssplbilling.api.salesinvoice_api.get_locked_bills')
    lockedBills.value = res || []
  } catch (err) {
    console.error('Failed to fetch locked bills:', err)
  } finally {
    isLoadingLocked.value = false
  }
}

async function handleForceUnlock(billNo) {
  if (!confirm(`Are you sure you want to force unlock bill ${billNo}?`)) return
  try {
    await frappePost('ssplbilling.api.salesinvoice_api.release_bill_edit', { bill_no: billNo })
    await fetchLockedBills()
  } catch (err) {
    console.error('Failed to release lock:', err)
    alert('Failed to release lock.')
  }
}

watch(currentTab, (newTab) => {
  if (newTab === 'locked-bills') {
    fetchLockedBills()
  } else if (newTab === 'dashboard') {
    focusSearch()
  }
})


// ==================== REDIS CACHE MANAGEMENT ====================
const isClearingRedis = ref(false)

async function handleClearRedisCache() {
  if (isClearingRedis.value) return
  isClearingRedis.value = true
  try {
    const res = await dashboardApi.clearDraftInvoiceCache()
    const resPur = await dashboardApi.clearDraftPurchaseCache()
    if (res?.status === 'success' && resPur?.status === 'success') {
      alert(`Success: Redis stock cache cleared & rebuilt successfully (${res.count} sales, ${resPur.count} purchase items cached).`)
      await refreshItemCache('Sales', null, defaultWarehouse.value || null)
    } else {
      alert('Failed to clear Redis cache: ' + (res?.message || resPur?.message || 'Unknown error'))
    }
  } catch (e) {
    console.error('[Dashboard] clearDraftInvoiceCache failed:', e)
    alert('Failed to clear Redis cache: ' + e.message)
  } finally {
    isClearingRedis.value = false
  }
}

async function handleFullSync() {
  if (isSyncing.value) return
  isSyncing.value = true
  try {
    await syncSettings()
    if (generalSettingsRef.value?.loadSettings) {
      await generalSettingsRef.value.loadSettings()
    }
    window.location.reload()
  } finally {
    isSyncing.value = false
  }
}

const defaultSeries = ref(localStorage.getItem('wb-series') || '')
const defaultWarehouse = ref(localStorage.getItem('wb-warehouse') || '')

async function syncSettings() {
  localStorage.removeItem(SETTINGS_CACHE_KEY)
  // force=true bypasses the series / opening-cash / naming-series caches too.
  await fetchSettings(selectedUser.value, true)
  await loadAllowedTiles(selectedUser.value !== session.user.value ? selectedUser.value : null, true)
  try {
    await refreshDiscountRuleCache()
  } catch (e) {
    console.warn('[Dashboard] refreshDiscountRuleCache failed:', e)
  }
}

// 1. Fetch allowed series for this user — cached per user with TTL.
//    Always rehydrate reactive state (even on cache hit) so a page reload
//    doesn't leave the series dropdown empty.
async function syncAllowedSeries(targetUser, force) {
  try {
    let d = null
    const cached = JSON.parse(localStorage.getItem(ALLOWED_SERIES_CACHE_KEY) || 'null')
    const cacheValid = !force && cached && cached.user === targetUser &&
      (Date.now() - cached.ts) < GENERIC_CACHE_TTL
    if (cacheValid) {
      d = cached.data
    } else {
      d = await dashboardApi.getAllowedSeries(targetUser)
      localStorage.setItem(ALLOWED_SERIES_CACHE_KEY, JSON.stringify({ data: d, user: targetUser, ts: Date.now() }))
    }
    availableSeries.value = d.allowed_series || []
    userAllowedString.value = d.user_allowed_string || ''
    if (availableSeries.value.length && !availableSeries.value.includes(defaultSeries.value)) {
      defaultSeries.value = availableSeries.value[0]
    }
  } catch (e) {
    console.warn('[Dashboard] getAllowedSeries failed:', e)
  }
}

// 2. Fetch global settings
async function syncBillingSettings(targetUser, force) {
  try {
    // Check cache first
    let settings = null
    const cached = JSON.parse(localStorage.getItem(SETTINGS_CACHE_KEY) || 'null')
    const cacheValid = !force && cached &&
      (Date.now() - cached.ts) < BILLING_SETTINGS_TTL &&
      cached.data?._current_user === targetUser
    if (cacheValid) {
      settings = cached.data
    } else {
      settings = await dashboardApi.getBillingSettings(targetUser)
      if (settings) {
        const settingsWithUser = { ...settings, _current_user: targetUser }
        localStorage.setItem(SETTINGS_CACHE_KEY, JSON.stringify({ data: settingsWithUser, ts: Date.now() }))
      }
    }
    
    systemSettings.value = settings
    // Sync user's zoom to localStorage so Sales Invoice can use it
    if (settings && settings.user_zoom) {
      localStorage.setItem('wb-zoom', settings.user_zoom)
    }
    if (settings && settings.wb_theme) {
      const t = settings.wb_theme.toLowerCase() === 'dark' ? 'dark' : 'light'
      localStorage.setItem('wb-theme', t)
      // Do not call applyTheme() here to avoid overwriting Session_Theme once logged in
    }
    if (settings && settings.cipher_map) {
      localStorage.setItem('wb-cipher', settings.cipher_map)
    }
    if (settings && settings.tax_paid_on_purchase) {
      localStorage.setItem('wb-tax-paid-on-purchase', settings.tax_paid_on_purchase)
    }
    if (settings && settings.discount_account) {
      localStorage.setItem('wb-discount-account', settings.discount_account)
    }
    if (settings && settings.short_or_excess_account) {
      localStorage.setItem('wb-short-or-excess-account', settings.short_or_excess_account)
    }

    // Sync roles to localStorage for permission inherited
    if (settings && settings.user_role) {
      const roles = settings.user_role
      localStorage.setItem('wb-role-admin', roles.admin ? '1' : '0')
      localStorage.setItem('wb-role-cashier', roles.cashier ? '1' : '0')
      localStorage.setItem('wb-role-biller', roles.biller ? '1' : '0')
      localStorage.setItem('wb-role-accounts', roles.accounts ? '1' : '0')
    }

    // Set billing defaults from the first visible series row
    const firstSeries = (settings?.billing_series || [])[0]
    if (firstSeries) {
      localStorage.setItem('wb-tax-type-incl', firstSeries.tax_type_incl ? '1' : '0')
    }

    // Sync printer settings to localStorage
    if (settings && settings.user_defaults) {
      const defaults = settings.user_defaults
      if (defaults.default_printer) localStorage.setItem('wb-printer', defaults.default_printer)
      if (defaults.warehouse) {
        localStorage.setItem('wb-warehouse', defaults.warehouse)
        defaultWarehouse.value = defaults.warehouse
      }
      if (defaults.cost_center) localStorage.setItem('wb-cost-center', defaults.cost_center)
      if (defaults.income_account) localStorage.setItem('wb-income-account', defaults.income_account)
      if (defaults.company) localStorage.setItem('wb-company', defaults.company)
    }

    // Printer & Template mapping from settings
    if (settings && settings.printer_settings) {
       localStorage.setItem('wb-printer-templates', JSON.stringify(settings.printer_settings))
    }

    // Sync Automatic Entries (single doctype) values to localStorage under ae-* keys
    if (settings && settings.automatic_entries) {
      const ae = settings.automatic_entries
      localStorage.setItem('ae-alternative_company', ae.alternative_company || '')
      localStorage.setItem('ae-warehouse', ae.warehouse || '')
      localStorage.setItem('ae_payment_series', ae.payment_entry_naming_settings || '')
      localStorage.setItem('ae-series', JSON.stringify(ae.series || []))
      localStorage.setItem('ae-accounts', JSON.stringify(ae.accounts || []))
    }

  } catch (e) {
    console.warn('[Dashboard] getBillingSettings failed:', e)
  }
}

// 2.5 Fetch license status from server
async function syncLicenseStatus() {
  try {
    const lic = await frappeGet('ssplbilling.api.license_api.get_license_status')
    localStorage.setItem('ae_license_info', JSON.stringify(lic))
    updateLicenseState()
  } catch (e) {
    console.warn('[Dashboard] get_license_status failed:', e)
  }
}

// 3. Sync today's opening box cash — refetch only once per calendar day
//    (date-keyed, NOT TTL: a stale value here would show yesterday's opening).
async function syncOpeningBoxCash(force) {
  try {
    const today = new Date().toLocaleDateString('en-CA')
    const haveToday = localStorage.getItem(OPENING_CASH_DATE_KEY) === today &&
      localStorage.getItem('wb-opening-box-cash') != null
    if (force || !haveToday) {
      const openingRes = await frappeGet('ssplbilling.api.cahierlog_api.get_opening_total', { date: today })
      if (openingRes) {
        const boxCash = String(openingRes.total || 0)
        localStorage.setItem('opening_cash', boxCash)
        localStorage.setItem('wb-opening-box-cash', boxCash)
        localStorage.setItem(OPENING_CASH_DATE_KEY, today)
      }
    }
  } catch (e) {
    console.warn('[Dashboard] opening box cash sync failed:', e)
  }
}

// 4. Fetch and store all naming series for the requested DocTypes.
//    Rarely changes → seriesCache refetches on TTL expiry or when any
//    wb-series-* key is missing/empty; consumers read those LS keys.
async function syncNamingSeriesStep(force) {
  try {
    await syncNamingSeries(force)
  } catch (e) {
    console.warn('[Dashboard] syncNamingSeries failed:', e)
  }
}

// 5. Fetch and store E-Way Bill threshold value
async function syncEwayThreshold() {
  try {
    const ewayVal = await frappeGet('ssplbilling.api.ewaybill_api.get_eway_threshold')
    const threshold = String(ewayVal || 0)
    localStorage.setItem('wb-eway-threshold', threshold)
    localStorage.setItem('wb-eway-threshould', threshold)
  } catch (e) {
    console.warn('[Dashboard] get_eway_threshold failed:', e)
  }
}

async function fetchSettings(user = null, force = false) {
  const targetUser = user || session.user.value
  await syncAllowedSeries(targetUser, force)
  await syncBillingSettings(targetUser, force)
  await syncLicenseStatus()
  await syncOpeningBoxCash(force)
  await syncNamingSeriesStep(force)
  await syncEwayThreshold()
}

const appVersion = ref(APP_VERSION)
const appUpdated = ref(APP_UPDATED)

const licenseInfo = ref(null)

const CLOCK_ABBR_STOPWORDS = new Set(['and', '&', 'of', 'the'])
const customerAbbr = computed(() => {
  // watch_text is an explicit, independently-settable field — takes priority
  // over auto-deriving an abbreviation from customer_name.
  const explicit = licenseInfo.value?.watch_text
  if (explicit) return explicit

  const name = licenseInfo.value?.customer_name
  if (!name) return 'CTR'
  const abbr = name
    .trim()
    .split(/\s+/)
    .filter((w) => w && !CLOCK_ABBR_STOPWORDS.has(w.toLowerCase()))
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 4)
  return abbr || 'CTR'
})

function updateLicenseState() {
  try {
    licenseInfo.value = JSON.parse(localStorage.getItem('ae_license_info') || 'null')
  } catch {
    licenseInfo.value = null
  }
}

const isLicenseInvalid = computed(() => {
  if (!licenseInfo.value) return false
  return !licenseInfo.value.valid || (licenseInfo.value.days_remaining != null && licenseInfo.value.days_remaining < 0)
})

const daysRemaining = computed(() => {
  if (licenseInfo.value && typeof licenseInfo.value.days_remaining === 'number') {
    return licenseInfo.value.days_remaining
  }
  return null
})

// No expiry_date on the license => unlimited. Otherwise: past 50 days remaining,
// show the actual expiry date; inside that window, show a day countdown instead.
const licenseStatusText = computed(() => {
  const info = licenseInfo.value
  if (!info || !info.valid) return null
  if (!info.expiry_date) return 'Unlimited'
  if (typeof info.days_remaining !== 'number') return null
  if (info.days_remaining > 50) return `valid till ${info.expiry_date}`
  return `${info.days_remaining} days left`
})

function handleNavigateHome() {
  router.push('/')
}

function cleanupOldKeys() {
  const keysToRemove = [
    'wb-general-settings-v1',
    'wb-general-settings-v2',
    'wb-billing-settings-v2'
  ]
  keysToRemove.forEach(k => localStorage.removeItem(k))
}

onMounted(async () => {
  updateLicenseState()
  cleanupOldKeys()
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('wb-navigate-home', handleNavigateHome)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  window.addEventListener('keydown', handleTileKeyNav)
  window.addEventListener('wb-item-cache-updated', _onItemCacheUpdated)
  focusSearch()

  const socket = getFrappeSocket()
  if (socket) {
    socketConnected.value = socket.connected
    socket.on('connect', _onSocketConnect)
    socket.on('disconnect', _onSocketDisconnect)
  }
  
  if (isActualAdmin.value) {
    try {
      allUsers.value = await dashboardApi.getAllUsers()
    } catch (e) {
      console.warn('[Dashboard] getAllUsers failed:', e)
    }
    fetchICCredits()
  }

  // Settings/series/opening-cash/naming-series: fetch only on cache miss/expiry (see fetchSettings)
  fetchSettings(selectedUser.value)
  // Per-user/group dashboard tile selection (SSPL Dashboard Tile Access),
  // resolved for the inherited settings user (falls back to logged-in user)
  loadAllowedTiles(selectedUser.value !== session.user.value ? selectedUser.value : null)
  // Items: skip if already cached this session and still fresh (WebSocket keeps stock live).
  // Seed warehouse-scoped (user's default warehouse) so per-warehouse stock is correct from
  // load and the first Ctrl+I in Sales Entry — same warehouse — needs no re-scope refetch.
  if (!cachedItems.value.length || (Date.now() - itemsLastSync.value) > ITEM_CACHE_TTL) {
    refreshItemCache('Sales', null, defaultWarehouse.value || null) // Preload items for fast entry
  }
  // Ledgers: hydrated from localStorage at module init; refresh only if empty or stale
  if (!cachedLedgers.value.length || (Date.now() - ledgersLastSync.value) > ITEM_CACHE_TTL) {
    refreshLedgerCache()      // Preload ledgers for fast search
  }
  // MQTT is live connection health — don't persist it; poll at most once per browser session
  if (!sessionStorage.getItem('wb-mqtt-checked')) {
    checkStatus()             // Retrieve MQTT server status once on load
    sessionStorage.setItem('wb-mqtt-checked', '1')
  }

  timeInterval = setInterval(() => {
    now.value = new Date()
  }, 1000)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('wb-navigate-home', handleNavigateHome)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  window.removeEventListener('keydown', handleTileKeyNav)
  window.removeEventListener('wb-item-cache-updated', _onItemCacheUpdated)
  clearTimeout(_flashTimer)

  const socket = getFrappeSocket()
  if (socket) {
    socket.off('connect', _onSocketConnect)
    socket.off('disconnect', _onSocketDisconnect)
  }
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})

</script>

<style scoped>
.pop-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.pop-leave-active {
  transition: all 0.2s ease-in;
}
.pop-enter-from {
  opacity: 0;
  transform: scale(0.9) translateY(20px);
}
.pop-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
