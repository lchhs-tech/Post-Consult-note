import streamlit as st
import os
import time
import tempfile

from main import summarize_consultation, extract_text_from_word_filelike
from word_generator import write_summary_to_docx
from email_utils import send_email_with_attachment   # email module import
from zoom_rec import ZoomClient

# Hardcoded Authentication Credentials
USERNAME = "admin"
PASSWORD = "password123"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


# ---------- LOGIN ----------
def login():
    st.set_page_config(page_title="Consultation Summary Tool")
    st.image("lc-logo-mobile1.png", width=150)
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ Login successful!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Invalid username or password")


# ---------- MAIN APP ----------
def main():
    st.set_page_config(page_title="Consultation Summary Tool", layout="wide")
    st.title("🩺 Post Consultation Summary Generator")

    # --- Upload Word File ---
    st.subheader("📂 Upload Word File")
    word_file = st.file_uploader("Upload a Word file (.docx)", type=["docx"])
    if word_file:
        extracted_text = extract_text_from_word_filelike(word_file)
        st.success("✅ Word file processed successfully!")
    else:
        extracted_text = ""

    # --- Upload Audio/Video File ---
    st.subheader("🎵 Upload Audio/Video File")
    av_file = st.file_uploader("Upload an audio/video file", type=["mp4", "mp3", "wav", "m4a"])
    if av_file:
        suffix = os.path.splitext(av_file.name)[1] if av_file.name else ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(av_file.read())
            temp_file_path = tmp_file.name
        st.success("✅ File uploaded successfully!")
    else:
        temp_file_path = None

    # --- Zoom URL Input ---
    st.subheader("🎥 Enter Zoom Recording URL")
    zoom_url = st.text_input("Zoom URL")
    if zoom_url:
        client = ZoomClient()
        temp_file_path = client.download_zoom_recording(zoom_url)
        if temp_file_path:
            st.success("✅ Zoom recording downloaded successfully!")
        else:
            st.error("❌ Failed to download Zoom recording.")

    # --- Generate Summary ---
    if st.button("🚀 Generate Summary"):
        if not temp_file_path:
            st.error("⚠️ Please upload an audio/video file or provide a Zoom recording URL.")
            return

        with st.spinner("Generating summary..."):
            summary = summarize_consultation(
                temp_file_path,
                extracted_text
            )
            
            # if summary:
                # Save summary to Word file
                # final_doc_path = write_summary_to_docx(summary)

                # --- Email Sending Section ---
            # if final_doc_path:
            if summary:
                send_email_with_attachment(
                    "sampada@lukecoutinho.com",
                    summary,
                )
                st.success("✅ Summary generated and email sent successfully!")

if __name__ == "__main__":
    if not st.session_state.authenticated:
        login()
    else:
        main()
