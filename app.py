import streamlit as st
import yt_dlp
import requests
import glob
import os
from openai import OpenAI

# ================= 配置区 =================
# 让代码去系统后台的“秘密金库”里找钥匙，绝对安全！
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
SILICON_API_KEY = st.secrets["SILICON_API_KEY"]
# ==========================================

# 初始化 AI 大脑
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

st.set_page_config(page_title="全能视频总结神器", page_icon="🎬", layout="centered")
import streamlit as st
# ... 其他 import 保持不变 ...

# --- 界面美化：背景图与联系方式 ---
def add_custom_style():
    st.markdown(
        f"""
        <style>
        # 1. 设置全局背景图 (这里找一张简约的摄影感背景，或换成你自己的图片链接)
        .stApp {{
            background-image: url("https://szfilehelper.weixin.qq.com/cgi-bin/mmwebwx-bin/webwxgetmsgimg??&MsgID=4002358105742879346&skey=@crypt_1dfea641_448b9a1e606ae8258f5784fa21e04b03&mmweb_appid=wx_webfilehelper");
            background-attachment: fixed;
            background-size: cover;
        }}
        
        # 2. 让中间的内容区域半透明，更有质感
        .block-container {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

add_custom_style()

# --- 侧边栏：添加你的个人信息 ---
with st.sidebar:
    st.image("https://via.placeholder.com/150", caption="高赫辰 - 开发者") # 这里以后可以换成你的头像链接
    st.markdown("### 👨‍💻 关于作者")
    st.write("我是高赫辰，一名对 AI 和摄影充满热情的开发者。")
    st.divider()
    st.markdown("")
    st.success("微信：AKKKDDDTTT") # 替换成你真实的微信号
    st.write("欢迎反馈建议或寻求合作！")
st.title("🎬 全自动视频 AI 总结神器")
st.markdown("支持 B站/抖音 等数百个平台。只需一个链接，剩下的交给 AI！")

# 用户输入链接
video_url = st.text_input("🔗 请粘贴你想总结的视频链接：", placeholder="例如：https://www.bilibili.com/video/BV1GJ411x7h7")

# --- 核心功能 1：抓取音频 ---
def download_audio(url):
import re  # 专门用来抠文字里的网址
import requests # 用来追踪短链接的真实地址

# --- 新增功能：从乱糟糟的分享文案里提取出网址 ---
def extract_url(text):
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    if urls:
        # 拿到网址后，如果是短链接，先把它还原成真实的长链接
        raw_url = urls[0]
        try:
            # 模拟浏览器去访问一下，看它最后跳到哪
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            response = requests.get(raw_url, headers=headers, allow_redirects=True, timeout=5)
            return response.url
        except:
            return raw_url
    return text

# --- 修改后的抓取音频函数 ---
def download_audio(url):
    # 1. 先把用户输入的（可能带文字的）链接清洗一遍
    clean_url = extract_url(url)
    
    # 2. 配置 yt-dlp，这次我们给它戴上“浏览器面具”
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'quiet': True,
        # ⚠️ 这一行是搞定抖音的关键：伪装成真正的浏览器
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # 使用清洗后的长链接下载
        ydl.download([clean_url])
    
    files = glob.glob("temp_audio.*")
    if files:
        return files[0]
    return None
    # 先清理之前可能残留的旧文件
    for old_file in glob.glob("temp_audio.*"):
        try: os.remove(old_file)
        except: pass

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s', # 固定名字前缀，方便我们等下找
        'quiet': True, # 让终端安静点，不刷屏
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # 找一下下载下来的文件到底叫什么后缀 (m4a, webm 等)
    files = glob.glob("temp_audio.*")
    if files:
        return files[0]
    return None

# --- 核心功能 2：超级耳朵 (语音转文字) ---
def audio_to_text(file_path):
    url = "https://api.siliconflow.cn/v1/audio/transcriptions"
    # 硅基流动提供的极速中文识别模型
    data = {"model": "FunAudioLLM/SenseVoiceSmall", "response_format": "text"}
    headers = {"Authorization": f"Bearer {SILICON_API_KEY}"}
    
    with open(file_path, "rb") as file:
        files = {"file": file}
        response = requests.post(url, files=files, data=data, headers=headers)
    
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"耳朵听写失败啦: {response.text}")

# --- 核心功能 3：AI 大脑总结 ---
def summarize_text(text):
    prompt = f"""
    你是一个专业的视频总结助手。请根据以下提取出的视频语音文本，输出结构化的总结：
    1. 【核心主题】：用一句话概括视频在讲什么。
    2. 【干货提取】：提取 3-5 个核心要点，精简有力。
    3. 【金句/亮点】：如果有特别精彩的观点，请列出1-2条。
    
    以下是视频文本内容：
    {text}
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# ================ 交互逻辑 ================
if st.button("🚀 一键提取并总结"):
    if not video_url:
        st.warning("⚠️ 老板，还没输入链接呢！")
    else:
        try:
            with st.status("AI 运转中，请端杯茶稍作等待...", expanded=True) as status:
                
                st.write("1️⃣ 正在强行突破次元壁，抓取视频声音...")
                audio_file = download_audio(video_url)
                if not audio_file:
                    st.error("抓取失败！请检查链接是否正确。")
                    st.stop()
                    
                st.write("2️⃣ 超级耳朵已开启，正在疯狂速记成文字...")
                transcript = audio_to_text(audio_file)
                
                st.write("3️⃣ 大脑高速运转，正在提炼全篇精华...")
                summary = summarize_text(transcript)
                
                status.update(label="✅ 全部搞定！", state="complete", expanded=False)
            
            # 展示最终成果！
            st.divider()
            st.success("🎉 总结完成！以下是视频的核心精华：")
            st.markdown(summary)
            
            # (可选) 展开查看原始听写的文字，方便核对
            with st.expander("🧐 想看看 AI 听写出来的原始逐字稿？点击展开"):
                st.write(transcript)
                
        except Exception as e:
            st.error(f"❌ 运行中出现了一点小意外：{e}")