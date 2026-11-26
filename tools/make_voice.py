"""預先產生語音教學 MP3（edge-tts 台灣神經語音，接近真人、免費、離線播放）。

產生到 web/assets/voice/*.mp3。voice.js 會優先播放這些 MP3；
若缺檔才退回瀏覽器內建語音合成。
"""
import asyncio
import os
import edge_tts

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "web", "assets", "voice")
os.makedirs(OUT, exist_ok=True)

# 預設語音：台灣親切女聲（接近真人）。可改 zh-TW-HsiaoYuNeural / zh-TW-YunJheNeural
VOICE = "zh-TW-HsiaoChenNeural"
RATE = "+0%"
PITCH = "+0Hz"

SCRIPTS = {
    "welcome": "歡迎使用資料助秘密碼查找器。這個工具只幫你找回自己忘記的密碼，全程都在你的電腦上進行。上面有六個分頁，點一下就能切換。每個頁面右上角都有聽說明按鈕，想聽就按。",
    "wifi": "這是 WiFi 密碼頁。按下列出按鈕，就會把這台電腦記住的所有無線網路密碼顯示出來。這些本來就存在你的電腦裡，我們只是幫你看清楚。密碼右邊有複製按鈕，點一下就複製好了。",
    "text": "這是文字抓密碼頁。把郵件或文件的內文整段貼進中間的框框，再按抓出密碼。如果文字裡有寫密碼是什麼，像是附件的密碼是某某某，就會自動幫你挑出來。",
    "archive": "這是壓縮檔密碼頁。先選擇你要開啟的壓縮檔，支援 ZIP、7z、RAR。建議用智慧模式，它會先試你以前成功過的密碼，再試常用密碼，最後才慢慢窮舉。成功之後密碼會自動記下來，下一次就更快。",
    "office": "這是 Office 密碼頁，可以找回 Word、Excel、PowerPoint 的開啟密碼。選好檔案後按開始回復。跟壓縮檔一樣，成功的密碼會存進學習庫，提高下次的成功機率。",
    "star": "這是星號密碼顯示頁。先把滑鼠移到某個軟體顯示圓點或星號的密碼欄上面，再按抓取按鈕，我們會試著把它還原成文字。要注意，瀏覽器和部分新式軟體因為系統限制讀不到。",
    "mail": "這是郵件密碼頁。按讀取按鈕，會把你電腦裡 Thunderbird 或 Outlook 已經記住的郵件帳號密碼找出來。全程只讀你自己的設定，不會連到網路，也不會去猜別人的信箱。",
    "found": "找到密碼了！已經幫你記到學習庫，下次會更快。",
    "voiceon": "語音教學已開啟。",
}


async def gen_one(name: str, text: str):
    path = os.path.join(OUT, name + ".mp3")
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(path)
    size = os.path.getsize(path)
    print(f"  {name}.mp3  ({size//1024} KB)")


async def main():
    print(f"語音：{VOICE} → {OUT}")
    for name, text in SCRIPTS.items():
        await gen_one(name, text)
    print("完成，共", len(SCRIPTS), "段")


if __name__ == "__main__":
    asyncio.run(main())
