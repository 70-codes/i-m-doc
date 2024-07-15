import requests


def get_access_token():
    consumer_key = "V6jFuRCVFEfzbzF3EQduGuvdLAC5cYG6AGq4k0CfORsmTNfD"
    consumer_secret = "kJOWWd2xu0CHisyDz2I1S4l9sTWUGOrDbyZAEK7EJR9NYJBOjBacY7AFEVRYN2kK"
    access_token_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    headers = {"Content-Type": "application/json"}
    auth = (consumer_key, consumer_secret)
    try:
        response = requests.get(access_token_url, headers=headers, auth=auth)
        response.raise_for_status()
        result = response.json()
        access_token = result["access_token"]
        return access_token
    except requests.exceptions.RequestException as e:
        return None
