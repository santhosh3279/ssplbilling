<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- ===================== HRMS SIDEBAR ===================== -->
    <aside class="flex w-64 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg">
      <!-- Portal Brand -->
      <div class="border-b border-[var(--color-border)] px-6 py-5">
        <div class="text-xl font-black tracking-wider text-[var(--color-employee)] flex items-center gap-2">
          <span>👥</span> SSPL HRMS
        </div>
        <div class="mt-1 text-xs text-[var(--color-text-muted)] uppercase tracking-widest font-semibold">
          Workforce Hub
        </div>
      </div>

      <!-- Navigation Links -->
      <nav class="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        <button
          @click="activeSubTab = 'dashboard'"
          class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-bold transition-all duration-200"
          :class="activeSubTab === 'dashboard' ? 'bg-[var(--color-employee)] text-white shadow-lg shadow-[var(--color-employee)]/20' : 'hover:bg-[var(--color-midlight)] text-[var(--color-text)]'"
        >
          <span class="text-lg">📊</span> Dashboard
        </button>

        <button
          @click="router.push('/hrms/employee')"
          class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-bold transition-all duration-200 hover:bg-[var(--color-midlight)] text-[var(--color-text)]"
        >
          <span class="text-lg">👥</span> Employees
        </button>

        <button
          @click="activeSubTab = 'attendance'"
          class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-bold transition-all duration-200"
          :class="activeSubTab === 'attendance' ? 'bg-[var(--color-employee)] text-white shadow-lg shadow-[var(--color-employee)]/20' : 'hover:bg-[var(--color-midlight)] text-[var(--color-text)]'"
        >
          <span class="text-lg">📅</span> Attendance
        </button>

        <button
          @click="activeSubTab = 'payroll'"
          class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-bold transition-all duration-200"
          :class="activeSubTab === 'payroll' ? 'bg-[var(--color-employee)] text-white shadow-lg shadow-[var(--color-employee)]/20' : 'hover:bg-[var(--color-midlight)] text-[var(--color-text)]'"
        >
          <span class="text-lg">💸</span> Payroll & Salary
        </button>

        <button
          @click="activeSubTab = 'leave'"
          class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-bold transition-all duration-200"
          :class="activeSubTab === 'leave' ? 'bg-[var(--color-employee)] text-white shadow-lg shadow-[var(--color-employee)]/20' : 'hover:bg-[var(--color-midlight)] text-[var(--color-text)]'"
        >
          <span class="text-lg">✉️</span> Leave Tracker
        </button>
      </nav>

      <!-- Back to wholesale billing -->
      <div class="border-t border-[var(--color-border)] p-4">
        <button
          @click="router.push('/')"
          class="flex w-full items-center justify-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] py-3 text-xs font-bold hover:bg-[var(--color-midlight)] transition-all duration-200 active:scale-95 text-[var(--color-text)]"
        >
          ← Back to Billing
        </button>
      </div>
    </aside>

    <!-- ===================== MAIN HUB PANEL ===================== -->
    <main class="flex-1 overflow-y-auto bg-[var(--color-bg)] flex flex-col">
      <!-- Top header bar -->
      <header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 class="text-2xl font-black uppercase tracking-wider text-[var(--color-text)]">
            HRMS Dashboard
          </h1>
          <p class="text-xs text-[var(--color-text-muted)] font-medium">Manage workforce operations & employee database</p>
        </div>

        <div class="flex items-center gap-4">
          <div class="text-right">
            <div class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">{{ todayDate }}</div>
            <div class="text-sm font-extrabold text-[var(--color-employee)]">{{ todayDay }}</div>
          </div>
          <div class="h-10 w-10 rounded-xl bg-[var(--color-employee)]/15 border border-[var(--color-employee)]/30 flex items-center justify-center text-xl shadow-inner">
            💼
          </div>
        </div>
      </header>

      <!-- Portal Dashboard Content -->
      <div v-if="activeSubTab === 'dashboard'" class="flex-1 p-8 space-y-8">
        <!-- Stats Widgets -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div class="bg-[var(--color-surface)] p-6 rounded-2xl border border-[var(--color-border)] shadow-md flex items-center justify-between relative overflow-hidden group hover:shadow-xl transition-all duration-300">
            <div class="space-y-1 z-10">
              <span class="text-xs font-black uppercase tracking-wider text-[var(--color-text-muted)]">Active Employees</span>
              <h2 class="text-4xl font-black text-[var(--color-employee)]">{{ employeeCount }}</h2>
              <p class="text-[10px] text-emerald-500 font-bold">● Synchronized</p>
            </div>
            <span class="text-5xl opacity-25 group-hover:scale-110 transition-transform duration-300">👥</span>
          </div>

          <div class="bg-[var(--color-surface)] p-6 rounded-2xl border border-[var(--color-border)] shadow-md flex items-center justify-between relative overflow-hidden group hover:shadow-xl transition-all duration-300">
            <div class="space-y-1 z-10">
              <span class="text-xs font-black uppercase tracking-wider text-[var(--color-text-muted)]">Present Today</span>
              <h2 class="text-4xl font-black text-emerald-500">{{ presentCount }}<span class="text-base text-[var(--color-text-muted)]">/{{ employeeCount }}</span></h2>
              <p class="text-[10px] text-[var(--color-text-muted)] font-medium">92% Attendance rate</p>
            </div>
            <span class="text-5xl opacity-25 group-hover:scale-110 transition-transform duration-300">📅</span>
          </div>

          <div class="bg-[var(--color-surface)] p-6 rounded-2xl border border-[var(--color-border)] shadow-md flex items-center justify-between relative overflow-hidden group hover:shadow-xl transition-all duration-300">
            <div class="space-y-1 z-10">
              <span class="text-xs font-black uppercase tracking-wider text-[var(--color-text-muted)]">On Leave</span>
              <h2 class="text-4xl font-black text-[var(--color-warning)]">3</h2>
              <p class="text-[10px] text-[var(--color-text-muted)] font-medium">Planned leaves today</p>
            </div>
            <span class="text-5xl opacity-25 group-hover:scale-110 transition-transform duration-300">✉️</span>
          </div>

          <div class="bg-[var(--color-surface)] p-6 rounded-2xl border border-[var(--color-border)] shadow-md flex items-center justify-between relative overflow-hidden group hover:shadow-xl transition-all duration-300">
            <div class="space-y-1 z-10">
              <span class="text-xs font-black uppercase tracking-wider text-[var(--color-text-muted)]">Payroll (August)</span>
              <h2 class="text-4xl font-black text-[var(--color-info)]">92%</h2>
              <p class="text-[10px] text-[var(--color-success)] font-bold">Processed</p>
            </div>
            <span class="text-5xl opacity-25 group-hover:scale-110 transition-transform duration-300">💸</span>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <!-- Quick actions panel -->
          <div class="bg-[var(--color-surface)] p-6 rounded-2xl border border-[var(--color-border)] shadow-md flex flex-col">
            <h3 class="text-base font-bold uppercase tracking-wider text-[var(--color-text)] border-b border-[var(--color-border)] pb-3 mb-4">Quick Actions</h3>
            <div class="flex-1 flex flex-col gap-3 justify-center">
              <button
                @click="router.push('/hrms/employee')"
                class="flex items-center gap-3 rounded-xl bg-[var(--color-employee)]/10 border border-[var(--color-employee)]/30 p-4 hover:bg-[var(--color-employee)] hover:text-white transition-all duration-300 group active:scale-95"
              >
                <span class="text-2xl group-hover:scale-110 transition-transform duration-200">➕</span>
                <div class="text-left">
                  <div class="font-bold text-sm">Add New Employee</div>
                  <div class="text-[10px] text-[var(--color-text-muted)] group-hover:text-white/80">Create standard record</div>
                </div>
              </button>

              <button
                @click="triggerAction('attendance')"
                class="flex items-center gap-3 rounded-xl bg-[var(--color-info)]/10 border border-[var(--color-info)]/30 p-4 hover:bg-[var(--color-info)] hover:text-white transition-all duration-300 group active:scale-95"
              >
                <span class="text-2xl group-hover:scale-110 transition-transform duration-200">📝</span>
                <div class="text-left">
                  <div class="font-bold text-sm">Bulk Attendance</div>
                  <div class="text-[10px] text-[var(--color-text-muted)] group-hover:text-white/80">Mark attendance for today</div>
                </div>
              </button>

              <button
                @click="triggerAction('payroll')"
                class="flex items-center gap-3 rounded-xl bg-[var(--color-success)]/10 border border-[var(--color-success)]/30 p-4 hover:bg-[var(--color-success)] hover:text-white transition-all duration-300 group active:scale-95"
              >
                <span class="text-2xl group-hover:scale-110 transition-transform duration-200">🖨️</span>
                <div class="text-left">
                  <div class="font-bold text-sm">Generate Payslips</div>
                  <div class="text-[10px] text-[var(--color-text-muted)] group-hover:text-white/80">Process salary slips</div>
                </div>
              </button>
            </div>
          </div>

          <!-- Pending leave approvals list -->
          <div class="lg:col-span-2 bg-[var(--color-surface)] p-6 rounded-2xl border border-[var(--color-border)] shadow-md">
            <h3 class="text-base font-bold uppercase tracking-wider text-[var(--color-text)] border-b border-[var(--color-border)] pb-3 mb-4">Pending Leave Requests</h3>
            <div class="space-y-4">
              <div
                v-for="leave in pendingLeaves"
                :key="leave.id"
                class="flex items-center justify-between rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4 shadow-sm"
              >
                <div class="flex items-center gap-3">
                  <div class="h-10 w-10 rounded-full bg-[var(--color-employee)]/20 text-[var(--color-employee)] flex items-center justify-center font-bold">
                    {{ leave.initials }}
                  </div>
                  <div>
                    <h4 class="font-bold text-sm">{{ leave.name }}</h4>
                    <p class="text-xs text-[var(--color-text-muted)]">{{ leave.type }} — {{ leave.dates }}</p>
                  </div>
                </div>
                
                <div class="flex gap-2">
                  <button
                    @click="approveLeave(leave)"
                    class="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs shadow-sm active:scale-95 transition-all"
                  >
                    Approve
                  </button>
                  <button
                    @click="rejectLeave(leave)"
                    class="px-3 py-1.5 rounded-lg bg-rose-500 hover:bg-rose-600 text-white font-bold text-xs shadow-sm active:scale-95 transition-all"
                  >
                    Reject
                  </button>
                </div>
              </div>
              <div v-if="!pendingLeaves.length" class="text-center py-8 text-sm text-[var(--color-text-muted)] italic">
                No pending leave requests today
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Attendance subtab view -->
      <div v-else-if="activeSubTab === 'attendance'" class="flex-1 p-8 space-y-6">
        <div class="bg-[var(--color-surface)] p-6 rounded-2xl border border-[var(--color-border)] shadow-md">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-4 mb-4">
            <h3 class="text-lg font-bold text-[var(--color-text)]">Daily Attendance Tracker</h3>
            <button
              @click="alert('Bulk attendance submission coming soon')"
              class="px-4 py-2 bg-[var(--color-employee)] text-white text-xs font-bold rounded-lg shadow-sm hover:brightness-110 active:scale-95 transition-all"
            >
              ✓ Submit Attendance
            </button>
          </div>
          <p class="text-sm text-[var(--color-text-muted)] mb-6">Attendance logs for standard employees for date {{ todayDate }}.</p>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm border-collapse text-[var(--color-text)]">
              <thead>
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 font-bold text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-6 py-4">Employee ID</th>
                  <th class="px-6 py-4">Name</th>
                  <th class="px-6 py-4">Check-in</th>
                  <th class="px-6 py-4">Check-out</th>
                  <th class="px-6 py-4">Status</th>
                  <th class="px-6 py-4 text-right font-bold">Action</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr v-for="emp in mockAttendance" :key="emp.id" class="hover:bg-[var(--color-midlight)]/40 transition-colors">
                  <td class="px-6 py-4 font-mono font-bold">{{ emp.id }}</td>
                  <td class="px-6 py-4 font-bold">{{ emp.name }}</td>
                  <td class="px-6 py-4 font-mono">{{ emp.in }}</td>
                  <td class="px-6 py-4 font-mono">{{ emp.out }}</td>
                  <td class="px-6 py-4">
                    <span
                      class="px-2.5 py-1 text-xs font-bold rounded-full"
                      :class="emp.status === 'Present' ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-500 border border-rose-500/20'"
                    >
                      ● {{ emp.status }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-right">
                    <button
                      @click="toggleAttendanceStatus(emp)"
                      class="px-3 py-1 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] hover:bg-[var(--color-midlight)] text-xs font-bold active:scale-95 transition-all"
                    >
                      Toggle
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Payroll subtab view -->
      <div v-else-if="activeSubTab === 'payroll'" class="flex-1 p-8 space-y-6">
        <div class="bg-[var(--color-surface)] p-6 rounded-2xl border border-[var(--color-border)] shadow-md">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-4 mb-4">
            <h3 class="text-lg font-bold text-[var(--color-text)]">Payroll Processing (August 2026)</h3>
            <button
              @click="alert('Payroll generation script triggered. Salary slips created.')"
              class="px-4 py-2 bg-[var(--color-success)] text-white text-xs font-bold rounded-lg shadow-sm hover:brightness-110 active:scale-95 transition-all"
            >
              ⚙ Processing Salary
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div class="p-4 bg-[var(--color-bg)] rounded-xl border border-[var(--color-border)] text-center">
              <div class="text-[10px] text-[var(--color-text-muted)] font-black uppercase tracking-wider">Salary Pool</div>
              <div class="text-xl font-bold mt-1 text-[var(--color-text)]">₹ 8,45,000.00</div>
            </div>
            <div class="p-4 bg-[var(--color-bg)] rounded-xl border border-[var(--color-border)] text-center">
              <div class="text-[10px] text-[var(--color-text-muted)] font-black uppercase tracking-wider">Processed Slips</div>
              <div class="text-xl font-bold mt-1 text-[var(--color-success)]">44 Slips (100%)</div>
            </div>
            <div class="p-4 bg-[var(--color-bg)] rounded-xl border border-[var(--color-border)] text-center">
              <div class="text-[10px] text-[var(--color-text-muted)] font-black uppercase tracking-wider">Disbursement Date</div>
              <div class="text-xl font-bold mt-1 text-[var(--color-info)]">01-Sep-2026</div>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm border-collapse text-[var(--color-text)]">
              <thead>
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 font-bold text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-6 py-4">Slip ID</th>
                  <th class="px-6 py-4">Employee</th>
                  <th class="px-6 py-4">Basic Pay</th>
                  <th class="px-6 py-4">Incentives</th>
                  <th class="px-6 py-4">Deductions</th>
                  <th class="px-6 py-4 text-right">Net Amount</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr class="hover:bg-[var(--color-midlight)]/40 transition-colors">
                  <td class="px-6 py-4 font-mono text-xs">SAL-SLIP-00891</td>
                  <td class="px-6 py-4 font-bold">Ramesh Kumar</td>
                  <td class="px-6 py-4 font-mono">₹ 24,000.00</td>
                  <td class="px-6 py-4 font-mono text-emerald-500">+ ₹ 1,450.00</td>
                  <td class="px-6 py-4 font-mono text-rose-500">- ₹ 200.00</td>
                  <td class="px-6 py-4 text-right font-black text-emerald-500">₹ 25,250.00</td>
                </tr>
                <tr class="hover:bg-[var(--color-midlight)]/40 transition-colors">
                  <td class="px-6 py-4 font-mono text-xs">SAL-SLIP-00892</td>
                  <td class="px-6 py-4 font-bold">Siddharth Sen</td>
                  <td class="px-6 py-4 font-bold">₹ 35,000.00</td>
                  <td class="px-6 py-4 font-mono text-emerald-500">+ ₹ 2,800.00</td>
                  <td class="px-6 py-4 font-mono text-rose-500">- ₹ 500.00</td>
                  <td class="px-6 py-4 text-right font-black text-emerald-500">₹ 37,300.00</td>
                </tr>
                <tr class="hover:bg-[var(--color-midlight)]/40 transition-colors">
                  <td class="px-6 py-4 font-mono text-xs">SAL-SLIP-00893</td>
                  <td class="px-6 py-4 font-bold">Karthik Raja</td>
                  <td class="px-6 py-4 font-bold">₹ 18,000.00</td>
                  <td class="px-6 py-4 font-mono text-emerald-500">+ ₹ 0.00</td>
                  <td class="px-6 py-4 font-mono text-rose-500">- ₹ 150.00</td>
                  <td class="px-6 py-4 text-right font-black text-emerald-500">₹ 17,850.00</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Leave subtab view -->
      <div v-else-if="activeSubTab === 'leave'" class="flex-1 p-8 space-y-6">
        <div class="bg-[var(--color-surface)] p-6 rounded-2xl border border-[var(--color-border)] shadow-md">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-4 mb-4">
            <h3 class="text-lg font-bold text-[var(--color-text)]">Leave Allocation & Balance</h3>
            <button
              @click="alert('Leave policy configurator opened')"
              class="px-4 py-2 bg-[var(--color-employee)] text-white text-xs font-bold rounded-lg shadow-sm hover:brightness-110 active:scale-95 transition-all"
            >
              ⚙ Leave Rules
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div class="p-4 bg-[var(--color-bg)] rounded-xl border border-[var(--color-border)] text-center">
              <div class="text-[10px] text-[var(--color-text-muted)] font-black uppercase tracking-wider">Annual Casual Leaves</div>
              <div class="text-2xl font-bold mt-1 text-[var(--color-employee)]">12 Days</div>
            </div>
            <div class="p-4 bg-[var(--color-bg)] rounded-xl border border-[var(--color-border)] text-center">
              <div class="text-[10px] text-[var(--color-text-muted)] font-black uppercase tracking-wider">Annual Sick Leaves</div>
              <div class="text-2xl font-bold mt-1 text-[var(--color-employee)]">10 Days</div>
            </div>
            <div class="p-4 bg-[var(--color-bg)] rounded-xl border border-[var(--color-border)] text-center">
              <div class="text-[10px] text-[var(--color-text-muted)] font-black uppercase tracking-wider">Earned Leaves Balance</div>
              <div class="text-2xl font-bold mt-1 text-[var(--color-employee)]">18 Days</div>
            </div>
            <div class="p-4 bg-[var(--color-bg)] rounded-xl border border-[var(--color-border)] text-center">
              <div class="text-[10px] text-[var(--color-text-muted)] font-black uppercase tracking-wider">Maternity/Paternity</div>
              <div class="text-2xl font-bold mt-1 text-[var(--color-employee)]">Standard</div>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm border-collapse text-[var(--color-text)]">
              <thead>
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 font-bold text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-6 py-4">Employee</th>
                  <th class="px-6 py-4">Casual Leaves Taken</th>
                  <th class="px-6 py-4">Sick Leaves Taken</th>
                  <th class="px-6 py-4">Remaining Balance</th>
                  <th class="px-6 py-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr class="hover:bg-[var(--color-midlight)]/40 transition-colors">
                  <td class="px-6 py-4 font-bold">Ramesh Kumar</td>
                  <td class="px-6 py-4">4 / 12</td>
                  <td class="px-6 py-4">2 / 10</td>
                  <td class="px-6 py-4 font-bold">24 Days</td>
                  <td class="px-6 py-4 text-right">
                    <span class="px-2.5 py-1 text-[10px] font-bold rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">Good Standing</span>
                  </td>
                </tr>
                <tr class="hover:bg-[var(--color-midlight)]/40 transition-colors">
                  <td class="px-6 py-4 font-bold">Siddharth Sen</td>
                  <td class="px-6 py-4">8 / 12</td>
                  <td class="px-6 py-4">1 / 10</td>
                  <td class="px-6 py-4 font-bold">13 Days</td>
                  <td class="px-6 py-4 text-right">
                    <span class="px-2.5 py-1 text-[10px] font-bold rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">Good Standing</span>
                  </td>
                </tr>
                <tr class="hover:bg-[var(--color-midlight)]/40 transition-colors">
                  <td class="px-6 py-4 font-bold">Karthik Raja</td>
                  <td class="px-6 py-4">11 / 12</td>
                  <td class="px-6 py-4">5 / 10</td>
                  <td class="px-6 py-4 font-bold">6 Days</td>
                  <td class="px-6 py-4 text-right">
                    <span class="px-2.5 py-1 text-[10px] font-bold rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/20">Low Balance</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { fetchEmployees } from '../api.js'

const router = useRouter()
const activeSubTab = ref('dashboard')

const employeeCount = ref(0)
const presentCount = ref(0)

const now = ref(new Date())

const todayDate = computed(() => {
  return now.value.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  })
})

