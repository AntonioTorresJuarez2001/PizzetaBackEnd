# pizzadashboard/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Endpoints para JWT:
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Rutas de tu app ventas:
    path("api/", include("ventas.urls")),

    # (Opcional) Puedes eliminar la ruta api-auth si ya no usas SessionAuthentication
    # path("api-auth/", include("rest_framework.urls")),
]
