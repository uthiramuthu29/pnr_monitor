import requests
import smtplib
import os
import json
from datetime import datetime, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ================= CONFIG =================

print("API KEY:", bool(os.environ.get("RAPIDAPI_KEY")))
print("EMAIL:", bool(os.environ.get("PNR_GMAIL_ADDRESS")))
print("PASS:", bool(os.environ.get("PNR_GMAIL_APP_PASSWORD")))


PNR_NUMBER = "4540418892"

API_URL = f"https://irctc-indian-railway-pnr-status.p.rapidapi.com/getPNRStatus/{PNR_NUMBER}"

HEADERS = {
    "X-RapidAPI-Key": os.environ.get("RAPIDAPI_KEY"),
    "X-RapidAPI-Host": "irctc-indian-railway-pnr-status.p.rapidapi.com"
}

STATE_FILE = "last_status.json"

EMAIL_SENDER = os.environ.get("PNR_GMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("PNR_GMAIL_APP_PASSWORD")

EMAIL_RECIPIENTS = [
    "uthiramuthusp29@gmail.com",
    "shanmugavelu434@gmail.com",
    "pponesakkiammal@gmail.com",
    "selvipriyadharshinisp24@gmail.com"
]

# =========================================


def is_quiet_hours():
    now = datetime.now().time()
    return now >= time(23, 0) or now <= time(6, 0)


def load_last_status():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_current_status(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)


def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(EMAIL_RECIPIENTS)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)


def fetch_pnr_status():
    response = requests.get(API_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.json()


def main():

    if is_quiet_hours():
        print("Quiet hours. Skipping check.")
        return

    data = fetch_pnr_status()

    if not data.get("success"):
        print("API failure")
        return

    pnr_data = data["data"]

    passenger = pnr_data.get("passengerList", [{}])[0]

    booking_status = passenger.get("bookingStatusDetails", "N/A")
    current_status = passenger.get("currentStatusDetails", "N/A")

    chart_status = pnr_data.get("chartStatus", "Unknown")
    chart_prepared = chart_status.lower() == "chart prepared"


    last_data = load_last_status()
    last_hour_status = last_data["currentStatus"] if last_data else "N/A"

    email_body = f"""
PNR : {PNR_NUMBER}

Booking Status :
{booking_status}

Last Hour Status :
{last_hour_status}

Current Status :
{current_status}

Chart Status :
{chart_status}

Checked at :
{datetime.now().strftime('%d %b %Y %I:%M %p')}
"""

    send_email(
        subject="🚆 IRCTC PNR Hourly Update",
        body=email_body
    )

    save_current_status({
        "currentStatus": current_status,
        "chartPrepared": chart_prepared
    })

    if chart_prepared:
        send_email(
            subject="✅ Chart Prepared – Final Update",
            body=f"""
PNR : {PNR_NUMBER}

FINAL STATUS :
{current_status}

Chart has been prepared.
Monitoring stopped.
"""
        )


if __name__ == "__main__":
    main()
