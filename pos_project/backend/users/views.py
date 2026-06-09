# users/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import (
    UserSerializer, 
    UserLoginSerializer, 
    UserChangePasswordSerializer,
    UserRoleUpdateSerializer
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'success': True,
                'user': {
                    'username': user.username,
                    'role': user.role,
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'message': str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'is_active', 'employment_type']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'employee_id']
    ordering_fields = ['username', 'date_joined', 'role', 'base_salary']
    ordering = ['-date_joined']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return User.objects.all()
        if user.role == 'admin':
            return User.objects.exclude(role='super_admin')
        if user.role == 'manager':
            return User.objects.filter(role__in=['cashier', 'storekeeper', 'viewer'])
        return User.objects.filter(id=user.id)
    
    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [AllowAny()]
        if self.action in ['update_role', 'destroy']:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'], url_path='me')
    def get_current_user(self, request):
        serializer = UserSerializer(request.user)
        data = serializer.data
        data['permissions'] = request.user.get_permissions_list()
        return Response(data)
    
    @action(detail=False, methods=['post'], url_path='login', permission_classes=[AllowAny])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({'success': False, 'message': str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response(
                {'success': False, 'message': 'Invalid username or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'success': False, 'message': 'User account is deactivated'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user.is_online = True
        user.last_activity = timezone.now()
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            user.last_login_ip = x_forwarded_for.split(',')[0]
        else:
            user.last_login_ip = request.META.get('REMOTE_ADDR')
        
        user.save(update_fields=['is_online', 'last_activity', 'last_login_ip'])
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'user': {
                'username': user.username,
                'role': user.role,
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'permissions': user.get_permissions_list()
        })
    
    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        user = request.user
        user.is_online = False
        user.save(update_fields=['is_online'])
        
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        
        return Response({"message": "Successfully logged out"})
    
    @action(detail=True, methods=['post'], url_path='change-password')
    def change_password(self, request, pk=None):
        user = self.get_object()
        
        if request.user.id != user.id and request.user.role not in ['super_admin', 'admin']:
            return Response(
                {"error": "You can only change your own password"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserChangePasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user.id == user.id:
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {"old_password": "Wrong password"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({"message": "Password changed successfully"})
    
    @action(detail=True, methods=['patch'], url_path='update-role')
    def update_role(self, request, pk=None):
        if request.user.role not in ['super_admin', 'admin']:
            return Response(
                {"error": "Only administrators can update user roles"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        
        if user.role == 'super_admin' and request.user.role != 'super_admin':
            return Response(
                {"error": "Only super admin can modify super admin users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserRoleUpdateSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        if request.user.role not in ['super_admin', 'admin']:
            return Response(
                {"error": "Only administrators can activate/deactivate users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        
        if user.id == request.user.id:
            return Response(
                {"error": "You cannot deactivate your own account"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_active = not user.is_active
        if not user.is_active:
            user.is_online = False
        user.save()
        
        status_text = "activated" if user.is_active else "deactivated"
        return Response({"message": f"User {user.username} {status_text}"})
    
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        
        if user.id == request.user.id:
            return Response(
                {"error": "You cannot delete your own account"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_active = False
        user.is_online = False
        user.save()
        
        return Response(
            {"message": f"User {user.username} has been deactivated"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='cashiers')
    def get_cashiers(self, request):
        cashiers = User.objects.filter(role='cashier', is_active=True)
        serializer = UserSerializer(cashiers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='by-role')
    def get_by_role(self, request):
        role = request.query_params.get('role')
        if not role:
            return Response(
                {"error": "Role parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        users = User.objects.filter(role=role, is_active=True)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)