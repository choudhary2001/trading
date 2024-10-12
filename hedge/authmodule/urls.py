# urls.py
from django.urls import path
from .views import *
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('api/signup/', SignUpView.as_view(), name='signup'),
    path('api/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('api/signin/', SignInView.as_view(), name='sign-in'),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name ='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/sign-out/', LogoutView.as_view(), name='logout'),
    path('api/me/', UserData.as_view(), name='user_data'),
    path('api/active/plan/', ActivePlanCreateView.as_view(), name='user_active_plan'),
    path('api/transections/', TransectionsView.as_view(), name='user_transections'),

    path('auth/login/', GoogleLoginView.as_view(), name='google-login'),

    path('api/payment/create/', CouponPaymentView.as_view(), name='coupen_payment'),
    path('api/paypal/create/', CreatePaymentView.as_view(), name='create_payment'),
    path('api/paypal/verify/', CreatePaymentVerificationView.as_view(), name='payment_verification'),

]
