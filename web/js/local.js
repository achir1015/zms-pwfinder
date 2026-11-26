/* 線上/手機純前端退路（無 Python 後端時）。
   目前提供「文字抓密碼」的純前端版；WiFi／星號／郵件／壓縮檔／Office
   需要系統權限或較重的運算，請用桌面版。壓縮檔日後可改接 zip.js 於前端。 */
(() => {
  // 偵測：若 /api/version 取不到，視為純前端
  fetch("/api/version").then(r => { if (!r.ok) markNoBackend(); }).catch(markNoBackend);
  function markNoBackend() { window.NO_BACKEND = true; }

  const LABELS = ["密碼", "通關密語", "解壓密碼", "開啟密碼", "口令", "password", "passcode", "pwd", "pass"];
  const re = new RegExp(
    "(?:" + LABELS.join("|") + ")\\s*(?:是|為|:|：|=|＝|->|→|\\s+is\\s+|\\s+)['\"「『<\\[(（【]?([!-~]{4,64})",
    "ig");

  window.Local = {
    extract(text) {
      const out = [], seen = new Set();
      let m;
      while ((m = re.exec(text))) {
        let tok = m[1].replace(/[\s。，、；！？」』>\])）】'"”’.,:;!?]+$/, "");
        if (tok.length < 4 || seen.has(tok)) continue;
        if (/^(https?:\/\/|www\.)/i.test(tok)) continue;
        if (/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(tok)) continue;
        seen.add(tok);
        const i = Math.max(0, m.index - 20);
        out.push({ password: tok, context: text.slice(i, m.index + m[0].length).replace(/\n/g, " ").trim() });
      }
      return out;
    }
  };
})();
