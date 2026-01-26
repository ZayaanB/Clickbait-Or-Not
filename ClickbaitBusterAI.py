import streamlit as st
import ollama
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import re

# --- APP CONFIG ---
st.set_page_config(page_title="Clickbait Buster", page_icon="🕵️‍♂️")
st.title("🕵️‍♂️ Clickbait Buster AI")

with st.sidebar:
    st.header("Settings")
    selected_model = st.selectbox("Choose Model", ["llama3.2", "mistral"])

# --- STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- EXTRACTION LOGIC ---
def get_video_data(url):
    try:
        ydl_opts = {'quiet': True, 'skip_download': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title'), info.get('id')
    except Exception:
        return None, None

def get_transcript_text(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'skip_download': True,
        'writeautosubs': True, 
        'subtitleslangs': ['en'],
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            # Use description as context fallback if subs are missing/blocked
            return info.get('description', 'No transcript available.')[:5000]
    except Exception as e:
        return f"Extraction error: {str(e)}"

# --- UI RENDERING ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT & INFERENCE ---
if prompt := st.chat_input("Paste a YouTube URL..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        def stream_generator():
            if "youtube.com" in prompt or "youtu.be" in prompt:
                with st.spinner("Analyzing..."):
                    title, v_id = get_video_data(prompt)
                    transcript = get_transcript_text(v_id)
                
                final_prompt = (
                    f"You are a modern Clickbait Auditor familiar with youtube marketing tactics. Dont take everything literally and understand metaphors, similies and other figures of speech.\n"
                    f"VIDEO TITLE: {title}\n"
                    f"TRANSCRIPT CONTENT: {transcript}\n\n"
                    f"--- SCORING RUBRIC (Be lenient) ---\n"
                    f"1-3: HONEST - Title is boring but accurate. No missing info.\n"
                    f"4-6: EXAGGERATED - Title uses 'best' or 'amazing' but is mostly true.\n"
                    f"7-9: MISLEADING - Title leaves out a massive detail or implies a lie.\n"
                    f"10: TOTAL FRAUD - Title has NOTHING to do with the video.\n\n"
                    f"--- EXAMPLES ---\n"
                    f"Example 1: Title 'My Day at the Park' (Score: 1/10)\n"
                    f"Example 2: Title 'I ALMOST DIED' but it was just a bee sting (Score: 10/10)\n\n"
                    f"ANALYSIS TASK:\n"
                    f"0. Provide a short summary of the video\n"
                    f"1. Give a Score based on the rubric.\n"
                    f"2. State one specific thing the title promised that the video didn't deliver.\n"
                    f"3. Verdict: Is it worth the user's time?\n"
                    f"4. Verdict: In what cases may it be worth the user's time?"
                )
            else:
                final_prompt = prompt

            try:
                stream = ollama.chat(
                    model=selected_model,
                    messages=[{'role': 'user', 'content': final_prompt}],
                    stream=True
                )
                for chunk in stream:
                    yield chunk['message']['content']
            except Exception as e:
                yield f"Inference Error: {e}"

        response_text = st.write_stream(stream_generator())
        st.session_state.messages.append({"role": "assistant", "content": response_text})