/* 主控：分頁、API、破解輪詢、檔案選擇、學習庫設定、更新、語音 */
(() => {
  const API = "";               // 同源後端（桌面版 pywebview / 本機伺服器）
  const isDesktop = () => !!(window.pywebview && window.pywebview.api);
  let hasBackend = true;        // 線上純前端時由 local.js 設 false

  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];

  function toast(msg) {
    const t = $("#toast"); t.textContent = msg; t.classList.add("show");
    clearTimeout(t._tm); t._tm = setTimeout(() => t.classList.remove("show"), 2200);
  }

  async function api(path, opts) {
    const r = await fetch(API + path, opts);
    return r.json();
  }

  function copyBtn(text) {
    const b = document.createElement("button");
    b.className = "copy-btn"; b.textContent = "複製";
    b.onclick = () => { navigator.clipboard.writeText(text); toast("已複製"); };
    return b;
  }

  function pwCard(label, value, extra) {
    const d = document.createElement("div"); d.className = "pwcard";
    const left = document.createElement("div");
    left.innerHTML = `<div class="k">${label}</div><div class="v">${value || "（空）"}</div>` +
      (extra ? `<div class="k">${extra}</div>` : "");
    d.appendChild(left);
    if (value) d.appendChild(copyBtn(value));
    return d;
  }

  /* ---------- 分頁切換 ---------- */
  $$(".tab").forEach(t => {
    t.onclick = () => {
      $$(".tab").forEach(x => x.classList.remove("active"));
      $$(".panel").forEach(x => x.classList.remove("active"));
      t.classList.add("active");
      $("#panel-" + t.dataset.tab).classList.add("active");
      if (Voice.isEnabled()) Voice.speakScript(t.dataset.tab);
    };
  });

  /* ---------- 語音 ---------- */
  $("#voiceToggle").onclick = () => {
    const on = !Voice.isEnabled();
    Voice.setEnabled(on);
    $("#voiceToggle").textContent = on ? "🔊 語音教學：開" : "🔇 語音教學：關";
    if (on) Voice.speak("voiceon");
  };
  $$(".voice-btn").forEach(b => b.onclick = () => Voice.speakScript(b.dataset.voice, b));

  /* ---------- WiFi ---------- */
  $("#wifiLoad").onclick = async () => {
    const box = $("#wifiResult"); box.innerHTML = '<span class="spinner"></span>讀取中…';
    try {
      const r = await api("/api/wifi/list");
      box.innerHTML = "";
      if (!r.items || !r.items.length) { box.innerHTML = '<div class="fail-box">沒有找到已儲存的 WiFi。</div>'; return; }
      r.items.forEach(it => box.appendChild(pwCard(it.ssid, it.password, it.auth)));
    } catch (e) { box.innerHTML = `<div class="fail-box">讀取失敗：${e}</div>`; }
  };

  /* ---------- 文字抓密碼 ---------- */
  $("#textRun").onclick = async () => {
    const box = $("#textResult"); const text = $("#textInput").value;
    if (!text.trim()) { toast("請先貼上文字"); return; }
    box.innerHTML = '<span class="spinner"></span>分析中…';
    try {
      const r = hasBackend
        ? await api("/api/text/extract", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) })
        : { items: Local.extract(text) };
      box.innerHTML = "";
      if (!r.items.length) { box.innerHTML = '<div class="fail-box">沒有在文字中找到密碼。</div>'; return; }
      r.items.forEach(it => box.appendChild(pwCard("找到密碼", it.password, it.context)));
    } catch (e) { box.innerHTML = `<div class="fail-box">分析失敗：${e}</div>`; }
  };

  /* ---------- 星號 ---------- */
  $("#starRun").onclick = async () => {
    const box = $("#starResult");
    if (!hasBackend) { box.innerHTML = '<div class="fail-box">星號顯示需要桌面版（線上版無系統權限）。</div>'; return; }
    box.innerHTML = '<span class="spinner"></span>讀取游標下的欄位…';
    try {
      const r = await api("/api/star/reveal");
      if (r.ok) box.innerHTML = "", box.appendChild(pwCard("還原結果", r.password, "控制項：" + (r.class || "")));
      else box.innerHTML = `<div class="fail-box">${r.error || "讀不到"}</div>`;
    } catch (e) { box.innerHTML = `<div class="fail-box">失敗：${e}</div>`; }
  };

  /* ---------- 郵件 ---------- */
  $("#mailLoad").onclick = async () => {
    const box = $("#mailResult");
    if (!hasBackend) { box.innerHTML = '<div class="fail-box">郵件密碼需要桌面版。</div>'; return; }
    box.innerHTML = '<span class="spinner"></span>讀取本機郵件設定…';
    try {
      const r = await api("/api/mail/list");
      box.innerHTML = "";
      const all = [...(r.thunderbird || []), ...(r.outlook || [])];
      const real = all.filter(x => !x.error);
      if (!real.length) {
        const errs = all.filter(x => x.error).map(x => x.error);
        box.innerHTML = `<div class="fail-box">沒有讀到郵件密碼。${errs.join("；") || "可能未安裝 Thunderbird / Outlook，或帳號未存密碼。"}</div>`;
        return;
      }
      real.forEach(x => box.appendChild(pwCard(
        `${x.source} · ${x.host || x.account || ""}`,
        x.password, x.username ? "帳號：" + x.username : "")));
    } catch (e) { box.innerHTML = `<div class="fail-box">失敗：${e}</div>`; }
  };

  /* ---------- 檔案選擇 ---------- */
  async function pickFile(inputId) {
    if (isDesktop()) {
      const p = await window.pywebview.api.pick_file();
      if (p) $("#" + inputId).value = p;
    } else {
      toast("線上版請直接貼上檔案路徑，或改用桌面版");
    }
  }
  $("#archivePick").onclick = () => pickFile("archivePath");
  $("#officePick").onclick = () => pickFile("officePath");

  /* ---------- 破解（壓縮檔 / Office 共用） ---------- */
  function setupCrack(cfg) {
    Options.build(cfg.optsId, cfg.prefix);
    let jobId = null, polling = null;
    const startBtn = $("#" + cfg.startBtn), stopBtn = $("#" + cfg.stopBtn);
    const prog = $("#" + cfg.progId), res = $("#" + cfg.resId);

    startBtn.onclick = async () => {
      const path = $("#" + cfg.pathId).value.trim();
      if (!path) { toast("請先選擇或輸入檔案路徑"); return; }
      if (!hasBackend) { res.innerHTML = '<div class="fail-box">此功能需要桌面版。</div>'; return; }
      res.innerHTML = ""; prog.innerHTML = '<span class="spinner"></span>啟動中…';
      startBtn.disabled = true; stopBtn.disabled = false;
      try {
        const r = await api("/api/crack/start", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path, target: cfg.target, options: Options.collect(cfg.prefix) })
        });
        if (!r.ok) { prog.innerHTML = ""; res.innerHTML = `<div class="fail-box">${r.error}</div>`; reset(); return; }
        jobId = r.job;
        polling = setInterval(poll, 600);
      } catch (e) { prog.innerHTML = ""; res.innerHTML = `<div class="fail-box">${e}</div>`; reset(); }
    };

    stopBtn.onclick = async () => {
      if (jobId) await api("/api/crack/stop/" + jobId, { method: "POST" });
      toast("已要求停止…");
    };

    async function poll() {
      if (!jobId) return;
      const r = await api("/api/crack/status/" + jobId);
      if (!r.ok) return;
      prog.innerHTML = `<span class="spinner"></span>已嘗試 <b>${r.tried.toLocaleString()}</b> 組` +
        (r.current ? ` · 目前：<code>${escapeHtml(r.current)}</code>` : "") +
        ` · ${r.elapsed.toFixed(1)} 秒`;
      if (["done", "stopped", "error"].includes(r.status)) {
        clearInterval(polling); prog.innerHTML = ""; reset();
        if (r.status === "error") { res.innerHTML = `<div class="fail-box">發生錯誤：${r.error}</div>`; return; }
        if (r.found) {
          res.innerHTML = `<div class="found-box">✅ 找到密碼！<div class="big">${escapeHtml(r.password || r.note || "")}</div>
            <div class="k" style="margin-top:6px">嘗試 ${r.tried.toLocaleString()} 組 · ${r.elapsed.toFixed(1)} 秒 · 已存入學習庫，下次更快</div></div>`;
          if (r.password) { const c = copyBtn(r.password); c.style.marginTop = "10px"; res.appendChild(c); }
          if (Voice.isEnabled()) Voice.speak("found");
        } else {
          res.innerHTML = `<div class="fail-box">試了 ${r.tried.toLocaleString()} 組仍未找到。可加入自備字典，或擴大窮舉字元與長度再試。</div>`;
        }
      }
    }
    function reset() { startBtn.disabled = false; stopBtn.disabled = true; jobId = null; }
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  setupCrack({ optsId: "archiveOpts", prefix: "ar", pathId: "archivePath",
    startBtn: "archiveStart", stopBtn: "archiveStop", progId: "archiveProgress",
    resId: "archiveResult", target: "archive" });
  setupCrack({ optsId: "officeOpts", prefix: "of", pathId: "officePath",
    startBtn: "officeStart", stopBtn: "officeStop", progId: "officeProgress",
    resId: "officeResult", target: "office" });

  /* ---------- 學習庫 / 資料庫 ---------- */
  const dbModal = $("#dbModal");
  $("#btnDb").onclick = async () => {
    dbModal.classList.add("show");
    try {
      const s = await api("/api/learn/stats");
      let html = `<p>後端：<b>${s.backend}</b></p><table><tr><th>模組</th><th>密碼數</th><th>累計命中</th></tr>`;
      (s.by_module || []).forEach(m => html += `<tr><td>${m.module}</td><td>${m.count}</td><td>${m.hits}</td></tr>`);
      if (!(s.by_module || []).length) html += `<tr><td colspan=3>尚無學習紀錄</td></tr>`;
      $("#learnStats").innerHTML = html + "</table>";
      const c = await api("/api/db/config");
      $("#dbEnabled").checked = !!c.db.enabled;
      $("#dbHost").value = c.db.host; $("#dbPort").value = c.db.port;
      $("#dbUser").value = c.db.user; $("#dbName").value = c.db.database;
    } catch (e) { $("#learnStats").innerHTML = "讀取失敗：" + e; }
  };
  $("#dbClose").onclick = () => dbModal.classList.remove("show");
  $("#dbSave").onclick = async () => {
    const db = {
      enabled: $("#dbEnabled").checked, host: $("#dbHost").value, port: parseInt($("#dbPort").value) || 3558,
      user: $("#dbUser").value, database: $("#dbName").value
    };
    const pw = $("#dbPass").value; if (pw) db.password = pw;
    const r = await api("/api/db/config", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ db }) });
    $("#dbMsg").innerHTML = r.ok ? `<div class="found-box">${r.message}</div>` : `<div class="fail-box">${r.message}</div>`;
  };

  /* ---------- 更新 ---------- */
  async function loadVersion() {
    try { const r = await api("/api/version"); $("#verTag").textContent = "v" + (r.version || "?"); window._ver = r; }
    catch { $("#verTag").textContent = ""; }
  }
  $("#btnUpdate").onclick = async () => {
    if (isDesktop()) {
      const r = await window.pywebview.api.check_update();
      if (r && r.has_update) toast(`有新版 v${r.latest}，開始下載…`);
      else toast("已是最新版");
    } else { toast("線上版會自動使用最新版"); }
  };

  /* ---------- 啟動 ---------- */
  loadVersion();
  // 純前端（無後端）時，local.js 會設 window.NO_BACKEND
  if (window.NO_BACKEND) hasBackend = false;
  setTimeout(() => { if (Voice.isEnabled()) Voice.speakScript("welcome"); }, 800);
})();
