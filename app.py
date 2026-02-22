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
        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600&display=swap');
        
        .stApp {{
            background-image: url("{background_url}") !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif !important;
        }}
        
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.45) !important;
            backdrop-filter: saturate(180%) blur(25px) !important;
            -webkit-backdrop-filter: saturate(180%) blur(25px) !important;
            padding: 3.5rem !important;
            border-radius: 32px !important;
            border: 1px solid rgba(255, 255, 255, 0.4) !important;
            box-shadow: 0 16px 40px rgba(0,0,0,0.15) !important;
            margin-top: 2rem !important;
        }}
        
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
            border-color: #0071e3 !important;
            box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.2) !important;
        }}
        
        .stButton button {{
            background-color: #0071e3 !important;
            color: white !important;
            border-radius: 20px !important;
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
        
        [data-testid="stSidebar"] {{
            background-color: rgba(240, 240, 245, 0.6) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border-right: 1px solid rgba(255,255,255,0.3) !important;
        }}
        
        /* 美化上传组件 */
        [data-testid="stFileUploader"] {{
            background-color: rgba(255,255,255,0.5) !important;
            border-radius: 16px !important;
            padding: 10px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_apple_css()

# ================= 3. 核心功能引擎 =================
def extract_clean_url(text):
    if not text: return None
    url_pattern = r"https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]"
    urls = re.findall(url_pattern, text)
    return urls[0] if urls else None

def download_media(url):
    for f in glob.glob("temp_media.*"):
        try: os.remove(f)
        except: pass

    if "douyin.com" in url:
        media_url = None
        # 扩展更多备用节点，增加幸存概率
        apis = [
            f"https://api.lolimi.cn/API/douyin/api.php?url={url}",
            f"https://tenapi.cn/v2/video?url={url}",
            f"https://api.yujn.cn/api/douyin?url={url}"
        ]
        
        for api in apis:
            try:
                res = requests.get(api, timeout=6).json()
                if "data" in res and isinstance(res["data"], dict):
                    media_url = res["data"].get("music") or res["data"].get("url") or res["data"].get("video")
                elif "music" in res or "video" in res:
                    media_url = res.get("music") or res.get("video")
                if media_url: break
            except: continue
            
        if not media_url:
            raise Exception("网络极度拥堵。建议使用 Plan B：直接保存抖音视频并上传！")
            
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
            media_data = requests.get(media_url, headers=headers, timeout=20).content
            ext = "mp3" if ".mp3" in media_url else "mp4"
            filename = f"temp_media.{ext}"
            with open(filename, "wb") as f:
                f.write(media_data)
            return filename
        except Exception:
            raise Exception("拿到地址了，但下载中断。请使用下方文件上传功能！")

    ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'temp_media.%(ext)s', 'quiet': True, 'no_warnings': True}
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
    if response.status_code == 200: return response.text
    else: raise Exception(f"AI 听写失败: {response.text}")

def summarize_text(text):
    prompt = f"你是一个专业的视频总结助手。请提取以下视频文本的核心主题、干货要点和金句亮点，排版要有极简高级感：\n\n{text}"
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# ================= 4. 网页布局与交互 =================
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
st.markdown("<p style='text-align: center; color: #e5e5ea; font-size: 18px; font-weight: 500;'>智能提炼，一眼即见核心。</p>", unsafe_allow_html=True)

# 🚀 核心改动：双通道输入（链接 or 文件）
user_input = st.text_input("🔗 方式一：粘贴视频分享链接", placeholder="长按粘贴 B站 或 抖音 链接...")
st.markdown("<p style='text-align: center; color: #e5e5ea; font-size: 14px; margin: -10px 0 10px 0;'>— 或 —</p>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("📂 方式二：直接上传视频/音频 (防网络拥堵 100% 成功率)", type=['mp4', 'mp3', 'm4a', 'wav'])

if st.button("开始解析 (Start)"):
    if not user_input and not uploaded_file:
        st.warning("⚠️ 请输入链接或上传文件哦")
    else:
        with st.status("Apple 芯片引擎启动中...", expanded=True) as status:
            try:
                media_file = None
                input_title = "本地文件解析"
                
                # 如果用户传了文件，直接走本地通道（最高优先级）
                if uploaded_file is not None:
                    st.write("1️⃣ 检测到本地文件，直接读取...")
                    file_ext = uploaded_file.name.split('.')[-1]
                    media_file = f"temp_upload.{file_ext}"
                    with open(media_file, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    input_title = uploaded_file.name[:15] + "..."
                
                # 如果没传文件，走链接解析通道
                else:
                    st.write("1️⃣ 解析网络协议与地址...")
                    clean_url = extract_clean_url(user_input)
                    if not clean_url: raise Exception("无效的链接格式")
                    st.write("2️⃣ 突破防线，提取多媒体流...")
                    media_file = download_media(clean_url)
                    if not media_file: raise Exception("媒体提取失败")
                    input_title = user_input[:12] + "..." if len(user_input) > 12 else user_input
                    
                # 统一转交 AI 处理
                st.write("⏳ 神经网络识别转换中 (这一步视文件大小可能需要十几秒)...")
                transcript = audio_to_text(media_file)
                
                st.write("🧠 大语言模型提炼中...")
                summary = summarize_text(transcript)
                
                st.session_state.history.append({"title": input_title, "summary": summary})
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