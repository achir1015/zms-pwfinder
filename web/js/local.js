/* 線上/手機純前端（無 Python 後端）邏輯。
   提供：文字抓密碼、瀏覽器端 ZIP 密碼破解（zip.js）、localStorage 成功密碼學習庫。
   WiFi／星號／郵件／Office 需要系統權限或較重運算 → 僅桌面版。 */
(() => {
  // 偵測後端是否存在；取不到 /api/version 視為純前端
  fetch("/api/version", { cache: "no-store" })
    .then(r => { if (!r.ok) markNoBackend(); })
    .catch(markNoBackend);
  function markNoBackend() { window.NO_BACKEND = true; document.dispatchEvent(new Event("nobackend")); }

  /* ---------- 文字抓密碼（純前端） ---------- */
  const LABELS = ["密碼", "通關密語", "解壓密碼", "開啟密碼", "口令", "password", "passcode", "passphrase", "pwd", "pass"];
  // 分隔符允許「是/為/:/= …」前後有空白，對齊桌面 Python 版
  const SEP = "(?:\\s*(?:是|為|乃|:|：|=|＝|->|→)\\s*|\\s+is\\s+|\\s+)";
  const reText = new RegExp(
    "(?:" + LABELS.join("|") + ")" + SEP + "['\"「『<\\[(（【]?([!-~]{4,64})",
    "ig");

  /* ---------- localStorage 成功密碼學習庫 ---------- */
  const LKEY = "pwfinder_learned";
  const LocalLearn = {
    all() { try { return JSON.parse(localStorage.getItem(LKEY) || "{}"); } catch { return {}; } },
    get(module) {
      const s = this.all();
      return Object.values(s).filter(r => !module || r.module === module)
        .sort((a, b) => (b.hits - a.hits) || (b.last - a.last)).map(r => r.password);
    },
    add(password, module, kind) {
      if (!password) return;
      const s = this.all(); const k = module + "::" + password;
      if (s[k]) { s[k].hits++; s[k].last = Date.now(); }
      else s[k] = { password, module, kind: kind || "", hits: 1, last: Date.now() };
      localStorage.setItem(LKEY, JSON.stringify(s));
    },
    stats() {
      const by = {}; Object.values(this.all()).forEach(r => {
        by[r.module] = by[r.module] || { module: r.module, count: 0, hits: 0 };
        by[r.module].count++; by[r.module].hits += r.hits;
      });
      return { backend: "瀏覽器本機（localStorage）", by_module: Object.values(by) };
    }
  };

  /* ---------- 候選密碼產生器（與桌面端一致的策略） ---------- */
  const CHARSETS = { digits: "0123456789", lower: "abcdefghijklmnopqrstuvwxyz",
    upper: "ABCDEFGHIJKLMNOPQRSTUVWXYZ", symbols: "!@#$%^&*()-_=+" };
  const COMMON = ["123456", "123456789", "12345678", "password", "qwerty", "111111",
    "000000", "888888", "abc123", "a123456", "iloveyou", "admin", "123123", "520520",
    "5201314", "woaini1314", "P@ssw0rd", "test123", "abcd1234", "666666"];

  function buildCharset(keys, custom) {
    let s = ""; (keys || []).forEach(k => s += CHARSETS[k] || ""); s += custom || "";
    return [...new Set(s)].join("");
  }
  function* bruteIter(charset, minL, maxL) {
    for (let L = Math.max(1, minL); L <= Math.max(1, maxL); L++) yield* product(charset, L);
  }
  function* product(cs, L, prefix = "") {
    if (L === 0) { yield prefix; return; }
    for (const c of cs) yield* product(cs, L - 1, prefix + c);
  }
  function* candidates(options, learned) {
    const seen = new Set();
    const emit = function* (arr) { for (const p of arr) { if (p && !seen.has(p)) { seen.add(p); yield p; } } };
    const mode = options.mode || "smart";
    if (mode === "smart" || mode === "dictionary") yield* emit(learned || []);
    let wl = options.wordlist || [];
    if (typeof wl === "string") wl = wl.split("\n").map(s => s.trim());
    if (mode === "smart" || mode === "dictionary") yield* emit(wl);
    if (mode === "smart") yield* emit(COMMON);
    if (mode === "smart" || mode === "brute") {
      const cs = buildCharset(options.charsets, options.custom_chars);
      if (cs) yield* emit(bruteIter(cs, +options.min_len || 1, +options.max_len || 4));
    }
  }

  /* ---------- 瀏覽器端 ZIP 破解（zip.js） ---------- */
  async function crackZip(file, options, cb) {
    // cb: {onProgress(tried,current), shouldStop()} ; 回傳 {found,password,tried}
    if (!window.zip) throw new Error("zip.js 未載入");
    zip.configure({ useWebWorkers: true });
    const learned = LocalLearn.get("archive");
    let tried = 0; const start = performance.now();
    for (const pwd of candidates(options, learned)) {
      if (cb.shouldStop && cb.shouldStop()) return { found: false, password: null, tried, stopped: true };
      tried++;
      let reader;
      try {
        reader = new zip.ZipReader(new zip.BlobReader(file), { password: pwd });
        const entries = await reader.getEntries();
        const f = entries.find(e => !e.directory);
        if (!f) { await reader.close(); return { found: true, password: pwd, tried }; }
        await f.getData(new zip.Uint8ArrayWriter(), { password: pwd,
          checkPasswordOnly: true });
        await reader.close();
        LocalLearn.add(pwd, "archive", "zip");
        return { found: true, password: pwd, tried, elapsed: (performance.now() - start) / 1000 };
      } catch (e) {
        try { if (reader) await reader.close(); } catch { }
      }
      if (cb.onProgress && tried % 50 === 0) {
        cb.onProgress(tried, pwd);
        await new Promise(r => setTimeout(r, 0)); // 讓畫面有機會更新
      }
    }
    return { found: false, password: null, tried, elapsed: (performance.now() - start) / 1000 };
  }

  window.Local = {
    LocalLearn,
    extract(text) {
      const out = [], seen = new Set(); let m;
      reText.lastIndex = 0;
      while ((m = reText.exec(text))) {
        let tok = m[1].replace(/[\s。，、；！？」』>\])）】'"”’.,:;!?]+$/, "");
        if (tok.length < 4 || seen.has(tok)) continue;
        if (/^(https?:\/\/|www\.)/i.test(tok)) continue;
        if (/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(tok)) continue;
        seen.add(tok);
        const i = Math.max(0, m.index - 20);
        out.push({ password: tok, context: text.slice(i, m.index + m[0].length).replace(/\n/g, " ").trim() });
      }
      return out;
    },
    crackZip,
  };
})();
