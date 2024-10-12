# admin.py
from django.contrib import admin
from .models import *

class TradeAlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'date_time', 'symbol', 'price', 'time_frame', 'strategy', 'entry', 'exit')
    list_filter = ('symbol', 'strategy', 'entry', 'exit')
    search_fields = ('symbol', 'strategy')
    ordering = ('-date_time',)

admin.site.register(TradeAlert, TradeAlertAdmin)

@admin.register(ApiIntegration)
class ApiIntegrationAdmin(admin.ModelAdmin):
    list_display = ['api_name', 'user', 'api_type', 'broker', 'created_at']
    search_fields = ['api_name', 'user__username']

class StrategyDataAdmin(admin.ModelAdmin):
    list_display = ('strategy', 'market', 'broker', 'symbol', 'entry_price', 'exit_price', 'pl', 'time_frame', 'created_at')
    list_filter = ('strategy', 'market', 'broker', 'symbol', 'time_frame')
    search_fields = ('strategy', 'symbol', 'broker')
    ordering = ('-created_at',)

admin.site.register(StrategyData, StrategyDataAdmin)

class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'market', 'broker', 'symbol', 'strategy', 'long_or_short', 'status', 'created_at')
    list_filter = ('market', 'broker', 'symbol', 'strategy', 'status')
    search_fields = ('symbol', 'strategy', 'user__username')
    ordering = ('-created_at',)

admin.site.register(Orders, OrdersAdmin)



@admin.register(OpenOrders)
class OpenOrdersAdmin(admin.ModelAdmin):
    list_display = ('market', 'broker', 'symbol', 'order_id', 'status', 'created_at')
    search_fields = ( 'market', 'broker', 'symbol', 'order_id')
    list_filter = ('market', 'broker', 'status', 'created_at')
    ordering = ('-created_at',)

    def changelist_view(self, request, extra_context=None):
        try:
            return super().changelist_view(request, extra_context)
        except Exception as e:
            # logger.error(f"Error in changelist view: {e}", exc_info=True)
            print(e)
            # raise