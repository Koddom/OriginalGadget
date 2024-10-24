from django.urls import path
from . import views


app_name = 'cart'

urlpatterns = [
    path('add', views.cart_add, name='cart_add'),
    path('remove_from_cart/<int:product_id>', views.remove_from_cart, name='remove_from_cart'),
    path('send_order/', views.send_order, name='send_order')
]
