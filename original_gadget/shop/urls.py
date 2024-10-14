from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('shop', views.index, name='shop'),
    path('product-details', views.index, name='product-details'),
    path('cart', views.cart, name='cart'),
    path('checkout', views.index, name='checkout'),
    path('shop/<str:category>', views.buy_category, name='buy_category'),
    path('shop/buy/<str:line>', views.buy_line, name='buy_line'),
    path('shop/buy-<str:category>/<str:product>', views.product_details, name='product_details'),
]