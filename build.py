import os
import subprocess

# Ensure the directory exists before writing files
os.makedirs("/var/www/hcaptcha", exist_ok=True)

# Ask for user input
site_key = input("Enter your hCaptcha Site Key: ")
secret_key = input("Enter your hCaptcha Secret Key: ")
protected_url = input("Enter the URL you want to protect: ")
domain_name = input("Enter your domain name (or server IP if no domain): ")

# Flask app code with user input
flask_code = f'''from flask import Flask, request, render_template_string, redirect
import requests

app = Flask(__name__)

HCAPTCHA_SITE_KEY = "{site_key}"
HCAPTCHA_SECRET_KEY = "{secret_key}"
PROTECTED_URL = "{protected_url}"

HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <title>hCaptcha Verification</title>
    <script src="https://js.hcaptcha.com/1/api.js" async defer></script>
</head>
<body>
    <h2>Verify to Access</h2>
    <form action="/verify" method="POST">
        <div class="h-captcha" data-sitekey="{{{{ site_key }}}}"></div>
        <br>
        <button type="submit">Submit</button>
    </form>
</body>
</html>"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE, site_key=HCAPTCHA_SITE_KEY)

@app.route("/verify", methods=["POST"])
def verify():
    token = request.form.get("h-captcha-response")
    data = {{
        "secret": HCAPTCHA_SECRET_KEY,
        "response": token
    }}
    
    response = requests.post("https://api.hcaptcha.com/siteverify", data=data).json()
    
    if response.get("success"):
        return redirect(PROTECTED_URL)
    else:
        return "<h1>Verification Failed. Please try again.</h1>"

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
'''

# Write Flask app to file
os.makedirs("/var/www/hcaptcha", exist_ok=True)
with open("/var/www/hcaptcha/app.py", "w") as f:
    f.write(flask_code)

# Install required packages
subprocess.run("sudo apt update && sudo apt install -y nginx python3 python3-pip certbot python3-certbot-nginx", shell=True, check=True)
subprocess.run("pip3 install flask requests gunicorn", shell=True, check=True)

# Nginx configuration
nginx_config = f'''server {{
    listen 80;
    server_name {domain_name};

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}'''

# Write Nginx config
with open("/etc/nginx/sites-available/hcaptcha", "w") as f:
    f.write(nginx_config)

# Enable site and restart Nginx
subprocess.run("sudo ln -s /etc/nginx/sites-available/hcaptcha /etc/nginx/sites-enabled/", shell=True, check=True)
subprocess.run("sudo nginx -t && sudo systemctl restart nginx", shell=True, check=True)

# Create systemd service for Flask app
systemd_service = '''[Unit]
Description=Flask app with hCaptcha
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/hcaptcha
ExecStart=/usr/local/bin/gunicorn --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
'''

with open("/etc/systemd/system/hcaptcha.service", "w") as f:
    f.write(systemd_service)

# Enable and start the Flask app service
subprocess.run("sudo systemctl daemon-reload", shell=True, check=True)
subprocess.run("sudo systemctl enable hcaptcha", shell=True, check=True)
subprocess.run("sudo systemctl start hcaptcha", shell=True, check=True)

# Obtain SSL certificates using Certbot
subprocess.run(f"sudo certbot --nginx -d {domain_name} --non-interactive --agree-tos --email cgmcfall@gmail.com", shell=True, check=True)

# Update Nginx to listen on HTTPS and reload
nginx_config_https = f'''server {{
    listen 80;
    server_name {domain_name};

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}

server {{
    listen 443 ssl;
    server_name {domain_name};

    ssl_certificate /etc/letsencrypt/live/{domain_name}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain_name}/privkey.pem;

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}'''

# Write the updated Nginx configuration
with open("/etc/nginx/sites-available/hcaptcha", "w") as f:
    f.write(nginx_config_https)

# Reload Nginx to apply HTTPS
subprocess.run("sudo nginx -t && sudo systemctl reload nginx", shell=True, check=True)

print("Setup Complete! Visit https://{domain_name} to test your hCaptcha-protected URL with HTTPS.")
