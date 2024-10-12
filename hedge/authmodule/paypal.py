# paypal.py
import paypalrestsdk
import logging

# Configure PayPal with your credentials
paypalrestsdk.configure({
    "mode": "sandbox",  # or "live"
    "client_id": "AQJ4rC4ZjMX_dIzXeOAa63LV3Q4025TWtwk9GiTrRz_CEnHPq5k52OiPWJBOkLnUwy4sDMrUTxQC8nXc",
    "client_secret": "EGDWSDSxL1aZ425CzTsCKxmFJT5DJ4LCBaa0L6JPMQ98uwlP3Q4Epb6eY3XoJGIu3ktLmSz5lngm3SU0",
    # "client_id": "AXmn0ys8TdwydlIrLeXNYJVKGaxOe8S5DkrgkJdVDJ1iN4R04HJN7oN3WpLC5QbPzNFn3prgmapkfDxZ",
    # "client_secret": "EH2J7tPz5EUcY75BoYbKCQKofE0iaCakmj5jWfKcPR0rVtXySYVROyYEXNFfCpXcA56C7s55bnL4h96X"
})

# Logging configuration
logging.basicConfig(level=logging.INFO)



def create_payment(amount, return_url, cancel_url):
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "transactions": [{
            "amount": {
                "total": f"{amount}",
                "currency": "USD"
            },
            "description": "Payment description"
        }],
        "redirect_urls": {
            "return_url": return_url,
            "cancel_url": cancel_url
        }
    })

    if payment.create():
        return payment
    else:
        return None

def execute_payment(payment_id, payer_id):
    payment = paypalrestsdk.Payment.find(payment_id)
    if payment.execute({"payer_id": payer_id}):
        return payment
    else:
        return None
