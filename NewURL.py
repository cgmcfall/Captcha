import os

# Ask for user input
protected_url = input("Enter the new URL you want to protect: ")

# Path to the Flask app file
flask_app_path = "/var/www/hcaptcha/app.py"

# Read the existing Flask app code
with open(flask_app_path, "r") as f:
    flask_code = f.read()

# Replace the old protected URL with the new one
new_flask_code = ""
for line in flask_code.splitlines():
    if line.startswith("PROTECTED_URL ="):
        new_flask_code += f'PROTECTED_URL = "{protected_url}"\n'
    else:
        new_flask_code += line + "\n"

# Write the updated Flask app code back to the file
with open(flask_app_path, "w") as f:
    f.write(new_flask_code)

# Restart the Flask app service to apply changes
os.system("sudo systemctl restart hcaptcha")

print("Protected URL updated successfully!")