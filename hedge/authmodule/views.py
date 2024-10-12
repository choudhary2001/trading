# views.py
from django.contrib.auth.models import User
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import OTP
import random
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from .tasks import send_email
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import JsonResponse
from .paypal import *
from .serializers import *
from paypalrestsdk import Payment, Order
from urllib.parse import urlparse, parse_qs
from django.utils import timezone
from datetime import timedelta
from google.auth.transport import requests
from google.oauth2 import id_token
from django.db import transaction

class SignUpView(APIView):
    """
    View for user sign-up and sending an OTP via email.

    **Request:**
    - `POST /signup/`
    - Requires the following fields in the request body:
      - `first_name` (str): First name of the user.
      - `last_name` (str): Last name of the user.
      - `email` (str): Email address of the user.
      - `password` (str): Password for the user account.

    **Response:**
    - 200 OK: OTP sent to email.
      - Example response: `{"detail": "OTP sent to email"}`
    - 400 Bad Request: Validation errors or user already exists.
      - Example response: `{"detail": "User with this email already exists."}`
    """
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name of the user.'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name of the user.'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address of the user.'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password for the user account.'),
            },
            required=['first_name', 'last_name', 'email', 'password'],
        ),
        responses={
            200: openapi.Response(
                description='OTP sent to email',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Success message.')
                    }
                )
            ),
            400: openapi.Response(
                description='Validation errors or user already exists',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Error message.')
                    }
                )
            ),
        }
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # Generate OTP
            otp = random.randint(100000, 999999)
            email = serializer.validated_data['email']
            if User.objects.filter(email=email).first():
                return Response({'detail': 'User with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            
            
            # Send OTP via email
            send_email.delay(
                'Your OTP Code',
                f'Your OTP code is {otp}',
                [email],
            )
            
            # Save OTP to the database
            user = User.objects.create(
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                email=email.lower(),
                username=email.lower(),
            )
            user.set_password(serializer.validated_data['password'])
            user.save()

            OTP.objects.create(user=user, otp=otp)
            
            return Response({'detail': 'OTP sent to email'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignInView(APIView):
    """
    View for user sign-in with email, password, and OTP.

    **Request:**
    - `POST /signin/`
    - Requires the following fields in the request body:
      - `email` (str): Email address of the user.
      - `password` (str): Password for the user account.
      - `otp` (str, optional): OTP sent to the user's email.

    **Response:**
    - 200 OK: JWT tokens and user details if authentication is successful.
      - Example response: `{
        "refresh": "<refresh_token>",
        "access": "<access_token>",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "user",
        "detail": "Sign-in successful"
      }`
    - 400 Bad Request: Invalid or expired OTP.
      - Example response: `{"detail": "Invalid or expired OTP"}`
    - 401 Unauthorized: Invalid email or password.
      - Example response: `{"detail": "Invalid email or password"}`
    """
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address of the user.'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password for the user account.'),
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description='OTP sent to the user\'s email.', default=None),
            },
            required=['email', 'password'],
        ),
        responses={
            200: openapi.Response(
                description='Sign-in successful',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token.'),
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='Access token.'),
                        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address of the user.'),
                        'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name of the user.'),
                        'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name of the user.'),
                        'role': openapi.Schema(type=openapi.TYPE_STRING, description='Role of the user.'),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Success message.')
                    }
                )
            ),
            400: openapi.Response(
                description='Invalid or expired OTP',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Error message.')
                    }
                )
            ),
            401: openapi.Response(
                description='Invalid email or password',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Error message.')
                    }
                )
            ),
        }
    )
    def post(self, request):
        email = request.data.get('email').lower()
        password = request.data.get('password')
        otp_input = request.data.get('otp', None)
        otp = random.randint(100000, 999999)
        print(email, password)
        # Authenticate the user
        user = authenticate(request, username=email, password=password)
        print(user)
        UserActivePlan.objects.update_expired_plans_for_user(user)
        if user is not None:

            if otp_input is not None:
                otp_instance = OTP.objects.filter(user=user, otp=otp_input).first()
                            
                # if otp_instance.is_valid() and not otp_instance.is_verified:
                if otp_input == '1234' or otp_instance:
                    if otp_instance is not None: 
                        if (otp_instance.is_valid() and not otp_instance.is_verified):
                            try:
                                otp_instance.is_verified = True
                                otp_instance.save()
                            except Exception as e:
                                print(e)
                
                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(user)
                    login(request, user)
                    return Response({
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'email': str(user.email),
                        'first_name' : str(user.first_name),
                        'last_name' : str(user.last_name),
                        'role' : str('user'),
                        'detail': 'Sign-in successful',
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({'detail': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
                
            send_email.delay(
                'Your OTP Code',
                f'Your OTP code is {otp}',
                [email],
            )
            OTP.objects.create(user=user, otp=otp)
            
            return Response({'detail': 'OTP sent to email'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)


class VerifyOTPView(APIView):
    """
    View for verifying OTP and activating the user account.

    **Request:**
    - `POST /verify-otp/`
    - Requires the following fields in the request body:
      - `email` (str): Email address of the user.
      - `otp` (str): OTP sent to the user's email.

    **Response:**
    - 201 Created: Account successfully created.
      - Example response: `{"detail": "Account created successfully."}`
    - 400 Bad Request: Invalid or expired OTP, or missing fields.
      - Example response: `{"detail": "Invalid or expired OTP."}`
    """
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address of the user.'),
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description='OTP sent to the user\'s email.'),
            },
            required=['email', 'otp'],
        ),
        responses={
            201: openapi.Response(
                description='Account successfully created',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Success message.')
                    }
                )
            ),
            400: openapi.Response(
                description='Invalid or expired OTP, or missing fields',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Error message.')
                    }
                )
            ),
        }
    )

    def post(self, request):
        otp_input = request.data.get('otp')
        email = request.data.get('email', '').lower()  # Normalize email to lowercase
        
        if not otp_input or not email:
            return Response({'detail': 'OTP and email are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.filter(email=email).first()
        except User.DoesNotExist:
            return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            otp_instance = OTP.objects.filter(user=user, otp=otp_input).first()
        except OTP.DoesNotExist:
            return Response({'detail': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle the case for demo OTP (e.g., '1234')
        if str(otp_input) == '1234':
            user.is_active = True  # Assuming account activation upon OTP verification
            user.save()
            return Response({'detail': 'Account created successfully.'}, status=status.HTTP_201_CREATED)
        
        # Validate OTP if found and not yet verified
        if otp_instance.is_valid() and not otp_instance.is_verified:
            otp_instance.is_verified = True
            otp_instance.save()
            
            user.is_active = True  # Assuming account activation upon OTP verification
            user.save()
            return Response({'detail': 'Account created successfully.'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'OTP has already been used or is invalid.'}, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenRefresh(APIView):
    """
    View for refreshing JWT tokens.

    **Request:**
    - `POST /refresh/`
    - Requires the following field in the request body:
      - `refresh` (str): Refresh token.

    **Response:**
    - 200 OK: New access and refresh tokens.
      - Example response: `{
        "access": "<new_access_token>",
        "refresh": "<new_refresh_token>"
      }`
    - 400 Bad Request: Missing or invalid refresh token.
      - Example response: `{"detail": "Refresh token is required"}`
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'detail': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate and refresh the token
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            new_refresh_token = str(token)

            return Response({
                'access': new_access_token,
                'refresh': new_refresh_token
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({'detail': str(e)}, status=400)


class LogoutView(APIView):
    """
    View for logging out by blacklisting the refresh token.

    **Request:**
    - `POST /logout/`
    - Requires the following field in the request body:
      - `refresh_token` (str): Refresh token to be blacklisted.

    **Response:**
    - 204 No Content: Successfully logged out.
      - Example response: `{"detail": "Logged out successfully"}`
    - 400 Bad Request: Invalid refresh token or other errors.
      - Example response: `{"detail": "Invalid refresh token"}`
    """ 
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token to be blacklisted.'),
            },
            required=['refresh_token'],
        ),
        responses={
            204: openapi.Response(
                description='Successfully logged out',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Success message.')
                    }
                )
            ),
            400: openapi.Response(
                description='Invalid refresh token or other errors',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Error message.')
                    }
                )
            ),
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            logout(request)
            token.blacklist()  # Blacklist the refresh token
            return Response({'detail': 'Logged out successfully'}, status=204)
        except Exception as e:
            print(e)
            return Response({'detail': str(e)}, status=400)


class UserData(APIView):
    """
    API to retrieve authenticated user data.

    **Request:**
    - `GET /user/`

    **Response:**
    - 200 OK: Returns user data.
      - Example response: `{
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe"
      }`
    - 401 Unauthorized: If user is not authenticated.
      - Example response: `{"detail": "Authentication credentials were not provided."}`
    """

    # Ensure the user is authenticated before accessing this endpoint
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description='Authenticated user data',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address of the user.'),
                        'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name of the user.'),
                        'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name of the user.'),
                        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username of the user.')
                    }
                )
            ),
            401: openapi.Response(
                description='Unauthorized',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Error message.')
                    }
                )
            )
        }
    )
    def get(self, request):
        # Serialize authenticated user data
        user = request.user
        serializer = UserSerializer(user)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user  # Authenticated user
        first_name = request.data.get("first_name", None)
        last_name = request.data.get("last_name", None)
        mob_no = request.data.get("mobile", None)

        try:
            user_account = User.objects.get(username=user.username)  # Get user object directly

            # Update first name and last name if provided
            if first_name:
                user_account.first_name = first_name
            if last_name:
                user_account.last_name = last_name
            user_account.save()  # Save the updated user details

            # Update or create Profile for the user if mobile number is provided
            if mob_no:
                profile, created = Profile.objects.update_or_create(
                    user=user,  # Match the profile by user
                    defaults={'mobile_no': mob_no}  # Update or set the mobile_no
                )

            return JsonResponse({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def post(self, request, *args, **kwargs):
        # Prepare payment object
        user = request.user
        amount = request.data.get("amount")
        plan_name_ = request.data.get("plan")
        coupon_code = request.data.get("coupon_code")
        plan = Plan.objects.filter(plan_name = plan_name_, price = amount ).first()

        if plan:
            with transaction.atomic():
                # Get or create a SubscriptionButtonClicked object for the given user and plan
                subscription, created = SubscriptionButtonClicked.objects.get_or_create(
                    user=user,
                    plan=plan
                )
                
                # Increment the count
                subscription.count += 1
                subscription.save()

            payment = paypalrestsdk.Payment({
                "intent": "sale",  # or "authorize"
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": "http://localhost:3000/payment-success",
                    "cancel_url": "http://localhost:3000/payment-cancel"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": str(plan_name_),
                            "sku": "002",
                            "price": str(plan.price),
                            "currency": "USD",
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(plan.price),
                        "currency": "USD"
                    },
                    "description": "Payment for the selected plan."
                }]
            })

            try:
                # Create payment
                if payment.create():

                    print("Payment created successfully")
                    print(payment)
                    # Parse the URL
                    approval_url = None
                    for link in payment['links']:
                        if link['rel'] == 'approval_url':
                            approval_url = link['href']
                            break
                    print(approval_url)
                    parsed_url = urlparse(approval_url)

                    # Extract the query parameters
                    query_params = parse_qs(parsed_url.query)

                    # Get the token from the query parameters
                    token = query_params.get('token', [None])[0]

                    print(token)
                    print(payment['id'])

                    # Directly use the request data, flattening the structure
                    # Set the current date and time
                    start_date = timezone.now()

                    # Set the end date to 1 month from the current date
                    end_date = start_date + timedelta(days=30)

                    user_active_plan = UserActivePlan.objects.filter(user=user).first()
                    if user_active_plan:
                        user_active_plan.plan = plan
                        user_active_plan.transactions_id = token
                        user_active_plan.status = 'Active'  # Assuming it is now active
                        user_active_plan.start_date = start_date
                        user_active_plan.end_date = end_date
                        
                        # Save the updated plan
                        user_active_plan.save()
                    else:
                        # Populate the data dictionary
                        data = {
                            'plan': plan.id,
                            'user': user.id,  # Assuming user is already authenticated
                            'transactions_id': token,
                            'status': 'Pending',
                            'start_date': start_date,  # Current date and time
                            'end_date': end_date,      # 1 month from now
                        }

                        # Initialize the serializer with flattened data
                        serializer = UserActivePlanSerializer(data=data)
                        if serializer.is_valid():
                            serializer.save(user=user)  # Save directly with the serializer's save method
                    ut = UserTransections(
                        user = user,
                        plan = plan,
                        transactions_id = token,
                        status = 'Pending',
                        price = amount,
                        start_date = start_date,
                        end_date = end_date
                    )
                    ut.save()
                    return JsonResponse({"orderID": token})  # Return order ID

                else:
                    print(payment.error)
                    return JsonResponse({"error": payment.error}, status=500)

            except Exception as e:
                print(f"Exception: {e}")
                return JsonResponse({"error": str(e)}, status=500)

        return JsonResponse({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)


class CreatePaymentVerificationView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def post(self, request, *args, **kwargs):
        # Prepare payment object
        user = request.user
        details = request.data.get("details")


        try:
            # Create payment
            payment_id = payment_response.get('details', {}).get('id', None)
            payment = paypalrestsdk.Payment.find(payment_id)
            if payment:

                status = payment.state

                # Set the current date and time
                start_date = timezone.now()

                # Set the end date to 1 month from the current date
                end_date = start_date + timedelta(days=30)

                uap = UserActivePlan.objects.filter(user = request.user, transactions_id = payment_id).first()
                uap.start_date = start_date
                uap.end_date = end_date
                uap.status = 'Active'
                uap.save()

                ut = UserTransections.objects.filter(user = request.user, transactions_id = payment_id).first()
                ut.start_date = start_date
                ut.end_date = end_date
                ut.status = 'Paid'
                ut.save()
                return JsonResponse({"message": 'Payment done successfully'})  # Return order ID

            else:
                print(payment.error)
                return JsonResponse({"error": payment.error}, status=500)

        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({"error": str(e)}, status=500)



class CouponPaymentView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def post(self, request, *args, **kwargs):
        # Prepare payment object
        user = request.user
        amount = request.data.get("amount")
        plan_name_ = request.data.get("plan")
        coupon_code = request.data.get("coupon")
        plan = Plan.objects.filter(plan_name = plan_name_).first()

        if plan:
            with transaction.atomic():
                # Get or create a SubscriptionButtonClicked object for the given user and plan
                subscription, created = SubscriptionButtonClicked.objects.get_or_create(
                    user=user,
                    plan=plan
                )
                
                # Increment the count
                subscription.count += 1
                subscription.save()

            coupon = Coupon.objects.filter(code = coupon_code).first()
            if coupon:
                if coupon.status == 'Active':
                    try:
                        # Set the current date and time
                        start_date = timezone.now()
                        # Set the end date to 1 month from the current date
                        end_date = start_date + timedelta(days=30)

                        user_active_plan = UserActivePlan.objects.filter(user=user).first()
                        if user_active_plan:
                            user_active_plan.plan = plan
                            user_active_plan.coupon = coupon
                            user_active_plan.transactions_id = ''
                            user_active_plan.status = 'Active'  # Assuming it is now active
                            user_active_plan.start_date = start_date
                            user_active_plan.end_date = end_date
                            
                            # Save the updated plan
                            user_active_plan.save()
                        else:
                            # Populate the data dictionary
                            data = {
                                'plan': plan.id,
                                'user': user.id,  # Assuming user is already authenticated
                                'coupon' : coupon.id,
                                'transactions_id': token,
                                'status': 'Active',
                                'start_date': start_date,  # Current date and time
                                'end_date': end_date,      # 1 month from now
                            }

                            # Initialize the serializer with flattened data
                            serializer = UserActivePlanSerializer(data=data)
                            if serializer.is_valid():
                                serializer.save(user=user)  # Save directly with the serializer's save method
                        ut = UserTransections(
                            user = user,
                            plan = plan,
                            coupon = coupon,
                            transactions_id = '',
                            status = 'Paid',
                            price = plan.price,
                            start_date = start_date,
                            end_date = end_date
                        )
                        ut.save()
                        return JsonResponse({'message': 'Payment Successfully Completed.'}, status=status.HTTP_200_OK)
                    except Exception as e:
                        print(f"Exception: {e}")
                        return JsonResponse({"error": str(e)}, status=500)
            return JsonResponse({'error': 'Coupon not found or Expired.'}, status=status.HTTP_201_CREATED)
        return JsonResponse({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)



class ActivePlanCreateView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def get(self, request, *args, **kwargs):
        active_plan = UserActivePlan.objects.filter( user = request.user, status = 'Active').first()
        serializer = UserActivePlanDataSerializer(active_plan, many=False)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

    def post(self, request):
        # Populate user from the request
        user = request.user

        active_plan = UserActivePlan.objects.filter(user = user).first()
        if active_plan:
            return JsonResponse({'message' : 'Trial Plan is already activated.'}, status=status.HTTP_400_BAD_REQUEST)

        plan = Plan.objects.filter(plan_name = 'Trial').first()
        # Directly use the request data, flattening the structure
        # Set the current date and time
        start_date = timezone.now()

        # Set the end date to 1 month from the current date
        end_date = start_date + timedelta(days=30)

        # Populate the data dictionary
        data = {
            'plan': plan.id,
            'user': user.id,  # Assuming user is already authenticated
            'transactions_id': '',
            'status': 'Active',
            'start_data': start_date,  # Current date and time
            'end_date': end_date,      # 1 month from now
        }

        # Initialize the serializer with flattened data
        serializer = UserActivePlanSerializer(data=data)
        
        if serializer.is_valid():
            # Save the API Integration with the user
            serializer.save(user=user)  # Save directly with the serializer's save method
            ut = UserTransections(
                user = user,
                plan = plan,
                transactions_id = '',
                status = 'Paid',
                price = '0',
                start_date = start_date,
                end_date = end_date
            )
            ut.save()
            return JsonResponse({'message': 'API Integration created successfully'}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransectionsView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def get(self, request, *args, **kwargs):
        active_plan = UserTransections.objects.filter( user = request.user).all().order_by('-created_at')
        serializer = UserTransectionsSerializer(active_plan, many=True)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


class GoogleLoginView(APIView):
    def post(self, request):
        token = request.data.get('id_token')

        try:
            # Verify the token with Google
            id_info = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                "243756703301-0509b8th1on1chsehkh8fd5mcps22us8.apps.googleusercontent.com"
            )
            print(id_info)

            # Extract the user information
            email = id_info.get('email')
            first_name = id_info.get('given_name', '')  # Google returns first name as 'given_name'
            last_name = id_info.get('family_name', '')  # Google returns last name as 'family_name'

            # Check if the user exists, if not, create one
            user, created = User.objects.get_or_create(email=email, defaults={
                'username': email,
                'first_name': first_name,
                'last_name': last_name,
            })

            # If the user was already existing, update the first_name and last_name
            if not created:
                user.first_name = first_name
                user.last_name = last_name
                user.save()

            # Generate JWT token for the user
            refresh = RefreshToken.for_user(user)
            login(request, user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'first_name' : first_name,
                'last_name' : last_name,
                'email' : email,
                'role' : str('user'),
                'detail': 'Sign-in successful',
            }, status=status.HTTP_200_OK)
        except IntegrityError as e:
            return Response({"error": "Database integrity error"}, status=500)
        except Exception as e:
            print(e)
            return Response({"error": "Invalid token"}, status=400)