import streamlit as st
import ollama
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

# 1. UI SETUP
st.set_page_config(page_title="Clickbait Buster", page_icon="🕵️‍♂️", layout="wide")
st.title("🕵️‍♂️ Clickbait Buster AI")

with st.sidebar:
    st.header("Settings")
    selected_model = st.selectbox("Choose Model", ["llama3.2", "phi3", "mistral"])
    st.caption("Llama 3.2 is best for most laptops.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. HELPER FUNCTIONS
def get_video_data(url):
    ydl_opts = {'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get('title'), info.get('id')

def get_transcript_text(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t['text'] for t in transcript])[:6000]
    except:
        return "No transcript available."

# 3. CHAT DISPLAY
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. CHAT LOGIC (The "Pro" Streaming Version)
if prompt := st.chat_input("Paste a YouTube URL or ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        def stream_generator():
            # Check if input is a YouTube link
            if "youtube.com" in prompt or "youtu.be" in prompt:
                with st.spinner("Extracting video data..."):
                    title, v_id = get_video_data(prompt)
                    transcript = get_transcript_text(v_id)
                
                final_prompt = f"Title: {title}\nContent: {transcript}\n\nTask: Analyze if the title is clickbait. Rate 1-10 and give a summary."
            else:
                final_prompt = prompt

            # Stream from Ollama
            stream = ollama.chat(model=selected_model, 
                                messages=[{'role': 'user', 'content': final_prompt}],
                                stream=True)
            for chunk in stream:
                yield chunk['message']['content']

        # This triggers the "typing" animation
        response_text = st.write_stream(stream_generator())
        st.session_state.messages.append({"role": "assistant", "content": response_text})