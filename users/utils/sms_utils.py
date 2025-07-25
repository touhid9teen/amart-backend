


import requests
from django.conf import settings

def send_sms(phone_number, message,request_id, is_unicode=0):

    print(f"----------------------Sending SMS to {phone_number} with message: {message}")  # Debugging line
    payload = {
        "auth": {
            "acode": settings.ARENA_SMS_API_ACODE,
            "apiKey": settings.ARENA_SMS_API_KEY
        },
        "smsInfo": {
            "requestID": request_id,
            "message": message,
            "is_unicode": is_unicode,
            "masking": settings.ARENA_SMS_MASKING,
            "msisdn": phone_number,
            "transactionType": "T",
            "contentID": ""
        }
    }

    headers = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    }

    # dummy_response ={'response': {'code': 200, 'timestamp': '2025-07-25 16:56:30', 'message': 'Success'}, 'info': {'request': 'SMS Send', 'requestID': 13, 'smsCount': 1, 'balance': 2863.0299999999997}}
    # return dummy_response

    response = requests.post(settings.ARENA_SMS_API_URL, json=payload, headers=headers)
    return response.json()
    