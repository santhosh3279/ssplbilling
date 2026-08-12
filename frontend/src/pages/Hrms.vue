<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- ===================== HRMS SIDEBAR ===================== -->
    <HrmsSidebar active="dashboard" />

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

              <button
                @click="openLeaveModal"
                class="flex items-center gap-3 rounded-xl bg-[var(--color-warning)]/10 border border-[var(--color-warning)]/30 p-4 hover:bg-[var(--color-warning)] hover:text-white transition-all duration-300 group active:scale-95"
              >
                <span class="text-2xl group-hover:scale-110 transition-transform duration-200">✉️</span>
                <div class="text-left">
                  <div class="font-bold text-sm">Leave Request</div>
                  <div class="text-[10px] text-[var(--color-text-muted)] group-hover:text-white/80">Submit new leave request</div>
                </div>
              </button>
            </div>
          </div>

          <!-- Pending leave approvals list -->
          <div class="lg:col-span-2 bg-[var(--color-surface)] p-6 rounded-2xl border border-[var(--color-border)] shadow-md">
            <h3 class="text-base font-bold uppercase tracking-wider text-[var(--color-text)] border-b border-[var(--color-border)] pb-3 mb-4 flex items-center justify-between">
              <span>Pending Leave Requests</span>
              <span v-if="session.fullName.value || session.user.value" class="text-xs text-[var(--color-text-muted)] font-medium normal-case">
                Approver: <strong class="text-[var(--color-employee)]">{{ session.fullName.value || session.user.value }}</strong>
              </span>
            </h3>
            <div class="space-y-4">
              <div v-if="leaveListError" class="rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-xs font-bold text-rose-500">
                {{ leaveListError }}
              </div>

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
                    <h4 class="font-bold text-sm flex items-center gap-2">
                      {{ leave.name }}
                      <span
                        class="rounded-lg border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
                        :class="leave.status === 'Open'
                          ? 'border-amber-500/30 bg-amber-500/10 text-amber-500'
                          : 'border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]'"
                      >
                        {{ leave.status }}
                      </span>
                    </h4>
                    <p class="text-xs text-[var(--color-text-muted)]">{{ leave.type }} — {{ leave.dates }}</p>
                    <p class="text-[10px] text-[var(--color-text-muted)]">
                      <span class="font-mono">{{ leave.id }}</span>
                      <span v-if="leave.appliedOn"> · Applied {{ leave.appliedOn }}</span>
                      <span v-if="leave.approver"> · Approver {{ leave.approver }}</span>
                    </p>
                    <p v-if="leave.reason" class="mt-1 text-[11px] italic text-[var(--color-text-muted)]">
                      “{{ leave.reason }}”
                    </p>
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
              <div v-if="loadingLeaves" class="text-center py-8 text-sm text-[var(--color-text-muted)] italic">
                Loading leave requests...
              </div>
              <div v-else-if="!pendingLeaves.length && !leaveListError" class="text-center py-8 text-sm text-[var(--color-text-muted)] italic">
                No pending leave requests
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
    <!-- ===================== LEAVE REQUEST MODAL ===================== -->
    <div
      v-if="showLeaveModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4"
    >
      <div class="w-full max-w-md bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <!-- Modal Header -->
        <div class="border-b border-[var(--color-border)] px-6 py-4 bg-[var(--color-surface-raised)]/50 flex items-center justify-between">
          <h3 class="text-base font-black uppercase tracking-wider text-[var(--color-text)] flex items-center gap-2">
            <span>✉️</span> Leave Request
          </h3>
          <button
            @click="closeLeaveModal"
            class="text-xl text-[var(--color-text-muted)] hover:text-[var(--color-text)] focus:outline-none"
          >
            &times;
          </button>
        </div>

        <!-- Modal Body (Form) -->
        <form @submit.prevent="submitLeaveRequest" class="p-6 space-y-4 overflow-y-auto">
          <!-- Employee -->
          <div class="space-y-1">
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Employee <span class="text-rose-500">*</span></label>
            <select
              v-model="leaveForm.employee"
              required
              class="w-full px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-warning)] text-[var(--color-text)]"
            >
              <option value="">Select employee...</option>
              <option v-for="emp in employeesList" :key="emp.name" :value="emp.name">
                {{ emp.employee_name }} ({{ emp.name }})
              </option>
            </select>
          </div>

          <!-- Leave Type -->
          <div class="space-y-1">
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Leave Type <span class="text-rose-500">*</span></label>
            <select
              v-model="leaveForm.leave_type"
              required
              class="w-full px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-warning)] text-[var(--color-text)]"
            >
              <option value="">Select type...</option>
              <option v-for="t in leaveTypes" :key="t.name" :value="t.name">
                {{ t.name }}
              </option>
            </select>
          </div>

          <!-- Leave Approver -->
          <div class="space-y-1">
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Leave Approver</label>
            <select
              v-model="leaveForm.leave_approver"
              class="w-full px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-warning)] text-[var(--color-text)]"
            >
              <option value="">Select approver...</option>
              <option v-for="user in leaveApprovers" :key="user.name" :value="user.name">
                {{ user.full_name || user.name }} ({{ user.name }})
              </option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <!-- From Date -->
            <div class="space-y-1">
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">From Date <span class="text-rose-500">*</span></label>
              <input
                v-model="leaveForm.from_date"
                type="date"
                required
                class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-warning)] text-[var(--color-text)]"
              />
            </div>

            <!-- To Date -->
            <div class="space-y-1">
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">To Date <span class="text-rose-500">*</span></label>
              <input
                v-model="leaveForm.to_date"
                type="date"
                required
                class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-warning)] text-[var(--color-text)]"
              />
            </div>
          </div>

          <!-- Half Day Checkbox -->
          <div class="flex items-center gap-2 py-1">
            <input
              v-model="leaveForm.half_day"
              id="half_day"
              type="checkbox"
              class="h-4 w-4 rounded border-[var(--color-border)] text-[var(--color-warning)] focus:ring-[var(--color-warning)]/30"
            />
            <label for="half_day" class="text-xs font-bold uppercase tracking-wider text-[var(--color-text)] cursor-pointer select-none">
              Half Day
            </label>
          </div>

          <!-- Half Day Date -->
          <div v-if="leaveForm.half_day" class="space-y-1">
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Half Day Date <span class="text-rose-500">*</span></label>
            <input
              v-model="leaveForm.half_day_date"
              type="date"
              required
              class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-warning)] text-[var(--color-text)]"
            />
          </div>

          <!-- Reason -->
          <div class="space-y-1">
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Reason</label>
            <textarea
              v-model="leaveForm.reason"
              rows="3"
              placeholder="Enter reason for leave..."
              class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-warning)] text-[var(--color-text)]"
            ></textarea>
          </div>

          <!-- Actions -->
          <div class="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              @click="closeLeaveModal"
              class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-5 py-3 text-xs font-bold hover:bg-[var(--color-midlight)] transition-all duration-200 text-[var(--color-text)]"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="submittingLeave"
              class="rounded-xl bg-[var(--color-warning)] text-white px-6 py-3 text-xs font-bold hover:brightness-110 active:scale-95 transition-all duration-200 shadow-md shadow-[var(--color-warning)]/15 disabled:opacity-50 flex items-center gap-2"
            >
              <span v-if="submittingLeave" class="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
              <span>Submit Request</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import HrmsSidebar from '../components/HrmsSidebar.vue'
