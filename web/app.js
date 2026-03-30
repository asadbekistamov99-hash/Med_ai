const API = location.origin;

// HOZIR FAQAT SHU TELEGRAM ACCOUNTGA ULANGAN
const FIXED_USER_ID = 7756050428;

let currentComplaint = "";

function showTab(tabId, btn) {
    document.querySelectorAll(".tab-content").forEach((el) => el.classList.remove("active"));
    document.querySelectorAll(".tab-btn").forEach((el) => el.classList.remove("active"));

    document.getElementById(tabId).classList.add("active");
    btn.classList.add("active");
}

function safeText(text) {
    return String(text ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

async function findDrug() {
    const text = document.getElementById("drug").value.trim();
    const box = document.getElementById("drugResult");

    if (!text) {
        alert("Dori nomini yozing");
        return;
    }

    box.innerHTML = `<div class="loader">Qidirilmoqda...</div>`;

    try {
        const res = await fetch(API + "/api/pill/identify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        const data = await res.json();
        box.innerHTML = `<div class="result-card">${safeText(data.answer || "Javob topilmadi")}</div>`;
    } catch (e) {
        box.innerHTML = `<div class="status-box">Dori qidirishda xato yuz berdi</div>`;
    }
}

async function startAnalysis() {
    const text = document.getElementById("symptom").value.trim();

    if (!text) {
        alert("Simptom yozing");
        return;
    }

    currentComplaint = text;
    document.getElementById("questions").innerHTML = `<div class="loader">Yuklanmoqda...</div>`;
    document.getElementById("result").innerHTML = "";

    try {
        const res = await fetch(API + "/api/symptom/questions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        const data = await res.json();

        let html = `
            <div class="result-card">
                <strong>${safeText(data.title || "Simptom")}</strong><br>
                ${safeText(data.medical_name || "")}
            </div>
        `;

        (data.questions || []).forEach((q, i) => {
            html += `
                <div class="q">
                    <label>${safeText(q)}</label>
                    <input id="q${i}" placeholder="Javob yozing" />
                </div>
            `;
        });

        html += `<button class="primary-btn" onclick="analyzeCurrent()">Analiz qilish</button>`;
        document.getElementById("questions").innerHTML = html;
    } catch (e) {
        document.getElementById("questions").innerHTML =
            `<div class="status-box">Simptom bo‘limida xato yuz berdi</div>`;
    }
}

function analyzeCurrent() {
    analyze(currentComplaint);
}

async function analyze(text) {
    const inputs = document.querySelectorAll("[id^='q']");
    const answers = [];

    inputs.forEach((i) => {
        answers.push((i.value || "").trim());
    });

    document.getElementById("result").innerHTML =
        `<div class="loader">Analiz qilinmoqda...</div>`;

    try {
        const res = await fetch(API + "/api/symptom/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                complaint: text,
                answers: answers
            })
        });

        const data = await res.json();

        document.getElementById("result").innerHTML =
            `<div class="result-card">${safeText(data.result || "Natija topilmadi")}</div>`;
    } catch (e) {
        document.getElementById("result").innerHTML =
            `<div class="status-box">Analizda xato yuz berdi</div>`;
    }
}

async function addReminder() {
    const med = document.getElementById("med").value.trim();
    const time = document.getElementById("time").value;
    const box = document.getElementById("reminderStatus");

    if (!med || !time) {
        alert("Dori va vaqt kiriting");
        return;
    }

    box.innerHTML = `<div class="loader">Saqlanmoqda...</div>`;

    try {
        const res = await fetch(API + "/api/reminder/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: FIXED_USER_ID,
                med: med,
                hhmm: time
            })
        });

        const data = await res.json();

        if (data.ok) {
            let text = `✅ Saqlandi\n\nUser ID: ${FIXED_USER_ID}\n\n`;

            (data.reminders || []).forEach((r) => {
                text += `💊 ${r.med} — ${r.hhmm}\n`;
            });

            box.innerHTML = `<div class="result-card">${safeText(text)}</div>`;
        } else {
            box.innerHTML = `<div class="status-box">${safeText(data.error || "Xato")}</div>`;
        }
    } catch (e) {
        box.innerHTML = `<div class="status-box">Saqlashda xato yuz berdi</div>`;
    }
}

async function loadStats() {
    const box = document.getElementById("statsResult");
    if (!box) return;

    box.innerHTML = `<div class="loader">Yuklanmoqda...</div>`;

    try {
        const res = await fetch(API + "/api/stats", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: FIXED_USER_ID
            })
        });

        const data = await res.json();

        box.innerHTML = `
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-number">${data.took ?? 0}</div>
                    <div class="stat-label">Vaqtida ichildi</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">${data.late_took ?? 0}</div>
                    <div class="stat-label">Kechikib ichildi</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">${data.missed ?? 0}</div>
                    <div class="stat-label">O‘tkazib yuborildi</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">${data.adherence_percent ?? 0}%</div>
                    <div class="stat-label">Intizom foizi</div>
                </div>
            </div>
        `;
    } catch (e) {
        box.innerHTML = `<div class="status-box">Statistikada xato yuz berdi</div>`;
    }
}