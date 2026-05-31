import json
import base64
from datetime import datetime
import requests
from django.conf import settings
from django.utils import timezone


def _get_access_token():
    url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate'
    if settings.MPESA_ENVIRONMENT == 'production':
        url = 'https://api.safaricom.co.ke/oauth/v1/generate'

    response = requests.get(url, auth=(
        settings.MPESA_CONSUMER_KEY,
        settings.MPESA_CONSUMER_SECRET
    ), params={'grant_type': 'client_credentials'})

    response.raise_for_status()
    return response.json()['access_token']


def _format_phone(phone):
    phone = phone.strip().replace(' ', '').replace('-', '').replace('+', '')
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    if not phone.startswith('254'):
        phone = '254' + phone
    return phone


def stk_push(phone, amount, order_id, callback_url):
    phone = _format_phone(phone)
    access_token = _get_access_token()

    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    if settings.MPESA_ENVIRONMENT == 'production':
        url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(
        f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}'.encode()
    ).decode()

    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(amount),
        'PartyA': phone,
        'PartyB': settings.MPESA_SHORTCODE,
        'PhoneNumber': phone,
        'CallBackURL': callback_url,
        'AccountReference': f'SN{order_id}',
        'TransactionDesc': 'SokoyaNguo Payment',
    }

    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def query_status(checkout_request_id):
    access_token = _get_access_token()

    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query'
    if settings.MPESA_ENVIRONMENT == 'production':
        url = 'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(
        f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}'.encode()
    ).decode()

    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id,
    }

    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()
