# analytics/tasks.py
import os
from celery import shared_task
from binance.client import Client
from django.core.signals import Signal
import logging

live_price_signal = Signal()
trade_created_signal = Signal()
logger = logging.getLogger(__name__)

@shared_task
def fetch_live_price():
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    client = Client(api_key, api_secret)
    try:
        symbol = 'ETHUSDT'
        ticker = client.get_symbol_ticker(symbol=symbol)
        price = ticker['price']
        logger.info(f"Fetched live price: {price}")  # Log the price
        live_price_signal.send(sender=None, price=price)
        return price
    except Exception as e:
        logger.error(f"Error fetching live price: {e}")
        return str(e)
