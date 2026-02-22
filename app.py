import streamlit as st
import yt_dlp
import requests
import re
import glob
import os
from openai import OpenAI

# ================= 1. 基础配置 =================
st.set_page_config(page_title="全能视频总结神器", page_icon="🎬", layout="centered")

DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
SILICON_API_KEY = st.secrets["SILICON_API_KEY"]
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

if "history" not in st.session_state:
    st.session_state.history = []
if "display_content" not in st.session_state:
    st.session_state.display_content = ""

# ================= 2. 界面视觉升级 =================
def apply_custom_css():
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url("https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?q=80&w=2070&auto=format&fit=crop") !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
        }
        .main .block-container {
            background-color: rgba(255, 255, 255, 0.85) !important;
            backdrop-filter: blur(15px) !important;
            padding: 3rem !important;
            border-radius: 20px !important;
            box-shadow: 0 8px 32px 0 rgba(0,0,0,0.15) !important;
            margin-top: 2rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

apply_custom_css()
def apply_custom_css():
    # 👇👇👇 你的专属摄影大作链接已经填好啦！ 👇👇👇
    background_url = "https://raw.githubusercontent.com/gaohechen0927-sketch/Repository-name/main/mybg.jpg.jpg"

# ================= 3. 核心功能引擎 (双通道下载) =================
def extract_clean_url(text):
    url_pattern = r"https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]"
    urls = re.findall(url_pattern, text)
    return urls[0] if urls else None

def download_audio(url):
    """双通道智能下载：抖音走第三方 API，其他走 yt-dlp"""
    for f in glob.glob("temp_audio.*"):
        try: os.remove(f)
        except: pass

    # 🚀 通道 A：专门对付抖音的“偷渡”方案
    if "douyin.com" in url:
        try:
            # 调用全网知名的免费无水印解析 API
            api_url = f"https://tenapi.cn/v2/video?url={url}"
            response = requests.get(api_url, timeout=15).json()
            
            if response.get("code") == 200:
                music_url = response["data"]["music"]
                # 直接将音频数据下载到本地
                audio_data = requests.get(music_url, timeout=15).content
                with open("temp_audio.mp3", "wb") as f:
                    f.write(audio_data)
                return "temp_audio.mp3"
            else:
                raise Exception("免费 API 接口暂时罢工了")
        except Exception as e:
            raise Exception(f"抖音解析失败，原因：{str(e)}")

    # 🚜 通道 B：B站等其他网站的常规抓取方案
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
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
    
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"耳朵听写失败: {response.text}")

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
    st.markdown("### 👨‍💻 关于作者")
    st.write("我是高赫辰，一名对AI与摄影充满热情的高一学生。")
    st.success("📱 微信：AKKKDDDTTT")
    st.divider()
    
    st.markdown("### 📜 历史总结记录")
    if not st.session_state.history:
        st.info("还没有总结过视频哦，快去试试吧！")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            if st.button(f"🎬 {item['title']}", key=f"hist_{i}"):
                st.session_state.display_content = item['summary']

st.title("🎬 全能视频 AI 总结神器")
st.markdown("支持 B站 / 抖音。**直接粘贴APP里的分享文案即可，不需要单独抠网址！**")

user_input = st.text_input("🔗 请在此粘贴：", placeholder="例如：【数码博主的年度推荐】 https://b23.tv/slYxUzF")

if st.button("🚀 一键提取并总结"):
    if not user_input:
        st.warning("⚠️ 老板，还没输入链接呢！")
    else:
        with st.status("AI 引擎全速运转中...", expanded=True) as status:
            try:
                st.write("1️⃣ 正在智能剔除多余文案，锁定真实链接...")
                clean_url = extract_clean_url(user_input)
                if not clean_url:
                    st.error("❌ 没在文本里找到有效的网址，请检查输入！")
                    st.stop()
                
                st.write(f"👉 成功锁定目标：{clean_url}")
                    
                st.write("2️⃣ 突破次元壁，下载音频中 (视时长大约需要 5-15 秒)...")
                audio_file = download_audio(clean_url)
                if not audio_file:
                    st.error("❌ 音频抓取失败，该视频可能设置了权限防抓取。")
                    st.stop()
                    
                st.write("3️⃣ 召唤超级耳朵，听写转换中...")
                transcript = audio_to_text(audio_file)
                
                st.write("4️⃣ 大脑深度思考，生成提炼总结...")
                summary = summarize_text(transcript)
                
                # 存入历史记录
                short_title = user_input[:15] + "..." if len(user_input) > 15 else user_input
                st.session_state.history.append({"title": short_title, "summary": summary})
                st.session_state.display_content = summary
                
                status.update(label="✅ 全部处理完成！", state="complete", expanded=False)
            except Exception as e:
                status.update(label="❌ 出现错误！", state="error")
                st.error(f"抱歉出错了，具体信息：{str(e)}")

# 集中显示
if st.session_state.display_content:
    st.divider()
    st.markdown(st.session_state.display_content)