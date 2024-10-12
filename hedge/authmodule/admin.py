# admin.py
from django.contrib import admin
from .models import *

class ModelLogAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'action', 'user', 'timestamp')  # Fields to display in the list view
    list_filter = ('action', 'model_name', 'user', 'timestamp')  # Filters for the sidebar
    search_fields = ('model_name', 'action', 'user__username')  # Fields to search

# Register the ModelLog model with the ModelLogAdmin class
admin.site.register(ModelLog, ModelLogAdmin)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'billings', 'unlimited_strategy_data', 'unlimited_orders', 'api_keys', 'ai_assistant', 'unlimited_devices', 'supports_long', 'supports_short', 'all_markets', 'all_brokers', 'custom_strategy', 'dedicated_support_manager')
    list_filter = ('plan_name', 'billings', 'unlimited_strategy_data', 'unlimited_orders', 'ai_assistant', 'supports_long', 'supports_short', 'all_markets', 'all_brokers')
    search_fields = ('plan_name',)


# Register the UserActivePlan model
@admin.register(UserActivePlan)
class UserActivePlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'created_at')  # Columns to display in the admin list view
    search_fields = ('user__username', 'plan__name')  # Fields that can be searched in the admin
    list_filter = ('status', 'start_date', 'end_date')  # Filters for the admin list view
    ordering = ('-created_at',)  # Default ordering of the list view


# Register the UserActivePlan model
@admin.register(UserTransections)
class UserTransectionsAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'created_at')  # Columns to display in the admin list view
    search_fields = ('user__username', 'plan__name')  # Fields that can be searched in the admin
    list_filter = ('status', 'start_date', 'end_date')  # Filters for the admin list view
    ordering = ('-created_at',)  # Default ordering of the list view


class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'plan', 'status', 'created_at')  # Columns to display in the admin list view
    search_fields = ('code', 'plan__name')  # Fields that can be searched
    list_filter = ('status', 'plan')  # Filters for the admin list view

admin.site.register(Coupon, CouponAdmin)
