import mysql.connector
from mysql.connector import Error

from query_to_db import CursorDB


def add_new_product(title, prefix_shop, sku_ya_market, price, line_id, full_name) -> int:
    """
    Добавляем новый товар, у товара обязательно должна быть линейка.
    slug заполняется добавляя в title дефисы в момент вставки
    :param title:
    :param prefix_shop: "sm", 'og', 'pd'
    :param sku_ya_market:
    :param price:
    :param line_id:
    :param full_name:
    :return:
    """
    cur = CursorDB()
    query = f'SELECT product_id FROM sku_of_product WHERE {prefix_shop.lower()}_sku = %s;'
    data = (sku_ya_market, )

    cur.cursor.execute(query, data)

    # Добавляем запись в продукты
    cur = CursorDB()
    query = '''INSERT INTO product_id (title, full_name) VALUES (%s, %s);
    '''
    data = (title, full_name)

    cur.cursor.execute(query, data)

    try:
        cur.cursor.execute(query, data)
        product_id = cur.cursor.lastrowid
    except Error as e:
        if e.errno == 1062:  # Дубликат названия. Ищем id существующего товара
            # print(e.msg)
            query = """SELECT id FROM product WHERE title = %s"""
            data = (title,)
            cur.cursor.execute(query, data)
            product_id = cur.cursor.fetchone()[0]
            print(f'- Товар с названием "{title}" уже существует под id: {product_id}')
            return

        elif e.errno == 1452:
            print(e.msg)
            return

        print(e.errno, '-', e.msg)

    # Добавляем стоимость
    cur = CursorDB()
    query = 'INSERT INTO price_of_product (product_id, price) VALUE (%s, %s);'
    data = (product_id, price)
    try:
        cur.cursor.execute(query, data)
    except Error as e:
        print(e)

    # Добавляем товар в линейку
    cur = CursorDB()
    query = 'INSERT INTO product_in_line (line_id, product_id) VALUE (%s, %s);'
    data = (line_id, product_id)
    try:
        cur.cursor.execute(query, data)
    except Error as e:
        print(e)

    return product_id


def main():
    pass


if __name__ == '__main__.py':
    main()
