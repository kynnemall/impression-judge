import os
import math
import gspread
import librosa
import warnings
warnings.filterwarnings('ignore')
import streamlit as st
from random import randint
from time import strftime, gmtime, time
from streamlit_player import st_player
from resemblyzer import VoiceEncoder
from utils import *

st.set_page_config(page_title="AI Impression Judge")
st.title("Impression Judge")

def connect_sheet():
    creds = {
            "type": st.secrets["type_"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"]
    }
    sa = gspread.service_account_from_dict(creds)
    sh = sa.open(st.secrets["sheet_name"])
    worksheet = sh.worksheet("Sheet1")
    return worksheet

def update_db(sheet, current_time, score, link, user_input):
    # find next clear row in sheet
    found_row = False
    num = 1000
    while found_row == False:
        res = sheet.get(f"A1:A{num}")
        print(f"Found {len(res)} occupied rows")
        if len(res) < num:
            num = len(res)
            found_row = True
        else:
            num += 1000

    link_ext = link.split("watch")[1]
    sheet.update(f"A{num+1}:D{num+1}", [[current_time, score, link_ext, user_input]])

@st.cache(allow_output_mutation=True)
def load_model():
    model = VoiceEncoder()
    return model

model = load_model()
worksheet = connect_sheet()

# st.info("This web app is currently benig improved, so some functionality may be affected at this time")
intro = """
<p>I'm the Impression Judge and I'm going to gauge how well you can do impressions! They can be voice impressions of celebrities, your favourite cartoon characters, or even imitations of random noises . . . It's all up to you!
<br>You just need to provide:</p>
<ol>
    <li>A link to a YouTube video containing the audio you're trying to mimic</li>
    <li>The start and end time (in seconds) of the section of YouTube video you want me to compare your recording to
    <li>An audio clip of your impression between 10 to 30 seconds</li>
</ol>
<p>My fancy AI will allow me to grade your impression and give it a score between 0 and 100 of how close your impression is to the original. To learn more, check out the sidebar on the left. Now if you're ready, let's see your impression!</p>
"""

st.markdown(intro, unsafe_allow_html=True)

with st.sidebar.expander("How does this web app use my data?"):
    data_usage = """
    <p><strong>No personal data is requested or stored by this web app.</strong><br>If you click on either the <em>agree</em> or <em>disagree</em> button after your impression was scored, 
    the app will store:
    <ol>
        <li>The time,</li>
        <li>the YouTube link you provided,</li>
        <li>your impression score, and
        <li>whether you agree with the app's score or not.</li>
    </p>
    """
    st.markdown(data_usage, unsafe_allow_html=True)

with st.sidebar.expander("How does the Impression Judge score my impressions?"):
    attribution = """
    <p>Impression Judge makes use of the VoiceEncoder model from the <a href="https://github.com/resemble-ai/Resemblyzer" target="_blank" rel="noopener noreferrer"><em>Resemblyzer</em></a> Python package provided by Resemble AI.
    This model processes audio signals and reduces that complex data into a sequence of 256 numbers. The Impression Judge compares
    those numbers and determines a similarity score out of 100.<br><br>I would like to thank them very much for this open source package which will be useful for many more applications I have in mind!
    </p>
    """
    st.markdown(attribution, unsafe_allow_html=True)

with st.sidebar.expander("Contact"):
    contact = """
    <p>You can contact the app creater on <a href="https://twitter.com/MartinPlatelet" target="_blank" rel="noopener noreferrer">Twitter</a> 
    with any queries or issues you may have. Feedback is always appreciated =)
    </p>
    """
    st.markdown(contact, unsafe_allow_html=True)

user_audio = st.file_uploader("Upload an mp3 recording", ["mp3", "m4a", "wav", "ogg"])
link = st.text_input("Paste link to YouTube video here")

if link and user_audio:
    print(user_audio)
    with st.spinner("Getting audio from YouTube video . . ."):
        os.system(f"youtube-dl --extract-audio --audio-format mp3 -o audiofile.mp3 {link}")
    st_player(link)

    st.write("YouTube audio")
    st.audio("audiofile.mp3")
    st.write("User audio")
    st.audio(user_audio)
    data,sr = librosa.load("audiofile.mp3")
    max_s = float(data.shape[0] / sr)
    user_data, sr = librosa.load(user_audio.name)
    user_data = len(user_data) / sr
    
    t0, t1 = st.slider("Select start and end time in seconds", min_value=0.0,
                        max_value=max_s, value=[0.0, max_s], step=1.0)
    t0_time = strftime("%H:%M:%S", gmtime(t0))
    t1_time = strftime("%H:%M:%S", gmtime(t1))
    col5, col6 = st.columns(2)
    col5.write(f"Current start time {t0_time}")
    col6.write(f"Current end time {t1_time}")
    
    if user_data > 30 or user_data < 10:
        st.info("Uploaded audio is greater than 30s. Please upload a file of 10-30s in length")
    if t1 - t0 > 30:
        st.info("Selected section is greater than 30s. Adjust the slider to select a section of 30s or less")
    if user_data <= 30 and user_data >= 10 and t1 - t0 <= 30:
        with st.spinner("Scoring your impression . . ."):
            score = round(judge(model, user_audio.name, t0, t1) * 100, 3)
        str_score = int(math.floor(score))
        st.markdown(f"<p><strong>Your score: {str_score}/100<strong></p>", unsafe_allow_html=True)
        if score > 95:
            st.write("Wow, that's an impressive impression! I thought it was the real deal!")
        elif score > 87:
            st.write("Great impression!")
        elif score > 80:
            st.write("Great impression, just one or two tiny details you can improve on, but great impression nonetheless")
        elif score > 70:
            st.write("That's a good impression you got there, could do with some polishing up though")
        else:
            st.write("Maybe you could do with a bit more practice. Why not check out this video for some tips?")
            with open("helpful_links.txt", "r") as f:
                links = f.readlines()
                num = randint(0, len(links))
                st_player(links[num])
        st.write("Do you agree with the judge's score?")
        curr_time = int(time())
        col1, col2 = st.columns(2)
        col1.button("Agree", on_click=update_db, args=(worksheet, curr_time, score, link, 1))
        col2.button("Disagree", on_click=update_db, args=(worksheet, curr_time, score, link, 0))

