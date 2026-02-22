import streamlit as st
import yt_dlp
import requests
import re
import glob
import os
from openai import OpenAI

# ================= 1. 基础配置 =================
st.set_page_config(page_title="GHC AI | Vision", page_icon="🍏", layout="centered")

DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
SILICON_API_KEY = st.secrets["SILICON_API_KEY"]
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

if "history" not in st.session_state:
    st.session_state.history = []
if "display_content" not in st.session_state:
    st.session_state.display_content = ""

# ================= 2. 界面视觉升级 =================
def apply_apple_css():
    background_url = "https://raw.githubusercontent.com/gaohechen0927-sketch/Repository-name/main/mybg.jpg.jpg"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{background_url}") !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
        }}
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.65) !important;
            backdrop-filter: saturate(180%) blur(25px) !important;
            padding: 3.5rem !important;
            border-radius: 32px !important;
            box-shadow: 0 16px 40px rgba(0,0,0,0.15) !important;
        }}
        .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{ color: #1d1d1f !important; }}
        .stButton button {{ background-color: #0071e3 !important; color: white !important; border-radius: 20px !important; }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_apple_css()

# ================= 3. 核心功能引擎 =================
def extract_clean_url(text):
    url_pattern = r"https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]"
    urls = re.findall(url_pattern, text)
    return urls[0] if urls else None

def fetch_douyin_info(url):
    apis = [f"https://api.lolimi.cn/API/douyin/api.php?url={url}", f"https://tenapi.cn/v2/video?url={url}"]
    for api in apis:
        try:
            res = requests.get(api, timeout=6).json()
            if res.get("code") == 200 or res.get("data"):
                data = res.get("data", res)
                return {"title": data.get("title"), "video": data.get("video") or data.get("url"), "music": data.get("music")}
        except: continue
    return None

def download_media(url):
    for f in glob.glob("temp_media.*"):
        try: os.remove(f)
        except: pass
    ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'temp_media.%(ext)s', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    files = glob.glob("temp_media.*")
    return files[0] if files else None

def audio_to_text(file_path):
    url = "https://api.siliconflow.cn/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {SILICON_API_KEY}"}
    data = {"model": "FunAudioLLM/SenseVoiceSmall", "response_format": "text"}
    with open(file_path, "rb") as f:
        response = requests.post(url, files={"file": f}, data=data, headers=headers)
    return response.text

def summarize_text(text):
    prompt = f"请总结以下视频内容：\n\n{text}"
    response = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content

# ================= 4. 网页布局 =================
tab1, tab2 = st.tabs(["✨ AI 总结", "🧰 提取工具"])

with tab1:
    user_input = st.text_input("🔗 粘贴链接", key="ai_in")
    up_file = st.file_uploader("📂 上传文件 (抖音推荐)", type=['mp4', 'mp3'])
    if st.button("开始解析", key="ai_btn"):
        with st.status("处理中..."):
            if up_file:
                with open("temp_upload.mp4", "wb") as f: f.write(up_file.getbuffer())
                media = "temp_upload.mp4"
            else:
                media = download_media(extract_clean_url(user_input))
            text = audio_to_text(media)
            summary = summarize_text(text)
            st.session_state.display_content = summary
            st.balloons()
    if st.session_state.display_content:
        st.markdown(f'<div style="background:white;padding:20px;border-radius:15px;color:black;">{st.session_state.display_content}</div>', unsafe_allow_html=True)

with tab2:
    t_input = st.text_input("🔗 抖音链接", key="tool_in")
    if st.button("提取", key="tool_btn"):
        info = fetch_douyin_info(extract_clean_url(t_input))
        if info:
            st.code(info['title'])
            st.video(info['video'])