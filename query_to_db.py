import mysql.connector
from mysql.connector import Error
from django.utils.text import slugify
from settings import connection_config_to_db
from settings import DB_NAME


class CursorDB:
    def __init__(self):
        self.connection = None
        try:
            self.connection = mysql.connector.connect(
                **connection_config_to_db
            )
            self.cursor = self.connection.cursor()
            self.cursor.execute(f'USE {DB_NAME}')
            # print("Connection to MySQL DB successful")
        except Error as e:
            if e.errno == 2061:
                print('Ошибка аутентификации')
            print(f"The error '{e}' occurred")
            return

    def __del__(self):
        if self.connection:
            self.connection.close()


def get_all_categories():
    """
    :return: Список категорий ['airpods', 'ipad', 'iphone', 'mac', 'pencil', 'watch']
    """
    query = "SELECT title, position FROM `category` ORDER BY position;"
    cur = CursorDB()
    try:
        cur.cursor.execute(query)
    except Error as e:
        print(e)

    categories = cur.cursor.fetchall()
    categories = [category[0] for category in categories]

    return categories


def get_lines_and_products_in_category(category):
    """
    [line: [{
    id:,
    title:,
    slug:,
    price:,
    }, {id:, title:, slug:, price:}, ...], line: [{}, {}], ...]
    :param category:
    :return:
    """
    cur = CursorDB()

    # сначала получаем таблицу продуктов в категории
    query = '''
        CREATE TEMPORARY TABLE product_in_category AS
        SELECT 
            product_id,
            line
        FROM `product_in_line`
        WHERE `line` in (
            SELECT line 
            FROM `product_line`
            WHERE `category` = %s AND is_available = 1
            )
        ORDER BY RAND()
        LIMIT 20;
        ;
    '''
    data = (category,)
    cur.cursor.execute(query, data)

    # # Затем формируем таблицу актуальных цен
    # query = '''
    #     CREATE TEMPORARY TABLE actual_price
    #     AS
    #     SELECT p.product_id, p.price
    #     FROM price_of_product p
    #     INNER JOIN (
    #         SELECT product_id, MAX(`date`) AS max_date
    #         FROM price_of_product
    #         GROUP BY product_id
    #     ) latest_price
    #     ON p.product_id = latest_price.product_id
    #     AND p.`date` = latest_price.max_date;
    # '''
    # cur.cursor.execute(query)

    # Временная таблица с картинками
    query = '''
        CREATE TEMPORARY TABLE image
        SELECT
            product_id,
            GROUP_CONCAT(name_of_img ORDER BY number_of_image ASC SEPARATOR ';') AS images
        FROM img_of_product
        WHERE product_id IN (SELECT product_id FROM product_in_category)
        GROUP BY product_id;
    '''
    try:
        cur.cursor.execute(query)
    except Error as e:
        print(e)

    # только теперь получаем необходимые данные соеденив все таблицы
    query = '''
    SELECT
        product.id, 
        product_in_category.line,
        product.title,
        product.slug,
        COALESCE(price_of_product.price, 0) as price,
        image.images
    FROM product_in_category
    LEFT JOIN product
    ON `product_in_category`.product_id = `product`.id
    LEFT JOIN `price_of_product`
    ON `product_in_category`.product_id = `price_of_product`.product_id
    LEFT JOIN `image`
    ON `product_in_category`.product_id = `image`.product_id
    ORDER BY line DESC;
    '''
    cur.cursor.execute(query)

    products_in_category = {}

    current_line = None
    products = []

    # Обход результатов запроса
    for row in cur.cursor:
        id = row[0]
        line = row[1]
        title = row[2]
        slug = row[3]
        price = int(row[4])
        images = [img_name.strip() for img_name in str(row[5]).split(';')]

        if line != current_line:  # если сменилась линейка продукта в обходе выборки
            if current_line is not None:
                products_in_category[current_line] = products

            current_line = line
            products = []

        # Добавляем продукт в текущий список продуктов
        category_slug = slugify(category)
        line_slug = slugify(line)
        path_to_img = f'img/product-img/{category_slug}/{line_slug}/'
        product = {
            'id': id,
            'title': title,
            'slug': slug,
            'price': price,
            'path_to_img': path_to_img,
            'images': images,
            'category': category,
            'line': line
        }
        products.append(product)

    # Сохраняем последнюю группу
    if current_line is not None:
        products_in_category[current_line] = products

    return products_in_category


