from django.urls import path

from . import views

app_name = "gallery"
urlpatterns = [
    path("", views.index, name="index"),
    path("painting/<slug:slug>/", views.detail, name="detail"),
    path("painting/<slug:slug>/buy/", views.checkout, name="checkout"),
    path("painting/<slug:slug>/add/", views.add_to_cart, name="add_to_cart"),  # still needed
    path("signup/", views.signup, name="signup"),
    path("orders/", views.orders, name="orders"),
    path("paystack/callback/", views.paystack_callback, name="paystack_callback"),
    path("orders/<int:pk>/remove/", views.remove_order, name="remove_order"),
    path("commission/", views.commission, name="commission"),
]