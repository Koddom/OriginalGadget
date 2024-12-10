from django.shortcuts import render, HttpResponse
import sys
import os
from cart.cart import Cart  # из приложения cart Импортируем корзину

# Добавляем путь к папке, содержащей query_to_db.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import query_to_db


def index(request):
    context = {
        'current_category': 'HOME'
    }
    request.session.flush()
    return render(request, 'shop/index.html', context=context)


def buy_category(request, category):

    selected_characteristic = {}
    # формируем словарь выбранных характеристик для дальнейшей фильтрации списка товаров
    if request.method == 'POST':
        for characteristic in request.POST.keys():
            if characteristic != 'csrfmiddlewaretoken':
                selected_characteristic[characteristic] = request.POST.getlist(characteristic)
                # lines_and_products = query_to_db
        # input(selected_characteristic)  # словарь выбранных характеристик
    category = category.replace('-', ' ')
    lines_and_products = query_to_db.get_lines_and_products_in_category(category)

    # lines = []
    list_of_products = []
    list_product_ids = []

    for line, products in lines_and_products.items():
        # lines.append(line)
        for product in products:
            list_of_products.append(product)
            list_product_ids.append(product['id'])

    # формируем словарь значений характеристик товаров
    values_of_characteristics = query_to_db.get_value_of_characteristics_for_products(list_product_ids)
    lines = query_to_db.get_lines_in_category(category)
    context = {
        'current_category': category,
        'current_line': None,
        'lines': lines,
        'list_of_products': list_of_products,
        'values_of_characteristics': values_of_characteristics
    }

    return render(request, 'shop/shop.html', context)


def buy_line(request, line):

    if request.method == 'POST':  # выбрали необходимые характеристики
        selected_characteristic = {}
        # формируем словарь выбранных характеристик для дальнейшей фильтрации списка товаров
        for characteristic in request.POST.keys():
            if characteristic != 'csrfmiddlewaretoken':
                selected_characteristic[characteristic] = request.POST.getlist(characteristic)
    # end POST

    current_line = line.replace('-', ' ')  # надеюсь в названии линейки продукта никогда не встретится тире

    current_category, lines = query_to_db.get_category_and_lines_by_line(current_line)
    list_of_products = query_to_db.get_products_in_line(current_line)

    list_product_ids = [product['id'] for product in list_of_products]
    values_of_characteristics = query_to_db.get_value_of_characteristics_for_products(list_product_ids)
    context = {
        'current_category': current_category,
        'current_line': current_line,
        'lines': lines,
        'list_of_products': list_of_products,  # [{id:, title:, slug:, price: ... и т.д.}, ]
        'values_of_characteristics': values_of_characteristics,
    }

    # return HttpResponse(line + category + str(lines_and_products[' '.join(line.split('-'))]))
    return render(request, 'shop/shop.html', context)


def product_details(request, category, product):
    """
    :param request:
    :param category:
    :param product:
    :return: Получить название, описание, актуальную стоимость.
    """
    product_slug = product
    product = query_to_db.get_info_product(product_slug)  # product - product_slug
    cart = Cart(request)
    product_in_cart = cart.has_product(str(product['id']))
    print(category)
    context = {
        'product': product,  #
        'category': category.replace('-', ' ', category.count('-')),
        'product_in_cart': product_in_cart
    }
    return render(request, 'shop/product-details.html', context)


def cart(request):
    cart = Cart(request)
    total_price_of_cart = cart.get_total_price()
    context = {
        'cart': cart,
        'total_price_of_cart': total_price_of_cart
    }
    return render(request, 'shop/cart.html', context=context)