import { fetchEmployees, fetchLeaveTypes, createLeaveApplication, fetchLeaveApprovers, fetchPendingLeaveApplications, approveLeaveApplication, rejectLeaveApplication } from '../api.js'
import { session } from '../session.js'

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

// Pending leaves list — unsubmitted Leave Application rows (docstatus 0)
const pendingLeaves = ref([])
const loadingLeaves = ref(false)
const leaveListError = ref('')

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

const employeesList = ref([])
const leaveTypes = ref([])
const leaveApprovers = ref([])
const showLeaveModal = ref(false)
const submittingLeave = ref(false)
const leaveForm = ref({
  employee: '',
  leave_type: '',
  leave_approver: '',
  from_date: '',
  to_date: '',
  half_day: false,
  half_day_date: '',
  reason: ''
})

async function openLeaveModal() {
  showLeaveModal.value = true
  if (!leaveTypes.value.length) {
    try {
      const res = await fetchLeaveTypes()
      leaveTypes.value = res || []
    } catch (err) {
      console.error('Failed to load leave types:', err)
    }
  }
  if (!leaveApprovers.value.length) {
    try {
      const res = await fetchLeaveApprovers()
      leaveApprovers.value = res || []
    } catch (err) {
      console.error('Failed to load leave approvers:', err)
    }
  }
}