def get_lines_in_category(category):
    """
    Возвращает список линеек в категории [line1, line2, ...]
    :param category:
    :return:
    """
    cur = CursorDB()
    query = '''
        SELECT line
        FROM product_line
        WHERE category = %s AND is_available = 1
        ORDER BY line_position DESC
        '''
    data = (category,)
    try:
        cur.cursor.execute(query, data)
    except Error as e:
        print(e)

    lines_in_category = [line[0] for line in cur.cursor.fetchall()]

    return lines_in_category


def get_value_of_characteristics_for_products(list_product_ids):
    """
    :param list_product_ids: [1,2,3,5...]
    :return: {characteristic1: [value1, value2, ..], characteristic2: [value1, value2, ..]}
    """
    if not len(list_product_ids):
        return {}

    placeholders = ', '.join(['%s'] * len(list_product_ids))
    query = f"""
    SELECT 
        characteristic, 
        value
    FROM characteristic_of_product
    WHERE product_id IN ({placeholders})
    GROUP BY `characteristic`, `value`
    ORDER BY `characteristic`;
    """
    cur = CursorDB()
    try:
        cur.cursor.execute(query, list_product_ids)

    except Error as e:
        print(e)
        return

    current_characteristic = None
    values_of_characteristic = {}
    values = []
    # обход по группировке. формируем словарь из выборки
    for row in cur.cursor:
        characteristic = row[0]
        value = row[1]
        if characteristic != current_characteristic:  # если сменилась характеристика
            if current_characteristic is not None:  # Пропускаем первую итерацию
                values_of_characteristic[current_characteristic] = values

            current_characteristic = characteristic
            values = []  # обнуляем список при переключении на новую характеристику

        # добавляем очередное значение характеристики в список values
        values.append(value)

    # Сохраняем последнюю характеристику и её значения
    if current_characteristic is not None:
        values_of_characteristic[current_characteristic] = values

    return values_of_characteristic


def get_products_in_line(line):
    """ Получает список продуктов в одной линейке
    :param line:
    :return: [{
    'id':,
    'title':,
    'slug':,
    'price':,
    'images': [],
    'category':
    },
    {id:, title:, slug:, price:, 'images': [], 'category'}, ...]
    1 - сначала создаём временную таблицу "товары в одной линейке"
    2 - чтобы создать временную таблицу "стоимость товара в линейке" (сюда попадую записи с дубликатами product_id)
    3 - чтобы создать временную таблицу "актуальная дата для стоимости товара в линейке", чтобы отфильтровать стоимость по дате
    4 - формируем таблицу с выборкой картинок в одну строку
    5 - Чтобы сделать финальную выборку
    """

    cur = CursorDB()

    # 1 - таблица "товары в одной линейке"
    query = '''
        CREATE TEMPORARY TABLE `product_in_one_line`
        SELECT `product_id`
        FROM `product_in_line`
        WHERE `line` = %s;
    '''
    data = (line,)
    try:
        cur.cursor.execute(query, data)
    except Error as e:
        print(e)

    # 2 - таблица "стоимость товара в линейке" содержит стоимость на все даты
    # query = '''
    #     CREATE TEMPORARY TABLE `price_of_product_in_line`
    #     SELECT
    #         product_in_one_line.product_id,
    #         `date`,
    #         price
    #     FROM product_in_one_line
    #     JOIN `price_of_product`
    #     ON product_in_one_line.product_id = `price_of_product`.`product_id`;
    # '''
    # try:
    #     cur.cursor.execute(query)
    # except Error as e:
    #     print(e)

    # 3 - таблица "актуальная дата для стоимости товара в линейке"
    # query = '''
    #     CREATE TEMPORARY TABLE `actual_date_for_price_of_product_in_line`
    #     SELECT
    #         product_id,
    #         MAX(`date`) AS `date`
    #     FROM `price_of_product_in_line`
    #     GROUP BY product_id;
    # '''
    # try:
    #     cur.cursor.execute(query)
    # except Error as e:
    #     print(e)

    # 4 - формируем таблицу с картинками
    query = '''
        CREATE TEMPORARY TABLE names_of_images
        SELECT
            product_id,
            GROUP_CONCAT(name_of_img ORDER BY number_of_image ASC SEPARATOR ';') AS names_of_images
        FROM img_of_product
        WHERE product_id IN (SELECT product_id FROM product_in_one_line)
        GROUP BY product_id;    
    '''
    try:
        cur.cursor.execute(query)
    except Error as e:
        print(e)

    # 5 - финальная выборка
    query = '''
        SELECT 
            product_in_one_line.product_id,
            product.`title`,
            product.slug,
            price_of_product.price,
            names_of_images.names_of_images,
            (SELECT `category` FROM `product_line` WHERE `line` = %s) AS `category`
        FROM `product_in_one_line`
        LEFT JOIN product
        ON product_in_one_line.product_id = product.id
        LEFT JOIN `price_of_product`
        ON product_in_one_line.product_id = price_of_product.product_id
        LEFT JOIN names_of_images
        ON product_in_one_line.product_id = names_of_images.product_id
        ;
    '''
    data = (line,)
    try:
        cur.cursor.execute(query, data)
    except Error as e:
        print(e)

    list_of_product = cur.cursor.fetchall()

    products = []
    for product_info in list_of_product:
        category = slugify(product_info[5])
        path_to_img = f'img/product-img/{category}/{slugify(line)}/'
        product = {
            'id': product_info[0],
            'title': product_info[1],
            'slug': product_info[2],
            'price': product_info[3],
            'images': [img_name.strip() for img_name in str(product_info[4]).split(';')],
            'path_to_img': path_to_img,
            'category': product_info[5],
            'line': line,
        }
        products.append(product)

    return products


