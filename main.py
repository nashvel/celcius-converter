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

# HTML Template with Fixed JavaScript
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body { font-family: Consolas; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #F8F9FA; }
    .container { width: 300px; background-color: #F0F8FF; padding: 15px; border: 1px solid #ccc; border-radius: 5px; text-align: center; }
    .label { font-size: 16px; display: block; margin-bottom: 10px; }
    input { width: 150px; padding: 5px; text-align: left; }
    .button-container { text-align: left; margin-top: 10px; }
    button { margin: 5px; padding: 8px 12px; font-size: 14px; border: 2px solid black; background-color: white; border-radius: 3px; cursor: pointer; }
    button:active { background-color: #ddd; }
  </style>
</head>
<body>

  <div class="container">
    <div class="label">Temperature Conversion</div>
    
    <br>

    <form id="convertForm">
      <div> 
        Celsius:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 
        <input type="number" step="any" name="celsius" id="celsius" autofocus required>
      </div>
    
      <div style="margin-top: 10px;"> 
        Fahrenheit:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 
        <input type="text" id="fahrenheit" disabled>
      </div>

      <div class="button-container">
        <button type="submit">Convert</button>
        <button type="button" id="clearBtn">Clear</button>
      </div>
    </form>
  </div>

  <script>
    document.getElementById("convertForm").addEventListener("submit", async function(event) {
        event.preventDefault(); // Prevent default form submission

        let celsiusValue = document.getElementById("celsius").value;

        if (celsiusValue === "") {
            alert("Please enter a Celsius value!");
            return;
        }

        let formData = new FormData();
        formData.append("celsius", celsiusValue);

        let response = await fetch("/convert", {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            let text = await response.text();
            document.body.innerHTML = text; // Update page with response
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

def get_user_location(ip: str):
    """Fetches user geolocation based on IP address."""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        return {
            "country": data.get("country"),
            "region": data.get("regionName"),
            "city": data.get("city"),
            "lat": data.get("lat"),
            "lon": data.get("lon"),
            "isp": data.get("isp")
        }
    except:
        return {"error": "Could not fetch location"}

def send_email(ip, location, device, celsius, fahrenheit, timestamp):
    """Sends an email with user details."""
    try:
        subject = "Temperature Conversion Alert"
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = SYSTEM_EMAIL
        msg["Subject"] = subject

        # Email body
        body = f"""
        🔥 Someone converted Celsius to Fahrenheit! 🔥

        🌡️ Converted Temperature: {celsius}°C → {fahrenheit}°F
        📍 IP Address: {ip}
        🌎 Location: {location.get("city")}, {location.get("region")}, {location.get("country")}
        📌 Coordinates: {location.get("lat")}, {location.get("lon")}
        🖥️ Device: {device['browser']} on {device['os']} ({device['device']})
        🕒 Time: {timestamp}

        Sent automatically by FastAPI
        """

        msg.attach(MIMEText(body, "plain"))

        # Connect to Gmail SMTP Server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
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
    # Convert Celsius to Fahrenheit
    fahrenheit = (celsius * 9/5) + 32

    # Get user IP
    client_ip = request.client.host

    # Get user agent (device details)
    user_agent_str = request.headers.get("user-agent", "")
    user_agent = parse(user_agent_str)

    device_details = {
        "browser": user_agent.browser.family,
        "os": user_agent.os.family,
        "device": user_agent.device.family,
    }

    # Get location info
    location_data = get_user_location(client_ip)

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Send email
    send_email(client_ip, location_data, device_details, celsius, fahrenheit, timestamp)

    # Log details
    log_data = {
        "ip": client_ip,
        "device": device_details,
        "location": location_data,
        "timestamp": timestamp
    }

    print("User Data:", log_data)  # Log user details

    # Return updated HTML
    return HTML_TEMPLATE.replace('value=""', f'value="{fahrenheit:.2f}"')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
