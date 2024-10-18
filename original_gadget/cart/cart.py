from django.conf import settings

import os, sys
# Добавляем путь к папке, содержащей query_to_db.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
# from query_to_db import *  # Импорт функции из query_to_db.py
import query_to_db


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            print('!!----!!', settings.CART_SESSION_ID)
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product_id, quantity=1, override_quantity=False):
        # price = query_to_db.get_actual_price_of_product(product_id)
        product_dict = query_to_db.get_info_product_for_cart(product_id)
        # {'title': , 'slug': , 'price': , 'description': , 'images': [], 'line': , 'category': , 'full_name': }
        if product_id not in self.cart:
            self.cart[product_id] = product_dict
            self.cart[product_id]['quantity'] = 0  # добавляем в словарь количество

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

        return product_dict

    def save(self):
        self.session.modified = True

    def remove(self, product_id):
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]

        self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = []  # список продуктов в корзине
        cart = self.cart.copy()
        # for product in products:
        #     cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = item['price']
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def __str__(self):
        text = ''
        for product_id in self.cart:
            text += str(product_id) + ', '
        return text

    def get_total_price(self):
        return sum(
            item['price'] * item['quantity']
            for item in self.cart.values()
        )

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def has_product(self, product_id):

        if product_id in self.cart:
            return True
        else:
            return False