def get_info_product(slug=None, product_id=None):
    """
    :param product_id:
    :param slug:
    :return: {
        'id': product_info[0],
        'title': product_info[1],
        'slug': product_info[2],
        'price': product_info[3],
        'description': product_info[4],
        'images': [img_name.strip() for img_name in product_info[5].split(';')],
        'line': product_info[6],
    }
    """
    cur = CursorDB()
    # временная таблица с товаром
    query = '''
        CREATE TEMPORARY TABLE cart_product
        SELECT *
        FROM product
        WHERE 
        slug = %s;
    '''
    data = (slug,)
    if product_id:
        query.replace('slug', 'id')
        data = (product_id,)

    try:
        cur.cursor.execute(query, data)
    except Error as e:
        print(e)

    # Временная таблица с ценой
    query = '''
        CREATE TEMPORARY TABLE actual_price
        SELECT 
            product_id,
            MAX(price) AS price
        FROM price_of_product
        WHERE product_id IN (
                        SELECT id FROM cart_product
        )
        GROUP BY product_id;
    '''
    try:
        cur.cursor.execute(query)
    except Error as e:
        print(e)

    # Временная таблица с описанием
    query = '''
        CREATE TEMPORARY TABLE description
        SELECT 
            product_id, 
            description
        FROM description_of_product
        WHERE product_id IN (SELECT id FROM cart_product);
    '''
    try:
        cur.cursor.execute(query)
    except Error as e:
        print(e)

    # Временная таблица с картинками
    query = '''
        CREATE TEMPORARY TABLE image
        SELECT
            product_id,
            GROUP_CONCAT(name_of_img ORDER BY number_of_image ASC SEPARATOR ';') AS images
        FROM img_of_product
        WHERE product_id IN (SELECT id FROM cart_product)
        GROUP BY product_id;
    '''
    try:
        cur.cursor.execute(query)
    except Error as e:
        print(e)

    # Временная таблица с категорией товара (узнаём через внутренний запрос к линейке товара)
    query = f'''
            CREATE TEMPORARY TABLE category_of_product
            SELECT 
                `category`
            FROM `product_line`
            WHERE `line` = (SELECT line FROM `product_in_line` WHERE `product_id` = (SELECT id FROM cart_product));
        '''
    try:
        cur.cursor.execute(query)
    except Error as e:
        print(e)

    # результирующая выборка
    query = '''
        SELECT 
            id,
            title,
            slug,
            price,
            IFNULL(description.description, '') AS description,
            IFNULL(image.images, '') AS images,
            pil.line,
            full_name,
            (SELECT category FROM category_of_product) AS category
        FROM cart_product cp
        LEFT JOIN actual_price
        ON cp.id = actual_price.product_id
        LEFT JOIN description
        ON cp.id = description.product_id
        LEFT JOIN image
        ON cp.id = image.product_id
        LEFT JOIN product_in_line pil
        ON cp.id = pil.product_id
        ;
    '''
    try:
        cur.cursor.execute(query)
    except Error as e:
        print(e)

    product_info = cur.cursor.fetchone()
    if product_info:
        # обработка если product_info[5] = ['']
        images = [img_name.strip() for img_name in product_info[5].split(';')] if product_info[5] else []
        category_slug = slugify(product_info[8])
        line_slug = slugify(product_info[6])
        path_to_img = f'img/product-img/{category_slug}/{line_slug}/'
        product_info = {
            'id': product_info[0],
            'title': product_info[1],
            'slug': product_info[2],
            'price': product_info[3],
            'description': product_info[4],
            'path_to_img': path_to_img,
            'images': images,
            'line': product_info[6],
            'full_name': product_info[7],
            'category': product_info[8],
        }
        return product_info
    else:
        return {}


