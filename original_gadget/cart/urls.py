from django.urls import path
from . import views


app_name = 'cart'

urlpatterns = [
    path('add', views.cart_add, name='cart_add'),
    path('add_cart_from_product/<int:product_id>', views.cart_add_from_product, name='cart_add_from_product'),
    path('remove_from_cart/<int:product_id>', views.remove_from_cart, name='remove_from_cart'),
    path('send_order/', views.send_order, name='send_order')
]
