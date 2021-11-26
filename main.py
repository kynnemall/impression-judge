import os
import math
import librosa
import warnings
warnings.filterwarnings('ignore')
import streamlit as st
from random import randint
from time import strftime, gmtime
from streamlit_player import st_player
from resemblyzer import VoiceEncoder
from utils import preprocess_audio, judge

st.set_page_config(page_title="AI Impersonation Judge")
st.title("Impersonation Judge")

@st.cache(allow_output_mutation=True)
def load_model():
    model = VoiceEncoder()
    return model

model = load_model()

st.info("This web app is still in production, so don't be surprised if it doesn't work as expected just yet")
intro = """
<p>I'm the Impersonation Judge and I'm going to gauge how well you can do voice impressions!
<br>You just need to provide:</p>
<ol>
    <li>A link to a YouTube video containing the audio you're trying to mimic</li>
    <li>The start and end time in seconds of the section you want me to compare you to
    <li>An audio clip of your impression</li>
</ol>
<p>My fancy AI will allow me to grade your impression and give it a score between 0 and 100 of how close your impression is to the original. If you're ready, let's go!</p>
"""
st.markdown(intro, unsafe_allow_html=True)
col1, col2 = st.columns(2)

user_audio = col1.file_uploader("Upload an mp3 recording", "mp3")
link = col2.text_input("Paste link to YouTube video here")

if link and user_audio:
    print(user_audio)
    col3, col4 = st.columns(2)
    with st.spinner("Getting audio from YouTube video"):
        os.system(f"youtube-dl --extract-audio --audio-format mp3 -o audiofile.mp3 {link}")
    st_player(link)

    col3.write("YouTube audio")
    col3.audio("audiofile.mp3")
    col4.write("User audio")
    col4.audio(user_audio)
    data,sr = librosa.load("audiofile.mp3")
    max_s = float(data.shape[0] / sr)
    
    t0, t1 = st.slider("Select start and end time in seconds", min_value=0.0,
                        max_value=max_s, value=[0.0, max_s], step=1.0)
    t0_time = strftime("%H:%M:%S", gmtime(t0))
    t1_time = strftime("%H:%M:%S", gmtime(t1)) 
    col5, col6 = st.columns(2)
    col5.write(f"Current start time {t0_time}")
    col6.write(f"Current end time {t1_time}")
    
    score = math.floor(judge(model, user_audio.name, t0, t1) * 100)
    st.write(f"Your score: {score}/100")
    if score > 95:
        st.write("Wow, that's an amazing impression! I could hardly tell the difference!")
    elif score > 80:
        st.write("Great impression, just one or two tiny details you can improve on, but great impression nonetheless")
    elif score > 70:
        st.write("That's a good impression you got there, could do with some polishing up though")
    else:
        st.write("Maybe you could do with a bit more practice. Why not check it this video for some tips?")
        with open("helpful_links.txt", "r") as f:
            links = f.readlines()
            num = randint(0, len(links))
            st.player(links[num])
    