def get_info_product_for_cart(product_id):
    """ Возвращает данные для заполения значения по ключу product_id
    (price, slug, line, category, title, full_name, images: [str])
    :param product_id:
    :return:
    """
    cur = CursorDB()
    # временная таблица с товаром
    query = '''
            CREATE TEMPORARY TABLE cart_product
            SELECT *
            FROM product
            WHERE 
            id = %s;
        '''
    data = (product_id,)

    try:
        cur.cursor.execute(query, data)
    except Error as e:
        print(e)


    # Временная таблица с описанием
    # query = '''
    #         CREATE TEMPORARY TABLE description
    #         SELECT
    #             product_id,
    #             description
    #         FROM description_of_product
    #         WHERE product_id IN (SELECT id FROM cart_product);
    #     '''
    # try:
    #     cur.cursor.execute(query)
    # except Error as e:
    #     print(e)

    # Временная таблица с картинками
    query = '''
            CREATE TEMPORARY TABLE image
            SELECT
                product_id,
                GROUP_CONCAT(name_of_img ORDER BY number_of_image ASC SEPARATOR ';') AS images
            FROM img_of_product
            WHERE product_id IN (SELECT id FROM cart_product)
            GROUP BY product_id;
        '''
    try:
        cur.cursor.execute(query)
    except Error as e:
        print(e)

    # Временная таблица с категорией товара (узнаём через внутренний запрос к линейке товара)
    query = f'''
            CREATE TEMPORARY TABLE category_of_product
            SELECT 
                `category`,
                {product_id} AS product_id
            FROM `product_line`
            WHERE `line` = (SELECT line FROM `product_in_line` WHERE `product_id` = {product_id});
        '''
    try:
        cur.cursor.execute(query)
    except Error as e:
        print(e)

    # результирующая выборка
    query = '''
            SELECT 
                cart_product.id,
                cart_product.title,
                cart_product.slug,
                price_of_product.price,
                description_of_product.description,
                COALESCE(image.images, '') AS images,
                product_in_line.line,
                category_of_product.category
            FROM cart_product
            LEFT JOIN price_of_product
            ON cart_product.id = price_of_product.product_id
            LEFT JOIN description_of_product
            ON cart_product.id = description_of_product.product_id
            LEFT JOIN image
            ON cart_product.id = image.product_id
            LEFT JOIN product_in_line
            ON cart_product.id = product_in_line.product_id
            LEFT JOIN category_of_product
            ON cart_product.id = category_of_product.product_id
            ;
        '''
    try:
        cur.cursor.execute(query)
    except Error as e:
        print(e)

    product_info = cur.cursor.fetchone()
    if product_info:
        category_slug = slugify(product_info[7])
        line_slug = slugify(product_info[6])
        list_of_images = [img_name.strip() for img_name in product_info[5].split(';')]
        if list_of_images == ['']:
            list_of_images = []
        product_info = {
            'id': product_info[0],
            'title': product_info[1],
            'slug': product_info[2],
            'price': product_info[3],
            'description': product_info[4],
            'path_to_img': f'img/product-img/{category_slug}/{line_slug}/',  # .../category/line/
            'images': list_of_images,
            'line': product_info[6],
            'category': product_info[7],
            'full_name': product_info[1],
        }
    else:
        product_info = {}

    return product_info


def get_actual_price_of_product(product_id) -> int:
    """
    Возвращает актуальную цену продукта
    :param product_id:
    :return:
    """
    cur = CursorDB()

    query = """
            SELECT price
            FROM price_of_product
            WHERE product_id = %s
        """
    data = (product_id,)
    try:
        cur.cursor.execute(query, data)
    except Error as e:
        print(e)

    price = cur.cursor.fetchone()

    return price[0] if price else 0


