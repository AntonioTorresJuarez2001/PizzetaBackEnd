# pizzadashboard/urls.py

from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import permissions
from ventas.views import current_user


# drf-yasg imports
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración del schema
schema_view = get_schema_view(
    openapi.Info(
        title="PizzaDashboard API",
        default_version='v1',
        description="Autenticación y CRUD de pizzerías/ventas",
        contact=openapi.Contact(email="soporte@tudominio.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # JWT auth
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Tu app de ventas
    path("api/", include("ventas.urls")),
    
    #usuarios
    path("user/", current_user), 

    # Documentación drf-yasg
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json'),
    path('swagger/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'),
    path('redoc/',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'),
]
