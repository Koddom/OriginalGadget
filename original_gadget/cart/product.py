import os, sys
# Добавляем путь к папке, содержащей query_to_db.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
# from query_to_db import *  # Импорт функции из query_to_db.py
import query_to_db


class Product:
    # Подумать над актуальностью класса Продукт
    def __init__(self, product_id):
        price, slug, line, category, title, full_name, images = query_to_db.get_actual_price_of_product()
        self.id = product_id
        self.price = price
        self.slug = slug
        self.line = line
        self.category = category
        self.title = title
        self.full_name = full_name
        self.images = images
        self.path_to_img = f'img/product-img{self.category}/{self.line}/'
