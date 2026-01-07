# users/api/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from shared.auth.serializers import LoginSerializer


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