const todayDay = computed(() => {
  return now.value.toLocaleDateString('en-IN', {
    weekday: 'long'
  })
})

// Pending leaves list
const pendingLeaves = ref([
  { id: 1, name: 'Anjali Sharma', initials: 'AS', type: 'Sick Leave', dates: '11 Aug - 12 Aug (2 Days)' },
  { id: 2, name: 'Vikram Singh', initials: 'VS', type: 'Casual Leave', dates: '14 Aug (1 Day)' }
])

const mockAttendance = ref([
  { id: 'EMP-001', name: 'Ramesh Kumar', in: '08:54 AM', out: '06:05 PM', status: 'Present' },
  { id: 'EMP-002', name: 'Siddharth Sen', in: '09:02 AM', out: '05:45 PM', status: 'Present' },
  { id: 'EMP-003', name: 'Anjali Sharma', in: '--:--', out: '--:--', status: 'Absent' },
  { id: 'EMP-004', name: 'Vikram Singh', in: '09:15 AM', out: '06:00 PM', status: 'Present' },
  { id: 'EMP-005', name: 'Karthik Raja', in: '08:42 AM', out: '06:00 PM', status: 'Present' }
])

function toggleAttendanceStatus(emp) {
  if (emp.status === 'Present') {
    emp.status = 'Absent'
    emp.in = '--:--'
    emp.out = '--:--'
  } else {
    emp.status = 'Present'
    emp.in = '09:00 AM'
    emp.out = '06:00 PM'
  }
  calculatePresentCount()
}

