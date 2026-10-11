from django.urls import path

from . import views

app_name = "customer-billing"
urlpatterns = [
    path("invoices/", views.customer_invoice_list, name="list"),
    path("invoices/<int:pk>/", views.customer_invoice_detail, name="detail"),
    path("invoices/<int:pk>/pay/", views.customer_invoice_pay, name="pay"),
]
