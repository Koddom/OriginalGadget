from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .cart import Cart
import os
import sys
# Добавляем путь к папке, содержащей query_to_db.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
# from query_to_db import *  # Импорт функции из query_to_db.py
import query_to_db


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)

    cart.add(product_id)
    # input(cart)
    data = {'category': 'iphone', 'product': 'iphone-se-2022-128-gb-starlight'}
    # input(cart)
    return redirect('product_details', category='iphone', product='iphone-se-2022-128-gb-starlight')


# def cart_detail(request):  # находится в shop/views.py
#     cart = Cart(request)
#     return render(request, 'cart/detail.html', {'cart': cart})
