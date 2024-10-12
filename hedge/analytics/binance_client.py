# your_app/binance_client.py

from binance.client import Client
from django.conf import settings
# Binance API credentials
# quant_key = "ZGNCPGhPU492dtG2mY2G9B6uXzfztfss6EoNi6qYQHh7LV0Ktt8rby1YeY697Sn8"
# quant_secret = b'fRngz6zClqdwkQiVrshj9CoLOpyC3fzMVgOjGeEnQ3d7HM9hDoMUM8ZjfQd1WHoB'

quant_key = "qQwoiGRn22B1D5GWXvlt8Wmi8T73uG7NgeXEbkYQ5rpgxA5510DdNoSGOjLyOL5h"
quant_secret = b'8xGJGaTTuSWBiiLnSzFFOcsz6FhEhhpIHjPGd2wF2sL5vgcWwiHVeCgfsZ6LdGbF'


class BinanceClient:
    def __init__(self):
        self.client = Client(quant_key, quant_secret)

    def get_symbol_price(self, symbol):
        """Get the current price of a symbol."""
        try:
            price = self.client.get_symbol_ticker(symbol=symbol)
            return price
        except Exception as e:
            print(f"Error fetching price: {e}")
            return None

    def create_order(self, symbol, side, order_type, quantity, price=None):
        """Create an order."""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity,
                price=price
            )
            return order
        except Exception as e:
            print(f"Error creating order: {e}")
            return None
