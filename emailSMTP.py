import smtplib
import os

my_email = os.environ.get("INFO_EMAIL")
my_password = os.environ.get("INFO_EMAIL_PASSWORD")


def send_verify_email(email, code):
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(user=my_email, password=my_password)
        connection.sendmail(
            from_addr=my_email,
            to_addrs=email,
            msg=f"Subject:Player Finder Verify\n\nYour verify code is: {code}"
        )
    print("email send")
