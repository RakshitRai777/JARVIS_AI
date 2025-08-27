from mailjet_rest import Client
import os

api_key = '2001047198444aba43aa59f1cf6fcf24'
api_secret = 'f4135e88b350e803dbd1c1677c7b3da9'
mailjet = Client(auth=(api_key, api_secret), version='v3.1')

data = {
  'Messages': [
    {
      "From": {
        "Email": "jarvisai77777770@gmail.com",
        "Name": "Rakshit Rai"
      },
      "To": [
        {
          "Email": "iphotos166@gmail.com",
          "Name": "Rakshit Rai"
        }
      ],
      "Subject": "Greetings from Mailjet.",
      "TextPart": "My first Mailjet email",
      "HTMLPart": "<h3>Dear passenger, welcome to Mailjet!</h3><br />May the delivery force be with you!"
    }
  ]
}

result = mailjet.send.create(data=data)
print(result.status_code)
print(result.json())