def get_category_and_lines_by_line(line):
    cur = CursorDB()
    query = '''
            SELECT `line`, `category`
            FROM `product_line`
            WHERE `category` = (SELECT `category` FROM `product_line` WHERE `line` = %s) AND is_available = 1
            ORDER BY line_position DESC
            '''
    data = (line,)
    try:
        cur.cursor.execute(query, data)
    except Error as e:
        print(e)

    category_and_lines = cur.cursor.fetchall()
    category = category_and_lines[0][1]
    lines = [value[0] for value in category_and_lines]

    return category, lines


# Функции записи в БД
def update_price(product_id, new_price):
    cur = CursorDB()
    """
    query = f'''
            INSERT INTO price_of_product (product_id, `date`, price)
            SELECT {product_id}, NOW(), {new_price}
            FROM dual
            WHERE NOT EXISTS ( -- проверяем существует ли хотя бы одна запись. 
                SELECT 1 -- необходимо при первом добавлении записи в таблицу price
                FROM price_of_product 
                WHERE product_id = {product_id} 
                ORDER BY `date` DESC 
                LIMIT 1
            ) OR (
                SELECT price 
                FROM price_of_product 
                WHERE product_id = {product_id} 
                ORDER BY `date` DESC 
                LIMIT 1
            ) != {new_price};
    '''
    """
    query = '''
        INSERT INTO price_of_product (product_id, price)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE price = VALUES(price);
    '''
    data = (product_id, new_price)
    try:
        cur.cursor.execute(query, data)
    except Error as e:
        print(e)


# Функции добавления объектов в БД
def add_iphone(title, full_name, line, memory, sim, colors: tuple, diagonal, description, sku_ya_shop: tuple = None):
    """
    Проверяет есть ли продукт в таблице sku_of_product
    и если есть
        Обновляет product, product_in_line, description_of_product
    иначе
        Добавляет записи в таблицы product, product_in_line, description_of_product, sku_of_productа
    НЕ устанавливает цену.

    :param title:
    :param full_name:
    :param line:
    :param memory:
    :param sim:
    :param colors:
    :param diagonal:
    :param description:
    :param sku_ya_shop: ('shop_prefix', 'sku_ya_market')
    :return: product_id
    """
    cur = CursorDB()

    # Проверяем есть ли продукт с таким sku

    shop_prefix, sku = sku_ya_shop
    query = f"SELECT product_id FROM sku_of_product WHERE {shop_prefix.lower()}_sku = '{sku}'"
    cur.cursor.execute(query)
    product_id = cur.cursor.fetchone()
    product_id = product_id[0] if product_id else None

    # либо обновляем информацию, либо создаём новые записи
    if product_id:
        print(f'Запись о: {title} : id {product_id} - уже существует в БД. Обновляем информацию')
        query = f"UPDATE product SET title = %s, full_name = %s WHERE id = %s"
        data = (title, full_name, product_id)
        # print(query % data)
        cur.cursor.execute(query, data)

        query = 'UPDATE product_in_line SET line = %s WHERE product_id = %s'
        data = (line, product_id)
        cur.cursor.execute(query, data)

        query = ''' 
            INSERT INTO description_of_product (product_id, description)         
            VALUES (%s, %s) 
            ON DUPLICATE KEY UPDATE description = %s;
        '''
        data = (product_id, description, description)
        cur.cursor.execute(query, data)

    else:  # Создаём новые записи
        print(f'Добавляем {title} в базу данных')

        # Добавляем продукт в product
        query = 'INSERT INTO product (title, full_name) VALUES (%s, %s);'
        data = (title, full_name)
        try:
            cur.cursor.execute(query, data)
            product_id = cur.cursor.lastrowid
        except Error as e:
            print(e)
            if e.errno == 1062:  # дубликат уникального значения (title или slug)
                query = f"SELECT id FROM product WHERE title LIKE '%{title}%'"

                cur.cursor.execute(query)
                product_id = cur.cursor.fetchone()[0]
                if e.msg.split()[-1] == 'title':  # Если пробелема в дубликате title,
                    pass

                print(f'В таблице product уже существует запись с title: {title}\n id = {product_id}')
                # answer = input('Обновить информацию о этой записи? Нажмите Enter для обновления'
                #                ' или введите любой символ для отмены. ')
                answer = ''
                update_this_entry = False if answer else True
                if not update_this_entry:
                    return

        # Добавляем продукт в product_in_line
        query = 'INSERT INTO product_in_line (line, product_id) VALUES (%s, %s)'
        data = (line, product_id)
        try:
            cur.cursor.execute(query, data)
        except Error as e:
            # if e.errno == 1062:

            print(e)

        # Добавляем ску продукта
        query = f"INSERT INTO sku_of_product (product_id, {shop_prefix.lower()}_sku) VALUES ({product_id}, '{sku}')"
        try:
            cur.cursor.execute(query)
        except Error as e:
            print(e)

    return product_id


