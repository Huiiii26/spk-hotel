from django.urls import path

from . import views

app_name = "billing-staff"
urlpatterns = [
    path("invoices/", views.invoice_list, name="list"),
    path("invoices/<int:pk>/", views.invoice_detail, name="detail"),
    path("invoices/<int:pk>/adjust/", views.invoice_adjust, name="adjust"),
    path("invoices/<int:pk>/payments/add/", views.payment_add, name="payment-add"),
]
