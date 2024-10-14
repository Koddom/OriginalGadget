import sys
import os

# Добавляем путь к папке, содержащей query_to_db.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# from query_to_db import *  # Импорт функции из query_to_db.py
import query_to_db


def categories_processor(request):
    categories = query_to_db.get_all_categories()  # Получаем список всех категорий
    # if 'mac' in categories:
    #     categories.insert(0, 'mac')
    # if 'iphone' in categories:
    #     categories.insert(1, 'iphone')
    # if 'ipad' in categories:
    #     categories.insert(2, 'ipad')
    # if 'watch' in categories:
    #     categories.insert(3, 'watch')
    # if 'apple vision pro' in categories:
    #     categories.insert(4, 'apple vision pro')
    # if 'airpods' in categories:
    #     categories.insert(5, 'airpods')
    # if 'airtag' in categories:
    #     categories.insert(6, 'airtag')

    return {'categories': categories}


def lines_processor(request):
    category = request.session.get()
    lines = query_to_db.get_lines_in_category(category)
    return lines
