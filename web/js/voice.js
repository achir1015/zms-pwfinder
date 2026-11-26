/* 語音動態教學 — 優先播放預先以 edge-tts 台灣神經語音產生的 MP3（接近真人、
   免費、離線）。若缺 MP3 才退回瀏覽器內建語音合成。 */
const Voice = (() => {
  let enabled = true;
  let audio = null;          // 目前播放的 Audio
  const synth = window.speechSynthesis;
  let voices = [];
  if (synth) {
    const load = () => (voices = synth.getVoices());
    load(); synth.onvoiceschanged = load;
  }

  // 文字腳本（供退回合成語音時使用，須與 tools/make_voice.py 一致）
  const SCRIPTS = {
    welcome: "歡迎使用資料助秘密碼查找器。這個工具只幫你找回自己忘記的密碼，全程都在你的電腦上進行。上面有六個分頁，點一下就能切換。每個頁面右上角都有聽說明按鈕，想聽就按。",
    wifi: "這是 WiFi 密碼頁。按下列出按鈕，就會把這台電腦記住的所有無線網路密碼顯示出來。這些本來就存在你的電腦裡，我們只是幫你看清楚。密碼右邊有複製按鈕，點一下就複製好了。",
    text: "這是文字抓密碼頁。把郵件或文件的內文整段貼進中間的框框，再按抓出密碼。如果文字裡有寫密碼是什麼，像是附件的密碼是某某某，就會自動幫你挑出來。",
    archive: "這是壓縮檔密碼頁。先選擇你要開啟的壓縮檔，支援 ZIP、7z、RAR。建議用智慧模式，它會先試你以前成功過的密碼，再試常用密碼，最後才慢慢窮舉。成功之後密碼會自動記下來，下一次就更快。",
    office: "這是 Office 密碼頁，可以找回 Word、Excel、PowerPoint 的開啟密碼。選好檔案後按開始回復。跟壓縮檔一樣，成功的密碼會存進學習庫，提高下次的成功機率。",
    star: "這是星號密碼顯示頁。先把滑鼠移到某個軟體顯示圓點或星號的密碼欄上面，再按抓取按鈕，我們會試著把它還原成文字。要注意，瀏覽器和部分新式軟體因為系統限制讀不到。",
    mail: "這是郵件密碼頁。按讀取按鈕，會把你電腦裡 Thunderbird 或 Outlook 已經記住的郵件帳號密碼找出來。全程只讀你自己的設定，不會連到網路，也不會去猜別人的信箱。",
    found: "找到密碼了！已經幫你記到學習庫，下次會更快。",
    voiceon: "語音教學已開啟。",
  };

  function stop() {
    if (audio) { audio.pause(); audio.currentTime = 0; audio = null; }
    if (synth) synth.cancel();
    document.querySelectorAll(".voice-btn.speaking").forEach(b => b.classList.remove("speaking"));
  }

  // 播放某段教學（key 對應 assets/voice/<key>.mp3）
  function playKey(key, btn) {
    if (!enabled) return;
    stop();
    const a = new Audio(`assets/voice/${key}.mp3`);
    audio = a;
    if (btn) btn.classList.add("speaking");
    const clear = () => { if (btn) btn.classList.remove("speaking"); if (audio === a) audio = null; };
    a.onended = clear;
    a.onerror = () => { clear(); synthSpeak(SCRIPTS[key] || ""); };  // 缺 MP3 → 合成
    a.play().catch(() => { clear(); synthSpeak(SCRIPTS[key] || ""); });
  }

  // 退回：瀏覽器內建語音合成（盡量挑台灣中文、自然的 Online/Natural 語音）
  function synthSpeak(text) {
    if (!enabled || !synth || !text) return;
    synth.cancel();
    const u = new SpeechSynthesisUtterance(text);
    const v = voices.find(x => /zh[-_]TW/i.test(x.lang) && /natural|online|曉|HsiaoChen|HsiaoYu/i.test(x.name))
      || voices.find(x => /zh[-_]TW/i.test(x.lang))
      || voices.find(x => /zh/i.test(x.lang));
    if (v) { u.voice = v; u.lang = v.lang; } else u.lang = "zh-TW";
    u.rate = 1.0; u.pitch = 1.0;
    synth.speak(u);
  }

  // 對外：播放教學段（優先 MP3）
  function speakScript(key, btn) { playKey(key, btn); }
  // 對外：播放任意短語（有對應 MP3 就用，否則合成）
  function speak(key_or_text) {
    if (SCRIPTS[key_or_text] !== undefined) return playKey(key_or_text);
    // 直接文字 → 合成（少用）
    synthSpeak(key_or_text);
  }

  function setEnabled(v) { enabled = v; if (!v) stop(); }
  function isEnabled() { return enabled; }

  return { speak, speakScript, stop, setEnabled, isEnabled, SCRIPTS };
})();
