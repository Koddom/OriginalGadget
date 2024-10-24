from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import requests

from .cart import Cart
import os
import sys
# Добавляем путь к папке, содержащей query_to_db.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
# from query_to_db import *  # Импорт функции из query_to_db.py
import query_to_db


@require_POST
def cart_add(request):

    product_id = request.POST.get('product_id')  # берём данные из AJAX запроса

    cart = Cart(request)
    product_info = cart.add(product_id)
    cart.quantity = cart.__len__()

    category = product_info['category']
    slug = product_info['slug']

    # Возвращаем JSON с количеством товаров в корзине
    return JsonResponse({'cart_quantity': cart.__len__()})
    # return redirect('product_details', category=category, product=slug)


@require_POST
def cart_add_from_product(request, product_id):
    """
    Данная функция является временным форком cart_add и работает без ajax запроса. Просто обновляя страницу
    :param request:
    :param product_id:
    :return:
    """

    cart = Cart(request)
    product_info = cart.add(product_id)
    cart.quantity = cart.__len__()

    category = product_info['category']
    slug = product_info['slug']

    return redirect('product_details', category=category, product=slug)


# @require_POST
def remove_from_cart(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    for item in cart:
        print(item)
    return redirect('cart')


@require_POST
def send_order(request):
    cart = Cart(request)
    text = request.POST.get('contact_info')  # получаем телефон или телегу которые указал пользователь
    text += '\n-----------\n'
    for item in cart:
        # print(item)
        text += f"**Товар:** {item['title']}\n**Цена:** {item['price']} ₽ \n----\n\n"

    token = '6888701276:AAHTtZfq0iKRl-mAbdGi7_LAbH4mc1EGOcs'

    url = f'https://api.telegram.org/bot{token}/sendMessage'

    chat_id = '480974372'

    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
    }
    requests.post(url, data)

    return redirect('cart')


# def cart_detail(request):  # находится в shop/views.py
#     cart = Cart(request)
#     return render(request, 'cart/detail.html', {'cart': cart})
