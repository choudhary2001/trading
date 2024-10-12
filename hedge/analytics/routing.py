from django.urls import re_path, path
from .consumers import *

websocket_urlpatterns = [
    re_path(r'ws/live-price/$', LivePriceConsumer.as_asgi()),
    path('ws/trades/', TradeConsumer.as_asgi()),
]
