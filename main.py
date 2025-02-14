from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from user_agents import parse
from datetime import datetime

# Email Credentials
SYSTEM_EMAIL = "nashvelbusiness@gmail.com"
GMAIL_USER = "nacht.system@gmail.com"
GMAIL_PASSWORD = "nngl cwvj bapf zixr"

app = FastAPI()

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Temperature Converter</title>
  <style>
    body { font-family: Consolas; text-align: center; padding: 50px; background-color: #F8F9FA; }
    .container { width: 300px; margin: auto; background: #FFF; padding: 15px; border-radius: 5px; box-shadow: 2px 2px 10px rgba(0,0,0,0.2); }
    input { width: 100px; padding: 5px; }
    button { margin-top: 10px; padding: 8px; background: #007BFF; color: white; border: none; cursor: pointer; }
  </style>
</head>
<body>
  <div class="container">
    <h3>Temperature Conversion</h3>
    <form id="convertForm">
      Celsius: <input type="number" step="any" name="celsius" id="celsius" required>
      <br><br>
      Fahrenheit: <input type="text" id="fahrenheit" disabled>
      <br><br>
      <button type="submit">Convert</button>
      <button type="button" id="clearBtn">Clear</button>
    </form>
  </div>

  <script>
    document.getElementById("convertForm").addEventListener("submit", async function(event) {
        event.preventDefault();
        let celsiusValue = document.getElementById("celsius").value;
        let formData = new FormData();
        formData.append("celsius", celsiusValue);

        let response = await fetch("/convert", { method: "POST", body: formData });
        if (response.ok) {
            let text = await response.text();
            document.body.innerHTML = text;
        } else {
            alert("Error converting temperature.");
        }
    });

    document.getElementById("clearBtn").addEventListener("click", function() {
        document.getElementById("celsius").value = "";
        document.getElementById("fahrenheit").value = "";
    });
  </script>
</body>
</html>
"""

def get_user_location():
    """Fetches user geolocation based on public IP."""
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        return {
            "ip": data.get("ip"),
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country"),
            "coordinates": data.get("loc"),
            "isp": data.get("org"),
        }
    except Exception as e:
        return {"error": f"Could not fetch location: {e}"}

def send_email(ip, location, device, celsius, fahrenheit, timestamp):
    """Sends an email with user details."""
    try:
        subject = "Temperature Conversion Alert"
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = SYSTEM_EMAIL
        msg["Subject"] = subject

        body = f"""
        🔥 Someone converted Celsius to Fahrenheit! 🔥

        🌡️ Converted Temperature: {celsius}°C → {fahrenheit}°F
        📍 IP Address: {ip}
        🌎 Location: {location.get("city")}, {location.get("region")}, {location.get("country")}
        📌 Coordinates: {location.get("coordinates")}
        🖥️ Device: {device['browser']} on {device['os']} ({device['device']})
        🕒 Time: {timestamp}

        Sent automatically by FastAPI
        """

        msg.attach(MIMEText(body, "plain"))

        # Secure email sending using SMTP_SSL
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, SYSTEM_EMAIL, msg.as_string())
        server.quit()
        print("✅ Email sent successfully!")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_TEMPLATE

@app.post("/convert", response_class=HTMLResponse)
async def convert_temperature(request: Request, celsius: float = Form(...)):
    # ✅ Convert Celsius to Fahrenheit
    fahrenheit = (celsius * 9/5) + 32  # Correct formula

    # ✅ Fetch user location (No changes needed)
    location_data = get_user_location()

    # ✅ Get user device info
    user_agent_str = request.headers.get("user-agent", "")
    user_agent = parse(user_agent_str)
    device_details = {
        "browser": user_agent.browser.family,
        "os": user_agent.os.family,
        "device": user_agent.device.family,
    }

    # ✅ Get timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ✅ Send Email with Conversion Details
    send_email(location_data["ip"], location_data, device_details, celsius, fahrenheit, timestamp)

    # ✅ Debugging: Print Conversion Results
    print(f"🌡️ Celsius: {celsius}°C → Fahrenheit: {fahrenheit}°F")
    
    # ✅ FIX: Replace the input field with the correct Fahrenheit value in HTML response
    updated_html = HTML_TEMPLATE.replace(
        '<input type="text" id="fahrenheit" disabled>',  
        f'<input type="text" id="fahrenheit" disabled value="{fahrenheit:.2f}">'
    )

    return updated_html


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