def add_mac(title, full_name, line, description, sku_ya_shop: tuple = None):
    """
        Проверяет есть ли продукт в таблице sku_of_product
        и если есть
            Обновляет product, product_in_line, description_of_product
        иначе
            Добавляет записи в таблицы product, product_in_line, description_of_product, sku_of_productа
        НЕ устанавливает цену.

        :param title:
        :param full_name:
        :param line:
        :param description:
        :param sku_ya_shop: ('shop_prefix', 'sku_ya_market')
        :return: product_id
        """
    cur = CursorDB()

    # Проверяем есть ли продукт с таким sku

    shop_prefix, sku = sku_ya_shop
    query = f"SELECT product_id FROM sku_of_product WHERE {shop_prefix.lower()}_sku = '{sku}'"
    cur.cursor.execute(query)
    product_id = cur.cursor.fetchone()
    product_id = product_id[0] if product_id else None
    if product_id:  # обновляем данные
        print(f'Запись о: {title} : id {product_id} - уже существует в БД. Обновляем информацию')
        query = f"UPDATE product SET title = %s, full_name = %s WHERE id = %s"
        data = (title, full_name, product_id)
        # print(query % data)
        cur.cursor.execute(query, data)

        query = 'UPDATE product_in_line SET line = %s WHERE product_id = %s'
        data = (line, product_id)
        cur.cursor.execute(query, data)

        query = 'UPDATE description_of_product SET description = %s WHERE product_id = %s'
        data = (description, product_id)
        cur.cursor.execute(query, data)

    else:  # добавляем новую запись
        print(f'Добавляем {title} в базу данных')

        # Добавляем продукт в product
        query = 'INSERT INTO product (title, full_name) VALUES (%s, %s);'
        data = (title, full_name)
        try:
            cur.cursor.execute(query, data)
            product_id = cur.cursor.lastrowid
        except Error as e:
            print(e)

        # Добавляем продукт в product_in_line
        query = 'INSERT INTO product_in_line (line, product_id) VALUES (%s, %s)'
        data = (line, product_id)
        try:
            cur.cursor.execute(query, data)
        except Error as e:
            print(e)

        # Добавляем ску продукта
        query = f"INSERT INTO sku_of_product (product_id, {shop_prefix.lower()}_sku) VALUES ({product_id}, '{sku}')"
        try:
            cur.cursor.execute(query)
        except Error as e:
            print(e)

    return product_id


def test():
    # установка изобрадений для товара в базе данных
    query = '''
        INSERT INTO img_of_product (product_id, number_of_image, name_of_img)
        SELECT id, 3, 'iphone-14-starlight-3.webp'
        FROM product
        WHERE title LIKE '%iPhone 14,%' 
        AND title LIKE '%starlight%'
        ON DUPLICATE KEY UPDATE name_of_img = 'iphone-14-starlight-3.webp';
    '''


def example():
    cur = CursorDB()
    query = '''
        
        '''
    data = ()
    try:
        cur.cursor.execute(query, data)
    except Error as e:
        print(e)

    price = cur.cursor.fetchone()


def main():
    # update_price(4419, 126)
    # get_products_in_line('iPhone 14')
    # get_category_and_lines_by_line('iPhone 16 Pro')
    # get_lines_and_products_in_category('iPad')
    # get_info_product_for_cart(100)
    # print(get_info_product('iphone-14-128-gb-nanosim-esim-blue'))
    print(get_info_product('iphone-15-128-gb-nanosim-nanosim-black'))


if __name__ == '__main__':
    main()
    # cur = CursorDB()
    # print(get_info_product('iphone-se-2022-128-gb-midnight'))
    # print(get_lines_and_products_in_category('iphone'))
    # print(get_products_in_line('iphone se 2022'))
    # print(get_category_and_lines_by_line('iphone se 2022'))
    # print(get_info_product_for_cart(492))
    # get_actual_price_of_product(492)
    # product = get_info_product_by_slug('iphone-se-2022-128-gb-starlight')
    # print(product)
    # selected_characteristic = {'memory_ssd': ['128 Gb', '64 Gb']}
    # get_products_in_line('iphone-se', selected_characteristic)
