from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from .models import User, StudentProfile, TeacherProfile
from academics.models import Student
from .serializers import (
    UserSerializer, StudentProfileSerializer, TeacherProfileSerializer, 
    LoginSerializer, ChangePasswordSerializer
)

class LoginAPIView(APIView):
    """API view for user login"""
    
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(username=email, password=password)
        
        if user:
            login(request, user)
            return Response({
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

class LogoutAPIView(APIView):
    """API view for user logout"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)

class UserAPIView(generics.RetrieveUpdateAPIView):
    """API view for retrieving and updating user info"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user

class ChangePasswordAPIView(APIView):
    """API view for changing password"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)

class StudentProfileAPIView(generics.RetrieveUpdateAPIView):
    """API view for retrieving and updating student profile"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StudentProfileSerializer
    
    def get_object(self):
        try:
            return self.request.user.student_profile
        except StudentProfile.DoesNotExist:
            # Create a new profile if it doesn't exist
            return StudentProfile.objects.create(user=self.request.user)

class TeacherProfileAPIView(generics.RetrieveUpdateAPIView):
    """API view for retrieving and updating teacher profile"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeacherProfileSerializer
    
    def get_object(self):
        try:
            return self.request.user.teacher_profile
        except TeacherProfile.DoesNotExist:
            # Create a new profile if it doesn't exist
            return TeacherProfile.objects.create(user=self.request.user) 