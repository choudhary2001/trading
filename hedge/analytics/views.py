# views.py
from django.http import JsonResponse
from django.views import View
from binance.client import Client
import os
import redis
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from .serializers import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from analytics.tasks import *
from django.db.models import Count, Sum, Q
from rest_framework.permissions import IsAuthenticated
import requests, json, hmac, hashlib, time, uuid
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import math
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT, TIME_IN_FORCE_GTC
from authmodule.models import *
from .binance_client import BinanceClient

# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

quant_key = "qQwoiGRn22B1D5GWXvlt8Wmi8T73uG7NgeXEbkYQ5rpgxA5510DdNoSGOjLyOL5h"
quant_secret = "8xGJGaTTuSWBiiLnSzFFOcsz6FhEhhpIHjPGd2wF2sL5vgcWwiHVeCgfsZ6LdGbF"

def get_market_price(symbol):
    # Fetch the current market price for the symbol
    api_endpoint = f'https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}'
    response = requests.get(api_endpoint)
    price_data = response.json()
    return float(price_data['price'])


class TradeCreateAPIView(APIView):
    @swagger_auto_schema(
        request_body=TradeSerializer,
        responses={
            201: openapi.Response(
                description="Trade created successfully",
                schema=TradeSerializer
            ),
            400: openapi.Response(
                description="Invalid data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'non_field_errors': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(type=openapi.TYPE_STRING),
                            description='List of error messages',
                        ),
                    }
                ),
            ),
        },
        operation_description="Create a new trade entry",
        operation_summary="Create Trade"
    )
    def post(self, request, *args, **kwargs):
        # print(request)
        # print(request.data)
        serializer = StrategyDataSerializer(data=request.data)
        strategy = request.data.get('strategy')
        market = request.data.get('market')
        broker = request.data.get('broker')
        symbol = request.data.get('symbol')
        entry_price = request.data.get('entry_price')
        exit_price = request.data.get('exit_price')
        pl = request.data.get('pl')
        time_frame = request.data.get('time_frame')
        entry_type = request.data.get('entry_type')
        stop_loss = request.data.get('stop_loss')
        order_no = request.data.get('order_no')
        api_name = request.data.get('api_name')
        currency = request.data.get('currency')
        percentage = request.data.get('percentage')
        order_1 = request.data.get('order_1')
        order_2 = request.data.get('order_2')
        order_3 = request.data.get('order_3')
        order_4 = request.data.get('order_4')
        order_5 = request.data.get('order_5')
        order_6 = request.data.get('order_6')
        order_7 = request.data.get('order_7')
        order_8 = request.data.get('order_8')
        order_type = request.data.get('order_type')
        patch = request.data['patch']
        
        if patch == "ADM8800145":
            if serializer.is_valid():
                trade = serializer.save()

                if order_type == "Limit":
                    order_type_ = "Limit Order"
                elif order_type == "Market":
                    order_type_ = "Market Order"
                else:
                    order_type_ = "Market Order"

                if entry_type == "Long Close":
                    long_or_short = "Long"
                elif entry_type == "Short Close":
                    long_or_short = "Short"
                elif entry_type == "Long":
                    long_or_short = "Long"
                elif entry_type == "Short":
                    long_or_short = "Short"
                else:
                    return JsonResponse({"message" : "Please Provide correct entry type"}, status=status.HTTP_400_BAD_REQUEST)

                # Fetch active orders for the given strategy and symbol
                orders = Orders.objects.filter(status="Active", symbol=symbol, strategy=strategy, order_type = order_type_, time_frame=time_frame, long_or_short = long_or_short).all()
                print(orders)
                for o in orders:
                    print(o)
                    if o.api.status == 'Active':
                            
                        binance_client = Client(o.api.api_key, o.api.secret_key)

                        # Get current ticker price from Binance
                        ticker = binance_client.get_symbol_ticker(symbol=symbol)
                        current_price = float(ticker['price'])

                        symbol_info = binance_client.get_symbol_info(symbol)
                        # print(symbol_info['filters'])
                        price_precision = symbol_info['filters'][0]['tickSize']  # Precision for price
                        # Initialize variables
                        quantity_precision = None

                        # Iterate through the filters to find 'LOT_SIZE'
                        for filter in symbol_info['filters']:
                            if filter['filterType'] == 'LOT_SIZE':
                                quantity_precision = filter.get('stepSize')
                                break  # Once found, exit the loop

                        # Check if the quantity_precision was found
                        if quantity_precision is None:
                            raise ValueError("Could not find 'stepSize' for symbol.")

                        order_type = ORDER_TYPE_LIMIT if o.order_type == "Limit Order" else ORDER_TYPE_MARKET

                        # Calculate risk amount and quantity
                        risk_amount = (int(o.risk_value) * percentage) / 100
                        quantity = round(risk_amount / current_price, 6)
                        precision_value = len(str(quantity_precision).split('.')[1].rstrip('0')) - 1
                        # print(precision_value)
                        rounded_price = round(entry_price, len(str(price_precision).split('.')[1].rstrip('0')))
                        rounded_quantity = round(quantity, precision_value)

                        # print(quantity, rounded_quantity)
                        # Determine trade direction based on entry_type
                        if entry_type == "Long":
                            entry_type_ = SIDE_BUY
                        elif entry_type == "Short":
                            entry_type_ = SIDE_SELL
                        elif entry_type == "Long Close" or entry_type == "Short Close":
                            entry_type_ = SIDE_SELL if entry_type == "Long Close" else SIDE_BUY  # Inverse to close position

                        # Binance Futures API requests require signature for authentication
                        try:

                            if o.option_strategies == 'Future':
                                if entry_type == "Long" or entry_type == "Short":
                                    # Open the order (Buy/Sell depending on Long/Short, or closing position)
                                    try:
                                        order = binance_client.futures_create_order(
                                            symbol=symbol,
                                            side=entry_type_,        # BUY or SELL based on entry_type
                                            type=order_type,         # Market/Limit order
                                            quantity=rounded_quantity,       # Calculated amount to trade
                                            price=rounded_price if order_type == ORDER_TYPE_LIMIT else None,  # Only set price for Limit orders
                                            timeInForce=TIME_IN_FORCE_GTC if order_type == ORDER_TYPE_LIMIT else None  # GTC for Limit orders
                                        )


                                        print("Order Opened:", order)
                                        # Save open order in the database
                                        open_order = OpenOrders(
                                            ord_id = order['orderId'],
                                            user=o.user, market=o.market, broker=o.broker, symbol=o.symbol, strategy=o.strategy,
                                            order_id=o.id, local_currency="USD", time_frame=o.time_frame, long_or_short=o.long_or_short,
                                            price=risk_amount, stop_loss=o.stop_loss, risk_value=o.risk_value, status=o.status, automation="yes",
                                            order_type = o.order_type,  option_strategies = o.option_strategies
                                        )
                                        open_order.save()
                                        print(open_order)
                                    except Exception as e:
                                        print(e)

                                print(o)
                                # If "Long Close" or "Short Close", cancel any associated open order
                                if entry_type == "Long Close" or entry_type == "Short Close":
                                    print(o)
                                    try:
                                        open_orders = OpenOrders.objects.filter(broker = o.broker, symbol = o.symbol, strategy = o.strategy, time_frame = o.time_frame, status = 'Active', long_or_short = long_or_short).all()
                                        
                                        # Update open order in the database
                                        for ods in open_orders:
                                            print(f"Cancelled {entry_type} Order: {ods.ord_id}")
                                            if ods.ord_id is not None:
                                                cancel_response = binance_client.futures_cancel_order(symbol=symbol, orderId=ods.ord_id)
                                                ods.status = "Closed"
                                                ods.save()
                                                # cancel_response = binance_client.futures_cancel_all_open_orders(symbol=symbol)
                                                print("Order Cancelled:", cancel_response)
                                    except Exception as e:
                                        print(e)
                                
                            if o.option_strategies == 'Spot':
                                if entry_type == "Long" or entry_type == "Short":
                                    try:
                                        # Open the order (Buy/Sell depending on Long/Short, or closing position)
                                        order = binance_client.create_order(
                                            symbol=symbol,
                                            side=entry_type_,        # BUY or SELL based on entry_type
                                            type=order_type,         # Market/Limit order
                                            quantity=rounded_quantity,       # Calculated amount to trade
                                            price=rounded_price if order_type == ORDER_TYPE_LIMIT else None,  # Only set price for Limit orders
                                            timeInForce=TIME_IN_FORCE_GTC if order_type == ORDER_TYPE_LIMIT else None  # GTC for Limit orders
                                        )
                                    
                                        print("Order Opened:", order)
                                        # Save open order in the database
                                        open_order = OpenOrders(
                                            ord_id = order['orderId'],
                                            user=o.user, market=o.market, broker=o.broker, symbol=o.symbol, strategy=o.strategy,
                                            order_id=o.id, local_currency="USD", time_frame=o.time_frame, long_or_short=o.long_or_short,
                                            price=risk_amount, stop_loss=o.stop_loss, risk_value=o.risk_value, status=o.status, automation="yes",
                                            order_type = o.order_type,  option_strategies = o.option_strategies
                                        )
                                        open_order.save()
                                        print(open_order)
                                    except Exception as e:
                                        print(e)


                                print(o)
                                # If "Long Close" or "Short Close", cancel any associated open order
                                if entry_type == "Long Close" or entry_type == "Short Close":
                                    print(o)
                                    try:
                                        open_orders = OpenOrders.objects.filter(broker = o.broker, symbol = o.symbol, strategy = o.strategy, time_frame = o.time_frame, status = 'Active', long_or_short = long_or_short).all()
                                        
                                        # Update open order in the database
                                        for ods in open_orders:
                                            print(f"Cancelled {entry_type} Order: {ods.ord_id}")
                                            if ods.ord_id is not None:
                                                cancel_response = binance_client.cancel_order(symbol=symbol, orderId=ods.ord_id)
                                                ods.status = "Closed"
                                                ods.save()
                                                # cancel_response = binance_client.futures_cancel_all_open_orders(symbol=symbol)
                                                print("Order Cancelled:", cancel_response)
                                    except Exception as e:
                                        print(e)
                                # cancel_response = binance_client.futures_cancel_all_open_orders(symbol=symbol)

                        except Exception as e:
                            print(f"Exception occurred while placing order: {e}")
                            return JsonResponse({"error" : f"{e}"}, status=status.HTTP_400_BAD_REQUEST)

                # Send trade created signal
                trade_created_signal.send(sender=StrategyData, trade_id=trade.id, trade_data=serializer.data)
                return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('id', openapi.IN_QUERY, description="ID of the trade to retrieve", type=openapi.TYPE_INTEGER)
        ],
        responses={200: TradeSerializer(many=True)},
        operation_description="Retrieve trade entries",
        operation_summary="Get Trades"
    )
    def get(self, request, *args, **kwargs):
        # Fetch query parameters
        trade_id = request.query_params.get('id', None)
        strategy = request.query_params.get('strategy', None)
        market = request.query_params.get('market', None)
        timeFrame = request.query_params.get('timeFrame', None)

        # Priority: Check for trade_id first
        if trade_id:
            try:
                trade = StrategyData.objects.filter(id=trade_id).first()
                if not trade:
                    return JsonResponse({'error': 'Trade not found'}, status=status.HTTP_404_NOT_FOUND)

                serializer = StrategyDataSerializer(trade)
                
                # Calculate unique symbols and brokers
                unique_symbols_count = StrategyData.objects.filter(id=trade_id).values('symbol').distinct().count()
                unique_brokers_count = StrategyData.objects.filter(id=trade_id).values('broker').distinct().count()

                # Calculate total value and local currency
                total_value = StrategyData.objects.filter(id=trade_id).aggregate(total=Sum('pl'))['total'] or 0  # Assuming 'pl' is the profit/loss field
                local_currency = 'USD'  # Or whichever currency is needed

                # Calculate long and short counts
                total_long_count = StrategyData.objects.filter(id=trade_id, entry_type='Long').count()
                total_short_count = StrategyData.objects.filter(id=trade_id, entry_type='Short').count()

                # Prepare response data
                response_data = {
                    'unique_symbols_count': unique_symbols_count,
                    'unique_brokers_count': unique_brokers_count,
                    'total_value': total_value,
                    'local_currency': local_currency,
                    'total_long_count': total_long_count,
                    'total_short_count': total_short_count,
                    'data': serializer.data
                }
                return JsonResponse(response_data, status=status.HTTP_200_OK)

            except Exception as e:
                print(e)
                return JsonResponse({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Filter by strategy, market, and timeFrame if trade_id is not provided
        filter_conditions = {}

        try:
            # If any filter conditions are present, apply them
            strategy_data = StrategyData.objects.all().order_by('-created_at')
            print(strategy, market, timeFrame)
            if strategy:
                strategy_data = strategy_data.filter(strategy = strategy)

            if market:
                strategy_data = strategy_data.filter(market = market)

            if timeFrame:
                strategy_data = strategy_data.filter(time_frame = timeFrame)

            print(strategy_data)
            serializer = StrategyDataSerializer(strategy_data, many=True)
            return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return JsonResponse({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ApiIntegrationCreateView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def get(self, request, *args, **kwargs):
        UserActivePlan.objects.update_expired_plans_for_user(request.user)
        apis = ApiIntegration.objects.filter(~Q(status='Deleted'), user = request.user).order_by('-created_at')
        serializer = ApiIntegrationSerializer(apis, many=True)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

    def post(self, request):
        # Populate user from the request
        user = request.user
        try:
            UserActivePlan.objects.update_expired_plans_for_user(user)
        except Exception as e:
            print(e)
        active_plan = UserActivePlan.objects.filter(user = user, status = 'Active').first()
        if not active_plan and not user.is_superuser:
            return JsonResponse({'message' : 'Please Activate Your Plan First.'}, status=status.HTTP_200_OK)

        total_api = ApiIntegration.objects.filter(user = user).all()
        if not user.is_superuser:
            if len(total_api) >= int(active_plan.plan.api_keys):
                return JsonResponse({'message' : 'Your Limit Excedded.'}, status=status.HTTP_200_OK)

        # Directly use the request data, flattening the structure
        data = {
            'api_name': request.data['formData']['api_name'],
            'broker': request.data['formData']['broker'],
            'api_key': request.data['formData']['api_key'],
            'secret_key': request.data['formData']['secret_key'],
            'api_type': request.data['formData']['api_type'],
            'status': 'Active',
            'user': user.id,  # Assuming user is already authenticated
        }

        # Initialize the serializer with flattened data
        serializer = ApiIntegrationSerializer(data=data)
        
        if serializer.is_valid():
            # Save the API Integration with the user
            serializer.save(user=user)  # Save directly with the serializer's save method
            return JsonResponse({'message': 'API Integration created successfully'}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        # Check if a specific Api ID is provided
        api_id = request.query_params.get('id', None)
        
        if api_id:
            try:
                api = ApiIntegration.objects.exclude(status='Deleted').filter(id=api_id, user = request.user).first()
                api.status = 'Deleted'
                api.save()
                return JsonResponse({'message': 'Successfully Deleted'}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return JsonResponse({'error': 'Api not found'}, status=status.HTTP_404_NOT_FOUND)
        return JsonResponse({'error': 'Api not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self, request, *args, **kwargs):
        # Check if a specific Api ID is provided
        api_id = request.query_params.get('id', None)
        
        if api_id:
            try:
                api = ApiIntegration.objects.exclude(status='Deleted').filter(id=api_id, user = request.user).first()
                api.status = 'Closed'
                api.save()
                return JsonResponse({'message': 'Successfully Updated'}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return JsonResponse({'error': 'Api not found'}, status=status.HTTP_404_NOT_FOUND)
        return JsonResponse({'error': 'Api not found'}, status=status.HTTP_404_NOT_FOUND)


class ApiOrderCreateView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def post(self, request):
        # Populate user from the request
        user = request.user

        # Directly use the request data, flattening the structure
        order = Orders.objects.filter(id = request.data['formData']['api']).first()

        data = {
            'broker': request.data['formData']['broker'],
            'strategy': request.data['formData']['selectedApiType'],
            'market': request.data['formData']['market'],
            'symbol': request.data['formData']['symbol'],
            'time_frame': request.data['formData']['timeFrame'],
            'long_or_short': request.data['formData']['direction'],
            'stop_loss': request.data['formData']['stopLoss'],
            'risk_value': request.data['formData']['riskCapitalValue'],
            'option_strategies': request.data['formData']['optionStrategies'],
            'order_type': request.data['formData']['orderType'],
            'status': request.data['formData']['status'],
            'user': user.id,
            'api' : request.data['formData']['api'],
        }

        print(data)
        try:
            # Initialize the serializer with flattened data
            serializer = OrderSerializer(data=data)
            
            if serializer.is_valid():
                # Save the API Integration with the user
                serializer.save(user=user)  # Save directly with the serializer's save method
                return JsonResponse({'message': 'Order created successfully'}, status=status.HTTP_200_OK)
            else:
                return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return JsonResponse({"error" : e}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        # Check if a specific trade ID is provided
        order_id = request.query_params.get('id', None)
        
        if order_id:
            try:
                order = Orders.objects.exclude(status='Deleted').filter(id=order_id, user = request.user).first()
                serializer = OrderDataSerializer(order)

                response_data = {
                    'data' : serializer.data
                }
                return JsonResponse(response_data, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return JsonResponse({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # If no ID, return all orders
            orders = Orders.objects.filter(~Q(status='Deleted'), user = request.user).order_by('-created_at')
            serializer = OrderDataSerializer(orders, many=True)
            return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        # Check if a specific orders ID is provided
        order_id = request.query_params.get('id', None)
        
        if order_id:
            try:
                order = Orders.objects.exclude(status='Deleted').filter(id=order_id, user = request.user).first()
                order.status = 'Deleted'
                order.save()
                return JsonResponse({'message': 'Successfully Deleted'}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return JsonResponse({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        return JsonResponse({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self, request, *args, **kwargs):
        # Check if a specific trade ID is provided
        order_id = request.query_params.get('id', None)
        
        if order_id:
            try:
                order = Orders.objects.exclude(status='Deleted').filter(id=order_id, user = request.user).first()
                order.status = 'Closed'
                order.save()
                return JsonResponse({'message': 'Successfully Updated'}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return JsonResponse({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        return JsonResponse({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


class ApiOpenOrderCreateView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def post(self, request):
        # Populate user from the request
        user = request.user
        try:
            print(request.data)
            # Directly use the request data, flattening the structure
            data = {
                'broker': request.data['broker'],
                'strategy': request.data['strategy'],
                'market': request.data['market'],
                'symbol': request.data['symbol'],
                'order_id': request.data['order_id'],
                'local_currency': request.data['local_currency'],
                'time_frame': request.data['time_frame'],
                'long_or_short': request.data['long_or_short'],
                'stop_loss': request.data['stop_loss'],
                'price': request.data['price'],
                'risk_value': request.data['risk_value'],
                'automation': request.data['automation'],
                'status': request.data['status'],

                # 'user': user.id,  # Assuming user is already authenticated
            }

            # Initialize the serializer with flattened data
            serializer = OpenOrderSerializer(data=data)
            
            if serializer.is_valid():
                # Save the API Integration with the user
                serializer.save()  # Save directly with the serializer's save method
                return JsonResponse({'message': 'Order created successfully'}, status=status.HTTP_200_OK)
            else:
                return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return JsonResponse({'error': f"{e}"}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        # Check if a specific trade ID is provided
        order_id = request.query_params.get('id', None)
        status_in = request.query_params.get('status', None)
        print(status_in)
        if order_id:
            try:
                order = OpenOrders.objects.filter(id=order_id, user = request.user).first()
                serializer = OpenOrderSerializer(order)

                response_data = {
                    serializer.data
                }
                return JsonResponse(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return JsonResponse({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        elif status_in:
            try:
                if status_in == 'Active':
                    order = OpenOrders.objects.filter(status=status_in, user = request.user).all()
                if status_in == 'Hold':
                    order = OpenOrders.objects.exclude(status='Active').filter(user = request.user).all()
                serializer = OpenOrderSerializer(order, many = True)
                print(serializer)

                response_data = {
                    'data' : serializer.data
                }
                return JsonResponse(response_data, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return JsonResponse({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
        
        else:
            # If no ID, return all orders
            orders = OpenOrders.objects.filter(user = request.user).order_by('-created_at')
            serializer = OpenOrderSerializer(orders, many=True)
            return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        # Check if a specific orders ID is provided
        order_id = request.query_params.get('id', None)
        
        if order_id:
            try:
                order = OpenOrders.objects.filter(id=order_id, user = request.user).first()
                order.status = 'Deleted'
                order.save()
                return JsonResponse({'message': 'Successfully Deleted'}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return JsonResponse({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        return JsonResponse({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self, request, *args, **kwargs):
        # Check if a specific trade ID is provided
        order_id = request.query_params.get('id', None)
        
        if order_id:
            try:
                order = OpenOrders.objects.exclude(status='Deleted').filter(id=order_id, user = request.user).first()
                order.status = 'Closed'
                order.save()
                return JsonResponse({'message': 'Successfully Updated'}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return JsonResponse({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        return JsonResponse({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)



