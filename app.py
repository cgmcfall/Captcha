from flask import Flask, render_template, request, redirect, session
import requests

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Zoom Vanity URL
ZOOM_URL = "https://zoom.us/my/yourvanityurl"

# Cloudflare Turnstile Keys
TURNSTILE_SITE_KEY = "YOUR_TURNSTILE_SITE_KEY"
TURNSTILE_SECRET_KEY = "YOUR_TURNSTILE_SECRET_KEY"

@app.route("/")
def home():
    if session.get("verified"):
        return redirect(ZOOM_URL)
    return f"""
        <html>
            <head>
                <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
            </head>
            <body>
                <form action="/verify" method="POST">
                    <div class="cf-turnstile" data-sitekey="{TURNSTILE_SITE_KEY}"></div>
                    <br/>
                    <button type="submit">Verify</button>
                </form>
            </body>
        </html>
    """

@app.route("/verify", methods=["POST"])
def verify():
    token = request.form.get("cf-turnstile-response")
    if not token:
        return "CAPTCHA required"

    response = requests.post(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data={"secret": TURNSTILE_SECRET_KEY, "response": token},
    ).json()

    if response.get("success"):
        session["verified"] = True
        return redirect(ZOOM_URL)
    return "CAPTCHA failed, try again."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)