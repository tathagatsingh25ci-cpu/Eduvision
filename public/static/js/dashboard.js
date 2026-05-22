(() => {
    const shell = document.querySelector(".dashboard-shell");
    if (!shell) return;

    const role = shell.dataset.role;
    const isStudent = role === "student";
    const isParent = role === "parent";
    const canManageStudents = role === "admin" || role === "teacher";
    const charts = {};
    let dashboardData = null;
    let selectedStudent = null;
    let selectedAttendanceId = null;
    let parentInitialViewShown = false;
    let searchTimer = null;

    const numberFields = [
        "attendance",
        "internal_marks",
        "semester_marks",
        "mathematics",
        "physics",
        "chemistry",
        "biology",
        "computer_science",
        "english",
        "geography",
        "history",
        "economics",
        "physical_education",
    ];

    const subjectLabels = {
        mathematics: "Mathematics",
        physics: "Physics",
        chemistry: "Chemistry",
        biology: "Biology",
        computer_science: "Computer Science",
        english: "English",
        geography: "Geography",
        history: "History",
        economics: "Economics",
        physical_education: "Physical Education",
    };

    const elements = {
        loading: document.getElementById("loadingOverlay"),
        sidebar: document.getElementById("sidebar"),
        statsGrid: document.getElementById("statsGrid"),
        studentsBody: document.getElementById("studentsBody"),
        studentCount: document.getElementById("studentCount"),
        studentForm: document.getElementById("studentForm"),
        studentId: document.getElementById("studentId"),
        studentFormTitle: document.getElementById("studentFormTitle"),
        studentFormMessage: document.getElementById("studentFormMessage"),
        studentFilters: document.getElementById("studentFilters"),
        studentTableSearch: document.getElementById("studentTableSearch"),
        streamFilter: document.getElementById("streamFilter"),
        classFilter: document.getElementById("classFilter"),
        focusFilter: document.getElementById("focusFilter"),
        attendanceFilter: document.getElementById("attendanceFilter"),
        selfMarksForm: document.getElementById("selfMarksForm"),
        selfMarksMessage: document.getElementById("selfMarksMessage"),
        uploadForm: document.getElementById("uploadForm"),
        uploadMessage: document.getElementById("uploadMessage"),
        profile: document.getElementById("studentProfile"),
        searchInput: document.getElementById("globalSearch"),
        searchResults: document.getElementById("searchResults"),
        insightGrid: document.getElementById("insightGrid"),
        recentActivity: document.getElementById("recentActivity"),
        topperCards: document.getElementById("topperCards"),
        leaderboardList: document.getElementById("leaderboardList"),
        subjectToppersBody: document.getElementById("subjectToppersBody"),
        heatmapGrid: document.getElementById("heatmapGrid"),
        attendanceRing: document.getElementById("attendanceRing"),
        attendanceRingValue: document.getElementById("attendanceRingValue"),
        attendanceHeroTitle: document.getElementById("attendanceHeroTitle"),
        attendanceHeroText: document.getElementById("attendanceHeroText"),
        attendanceSummary: document.getElementById("attendanceSummary"),
        attendanceStudentCount: document.getElementById("attendanceStudentCount"),
        attendanceStudentList: document.getElementById("attendanceStudentList"),
        attendanceDetailTitle: document.getElementById("attendanceDetailTitle"),
        attendanceDetailStatus: document.getElementById("attendanceDetailStatus"),
        attendanceDetail: document.getElementById("attendanceDetail"),
        smartSessionForm: document.getElementById("smartSessionForm"),
        teacherNoteForm: document.getElementById("teacherNoteForm"),
        smartSessionCount: document.getElementById("smartSessionCount"),
        smartSessionList: document.getElementById("smartSessionList"),
        assistantToggle: document.getElementById("assistantToggle"),
        assistantClose: document.getElementById("assistantClose"),
        assistantPanel: document.getElementById("assistantPanel"),
        assistantForm: document.getElementById("assistantForm"),
        assistantInput: document.getElementById("assistantInput"),
        assistantMessages: document.getElementById("assistantMessages"),
        parentLookupForm: document.getElementById("parentStudentLookupForm"),
        parentLookupInput: document.getElementById("parentStudentLookupInput"),
        parentLookupResults: document.getElementById("parentLookupResults"),
        parentWardFocus: document.getElementById("parentWardFocus"),
        parentWardGrid: document.getElementById("parentWardGrid"),
        parentAlertGrid: document.getElementById("parentAlertGrid"),
        reportPdfLink: document.getElementById("reportPdfLink"),
        selectedPdfLink: document.getElementById("selectedPdfLink"),
        usersBody: document.getElementById("usersBody"),
        userCount: document.getElementById("userCount"),
    };

    const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }[char]));

    function showLoading(show) {
        elements.loading?.classList.toggle("show", show);
    }

    async function fetchJson(url, options = {}) {
        const response = await fetch(url, options);
        let data = {};
        try {
            data = await response.json();
        } catch (error) {
            data = {};
        }
        if (!response.ok) {
            throw new Error(data.message || data.error || `Request failed with ${response.status}`);
        }
        return data;
    }

    function setMessage(node, text, state = "") {
        if (!node) return;
        node.textContent = text;
        node.className = `message ${state}`.trim();
    }

    function applyRoleVisibility() {
        document.querySelectorAll(".admin-only, .teacher-only, .student-only, .parent-only").forEach((node) => {
            const allowed =
                (role === "admin" && node.classList.contains("admin-only")) ||
                (role === "teacher" && node.classList.contains("teacher-only")) ||
                (role === "student" && node.classList.contains("student-only")) ||
                (role === "parent" && node.classList.contains("parent-only"));
            node.classList.toggle("hidden", !allowed);
        });
    }

    function updateClock() {
        const node = document.getElementById("liveClock");
        if (!node) return;
        node.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    }

    function animateNumber(node, target, suffix = "") {
        const numeric = Number(target) || 0;
        const start = performance.now();
        const duration = 760;

        function step(now) {
            const progress = Math.min(1, (now - start) / duration);
            const value = numeric * (1 - Math.pow(1 - progress, 3));
            node.textContent = `${Number.isInteger(numeric) ? Math.round(value) : value.toFixed(1)}${suffix}`;
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    function renderStats(stats) {
        const cards = [
            ["School Average", stats.school_average, "%", "Current academic pulse"],
            ["Total Students", stats.total_students, "", "Active profiles"],
            ["Pass Percentage", stats.pass_percentage, "%", "Students above pass mark"],
            ["Toppers", stats.toppers_count, "", "Students above 85%"],
            ["At Risk Students", stats.at_risk_count, "", "Moderate and high risk"],
            ["AI Accuracy", stats.prediction_accuracy, "%", "Model confidence estimate"],
        ];

        elements.statsGrid.innerHTML = cards.map(([label, value, suffix, meta]) => `
            <article class="metric-card">
                <div class="metric-label">${escapeHtml(label)}</div>
                <div class="metric-value" data-value="${escapeHtml(value)}" data-suffix="${escapeHtml(suffix)}">0${escapeHtml(suffix)}</div>
                <div class="metric-meta">${escapeHtml(meta)}</div>
            </article>
        `).join("");

        elements.statsGrid.querySelectorAll(".metric-value").forEach((node) => {
            animateNumber(node, node.dataset.value, node.dataset.suffix);
        });
    }

    function riskClass(risk) {
        if (risk === "High Risk") return "danger";
        if (risk === "Moderate Risk") return "warning";
        return "success";
    }

    function attendancePillClass(status) {
        if (status === "Critical") return "danger";
        if (status === "Watch") return "warning";
        return "success";
    }

    function studentMatchesFilters(student) {
        const query = (elements.studentTableSearch?.value || "").trim().toLowerCase();
        const stream = (elements.streamFilter?.value || "").trim().toLowerCase();
        const className = (elements.classFilter?.value || "").trim().toLowerCase();
        const focus = elements.focusFilter?.value || "";
        const attendance = elements.attendanceFilter?.value || "";

        const haystack = [student.name, student.roll_number, student.class_name, student.stream]
            .join(" ")
            .toLowerCase();
        if (query && !haystack.includes(query)) return false;
        if (stream && String(student.stream || "").toLowerCase() !== stream) return false;
        if (className && String(student.class_name || "").toLowerCase() !== className) return false;
        if (focus === "toppers" && Number(student.percentage) < 85) return false;
        if (focus === "weak" && Number(student.percentage) >= 50 && student.risk_level === "Low Risk") return false;
        if (attendance === "low" && Number(student.attendance) >= 75) return false;
        if (attendance === "excellent" && Number(student.attendance) < 90) return false;
        return true;
    }

    function applyStudentFilters() {
        if (!dashboardData) return;
        const filtered = dashboardData.students.filter(studentMatchesFilters);
        renderStudents(filtered);
    }

    function renderStudents(students) {
        elements.studentCount.textContent = `${students.length} records`;
        if (!students.length) {
            elements.studentsBody.innerHTML = `<tr><td colspan="9">No student records found.</td></tr>`;
            return;
        }

        elements.studentsBody.innerHTML = students.map((student) => `
            <tr>
                <td><span class="rank-badge">${student.rank}</span></td>
                <td><strong>${escapeHtml(student.name)}</strong><br><span class="muted">${escapeHtml(student.category)}</span></td>
                <td>${escapeHtml(student.roll_number)}</td>
                <td>${escapeHtml(student.class_name)}-${escapeHtml(student.section || "")}</td>
                <td>${escapeHtml(student.stream || "")}</td>
                <td>${escapeHtml(student.attendance)}%</td>
                <td><span class="pill">${escapeHtml(student.percentage)}%</span></td>
                <td><span class="pill ${riskClass(student.risk_level)}">${escapeHtml(student.risk_level)}</span></td>
                <td>
                    <div class="actions">
                        <button class="btn secondary" type="button" data-action="view" data-id="${student.id}">View</button>
                        ${canManageStudents ? `<button class="btn secondary" type="button" data-action="edit" data-id="${student.id}">Edit</button>
                        <button class="btn danger" type="button" data-action="delete" data-id="${student.id}">Delete</button>` : ""}
                    </div>
                </td>
            </tr>
        `).join("");

        elements.studentsBody.querySelectorAll("[data-action='view']").forEach((button) => {
            button.addEventListener("click", () => selectStudent(button.dataset.id, true));
        });
        elements.studentsBody.querySelectorAll("[data-action='edit']").forEach((button) => {
            button.addEventListener("click", () => editStudent(button.dataset.id));
        });
        elements.studentsBody.querySelectorAll("[data-action='delete']").forEach((button) => {
            button.addEventListener("click", () => deleteStudent(button.dataset.id));
        });
    }

    function chartGradient(canvas, start, end) {
        const ctx = canvas.getContext("2d");
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height || 260);
        gradient.addColorStop(0, start);
        gradient.addColorStop(1, end);
        return gradient;
    }

    function renderChart(key, canvasId, config) {
        if (!window.Chart) return;
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        if (charts[key]) charts[key].destroy();
        charts[key] = new Chart(canvas, config);
    }

    function baseChartOptions(extra = {}) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 900, easing: "easeOutQuart" },
            plugins: {
                legend: { labels: { color: "#8fa8bd", boxWidth: 12 } },
            },
            scales: {
                x: { ticks: { color: "#8fa8bd" }, grid: { color: "rgba(143,168,189,0.1)" } },
                y: { ticks: { color: "#8fa8bd" }, grid: { color: "rgba(143,168,189,0.1)" }, beginAtZero: true, suggestedMax: 100 },
            },
            ...extra,
        };
    }

    function renderCharts(data) {
        const subjects = data.subject_averages.subjects;
        const averages = data.subject_averages.averages;
        const subjectCanvas = document.getElementById("subjectChart");
        const categoryEntries = Object.entries(data.category_distribution);
        const streamEntries = Object.entries(data.stream_comparison);

        renderChart("subject", "subjectChart", {
            type: "bar",
            data: {
                labels: subjects,
                datasets: [{
                    label: "Average",
                    data: averages,
                    borderWidth: 1,
                    borderColor: "rgba(34,211,238,0.72)",
                    backgroundColor: subjectCanvas ? chartGradient(subjectCanvas, "rgba(34,211,238,0.82)", "rgba(34,197,94,0.2)") : "#22d3ee",
                    borderRadius: 8,
                }],
            },
            options: baseChartOptions(),
        });

        renderChart("category", "categoryChart", {
            type: "doughnut",
            data: {
                labels: categoryEntries.map(([label]) => label),
                datasets: [{
                    data: categoryEntries.map(([, value]) => value),
                    backgroundColor: ["#22d3ee", "#22c55e", "#a3e635", "#f59e0b", "#fb7185"],
                    borderColor: "rgba(3,7,18,0.8)",
                    borderWidth: 3,
                }],
            },
            options: baseChartOptions({ scales: {} }),
        });

        renderChart("stream", "streamChart", {
            type: "bar",
            data: {
                labels: streamEntries.map(([label]) => label),
                datasets: [{
                    label: "Stream average",
                    data: streamEntries.map(([, value]) => value),
                    backgroundColor: ["rgba(34,211,238,0.72)", "rgba(34,197,94,0.7)", "rgba(244,114,182,0.68)"],
                    borderRadius: 8,
                }],
            },
            options: baseChartOptions(),
        });

        renderChart("trend", "trendChart", {
            type: "line",
            data: {
                labels: data.class_trend.labels,
                datasets: [{
                    label: "Class average",
                    data: data.class_trend.values,
                    tension: 0.42,
                    borderColor: "#22d3ee",
                    backgroundColor: "rgba(34,211,238,0.14)",
                    fill: true,
                    pointRadius: 4,
                }],
            },
            options: baseChartOptions(),
        });

        renderChart("attendance", "attendanceChart", {
            type: "scatter",
            data: {
                datasets: [{
                    label: "Students",
                    data: data.attendance_vs_marks.map((item) => ({ x: item.attendance, y: item.marks })),
                    backgroundColor: "rgba(34,211,238,0.78)",
                    borderColor: "#22d3ee",
                    pointRadius: 5,
                }],
            },
            options: baseChartOptions({
                scales: {
                    x: { min: 0, max: 100, ticks: { color: "#8fa8bd" }, grid: { color: "rgba(143,168,189,0.1)" }, title: { display: true, text: "Attendance", color: "#8fa8bd" } },
                    y: { min: 0, max: 100, ticks: { color: "#8fa8bd" }, grid: { color: "rgba(143,168,189,0.1)" }, title: { display: true, text: "Marks", color: "#8fa8bd" } },
                },
            }),
        });

        renderChart("radar", "radarChart", {
            type: "radar",
            data: {
                labels: data.radar.subjects,
                datasets: [{
                    label: "Subject strength",
                    data: data.radar.averages,
                    borderColor: "#22c55e",
                    backgroundColor: "rgba(34,197,94,0.18)",
                    pointBackgroundColor: "#22d3ee",
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        min: 0,
                        max: 100,
                        grid: { color: "rgba(143,168,189,0.16)" },
                        angleLines: { color: "rgba(143,168,189,0.16)" },
                        pointLabels: { color: "#8fa8bd" },
                        ticks: { color: "#8fa8bd", backdropColor: "transparent" },
                    },
                },
                plugins: { legend: { labels: { color: "#8fa8bd" } } },
            },
        });
    }

    function renderHeatmap(heatmap) {
        elements.heatmapGrid.innerHTML = heatmap.cells.map((cell) => {
            const alpha = Math.max(0.08, Number(cell.value) / 115);
            return `
                <div class="heat-cell" style="background: rgba(34, 211, 238, ${alpha}); border-color: rgba(34, 211, 238, ${Math.min(0.5, alpha + 0.1)});">
                    <span>${escapeHtml(cell.class_name)} / ${escapeHtml(cell.subject)}</span>
                    <strong>${escapeHtml(cell.value)}%</strong>
                </div>
            `;
        }).join("");
    }

    function renderInsights(insights) {
        elements.insightGrid.innerHTML = insights.map((item) => `
            <article class="insight-card">
                <span class="pill">${escapeHtml(item.tone)}</span>
                <h3 style="margin-top: 12px;">${escapeHtml(item.title)}</h3>
                <p class="lead">${escapeHtml(item.text)}</p>
            </article>
        `).join("");
    }

    function renderRecentActivity(items) {
        elements.recentActivity.innerHTML = items.length ? items.map((item) => `
            <div class="activity-item">
                <strong>${escapeHtml(item.title)}</strong>
                <p class="message">${escapeHtml(item.meta)}</p>
                <span class="muted">${escapeHtml(item.time)}</span>
            </div>
        `).join("") : `<p class="lead">No recent activity.</p>`;
    }

    function renderToppers(toppers) {
        const overall = toppers.overall_topper;
        const streams = Object.entries(toppers.stream_toppers);
        elements.topperCards.innerHTML = `
            <article class="metric-card">
                <div class="metric-label">Overall Topper</div>
                <div class="metric-value">${overall ? escapeHtml(overall.percentage) : 0}%</div>
                <div class="metric-meta">${overall ? escapeHtml(overall.name) : "No data"}</div>
            </article>
            ${streams.map(([stream, top]) => `
                <article class="metric-card">
                    <div class="metric-label">${escapeHtml(stream)} Topper</div>
                    <div class="metric-value">${escapeHtml(top.percentage)}%</div>
                    <div class="metric-meta">${escapeHtml(top.name)}</div>
                </article>
            `).join("")}
        `;

        elements.leaderboardList.innerHTML = toppers.leaderboard.map((student) => `
            <div class="leaderboard-item">
                <span class="rank-badge">${student.rank}</span>
                <div><strong>${escapeHtml(student.name)}</strong><br><span class="muted">${escapeHtml(student.stream)} | ${escapeHtml(student.roll_number)}</span></div>
                <span class="pill">${escapeHtml(student.percentage)}%</span>
            </div>
        `).join("");

        elements.subjectToppersBody.innerHTML = Object.entries(toppers.subject_toppers).map(([subject, top]) => `
            <tr><td>${escapeHtml(subject)}</td><td>${escapeHtml(top.name)}</td><td><span class="pill">${escapeHtml(top.marks)}</span></td></tr>
        `).join("");
    }

    function attendancePortalData() {
        return dashboardData?.attendance_portal || { summary: {}, students: [] };
    }

    function smartAttendanceData() {
        return dashboardData?.smart_attendance || { sessions: [], notes: [] };
    }

    function renderSmartAttendance(data = smartAttendanceData()) {
        if (!elements.smartSessionList) return;
        const sessions = data.sessions || [];
        const notes = data.notes || [];
        if (elements.smartSessionCount) elements.smartSessionCount.textContent = `${sessions.length} sessions`;
        if (!sessions.length && !notes.length) {
            elements.smartSessionList.innerHTML = `<p class="lead">No smart attendance sessions or notes yet.</p>`;
            return;
        }
        const sessionHtml = sessions.map((session) => {
            const submissions = session.submissions || [];
            const latest = submissions.slice(0, 4).map((item) => `
                <p class="message">${escapeHtml(item.student_name)}: ${escapeHtml(item.status)} | ${escapeHtml(item.risk_flags)}</p>
            `).join("");
            return `
                <article class="smart-session-card">
                    <div class="attendance-class-head">
                        <div>
                            <strong>${escapeHtml(session.subject)} | Class ${escapeHtml(session.class_name)}-${escapeHtml(session.section)}</strong>
                            <span class="muted">Late after ${escapeHtml(session.late_after_minutes)} min | Radius ${escapeHtml(session.radius_meters)}m</span>
                        </div>
                        <span class="pill ${session.active ? "success" : "warning"}">${session.active ? "Active" : "Closed"}</span>
                    </div>
                    <div class="qr-token">${escapeHtml(session.qr_token)}</div>
                    <p class="message">QR expires in ${escapeHtml(session.qr_expires_in)}s. Face + device + geofence checks are enabled.</p>
                    ${session.meeting_url ? `<div class="actions"><a class="btn" href="${escapeHtml(session.meeting_url)}" target="_blank" rel="noopener">Join Live Class</a></div>` : ""}
                    ${isStudent ? `
                        <form class="attendance-edit-form smart-submit-form" data-session="${session.id}">
                            <label>QR Token <input name="qr_token" value="${escapeHtml(session.qr_token)}"></label>
                            <label>Device ID <input name="device_id" value="${escapeHtml(navigator.userAgent.slice(0, 28))}"></label>
                            <label>Face <select name="face_verified"><option value="true">Verified</option><option value="">Manual review</option></select></label>
                            <input type="hidden" name="selfie_verified" value="true">
                            <button class="btn secondary" type="submit">Mark Present</button>
                        </form>
                    ` : ""}
                    ${canManageStudents ? `
                        <form class="attendance-edit-form smart-manual-form" data-session="${session.id}">
                            <label>Roll <input name="roll_number" placeholder="STU001"></label>
                            <label>Status <select name="status"><option>Present</option><option>Late</option><option>Absent</option><option>Medical leave</option></select></label>
                            <button class="btn secondary" type="submit">Manual Backup</button>
                        </form>
                    ` : ""}
                    ${latest}
                </article>
            `;
        }).join("");
        const noteHtml = notes.map((note) => `
            <article class="smart-session-card">
                <span class="pill">Notes/PDF</span>
                <strong>${escapeHtml(note.title)}</strong>
                <p class="message">${escapeHtml(note.subject)} | Class ${escapeHtml(note.class_name)}-${escapeHtml(note.section)} | ${escapeHtml(note.file_name)}</p>
                <p class="lead">${escapeHtml(note.description)}</p>
                ${note.download_url ? `<div class="actions"><a class="btn secondary" href="${escapeHtml(note.download_url)}" target="_blank">Open Notes</a></div>` : ""}
            </article>
        `).join("");
        elements.smartSessionList.innerHTML = sessionHtml + noteHtml;
        elements.smartSessionList.querySelectorAll(".smart-submit-form").forEach((form) => form.addEventListener("submit", submitSmartAttendance));
        elements.smartSessionList.querySelectorAll(".smart-manual-form").forEach((form) => form.addEventListener("submit", submitManualAttendance));
    }

    function renderAttendancePortal(portal) {
        if (!elements.attendanceStudentList) return;
        const students = portal.students || [];
        const summary = portal.summary || {};
        const average = Number(summary.average || 0);

        elements.attendanceRing?.style.setProperty("--value", average);
        if (elements.attendanceRingValue) elements.attendanceRingValue.textContent = `${average}%`;
        if (elements.attendanceStudentCount) elements.attendanceStudentCount.textContent = `${students.length} students`;
        if (elements.attendanceHeroTitle) elements.attendanceHeroTitle.textContent = isStudent ? "My Attendance" : "Attendance Command";
        if (elements.attendanceHeroText) {
            elements.attendanceHeroText.textContent = `${summary.healthy_count || 0} healthy, ${summary.watch_count || 0} on watch, ${summary.critical_count || 0} critical across class attendance records.`;
        }

        if (elements.attendanceSummary) {
            elements.attendanceSummary.innerHTML = [
                ["Average", average, "%"],
                ["Healthy", summary.healthy_count || 0, ""],
                ["Watch", summary.watch_count || 0, ""],
                ["Critical", summary.critical_count || 0, ""],
            ].map(([label, value, suffix]) => `
                <article class="metric-card compact">
                    <div class="metric-label">${escapeHtml(label)}</div>
                    <div class="metric-value">${escapeHtml(value)}${escapeHtml(suffix)}</div>
                </article>
            `).join("");
        }

        if (!students.length) {
            elements.attendanceStudentList.innerHTML = `<p class="lead">No attendance records found.</p>`;
            renderAttendanceDetail(null);
            return;
        }

        if (!selectedAttendanceId || !students.some((item) => String(item.student.id) === String(selectedAttendanceId))) {
            selectedAttendanceId = students[0].student.id;
        }

        elements.attendanceStudentList.innerHTML = students.map((item) => {
            const student = item.student;
            const active = String(student.id) === String(selectedAttendanceId) ? "active" : "";
            return `
                <button class="attendance-row ${active}" type="button" data-attendance-student="${student.id}">
                    <span class="rank-badge">${escapeHtml(student.rank)}</span>
                    <span>
                        <strong>${escapeHtml(student.name)}</strong>
                        <small>${escapeHtml(student.roll_number)} | Class ${escapeHtml(student.class_name)}-${escapeHtml(student.section || "")}</small>
                    </span>
                    <span class="attendance-row-score">
                        <strong>${escapeHtml(item.overall_percentage)}%</strong>
                        <small>${escapeHtml(item.missed_classes)} missed</small>
                    </span>
                </button>
            `;
        }).join("");

        elements.attendanceStudentList.querySelectorAll("[data-attendance-student]").forEach((button) => {
            button.addEventListener("click", () => {
                selectedAttendanceId = button.dataset.attendanceStudent;
                renderAttendancePortal(attendancePortalData());
            });
        });

        const selected = students.find((item) => String(item.student.id) === String(selectedAttendanceId));
        renderAttendanceDetail(selected);
    }

    function renderAttendanceDetail(item) {
        if (!elements.attendanceDetail) return;
        if (!item) {
            elements.attendanceDetail.innerHTML = `<p class="lead">Open a student to review class attendance.</p>`;
            return;
        }

        const student = item.student;
        elements.attendanceDetailTitle.textContent = student.name;
        elements.attendanceDetailStatus.textContent = item.status;
        elements.attendanceDetailStatus.className = `pill ${attendancePillClass(item.status)}`;

        const classRows = item.classes.map((entry) => `
            <article class="attendance-class-card" data-subject="${escapeHtml(entry.subject_key)}">
                <div class="attendance-class-head">
                    <div>
                        <strong>${escapeHtml(entry.subject)}</strong>
                        <span class="muted">${escapeHtml(entry.attended_classes)} of ${escapeHtml(entry.total_classes)} classes attended</span>
                    </div>
                    <span class="pill ${attendancePillClass(entry.status)}">${escapeHtml(entry.percentage)}%</span>
                </div>
                <div class="progress"><div class="progress-fill" style="width: ${Math.min(100, Number(entry.percentage))}%"></div></div>
                <p class="message">${escapeHtml(entry.next_action)}</p>
                <div class="actions">
                    <a class="btn secondary" href="/api/attendance/pdf/${student.id}" target="_blank">Attendance PDF</a>
                    <a class="btn secondary" href="/api/report/pdf/${student.id}" target="_blank">Report PDF</a>
                </div>
                ${canManageStudents ? `
                    <form class="attendance-edit-form" data-student="${student.id}" data-subject="${escapeHtml(entry.subject_key)}">
                        <label>Attended <input name="attended_classes" type="number" min="0" max="500" value="${escapeHtml(entry.attended_classes)}"></label>
                        <label>Total <input name="total_classes" type="number" min="1" max="500" value="${escapeHtml(entry.total_classes)}"></label>
                        <button class="btn secondary" type="submit">Update</button>
                    </form>
                ` : ""}
            </article>
        `).join("");

        elements.attendanceDetail.innerHTML = `
            <div class="attendance-profile-strip">
                <div><span class="metric-label">Overall</span><strong>${escapeHtml(item.overall_percentage)}%</strong></div>
                <div><span class="metric-label">Attended</span><strong>${escapeHtml(item.attended_classes)}</strong></div>
                <div><span class="metric-label">Total</span><strong>${escapeHtml(item.total_classes)}</strong></div>
                <div><span class="metric-label">Low Subjects</span><strong>${escapeHtml(item.low_subject_count)}</strong></div>
            </div>
            <div class="attendance-profile-strip">
                <div><span class="metric-label">Need For 75%</span><strong>${escapeHtml(item.classes_needed_for_75)}</strong></div>
                <div><span class="metric-label">Can Miss</span><strong>${escapeHtml(item.classes_can_miss)}</strong></div>
                <div><span class="metric-label">Predicted</span><strong>${escapeHtml(item.predicted_semester_attendance)}%</strong></div>
                <div><span class="metric-label">Streak</span><strong>${escapeHtml((item.streaks || [])[0] || "-")}</strong></div>
            </div>
            <div class="weekly-bars">
                ${(item.weekly_graph || []).map((point) => `<div class="weekly-bar"><span style="height:${Math.max(8, Number(point.value || 0))}%"></span>${escapeHtml(point.label)}</div>`).join("")}
            </div>
            <div class="tag-cloud">${(item.ai_suggestions || []).map((suggestion) => `<span class="pill warning">${escapeHtml(suggestion)}</span>`).join("")}</div>
            ${item.lowest_subject ? `<p class="lead">Lowest attendance: ${escapeHtml(item.lowest_subject.subject)} at ${escapeHtml(item.lowest_subject.percentage)}%.</p>` : ""}
            <div class="attendance-class-grid">${classRows}</div>
        `;

        elements.attendanceDetail.querySelectorAll(".attendance-edit-form").forEach((form) => {
            form.addEventListener("submit", updateAttendanceClass);
        });
    }

    function renderParentMessages(messages = []) {
        if (!elements.parentAlertGrid) return;
        if (!messages.length) {
            elements.parentAlertGrid.innerHTML = `
                <article class="insight-card">
                    <span class="pill success">Clear</span>
                    <h3 style="margin-top: 12px;">No urgent messages</h3>
                    <p class="lead">Your linked wards are currently clear of low-mark and attendance warnings.</p>
                </article>
            `;
            return;
        }
        elements.parentAlertGrid.innerHTML = messages.map((item) => `
            <article class="parent-alert-card ${escapeHtml(item.tone)}">
                <span class="pill ${escapeHtml(item.tone)}">${escapeHtml(item.type)}</span>
                <h3>${escapeHtml(item.title)}</h3>
                <p class="lead">${escapeHtml(item.text)}</p>
                <p class="message">${escapeHtml(item.meta)}</p>
                <div class="actions">
                    <a class="btn secondary" href="/api/report/pdf/${item.student_id}" target="_blank">Report PDF</a>
                    <a class="btn secondary" href="/api/attendance/pdf/${item.student_id}" target="_blank">Attendance PDF</a>
                </div>
            </article>
        `).join("");
    }

    function renderParentPortal() {
        if (!elements.parentWardGrid) return;
        const wards = dashboardData?.students || [];
        if (!wards.length) {
            elements.parentWardFocus.innerHTML = `
                <span class="feature-icon">WD</span>
                <h3>No ward opened yet</h3>
                <p class="lead">Search a registered student by name or roll number to unlock marks analysis, attendance, reports, and parent messages.</p>
            `;
            elements.parentWardGrid.innerHTML = `
                <article class="parent-empty-state">
                    <h3>Start with the search box above</h3>
                    <p class="lead">Once you open a student, their analytics will stay available in this parent portal.</p>
                </article>
            `;
            return;
        }

        const primary = wards[0];
        elements.parentWardFocus.innerHTML = `
            <p class="eyebrow">Active ward</p>
            <h3>${escapeHtml(primary.name)}</h3>
            <div class="details-list">
                <div><span>Roll Number</span><strong>${escapeHtml(primary.roll_number)}</strong></div>
                <div><span>Class</span><strong>${escapeHtml(primary.class_name)}-${escapeHtml(primary.section || "")}</strong></div>
                <div><span>Marks</span><strong>${escapeHtml(primary.percentage)}%</strong></div>
                <div><span>Attendance</span><strong>${escapeHtml(primary.attendance)}%</strong></div>
                <div><span>Risk</span><strong>${escapeHtml(primary.risk_level)}</strong></div>
            </div>
            <div class="actions" style="margin-top: 14px;">
                <button class="btn secondary" type="button" data-parent-view="${primary.id}">Open Analysis</button>
                <a class="btn secondary" href="/api/report/pdf/${primary.id}" target="_blank">Report PDF</a>
                <a class="btn secondary" href="/api/attendance/pdf/${primary.id}" target="_blank">Attendance PDF</a>
            </div>
        `;

        elements.parentWardGrid.innerHTML = wards.map((ward) => `
            <article class="parent-ward-card">
                <div class="parent-ward-top">
                    <span class="rank-badge">${escapeHtml(ward.rank)}</span>
                    <div>
                        <h3>${escapeHtml(ward.name)}</h3>
                        <p class="message">${escapeHtml(ward.roll_number)} | Class ${escapeHtml(ward.class_name)}-${escapeHtml(ward.section || "")}</p>
                    </div>
                    <span class="pill ${riskClass(ward.risk_level)}">${escapeHtml(ward.risk_level)}</span>
                </div>
                <div class="parent-metric-row">
                    <div><span>Marks</span><strong>${escapeHtml(ward.percentage)}%</strong></div>
                    <div><span>Attendance</span><strong>${escapeHtml(ward.attendance)}%</strong></div>
                    <div><span>Predicted</span><strong>${escapeHtml(ward.predicted_percentage)}%</strong></div>
                </div>
                <div class="actions">
                    <button class="btn secondary" type="button" data-parent-view="${ward.id}">Full Analysis</button>
                    <a class="btn secondary" href="/api/attendance/pdf/${ward.id}" target="_blank">Attendance PDF</a>
                    <a class="btn secondary" href="/api/report/pdf/${ward.id}" target="_blank">Report PDF</a>
                </div>
            </article>
        `).join("");

        document.querySelectorAll("[data-parent-view]").forEach((button) => {
            button.addEventListener("click", () => selectStudent(button.dataset.parentView, true));
        });
    }

    async function searchParentStudent(query) {
        if (!elements.parentLookupResults) return;
        const value = query.trim();
        if (value.length < 2) {
            elements.parentLookupResults.innerHTML = `<p class="message">Type at least 2 characters.</p>`;
            return;
        }
        try {
            showLoading(true);
            const results = await fetchJson(`/api/parent/student-lookup?q=${encodeURIComponent(value)}`);
            elements.parentLookupResults.innerHTML = results.length ? results.map((student) => `
                <article class="parent-lookup-card">
                    <div>
                        <strong>${escapeHtml(student.name)}</strong>
                        <p class="message">${escapeHtml(student.roll_number)} | Class ${escapeHtml(student.class_name)}-${escapeHtml(student.section || "")} | ${escapeHtml(student.stream || "")}</p>
                    </div>
                    <div class="parent-lookup-score">
                        <span class="pill">${escapeHtml(student.percentage)}%</span>
                        <button class="btn secondary" type="button" data-parent-open="${student.id}">${student.linked ? "Open" : "Open Ward"}</button>
                    </div>
                </article>
            `).join("") : `<p class="lead">No registered student matched that name.</p>`;

            elements.parentLookupResults.querySelectorAll("[data-parent-open]").forEach((button) => {
                button.addEventListener("click", () => openParentWard(button.dataset.parentOpen));
            });
        } catch (error) {
            elements.parentLookupResults.innerHTML = `<p class="message error">${escapeHtml(error.message)}</p>`;
        } finally {
            showLoading(false);
        }
    }

    async function openParentWard(studentId) {
        try {
            showLoading(true);
            await fetchJson(`/api/parent/students/${studentId}/link`, { method: "POST" });
            await loadDashboard();
            await selectStudent(studentId, false);
            switchView("parent-portal");
            window.showToast("Ward analytics opened");
        } catch (error) {
            window.showToast(error.message);
        } finally {
            showLoading(false);
        }
    }

    async function updateAttendanceClass(event) {
        event.preventDefault();
        const form = event.currentTarget;
        const payload = Object.fromEntries(new FormData(form).entries());
        payload.attended_classes = Number(payload.attended_classes || 0);
        payload.total_classes = Number(payload.total_classes || 0);
        if (payload.attended_classes > payload.total_classes) {
            window.showToast("Attended classes cannot exceed total classes");
            return;
        }
        try {
            showLoading(true);
            await fetchJson(`/api/attendance/${form.dataset.student}/${form.dataset.subject}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const portal = await fetchJson("/api/attendance");
            dashboardData.attendance_portal = portal;
            renderAttendancePortal(portal);
            await loadDashboard();
            switchView("attendance");
            window.showToast("Attendance updated");
        } catch (error) {
            window.showToast(error.message);
        } finally {
            showLoading(false);
        }
    }

    async function createSmartSession(event) {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
        ["radius_meters", "latitude", "longitude"].forEach((field) => {
            if (payload[field] !== "") payload[field] = Number(payload[field]);
        });
        const defaultMeetingUrl = "https://zoom.us/start/videomeeting";
        const initialMeetingUrl = String(payload.meeting_url || "").trim() || defaultMeetingUrl;
        const meetingWindow = window.open(initialMeetingUrl, "_blank");
        try {
            showLoading(true);
            const data = await fetchJson("/api/smart-attendance/sessions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            await loadDashboard();
            switchView("attendance");
            window.showToast("Smart attendance session generated");
            if (meetingWindow && data.session?.meeting_url && data.session.meeting_url !== initialMeetingUrl) {
                meetingWindow.location.href = data.session.meeting_url;
            }
        } catch (error) {
            if (meetingWindow) meetingWindow.close();
            window.showToast(error.message);
        } finally {
            showLoading(false);
        }
    }

    async function submitSmartAttendance(event) {
        event.preventDefault();
        const form = event.currentTarget;
        const payload = Object.fromEntries(new FormData(form).entries());
        payload.face_verified = payload.face_verified === "true";
        payload.selfie_verified = true;
        try {
            if (navigator.geolocation) {
                const position = await new Promise((resolve) => navigator.geolocation.getCurrentPosition(resolve, () => resolve(null), { timeout: 2500 }));
                if (position) {
                    payload.latitude = position.coords.latitude;
                    payload.longitude = position.coords.longitude;
                }
            }
            showLoading(true);
            const data = await fetchJson(`/api/smart-attendance/sessions/${form.dataset.session}/submit`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            await loadDashboard();
            window.showToast(`Attendance ${data.submission.status}: ${data.submission.risk_flags}`);
        } catch (error) {
            window.showToast(error.message);
        } finally {
            showLoading(false);
        }
    }

    async function submitManualAttendance(event) {
        event.preventDefault();
        const form = event.currentTarget;
        const payload = Object.fromEntries(new FormData(form).entries());
        try {
            showLoading(true);
            await fetchJson(`/api/smart-attendance/sessions/${form.dataset.session}/manual`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            await loadDashboard();
            switchView("attendance");
            window.showToast("Manual attendance saved");
        } catch (error) {
            window.showToast(error.message);
        } finally {
            showLoading(false);
        }
    }

    async function createTeacherNote(event) {
        event.preventDefault();
        const form = event.currentTarget;
        const payload = new FormData(form);
        try {
            showLoading(true);
            await fetchJson("/api/teacher/notes", { method: "POST", body: payload });
            form.reset();
            await loadDashboard();
            window.showToast("Notes added");
        } catch (error) {
            window.showToast(error.message);
        } finally {
            showLoading(false);
        }
    }

    function addAssistantMessage(text, type = "bot") {
        if (!elements.assistantMessages) return;
        const node = document.createElement("div");
        node.className = `assistant-message ${type}`;
        node.textContent = text;
        elements.assistantMessages.appendChild(node);
        elements.assistantMessages.scrollTop = elements.assistantMessages.scrollHeight;
        return node;
    }

    async function askAssistant(event) {
        event.preventDefault();
        const message = elements.assistantInput?.value.trim();
        if (!message) return;
        elements.assistantInput.value = "";
        addAssistantMessage(message, "user");
        const thinking = addAssistantMessage("I am listening...", "bot thinking");
        try {
            const data = await fetchJson("/api/assistant", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message, student_id: selectedStudent?.id }),
            });
            if (thinking) thinking.remove();
            addAssistantMessage(data.reply || "I am here, but I could not find the right words for that. Say it another way?");
        } catch (error) {
            if (thinking) thinking.remove();
            addAssistantMessage(error.message);
        }
    }

    function populateSelfMarksForm(student) {
        if (!elements.selfMarksForm || role !== "student") return;
        const form = elements.selfMarksForm;
        ["class_name", "section", "stream", "attendance", "internal_marks", "semester_marks"].forEach((field) => {
            if (form.elements[field]) form.elements[field].value = student[field] ?? "";
        });
        Object.entries(student.subject_fields || {}).forEach(([field, value]) => {
            if (form.elements[field]) form.elements[field].value = value;
        });
    }

    function renderUsers(users) {
        if (!elements.usersBody) return;
        elements.userCount.textContent = `${users.length} users`;
        elements.usersBody.innerHTML = users.map((user) => `
            <tr>
                <td><strong>${escapeHtml(user.full_name || user.username)}</strong></td>
                <td>${escapeHtml(user.username)}</td>
                <td>${escapeHtml(user.email || "-")}</td>
                <td><span class="pill">${escapeHtml(user.role)}</span></td>
                <td><button class="btn danger" type="button" data-user-delete="${user.id}">Delete</button></td>
            </tr>
        `).join("");
        elements.usersBody.querySelectorAll("[data-user-delete]").forEach((button) => {
            button.addEventListener("click", () => deleteUser(button.dataset.userDelete));
        });
    }

    async function loadUsers() {
        if (role !== "admin" || !elements.usersBody) return;
        try {
            const users = await fetchJson("/api/users");
            renderUsers(users);
        } catch (error) {
            window.showToast(error.message);
        }
    }

    async function deleteUser(id) {
        if (!confirm("Delete this user account?")) return;
        try {
            showLoading(true);
            await fetchJson(`/api/users/${id}`, { method: "DELETE" });
            await loadUsers();
            window.showToast("User deleted");
        } catch (error) {
            window.showToast(error.message);
        } finally {
            showLoading(false);
        }
    }

    function renderProfile(student) {
        selectedStudent = student;
        const prediction = student.prediction;
        const pdfUrl = `/api/report/pdf/${student.id}`;
        elements.reportPdfLink.href = pdfUrl;
        elements.selectedPdfLink.href = pdfUrl;
        populateSelfMarksForm(student);

        const subjectChips = Object.entries(student.subjects).map(([subject, marks]) => `
            <div class="subject-chip">
                <span>${escapeHtml(subject)}</span>
                <strong>${escapeHtml(marks)}</strong>
                <div class="progress"><div class="progress-fill" style="width: ${Math.min(100, Number(marks))}%"></div></div>
            </div>
        `).join("");

        elements.profile.innerHTML = `
            <header>
                <div>
                    <p class="eyebrow">Rank #${escapeHtml(student.rank)}</p>
                    <h3>${escapeHtml(student.name)}</h3>
                </div>
                <span class="pill">${escapeHtml(prediction.risk_level)}</span>
            </header>
            <div class="details-list">
                <div><span>Roll Number</span><strong>${escapeHtml(student.roll_number)}</strong></div>
                <div><span>Class</span><strong>${escapeHtml(student.class_name)}-${escapeHtml(student.section || "")}</strong></div>
                <div><span>Stream</span><strong>${escapeHtml(student.stream || "")}</strong></div>
                <div><span>Current Percentage</span><strong>${escapeHtml(student.percentage)}%</strong></div>
                <div><span>Expected Final Result</span><strong>${escapeHtml(prediction.expected_final_result)}%</strong></div>
                <div><span>Improvement Chance</span><strong>${escapeHtml(prediction.improvement_chance)}%</strong></div>
                <div><span>Pass/Fail</span><strong>${escapeHtml(prediction.pass_fail)}</strong></div>
            </div>
            <div style="margin: 18px 0;">
                <span class="metric-label">AI Confidence</span>
                <div class="progress" style="margin-top: 8px;"><div class="progress-fill" style="width: ${prediction.confidence}%"></div></div>
                <p class="message">${escapeHtml(prediction.confidence)}%</p>
            </div>
            <div class="tag-cloud">
                <span class="pill success">Strong: ${escapeHtml(student.strong_subjects.join(", ") || "Building")}</span>
                <span class="pill warning">Focus: ${escapeHtml(student.weak_subjects.join(", ") || "None")}</span>
            </div>
            <div class="subject-grid">${subjectChips}</div>
            <div style="margin-top: 18px;">
                <h3>Recommendations</h3>
                <div class="insight-grid">
                    ${prediction.recommendations.map((item) => `<div class="insight-card">${escapeHtml(item)}</div>`).join("")}
                </div>
            </div>
        `;

        renderChart("profile", "profileChart", {
            type: "bar",
            data: {
                labels: Object.keys(student.subjects),
                datasets: [{
                    label: student.name,
                    data: Object.values(student.subjects),
                    backgroundColor: "rgba(34,211,238,0.72)",
                    borderColor: "#22d3ee",
                    borderWidth: 1,
                    borderRadius: 8,
                }],
            },
            options: baseChartOptions(),
        });
    }

    async function selectStudent(id, openPrediction = false) {
        try {
            showLoading(true);
            const student = await fetchJson(`/api/students/${id}`);
            renderProfile(student);
            if (openPrediction) switchView("prediction");
        } catch (error) {
            window.showToast(error.message);
        } finally {
            showLoading(false);
        }
    }

    async function editStudent(id) {
        try {
            const student = await fetchJson(`/api/students/${id}`);
            const form = elements.studentForm;
            elements.studentFormTitle.textContent = `Edit ${student.name}`;
            elements.studentId.value = student.id;
            ["name", "roll_number", "class_name", "section", "stream", "attendance", "internal_marks", "semester_marks"].forEach((field) => {
                if (form.elements[field]) form.elements[field].value = student[field] ?? "";
            });
            Object.entries(student.subject_fields).forEach(([field, value]) => {
                if (form.elements[field]) form.elements[field].value = value;
            });
            switchView("students");
        } catch (error) {
            window.showToast(error.message);
        }
    }

    async function deleteStudent(id) {
        if (!confirm("Delete this student record?")) return;
        try {
            showLoading(true);
            await fetchJson(`/api/students/${id}`, { method: "DELETE" });
            await loadDashboard();
            window.showToast("Student deleted");
        } catch (error) {
            window.showToast(error.message);
        } finally {
            showLoading(false);
        }
    }

    function resetStudentForm() {
        elements.studentForm?.reset();
        if (elements.studentId) elements.studentId.value = "";
        if (elements.studentFormTitle) elements.studentFormTitle.textContent = "Add Student";
        setMessage(elements.studentFormMessage, "");
    }

    function switchView(view) {
        document.querySelectorAll(".view-section").forEach((section) => {
            section.classList.toggle("active", section.id === `view-${view}`);
        });
        document.querySelectorAll(".sidebar-link").forEach((link) => {
            link.classList.toggle("active", link.dataset.view === view);
        });
        elements.sidebar.classList.remove("open");
        if (view === "users") loadUsers();
    }

    async function handleSearch(value) {
        const query = value.trim();
        if (query.length < 2) {
            elements.searchResults.classList.remove("open");
            elements.searchResults.innerHTML = "";
            return;
        }
        try {
            const results = await fetchJson(`/api/search?q=${encodeURIComponent(query)}`);
            elements.searchResults.innerHTML = results.length ? results.map((student) => `
                <div class="search-result" data-id="${student.id}">
                    <strong>${escapeHtml(student.name)}</strong>
                    <span class="muted">${escapeHtml(student.roll_number)} | ${escapeHtml(student.class_name)} | ${escapeHtml(student.stream)}</span>
                    <span class="pill">${escapeHtml(student.predicted_percentage)}% predicted</span>
                </div>
            `).join("") : `<div class="search-result">No matches found</div>`;
            elements.searchResults.classList.add("open");
            elements.searchResults.querySelectorAll("[data-id]").forEach((node) => {
                node.addEventListener("click", () => {
                    elements.searchResults.classList.remove("open");
                    elements.searchInput.value = "";
                    selectStudent(node.dataset.id, true);
                });
            });
        } catch (error) {
            window.showToast(error.message);
        }
    }

    async function loadDashboard() {
        showLoading(true);
        try {
            dashboardData = await fetchJson("/api/analytics/overview");
            renderStats(dashboardData.stats);
            applyStudentFilters();
            renderCharts(dashboardData);
            renderHeatmap(dashboardData.heatmap);
            renderInsights(dashboardData.insights);
            renderRecentActivity(dashboardData.recent_activity);
            renderToppers(dashboardData.toppers);
            renderAttendancePortal(dashboardData.attendance_portal);
            renderSmartAttendance(dashboardData.smart_attendance);
            renderParentMessages(dashboardData.parent_messages || []);
            renderParentPortal();
            if (dashboardData.students.length && !selectedStudent) {
                await selectStudent(dashboardData.students[0].id, false);
            }
            if (role === "admin") loadUsers();
            if (isParent && !parentInitialViewShown) {
                parentInitialViewShown = true;
                switchView("parent-portal");
            }
        } catch (error) {
            window.showToast(error.message);
        } finally {
            showLoading(false);
        }
    }

    document.querySelectorAll(".sidebar-link").forEach((link) => {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            if (!link.classList.contains("hidden")) switchView(link.dataset.view);
        });
    });

    document.getElementById("openSidebar")?.addEventListener("click", () => elements.sidebar.classList.add("open"));
    document.getElementById("closeSidebar")?.addEventListener("click", () => elements.sidebar.classList.remove("open"));
    document.getElementById("resetStudentForm")?.addEventListener("click", resetStudentForm);
    elements.smartSessionForm?.addEventListener("submit", createSmartSession);
    elements.teacherNoteForm?.addEventListener("submit", createTeacherNote);
    elements.assistantToggle?.addEventListener("click", () => elements.assistantPanel?.classList.toggle("open"));
    elements.assistantClose?.addEventListener("click", () => elements.assistantPanel?.classList.remove("open"));
    elements.assistantForm?.addEventListener("submit", askAssistant);

    elements.searchInput?.addEventListener("input", (event) => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => handleSearch(event.target.value), 220);
    });

    elements.studentFilters?.addEventListener("input", applyStudentFilters);
    elements.studentFilters?.addEventListener("change", applyStudentFilters);
    elements.studentFilters?.addEventListener("reset", () => {
        setTimeout(applyStudentFilters, 0);
    });

    elements.parentLookupForm?.addEventListener("submit", (event) => {
        event.preventDefault();
        searchParentStudent(elements.parentLookupInput?.value || "");
    });

    elements.studentForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const payload = Object.fromEntries(new FormData(form).entries());
        numberFields.forEach((field) => {
            payload[field] = Number(payload[field] || 0);
        });
        const id = elements.studentId.value;
        try {
            showLoading(true);
            await fetchJson(id ? `/api/students/${id}` : "/api/students", {
                method: id ? "PUT" : "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            resetStudentForm();
            await loadDashboard();
            setMessage(elements.studentFormMessage, "Student record saved", "success");
            window.showToast("Student record saved");
        } catch (error) {
            setMessage(elements.studentFormMessage, error.message, "error");
        } finally {
            showLoading(false);
        }
    });

    elements.selfMarksForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const payload = Object.fromEntries(new FormData(form).entries());
        numberFields.forEach((field) => {
            if (field in payload) payload[field] = Number(payload[field] || 0);
        });
        try {
            showLoading(true);
            const data = await fetchJson("/api/student/marks", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            await loadDashboard();
            if (data.student) renderProfile(data.student);
            setMessage(elements.selfMarksMessage, "Your marks were updated", "success");
            window.showToast("Student analytics updated");
        } catch (error) {
            setMessage(elements.selfMarksMessage, error.message, "error");
        } finally {
            showLoading(false);
        }
    });

    elements.uploadForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const body = new FormData(event.currentTarget);
        try {
            showLoading(true);
            const data = await fetchJson("/api/upload/csv", { method: "POST", body });
            await loadDashboard();
            setMessage(elements.uploadMessage, `Added ${data.count}, updated ${data.updated}, skipped ${data.skipped}`, "success");
            window.showToast("Dataset imported");
        } catch (error) {
            setMessage(elements.uploadMessage, error.message, "error");
        } finally {
            showLoading(false);
        }
    });

    document.getElementById("trainModelBtn")?.addEventListener("click", async () => {
        try {
            showLoading(true);
            const data = await fetchJson("/api/train-model", { method: "POST" });
            await loadDashboard();
            window.showToast(data.message);
        } catch (error) {
            window.showToast(error.message);
        } finally {
            showLoading(false);
        }
    });

    document.addEventListener("click", (event) => {
        if (!event.target.closest(".search-box")) {
            elements.searchResults?.classList.remove("open");
        }
    });

    applyRoleVisibility();
    updateClock();
    setInterval(updateClock, 1000);
    loadDashboard();
})();
