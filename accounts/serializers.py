from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, StudentProfile, TeacherProfile
from academics.models import Student

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'user_type', 'profile_pic', 'phone_number', 'address', 'date_of_birth')
        read_only_fields = ('id', 'email', 'user_type')

class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for StudentProfile model"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = ('id', 'user', 'admission_number', 'parent_name', 'parent_phone', 'parent_email', 'blood_group', 'emergency_contact')
        read_only_fields = ('id', 'user')

class TeacherProfileSerializer(serializers.ModelSerializer):
    """Serializer for TeacherProfile model"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TeacherProfile
        fields = ('id', 'user', 'employee_id', 'qualification', 'experience', 'joining_date')
        read_only_fields = ('id', 'user')

class LoginSerializer(serializers.Serializer):
    """Serializer for login"""
    
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    
    old_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(style={'input_type': 'password'})
    confirm_password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, data):
        request = self.context.get('request')
        
        if not authenticate(username=request.user.email, password=data.get('old_password')):
            raise serializers.ValidationError({'old_password': 'Incorrect old password.'})
        
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'New passwords do not match.'})
        
        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'user_type', 'password', 'confirm_password')
    
    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        return user 