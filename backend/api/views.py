from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
import json


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Yeni kullanıcı kaydı"""
    try:
        data = request.data
        
        # Gerekli alanları kontrol et
        full_name = data.get('fullName', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not full_name or not email or not password:
            return Response({
                'success': False,
                'message': 'Tüm alanları doldurun.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Email zaten kayıtlı mı?
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'message': 'Bu e-posta adresi zaten kayıtlı.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Username olarak email kullan
        if User.objects.filter(username=email).exists():
            return Response({
                'success': False,
                'message': 'Bu e-posta adresi zaten kayıtlı.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Şifre kontrolü
        if len(password) < 6:
            return Response({
                'success': False,
                'message': 'Şifre en az 6 karakter olmalıdır.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # İsim parçala
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Kullanıcı oluştur
        user = User.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=make_password(password)
        )
        
        return Response({
            'success': True,
            'message': 'Hesap başarıyla oluşturuldu.',
            'user': {
                'id': user.id,
                'email': user.email,
                'fullName': f"{user.first_name} {user.last_name}".strip(),
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Bir hata oluştu: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Kullanıcı girişi"""
    try:
        data = request.data
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return Response({
                'success': False,
                'message': 'E-posta ve şifre gereklidir.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Kullanıcıyı bul
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'E-posta veya şifre hatalı.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Şifre kontrolü
        user = authenticate(username=user.username, password=password)
        
        if user is None:
            return Response({
                'success': False,
                'message': 'E-posta veya şifre hatalı.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'success': False,
                'message': 'Hesabınız devre dışı bırakılmış.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'success': True,
            'message': 'Giriş başarılı.',
            'user': {
                'id': user.id,
                'email': user.email,
                'fullName': f"{user.first_name} {user.last_name}".strip(),
                'isStaff': user.is_staff,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Bir hata oluştu: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user(request, user_id):
    """Kullanıcı bilgilerini getir"""
    try:
        user = User.objects.get(id=user_id)
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'fullName': f"{user.first_name} {user.last_name}".strip(),
                'isStaff': user.is_staff,
                'dateJoined': user.date_joined,
            }
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Kullanıcı bulunamadı.'
        }, status=status.HTTP_404_NOT_FOUND)
