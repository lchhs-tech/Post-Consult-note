import streamlit as st
import os
import time
from email_utils import send_email_with_attachment
from main import summarize_consultation, extract_text_from_word_filelike
from word_generator import write_summary_to_docx
from zoom_rec import ZoomClient
import tempfile

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

    st.markdown("Paste a **Zoom Recording URL** and optionally upload a **preconsult note (.docx)** and/or a **manual audio/video file** to generate a summary.")

    # Upload Preconsult Note
    uploaded_word_file = st.file_uploader("Upload Preconsult Note (.docx) [Optional]", type=["docx"])

    # ✅ New uploader in the middle for audio/video
    uploaded_media_file = st.file_uploader(
        "Upload Audio/Video File (.mp4, .m4a, .wav) [Optional]",
        type=["mp4", "m4a", "wav"]
    )

    # Zoom URL
    zoom_url = st.text_input("🔗 Zoom Recording URL")

    if st.button("Generate Summary (.docx)"):
        st.info("⏳ Downloading and processing inputs...")

        extracted_text = ""

        # Handle preconsult note
        if uploaded_word_file:
            try:
                extracted_text = extract_text_from_word_filelike(uploaded_word_file)
            except Exception as e:
                st.error(f"❌ Failed to read Word file: {e}")

        file_path = None  # default None, will set based on input

        if uploaded_media_file:
            # ✅ If user uploaded manual audio/video, use that instead of Zoom
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_media_file.name)[1]) as tmp_media:
                tmp_media.write(uploaded_media_file.read())
                tmp_media.flush()
                file_path = tmp_media.name

        elif zoom_url:
    # ✅ Else fallback to Zoom
            with st.spinner("🔄 Fetching recording from Zoom..."):
                try:
                    ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
                    ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
                    ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")

                    zoom_client = ZoomClient(ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET)
                    recording_info = zoom_client.get_recording_by_meeting_url(zoom_url)

                    with tempfile.TemporaryDirectory() as tmpdir:
                        zoom_client.download_recording(recording_info, download_dir=tmpdir)

                        downloaded_files = [
                            os.path.join(tmpdir, f)
                            for f in os.listdir(tmpdir)
                            if f.endswith((".mp4", ".m4a"))
                        ]
                        if not downloaded_files:
                            st.error("❌ No audio/video file found in Zoom recording.")
                            return

                        # ✅ copy to a safe temp file that persists after block exits
                        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(downloaded_files[0])[1])
                        with open(downloaded_files[0], "rb") as src, open(tmp_file.name, "wb") as dst:
                            dst.write(src.read())

                        file_path = tmp_file.name
                except Exception as e:
                    st.error(f"❌ Failed to process Zoom recording: {e}")
                    return

        if file_path:
            # Run summarization
            with st.spinner("🔄 Generating the summary"):
                summary = summarize_consultation(file_path, extracted_text)
                
                # final_doc_path = write_summary_to_docx([summary])

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


# ---------- RUN ----------
if st.session_state.authenticated:
    main_app()
else:
    login()