function closeLeaveModal() {
  showLeaveModal.value = false
  leaveForm.value = {
    employee: '',
    leave_type: '',
    leave_approver: '',
    from_date: '',
    to_date: '',
    half_day: false,
    half_day_date: '',
    reason: ''
  }
}

async function submitLeaveRequest() {
  submittingLeave.value = true
  try {
    const payload = {
      employee: leaveForm.value.employee,
      leave_type: leaveForm.value.leave_type,
      leave_approver: leaveForm.value.leave_approver || undefined,
      from_date: leaveForm.value.from_date,
      to_date: leaveForm.value.to_date,
      half_day: leaveForm.value.half_day ? 1 : 0,
      half_day_date: leaveForm.value.half_day ? leaveForm.value.half_day_date : undefined,
      reason: leaveForm.value.reason
    }
    const res = await createLeaveApplication(payload)
    alert(`Leave Request submitted successfully: ${res.name}`)
    closeLeaveModal()
    await loadPendingLeaves()
  } catch (err) {
    console.error('Failed to submit leave request:', err)
    alert(err.message || 'Failed to submit leave request.')
  } finally {
    submittingLeave.value = false
  }
}

async function loadPendingLeaves() {
  leaveListError.value = ''
  loadingLeaves.value = true
  try {
    const list = await fetchPendingLeaveApplications()
    pendingLeaves.value = (list || []).map(doc => {
      const empName = doc.employee_name || doc.employee || 'Staff Member'
      const initials = empName
        .split(' ')
        .map(p => p[0])
        .filter(Boolean)
        .join('')
        .toUpperCase()
        .slice(0, 2)

      const formatDate = (dateStr) => {
        if (!dateStr) return ''
        const parts = dateStr.split('-')
        if (parts.length === 3) {
          const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
          return `${parseInt(parts[2], 10)} ${months[parseInt(parts[1], 10) - 1]}`
        }
        return dateStr
      }

      const dateRange = doc.from_date === doc.to_date
        ? formatDate(doc.from_date)
        : `${formatDate(doc.from_date)} - ${formatDate(doc.to_date)}`

      const daysLabel = doc.total_leave_days === 1 ? '1 Day' : `${doc.total_leave_days} Days`

      return {
        id: doc.name,
        name: empName,
        initials: initials || 'EE',
        type: doc.leave_type,
        dates: `${dateRange} (${daysLabel})`,
        reason: doc.reason || '',
        // status is the Leave Application workflow state; the row is still docstatus 0,
        // so an "Approved"/"Rejected" label here means a submit that never went through.
        status: doc.status || 'Open',
        approver: doc.leave_approver || '',
        appliedOn: formatDate(doc.posting_date)
      }
    })
  } catch (err) {
    console.error('Failed to load pending leave requests:', err)
    leaveListError.value = stripHtml(err.message) || 'Failed to load pending leave requests.'
    pendingLeaves.value = []
  } finally {
    loadingLeaves.value = false
  }
}

// frappe.throw() ships HTML (links, <strong>), which reads as markup in an alert box.
function stripHtml(text) {
  if (!text) return ''
  return String(text)
    .replace(/<br\s*\/?>/gi, ' ')
    .replace(/<[^>]+>/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

async function loadStats() {
  try {
    const list = await fetchEmployees()
    employeesList.value = list || []
    employeeCount.value = list?.length || 0
    calculatePresentCount()
  } catch (err) {
    console.error('Failed to load employee list for stats:', err)
    employeeCount.value = 5 // fallback
    calculatePresentCount()
  }
}

async function approveLeave(leave) {
  try {
    await approveLeaveApplication(leave.id)
    alert(`Leave request approved successfully!`)
    await loadPendingLeaves()
  } catch (err) {
    console.error('Failed to approve leave request:', err)
    const msg = stripHtml(err.message) || 'Failed to approve leave request.'
    leaveListError.value = msg
    alert(msg)
  }
}

async function rejectLeave(leave) {
  try {
    await rejectLeaveApplication(leave.id)
    alert(`Leave request rejected successfully.`)
    await loadPendingLeaves()
  } catch (err) {
    console.error('Failed to reject leave request:', err)
    const msg = stripHtml(err.message) || 'Failed to reject leave request.'
    leaveListError.value = msg
    alert(msg)
  }
}

function triggerAction(action) {
  if (action === 'attendance') {
    activeSubTab.value = 'attendance'
  } else if (action === 'payroll') {
    activeSubTab.value = 'payroll'
  }
}

onMounted(async () => {
  await loadStats()
  await loadPendingLeaves()
})
</script>
