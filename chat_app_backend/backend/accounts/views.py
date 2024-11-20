# accounts/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from accounts.tokenauthencation import JWTAuthentication
from .serializers import UserSerializer, LoginSerialzer
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from django.core.mail import send_mail
import jwt
from datetime import datetime, timedelta
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse

User = get_user_model()

@api_view(['POST'])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        # Temporarily store user data
        email = serializer.validated_data['email']

        # Check if the user already exists
        if User.objects.filter(email=email).exists():
            return Response({"message": "Email already in use"}, status=400)

        # Generate a token for email verification
        payload = {
            "email": email,
            "first_name": serializer.validated_data['first_name'],
            "last_name": serializer.validated_data['last_name'],
            "password": serializer.validated_data['password'],
            "exp": datetime.utcnow() + timedelta(hours=24)  # Set token expiration
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # Build verification link
        verification_link = request.build_absolute_uri(
            reverse("verify_email") + f"?token={token}"
        )

        # Send verification email
        send_mail(
            subject="Verify Your Email",
            message=f"Click the link to verify your account: {verification_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"message": "Verification email sent"}, status=201)
    
    return Response(serializer.errors, status=400)


from django.shortcuts import render

@api_view(['GET'])
def verify_email(request):
    token = request.GET.get('token')
    try:
        # Decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email = payload["email"]

        # Check if the user already exists to avoid duplicate creation
        if User.objects.filter(email=email).exists():
            # Render the success page for an already verified user
            return render(request, 'email_verification.html', {"message": "User already verified"})

        # Create and activate the user account
        serializer = UserSerializer(data={
            "email": email,
            "first_name": payload["first_name"],
            "last_name": payload["last_name"],
            "password": payload["password"],
        })
        if serializer.is_valid():
            user = serializer.save()  # Save the user only after email verification
            user.set_password(payload["password"])  # Encrypt the password
            user.save()  # Save the updated user with the hashed password

            # Render the success page for a newly verified user
            return render(request, 'email_verification.html', {"message": "Account verified and created"})
        
        return Response(serializer.errors, status=400)
    except jwt.ExpiredSignatureError:
        # Render the error page with an expiration message
        return render(request, 'email_verification.html', {"message": "Verification link has expired"})
    except jwt.InvalidTokenError:
        # Render the error page with an invalid link message
        return render(request, 'email_verification.html', {"message": "Invalid verification link"})

@api_view(['POST'])
def login(request):
    serializer = LoginSerialzer(data=request.data)
    if serializer.is_valid():
        token = JWTAuthentication.generate_token(payload=serializer.data)
        return Response({
            "message": "Login successfull",
            'token': token,
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def list_users(request):
    user = request.user
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response({
        "users": serializer.data,
        "logged_in_user": {"email": user.email, "is_staff": user.is_staff},
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    user = request.user
    return JsonResponse({
        'id': user.id,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    })

