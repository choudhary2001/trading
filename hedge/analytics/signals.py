# analytics/signals.py
from analytics.tasks import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from django.dispatch import receiver
from .models import TradeAlert
from django.core.signals import Signal

# Define a custom signal for trade creation with parameters


logger = logging.getLogger(__name__)

def send_live_price(sender, price, **kwargs):
    channel_layer = get_channel_layer()
    logger.info(f"Sending live price update: {price}")  # Log the sending action
    async_to_sync(channel_layer.group_send)(
        'live_price',
        {
            'type': 'live_price_update',
            'price': price
        }
    )

live_price_signal.connect(send_live_price)



@receiver(trade_created_signal)
def trade_created_handler(sender, trade_id, trade_data, **kwargs):
    # Handle what happens when a trade is created
    print(f"Trade created: ID={trade_id}, Data={trade_data}")
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'trades_group',  # Replace with your actual group name
        {
            'type': 'trade_update',
            'trade_id': trade_id,
            'trade_data': trade_data,
        }
    )