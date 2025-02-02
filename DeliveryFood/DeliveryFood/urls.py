from django.contrib import admin
from django.urls import path, re_path, include
from django.conf.urls.static import static
from rest_framework import permissions

from . import settings

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="DELIVERY FOOD API Documentation",
        default_version="v1",
        description="Описание API проекта DELIVERY FOOD",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="leraignatovaabc@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("Delivery.urls_api")),
    path("", include("Delivery.urls_templates")),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
]


if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

