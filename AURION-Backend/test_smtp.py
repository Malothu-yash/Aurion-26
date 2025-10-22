import smtplib

sender = "rathodvamshi369@gmail.com"
password = "cwnc dchn qkgq fnzu"  # paste the 16-char app password
receiver = "yashwanthnayakmalothu@gmail.com"

message = """\
Subject: Test Email from Aurion

This is a direct test email from Aurion Gmail SMTP.
"""

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, message)
        print("✅ Email sent successfully!")
except Exception as e:
    print("❌ Error:", e)
