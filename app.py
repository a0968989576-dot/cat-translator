import streamlit as st
import io
from gtts import gTTS
from google import genai
from PIL import Image

# ==========================================
# 1. 你的 Gemini API Key
# ==========================================
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# 🌟 初始化新版 AI 客戶端
client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_ID = 'gemini-2.5-flash'

# --- 網頁基本設定 ---
st.set_page_config(page_title="AI 貓咪讀心術", page_icon="📷", layout="centered")
st.title("🐾 AI 貓咪影像讀心術 (Web 版) 🐾")
st.write("讓 AI 看看主子在想什麼？你可以直接拍照，或是上傳手機裡的照片！")

# --- 語音播放功能 (直接在網頁產生播放器) ---


def play_voice(text):
    try:
        tts = gTTS(text=text, lang='zh-TW')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        st.audio(audio_buffer, format='audio/mp3', autoplay=True)
    except Exception as e:
        st.error(f"語音發生錯誤：{e}")


# --- 核心功能：相機與照片輸入 ---
st.subheader("📷 取得貓咪影像")

# Streamlit 超強功能：同時提供相機與檔案上傳
picture = st.camera_input("📸 點擊開啟相機即時拍照")
uploaded_file = st.file_uploader(
    "📂 或者上傳一張已經拍好的照片", type=["jpg", "jpeg", "png"])

# 判斷使用者是用相機還是上傳 (相機優先)
image_to_process = picture or uploaded_file

if image_to_process:
    # 顯示要分析的照片
    st.image(image_to_process, caption="準備分析這張照片...", use_container_width=True)

    if st.button("✨ 開始讀心！", type="primary"):
        with st.spinner("👁️ 正在仔細觀察貓咪的神情..."):
            try:
                # 讀取影像並準備發送給 AI
                img = Image.open(image_to_process)

                prompt = """
                你是一個「貓咪肢體語言翻譯機」。請看這張照片中的貓咪。
                根據牠的動作、表情或周圍環境，翻譯出牠此刻內心最真實的一句中文心聲。
                條件限制：
                1. 語氣必須符合畫面情境（例如：鄙視、想睡、討食、無奈）。
                2. 請「直接」給出那句話，不要描述畫面，也不要有任何前言或引號。
                3. 字數控制在 30 字以內。
                """

                # 呼叫 AI 進行視覺分析
                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=[img, prompt]
                )

                result_text = response.text.strip()

                # 顯示結果並發聲
                st.success(f"👉 貓咪真正的意思是：『{result_text}』")
                play_voice(result_text)

            except Exception as e:
                st.error(f"(視覺分析失敗... {e})")
