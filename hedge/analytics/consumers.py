# analytics/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LivePriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "live_price",
            self.channel_name
        )
        await self.accept()
        print("WebSocket connection opened")  # Debug print

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "live_price",
            self.channel_name
        )
        print("WebSocket connection closed")  # Debug print

    async def live_price_update(self, event):
        price = event['price']
        print(f"Sending live price update: {price}")  # Debug print
        await self.send(text_data=json.dumps({
            'price': price
        }))



class TradeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("trades_group", self.channel_name)
        await self.accept()
        print("WebSocket connection opened")  # Debug print

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("trades_group", self.channel_name)
        print("WebSocket connection closed")  # Debug print

    async def trade_update(self, event):
        trade_id = event['trade_id']
        trade_data = event['trade_data']
        await self.send(text_data=json.dumps({
            'trade_id': trade_id,
            'trade_data': trade_data,
        }))