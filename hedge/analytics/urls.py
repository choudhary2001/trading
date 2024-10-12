# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('trade/alert/', TradeCreateAPIView.as_view(), name='trade_alert'),
    path('api/create-api-integration/', ApiIntegrationCreateView.as_view(), name='create-api-integration'),
    path('api/create-order/', ApiOrderCreateView.as_view(), name='create-api-integration'),
    path('api/open-order/', ApiOpenOrderCreateView.as_view(), name='create-api-order'),

]
