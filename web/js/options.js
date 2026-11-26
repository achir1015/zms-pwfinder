/* 破解選項 UI（壓縮檔 / Office 共用） */
const Options = (() => {
  function build(containerId, prefix) {
    const el = document.getElementById(containerId);
    el.innerHTML = `
      <div class="opt-box">
        <h4>回復方式</h4>
        <div class="mode-row" id="${prefix}Modes">
          <button class="mode-pill sel" data-mode="smart">🤖 智慧（學習庫→常用→窮舉）</button>
          <button class="mode-pill" data-mode="dictionary">📖 字典</button>
          <button class="mode-pill" data-mode="brute">🔢 純窮舉</button>
        </div>
        <div class="wl-area">
          <label class="k" style="font-size:13px;color:#6b7694">自備字典（每行一個密碼，可留空）</label>
          <textarea id="${prefix}Wordlist" placeholder="例如：&#10;生日2024&#10;mypass123"></textarea>
        </div>
        <div class="cs-row" id="${prefix}Charsets">
          <span style="font-size:13px;color:#6b7694">窮舉字元：</span>
          <label><input type="checkbox" value="digits" checked> 數字</label>
          <label><input type="checkbox" value="lower" checked> 小寫</label>
          <label><input type="checkbox" value="upper"> 大寫</label>
          <label><input type="checkbox" value="symbols"> 符號</label>
        </div>
        <div class="cs-row">
          <span style="font-size:13px;color:#6b7694">自訂字元：</span>
          <input type="text" id="${prefix}Custom" style="width:160px" placeholder="例如 _.@">
        </div>
        <div class="len-row">
          長度 <input type="number" id="${prefix}Min" value="1" min="1" max="12">
          到 <input type="number" id="${prefix}Max" value="4" min="1" max="12">
          <span style="color:#c0392b">（窮舉長度越大越慢，建議先靠學習庫與字典）</span>
        </div>
      </div>`;
    // 模式切換
    el.querySelectorAll(".mode-pill").forEach(p => {
      p.onclick = () => {
        el.querySelectorAll(".mode-pill").forEach(x => x.classList.remove("sel"));
        p.classList.add("sel");
      };
    });
  }

  function collect(prefix) {
    const mode = document.querySelector(`#${prefix}Modes .mode-pill.sel`)?.dataset.mode || "smart";
    const charsets = [...document.querySelectorAll(`#${prefix}Charsets input:checked`)].map(c => c.value);
    return {
      mode,
      wordlist: document.getElementById(prefix + "Wordlist").value,
      charsets,
      custom_chars: document.getElementById(prefix + "Custom").value,
      min_len: parseInt(document.getElementById(prefix + "Min").value) || 1,
      max_len: parseInt(document.getElementById(prefix + "Max").value) || 4,
    };
  }

  return { build, collect };
})();
