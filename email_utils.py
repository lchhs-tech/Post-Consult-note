import smtplib
import os
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load environment variables from .env
load_dotenv()

def send_email_with_attachment(to_email, message):
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_USER = os.getenv("EMAIL_USER")   # your Gmail address
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    # Create the SMTP session
    s = smtplib.SMTP(EMAIL_HOST, 587)
    s.starttls()
    s.login(EMAIL_USER, EMAIL_PASS)

    # Create MIME message
    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = "Post Consult Summary"

    health_history_items = message.get("health_history", [])
    if isinstance(health_history_items, list):
        health_history_html = "<ul>"
        for item in health_history_items:
            health_history_html += f"<li>{item}</li>"
        health_history_html += "</ul>"
    else:
        health_history_html = f"<p>{health_history_items}</p>"

    lifestyle_habits_items = message.get("discussion_recommendations", [])
    if isinstance(lifestyle_habits_items, list):
        lifestyle_habits_html = "<ul>"
        for item in lifestyle_habits_items:
            lifestyle_habits_html += f"<li>{item}</li>"
        lifestyle_habits_html += "</ul>"
    else:
        lifestyle_habits_html = f"<p>{lifestyle_habits_items}</p>"
    # HTML formatted message with bold headings
    html_message = f"""
    <html>
      <body>
        <p>
        <b>{message.get('age', 'N/A')}</b>/ <b>{message.get('gender', 'N/A')}</b>/ <b>{message.get('marital_status', 'N/A')}</b>/ <b>{message.get('city', 'N/A')}</b>/<b>{message.get('food_preference', 'N/A')}</b>/ <b>{message.get('height_feet', 'N/A')}</b>/ <b> {message.get('weight_kg', 'N/A')}</b>/ <b>{message.get('profession', 'N/A')}</b>
        <br>
        <br>
        <b>Health History:</b><br>
         {health_history_html}
        <br>
        <b>Discussion Recommendations:</b><br>
        {lifestyle_habits_html}
        <br>
        <b>Warm Message:</b><br>
        <p>{message.get('warm_message', 'N/A')}
        </p>
      </body>
    </html>
    """

    # Attach the HTML message
    msg.attach(MIMEText(html_message, "html"))

    # Send email
    s.sendmail(EMAIL_USER, to_email, msg.as_string())

    # Terminate session
    s.quit()
