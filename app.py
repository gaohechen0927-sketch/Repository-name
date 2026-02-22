import streamlit as st
import yt_dlp
import requests
import re
import glob
import os
from openai import OpenAI

# ================= 1. 基础配置 =================
st.set_page_config(page_title="高赫辰的AI神器", page_icon="📸", layout="centered")

DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
SILICON_API_KEY = st.secrets["SILICON_API_KEY"]
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

# 初始化历史记录，这是左侧边栏能显示记录的关键！
if "history" not in st.session_state:
    st.session_state.history = []
if "display_content" not in st.session_state:
    st.session_state.display_content = ""

# ================= 2. 界面视觉升级 (你的专属摄影大作) =================
def apply_custom_css():
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
            background-color: rgba(255, 255, 255, 0.8) !important;
            backdrop-filter: blur(10px) !important;
            padding: 3rem !important;
            border-radius: 20px !important;
            box-shadow: 0 8px 32px 0 rgba(0,0,0,0.15) !important;
            margin-top: 2rem !important;
        }}
        .stButton button {{
            background-color: #ff4b4b !important;
            color: white !important;
            border-radius: 10px !important;
            font-weight: bold !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_custom_css()

# ================= 3. 核心功能引擎 (抖音破壁 + B站双通道) =================
def extract_clean_url(text):
    url_pattern = r"https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]"
    urls = re.findall(url_pattern, text)
    return urls[0] if urls else None

def download_audio(url):
    for f in glob.glob("temp_audio.*"):
        try: os.remove(f)
        except: pass

    # 🚀 专门对付抖音的 API 通道
    if "douyin.com" in url:
        try:
            api_url = f"https://tenapi.cn/v2/video?url={url}"
            response = requests.get(api_url, timeout=15).json()
            if response.get("code") == 200:
                music_url = response["data"]["music"]
                audio_data = requests.get(music_url, timeout=15).content
                with open("temp_audio.mp3", "wb") as f:
                    f.write(audio_data)
                return "temp_audio.mp3"
            else:
                raise Exception("免费解析接口暂时繁忙，请稍后再试")
        except Exception as e:
            raise Exception(f"抖音解析遇到问题: {str(e)}")

    # 🚜 B站等常规通道
    ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'temp_audio.%(ext)s', 'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    files = glob.glob("temp_audio.*")
    return files[0] if files else None

def audio_to_text(file_path):
    url = "https://api.siliconflow.cn/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {SILICON_API_KEY}"}
    data = {"model": "FunAudioLLM/SenseVoiceSmall", "response_format": "text"}
    with open(file_path, "rb") as f:
        response = requests.post(url, files={"file": f}, data=data, headers=headers)
    if response.status_code == 200: return response.text
    else: raise Exception(f"听写失败: {response.text}")

def summarize_text(text):
    prompt = f"你是一个专业的视频总结助手。请提取以下视频文本的核心主题、干货要点和金句亮点：\n\n{text}"
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# ================= 4. 网页布局与交互 =================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3685/3685253.png", width=100)
    st.markdown("### 👨‍💻 摄影师 & 开发者")
    st.write("**高赫辰** 的专属 AI 工具。")
    st.divider()
    
    # 这里是展示历史记录的逻辑
    st.markdown("### 📜 历史足迹")
    if not st.session_state.history:
        st.caption("这里空空如也...")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            if st.button(f"📄 {item['title']}", key=f"hist_{i}"):
                st.session_state.display_content = item['summary']

st.title("📸 高赫辰的视频 AI 暗房")
st.caption("支持 B站 / 抖音。直接粘贴分享文案即可！")

user_input = st.text_input("🎞️ 投入你的视频“底片”（分享链接）：")

if st.button("🧨 点火！开始冲洗"):
    if not user_input:
        st.warning("⚠️ 底片呢？还没放入链接哦！")
    else:
        with st.status("暗房工作中，请稍候...", expanded=True) as status:
            try:
                st.write("1️⃣ 智能解析链接...")
                clean_url = extract_clean_url(user_input)
                if not clean_url: raise Exception("没找到有效的链接")
                
                st.write("2️⃣ 提取音频素材...")
                audio_file = download_audio(clean_url)
                if not audio_file: raise Exception("音频提取失败")
                    
                st.write("3️⃣ 转化为文字底稿...")
                transcript = audio_to_text(audio_file)
                
                st.write("4️⃣ AI 后期处理中，正在出片...")
                summary = summarize_text(transcript)
                
                # 记录成功，保存历史，放气球！
                short_title = user_input[:15] + "..." if len(user_input) > 15 else user_input
                st.session_state.history.append({"title": short_title, "summary": summary})
                st.session_state.display_content = summary
                
                status.update(label="✨ 冲洗完成！完美出片！", state="complete", expanded=False)
                st.balloons() # 庆祝气球特效！
                
            except Exception as e:
                status.update(label="💥 冲洗失败！", state="error")
                st.error(f"错误原因：{str(e)}")
                st.snow() # 失败下雪特效

if st.session_state.display_content:
    st.divider()
    st.markdown("### 🖼️ 最终成片：")
    st.markdown(st.session_state.display_content)