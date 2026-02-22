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
            background-color: rgba(255, 255, 255, 0.65) !important;
            backdrop-filter: saturate(180%) blur(25px) !important;
            -webkit-backdrop-filter: saturate(180%) blur(25px) !important;
            padding: 3.5rem !important;
            border-radius: 32px !important;
            border: 1px solid rgba(255, 255, 255, 0.5) !important;
            box-shadow: 0 16px 40px rgba(0,0,0,0.15) !important;
            margin-top: 2rem !important;
        }}
        
        .stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown strong {{
            color: #1d1d1f !important;
        }}
        
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{
            color: #1d1d1f !important;
        }}

        .stTextInput input {{
            border-radius: 16px !important;
            border: 1px solid rgba(0,0,0,0.05) !important;
            padding: 14px 20px !important;
            background-color: rgba(255, 255, 255, 0.8) !important;
            color: #1d1d1f !important;
            font-size: 16px !important;
            transition: all 0.3s ease !important;
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
            background-color: rgba(240, 240, 245, 0.75) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border-right: 1px solid rgba(255,255,255,0.3) !important;
        }}
        
        /* 美化选项卡 Tab 的样式 */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 24px;
            background-color: transparent;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 10px 10px 0 0;
            color: #555 !important;
            font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{
            color: #0071e3 !important;
            border-bottom: 3px solid #0071e3 !important;
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

# 🚀 新增：专门用于抓取视频信息（文案、无水印链接）的函数
def fetch_douyin_info(url):
    apis = [
        f"https://api.lolimi.cn/API/douyin/api.php?url={url}",
        f"https://tenapi.cn/v2/video?url={url}",
        f"https://api.yujn.cn/api/douyin?url={url}"
    ]
    for api in apis:
        try:
            res = requests.get(api, timeout=6).json()
            if "data" in res and isinstance(res["data"], dict):
                return {
                    "title": res["data"].get("title", "未提取到文案"),
                    "video": res["data"].get("video") or res["data"].get("url"),
                    "music": res["data"].get("music")
                }
        except: continue
    return None

def download_media(url):
    for f in glob.glob("temp_media.*"):
        try: os.remove(f)
        except: pass

    if "douyin.com" in url:
        raise Exception("抖音防火墙拦截。请直接使用下方【上传视频】功能，100%成功率！")

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

# 🚀 引入高级选项卡设计
tab1, tab2 = st.tabs(["✨ AI 视频总结暗房", "🧰 无水印与文案提取"])

# ----------------- Tab 1: AI 视频总结 -----------------
with tab1:
    st.markdown("<p style='text-align: center; color: #1d1d1f; font-size: 16px; margin-top: 10px;'>智能提炼，一眼即见核心。</p>", unsafe_allow_html=True)
    
    user_input = st.text_input("🔗 方式一：粘贴链接", placeholder="B站等平台推荐直接粘贴分享链接...", key="ai_input")
    st.markdown("<p style='text-align: center; color: #1d1d1f; font-size: 14px; margin: -10px 0 10px 0;'>— 或 —</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("📂 方式二：直接传文件", type=['mp4', 'mp3', 'm4a', 'wav'], help="抖音视频防拦截神器！")

    if st.button("开始解析 (Start)", key="ai_btn"):
        if not user_input and not uploaded_file:
            st.warning("⚠️ 请输入链接或上传文件哦")
        else:
            with st.status("Apple 芯片引擎启动中...", expanded=True) as status:
                try:
                    media_file = None
                    input_title = "本地文件解析"
                    
                    if uploaded_file is not None:
                        st.write("1️⃣ 读取本地加密文件...")
                        file_ext = uploaded_file.name.split('.')[-1]
                        media_file = f"temp_upload.{file_ext}"
                        with open(media_file, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        input_title = uploaded_file.name[:15] + "..."
                    else:
                        st.write("1️⃣ 解析网络协议与地址...")
                        clean_url = extract_clean_url(user_input)
                        if not clean_url: raise Exception("无效的链接格式")
                        st.write("2️⃣ 突破防线，提取流媒体...")
                        media_file = download_media(clean_url)
                        if not media_file: raise Exception("媒体提取失败")
                        input_title = user_input[:12] + "..." if len(user_input) > 12 else user_input
                        
                    st.write("⏳ 神经网络识别转换中...")
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
        st.markdown(
            f"""<div style="background-color: rgba(255, 255, 255, 0.9); padding: 30px; border-radius: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); margin-top: 20px;">
                {st.session_state.display_content}
            </div>""", unsafe_allow_html=True
        )

# ----------------- Tab 2: 无水印与文案提取 (新功能) -----------------
with tab2:
    st.markdown("<p style='text-align: center; color: #1d1d1f; font-size: 16px; margin-top: 10px;'>一键去除抖音水印，提取原视频与爆款文案。</p>", unsafe_allow_html=True)
    
    tool_input = st.text_input("🔗 请输入抖音分享链接：", placeholder="长按粘贴抖音分享链接...", key="tool_input")
    
    if st.button("开始提取 (Extract)", key="tool_btn"):
        if not tool_input:
            st.warning("⚠️ 请先粘贴抖音链接哦")
        else:
            with st.spinner("正在呼叫黑客接口拦截数据..."):
                clean_url = extract_clean_url(tool_input)
                if not clean_url:
                    st.error("❌ 没找到链接，请检查输入")
                else:
                    info = fetch_douyin_info(clean_url)
                    if info and info.get("video"):
                        st.success("✅ 拦截成功！")
                        
                        # 展示文案并提供一键复制框
                        st.markdown("### 📝 视频文案")
                        st.code(info['title'], language="text") # st.code 自带一键复制按钮
                        
                        st.markdown("### 🎬 无水印视频")
                        # 直接在网页播放无水印视频，右下角自带下载按钮
                        st.video(info['video'])
                        
                        # 提供原背景音乐试听
                        if info.get("music"):
                            st.markdown("### 🎵 原声背景音乐")
                            st.audio(info['music'])
                    else:
                        st.error("❌ 提取失败，可能是抖音接口暂时拥堵，请稍后再试。")
