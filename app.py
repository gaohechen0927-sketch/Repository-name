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

# ================= 2. 界面视觉升级 (Apple 顶级毛玻璃美学) =================
def apply_apple_css():
    background_url = "https://raw.githubusercontent.com/gaohechen0927-sketch/Repository-name/main/mybg.jpg.jpg"
    st.markdown(
        f"""
        <style>
        /* 引入 Apple 字体体系 */
        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600&display=swap');
        
        .stApp {{
            background-image: url("{background_url}") !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif !important;
        }}
        
        /* 核心卡片：Apple 原生毛玻璃配方 */
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.45) !important; /* 更通透的底色 */
            backdrop-filter: saturate(180%) blur(25px) !important; /* 关键：饱和度提升+强模糊 */
            -webkit-backdrop-filter: saturate(180%) blur(25px) !important;
            padding: 3.5rem !important;
            border-radius: 32px !important; /* 更大的平滑圆角 */
            border: 1px solid rgba(255, 255, 255, 0.4) !important; /* 玻璃边缘高光 */
            box-shadow: 0 16px 40px rgba(0,0,0,0.15) !important; /* 柔和悬浮阴影 */
            margin-top: 2rem !important;
        }}
        
        /* Apple 风输入框 */
        .stTextInput input {{
            border-radius: 16px !important;
            border: 1px solid rgba(0,0,0,0.05) !important;
            padding: 14px 20px !important;
            background-color: rgba(255, 255, 255, 0.7) !important;
            font-size: 16px !important;
            transition: all 0.3s ease !important;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
        }}
        .stTextInput input:focus {{
            border-color: #0071e3 !important; /* Apple 科技蓝 */
            box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.2) !important;
        }}
        
        /* Apple 风按钮 */
        .stButton button {{
            background-color: #0071e3 !important; /* Apple 科技蓝 */
            color: white !important;
            border-radius: 20px !important; /* 胶囊圆角 */
            padding: 10px 24px !important;
            font-weight: 600 !important;
            border: none !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
        }}
        .stButton button:hover {{
            background-color: #0077ED !important;
            transform: scale(1.01) !important;
            box-shadow: 0 4px 12px rgba(0, 113, 227, 0.3) !important;
        }}
        
        /* 侧边栏玻璃化 */
        [data-testid="stSidebar"] {{
            background-color: rgba(240, 240, 245, 0.6) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border-right: 1px solid rgba(255,255,255,0.3) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_apple_css()

# ================= 3. 核心功能引擎 (抖音双保险 API + B站) =================
def extract_clean_url(text):
    url_pattern = r"https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]"
    urls = re.findall(url_pattern, text)
    return urls[0] if urls else None

def download_audio(url):
    for f in glob.glob("temp_audio.*"):
        try: os.remove(f)
        except: pass

    # 🚀 抖音双保险下载通道
    if "douyin.com" in url:
        # 尝试路线 1：主 API
        try:
            res1 = requests.get(f"https://tenapi.cn/v2/video?url={url}", timeout=10).json()
            if res1.get("code") == 200:
                music_url = res1["data"]["music"]
            else:
                raise Exception("主通道忙")
        except:
            # 主路线失败，尝试路线 2：备用 API
            try:
                res2 = requests.get(f"https://api.vvhan.com/api/douyin?url={url}", timeout=10).json()
                if res2.get("success"):
                    music_url = res2["music"]
                else:
                    raise Exception("备用通道也忙")
            except:
                raise Exception("免费解析网络太拥堵了，请休息 2 分钟后再试一试~")

        # 下载拿到链接的音频
        try:
            audio_data = requests.get(music_url, timeout=15).content
            with open("temp_audio.mp3", "wb") as f:
                f.write(audio_data)
            return "temp_audio.mp3"
        except Exception as e:
            raise Exception("下载音频文件时网络中断了")

    # 🚜 B站等常规通道保持不变
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
    prompt = f"你是一个专业的视频总结助手。请提取以下视频文本的核心主题、干货要点和金句亮点，排版要有极简高级感：\n\n{text}"
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# ================= 4. 网页布局与交互 (Apple 极简排版) =================
with st.sidebar:
    st.markdown("###  开发者信息")
    st.write("**高赫辰** / 设计与构建")
    st.divider()
    
    st.markdown("### 🕒 历史摘要")
    if not st.session_state.history:
        st.caption("暂无记录")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            if st.button(f"📄 {item['title']}", key=f"hist_{i}"):
                st.session_state.display_content = item['summary']

st.markdown("<h1 style='text-align: center; color: #1d1d1f;'>Vision AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #86868b; font-size: 18px;'>智能提炼，一眼即见核心。</p>", unsafe_allow_html=True)

user_input = st.text_input("视频分享链接", placeholder="长按粘贴 B站 或 抖音 链接...")

if st.button("开始解析 (Start)"):
    if not user_input:
        st.warning("⚠️ 请先输入链接哦")
    else:
        with st.status("Apple 芯片引擎启动中...", expanded=True) as status:
            try:
                st.write("1️⃣ 解析协议与地址...")
                clean_url = extract_clean_url(user_input)
                if not clean_url: raise Exception("无效的链接格式")
                
                st.write("2️⃣ 下载流媒体音频...")
                audio_file = download_audio(clean_url)
                if not audio_file: raise Exception("媒体提取失败")
                    
                st.write("3️⃣ 神经网络识别文字...")
                transcript = audio_to_text(audio_file)
                
                st.write("4️⃣ 大语言模型提炼中...")
                summary = summarize_text(transcript)
                
                short_title = user_input[:12] + "..." if len(user_input) > 12 else user_input
                st.session_state.history.append({"title": short_title, "summary": summary})
                st.session_state.display_content = summary
                
                status.update(label="✨ 解析完成", state="complete", expanded=False)
                st.balloons() 
                
            except Exception as e:
                status.update(label="💥 任务中断", state="error")
                st.error(f"异常报告：{str(e)}")
                st.snow()

if st.session_state.display_content:
    st.divider()
    st.markdown(st.session_state.display_content)