function calculatePresentCount() {
  const present = mockAttendance.value.filter(a => a.status === 'Present').length
  const absent = mockAttendance.value.filter(a => a.status === 'Absent').length
  const total = employeeCount.value || mockAttendance.value.length
  
  // scale proportional to actual count
  if (employeeCount.value > 0) {
    const ratio = present / (present + absent)
    presentCount.value = Math.round(employeeCount.value * ratio)
  } else {
    presentCount.value = present
  }
}

async function loadStats() {
  try {
    const list = await fetchEmployees()
    employeeCount.value = list?.length || 0
    calculatePresentCount()
  } catch (err) {
    console.error('Failed to load employee list for stats:', err)
    employeeCount.value = 5 // fallback
    calculatePresentCount()
  }
}

function approveLeave(leave) {
  alert(`Leave request approved for ${leave.name}`)
  pendingLeaves.value = pendingLeaves.value.filter(l => l.id !== leave.id)
}

function rejectLeave(leave) {
  alert(`Leave request rejected for ${leave.name}`)
  pendingLeaves.value = pendingLeaves.value.filter(l => l.id !== leave.id)
}

function triggerAction(action) {
  if (action === 'attendance') {
    activeSubTab.value = 'attendance'
  } else if (action === 'payroll') {
    activeSubTab.value = 'payroll'
  }
}

onMounted(() => {
  loadStats()
})
</script>
