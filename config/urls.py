"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core import views as core_views

handler404 = core_views.error_404
handler500 = core_views.error_500

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("customer/", include("apps.customers.urls")),
    path("rooms/", include("apps.rooms.urls")),
    path("bookings/", include("apps.bookings.urls")),
    path("customer/", include("apps.bookings.customer_urls")),
    path("customer/", include("apps.billing.customer_urls")),
    path("staff/", include("apps.rooms.staff_urls")),
    path("staff/", include("apps.customers.staff_urls")),
    path("staff/", include("apps.bookings.staff_urls")),
    path("staff/", include("apps.services.urls")),
    path("staff/", include("apps.billing.urls")),
    path("staff/", include("apps.reports.urls")),
    path("ai/", include("apps.ai_integration.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
