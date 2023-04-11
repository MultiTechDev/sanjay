from twilio.rest import Client


# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = 'ACc5656af19acaa8fe0166ebf6ce120791'
auth_token = '9f4be7d5b536f706a75ac2088de9390c'
client = Client(account_sid, auth_token)

def sendSMS(sender,recipient,body):
    message = client.messages \
                    .create(
                        body=body,
                        from_=sender,
                        to=recipient
                    )

    print(message.sid)