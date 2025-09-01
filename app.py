import streamlit as st
import os
import time

from main import summarize_consultation, extract_text_from_word_filelike
from word_generator import write_summary_to_docx
from zoom_rec import ZoomClient

# Hardcoded Authentication Credentials
USERNAME = "admin"
PASSWORD = "password123"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ---------- LOGIN ----------
def login():
    st.set_page_config(page_title="Login - Post Consult Note Summarizer", page_icon="🔒")
    st.image("lc-logo-mobile1.png", width=150)
    st.title("🔒 Login to Access")
    username = st.text_input("👤 Username", value="", key="username")
    password = st.text_input("🔑 Password", value="", type="password", key="password")

    if st.button("🔓 Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ Login Successful! Redirecting...")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Invalid Username or Password")

def logout():
    st.session_state.authenticated = False
    st.rerun()

# ---------- MAIN APP ----------
def main_app():
    st.set_page_config(page_title="Pre-Consult Notes", layout="wide")

    col1, col2 = st.columns([5, 1])
    with col1:
        st.image("lc-logo-mobile1.png", width=150)
        st.title("Post-Consult Notes")
    with col2:
        if st.button("🚪 Logout"):
            logout()

    st.markdown("Paste a **Zoom Recording URL** and optionally upload a **preconsult note (.docx)** to generate a summary.")

    uploaded_word_file = st.file_uploader("Upload Preconsult Note (.docx) [Optional]", type=["docx"])
    zoom_url = st.text_input("🔗 Zoom Recording URL")

    if st.button("Generate Summary (.docx)"):
        st.info("⏳ Downloading and processing Zoom recording...")

        extracted_text = ""
        if uploaded_word_file:
            try:
                extracted_text = extract_text_from_word_filelike(uploaded_word_file)
            except Exception as e:
                st.error(f"❌ Failed to read Word file: {e}")

        with st.spinner("🔄 Fetching recording from Zoom..."):
            try:
                ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
                ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
                ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")

                zoom_client = ZoomClient(ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET)
                recording_info = zoom_client.get_recording_by_meeting_url(zoom_url)

                # download into temp dir
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    zoom_client.download_recording(recording_info, download_dir=tmpdir)

                    downloaded_files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.endswith((".mp4", ".m4a"))]
                    if not downloaded_files:
                        st.error("❌ No audio/video file found in Zoom recording.")
                        return

                    # Pick first downloaded file
                    file_path = downloaded_files[0]

                    summary = summarize_consultation(file_path, extracted_text)
                    final_doc_path = write_summary_to_docx([summary])

                    with open(final_doc_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Final Summary (.docx)",
                            data=f,
                            file_name="Post_Consult_note_Summary.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

            except Exception as e:
                st.error(f"❌ Failed to process Zoom recording: {e}")

# ---------- RUN ----------
if st.session_state.authenticated:
    main_app()
else:
    login()
