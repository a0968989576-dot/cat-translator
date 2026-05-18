import streamlit as st
import io
import tempfile
import os
import time
from gtts import gTTS
from google import genai
from PIL import Image

# ==========================================
# 1. 你的 Gemini API Key
# ==========================================
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# 🌟 初始化新版 AI 客戶端
client = genai.Client(api_key=GOOGLE_API_KEY)

# --- 網頁基本設定 ---
st.set_page_config(page_title="AI 貓咪讀心術", page_icon="🐾", layout="centered")
st.title("🐾 AI 貓咪影像讀心術 🐾")
st.write("讓 AI 看看主子在想什麼？你可以拍照，或是上傳手機裡的照片與**短影片**！")

# --- 語音播放功能 ---
def play_voice(text):
    try:
        tts = gTTS(text=text, lang='zh-TW')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        st.audio(audio_buffer, format='audio/mp3', autoplay=True)
    except Exception as e:
        st.error(f"語音發生錯誤：{e}")

# --- 核心功能：相機與檔案輸入 ---
st.subheader("📷 取得貓咪影像")

st.info("💡 小提醒：如果按了拍照沒反應，代表您之前可能按到了『拒絕』。請點擊手機網址列旁邊的「🔒鎖頭」、「Aa」或「🎛️ 調整拉桿」圖示，手動將相機權限改為「允許」再重新整理歐！")

# 📸 相機拍照
picture = st.camera_input("📸 點擊開啟相機即時拍照")

# 📂 檔案上傳 (升級支援影片格式！)
uploaded_file = st.file_uploader(
    "📂 或者上傳一張照片 / 短影片 (建議 5~10 秒內)", 
    type=["jpg", "jpeg", "png", "mp4", "mov", "avi"]
)

# 判斷使用者是用相機還是上傳 (相機優先)
media_to_process = picture or uploaded_file

if media_to_process:
    # 修正 Bug：判斷「目前真正要處理的檔案」是不是影片檔
    is_video = False
    if media_to_process.name.split('.')[-1].lower() in ['mp4', 'mov', 'avi']:
        is_video = True

    # 顯示要分析的畫面
    if is_video:
        st.video(media_to_process)
        st.warning("⏳ 影片需要上傳與處理時間，請耐心等候幾秒鐘喔！")
    else:
        st.image(media_to_process, caption="準備分析這張照片...", use_container_width=True)

    if st.button("✨ 開始讀心！", type="primary"):
        with st.spinner("👁️ 正在仔細觀察貓咪的神情..."):
            try:
                prompt = """
                你是一個「貓咪肢體語言翻譯機」。請看這段畫面中的貓咪。
                根據牠的動作、表情、周圍環境，以及『影片中的聲音（例如：喵喵叫、呼嚕聲或背景環境音）』，翻譯出牠此刻內心最真實的一句中文心聲。
                條件限制：
                1. 語氣必須符合畫面情境（例如：鄙視、想睡、討食、無奈）。
                2. 請「直接」給出那句話，不要描述畫面，也不要有任何前言或引號。
                3. 字數控制在 30 字以內。
                """

                if is_video:
                    # 🎬 【處理影片邏輯】
                    # 1. 將影片先存成暫存檔 (Google AI 需要讀取實體檔案)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                        tmp_file.write(media_to_process.read())
                        tmp_path = tmp_file.name
                    
                    # 2. 上傳影片給 Google
                    uploaded_vid = client.files.upload(file=tmp_path)

                    # 3. 讓程式等一下，確保 Google 看完影片了
                    while uploaded_vid.state.name == "PROCESSING":
                        time.sleep(2)
                        uploaded_vid = client.files.get(name=uploaded_vid.name)
                    
                    # 4. 開始發送詢問
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[uploaded_vid, prompt]
                    )

                    # 5. 翻完後把暫存檔刪掉，節省空間
                    os.remove(tmp_path)

                else:
                    # 🖼️ 【處理照片邏輯】(原本的寫法)
                    img = Image.open(media_to_process)
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[img, prompt]
                    )

                # 取得翻譯結果
                result_text = response.text.strip()

                # 顯示結果並發聲
                st.success(f"👉 貓咪真正的意思是：『{result_text}』")
                play_voice(result_text)

            except Exception as e:
                # 錯誤攔截機制：檢查是不是點太快觸發了 429 限制
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    st.warning("⚠️ 翻譯機稍稍過熱啦！因為目前使用人數較多，請等 30 秒後再試喔！")
                else:
                    st.error(f"(分析失敗，請稍後再試... 錯誤代碼: {e})")
