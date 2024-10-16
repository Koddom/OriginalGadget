import requests
import json
import csv
import re
import sys
import query_to_db

'''
[
    {
        "id": 91491,
        "name": "Мобильные телефоны"
    },
    {
        "id": 6427100,
        "Планшеты": "Планшеты"   
    }
]
'''
TOKEN = 'y0_AgAAAAA13VXGAAvz6QAAAAEHf7cVAAAB69pht3BEXrh32mlfvcdJRy7noQ'


headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}


# Форматные функции
def replace_letter_of_memory(title):
    pattern_gb = r'(ГБ|Гб|гб|гБ|GB|Gb|gb|gB)'
    match = re.search(pattern_gb, title)
    if match:
        title = title.replace(match.group(1), 'Gb')

    pattern_tb = r'(ТБ|Тб|Tb|TB)'
    match = re.search(pattern_tb, title)
    if match:
        title = title.replace(match.group(1), 'Tb')

    if '(PRODUCT)RED' in title:
        title = title.replace('(PRODUCT)RED', 'красный')

    return title


def define_line_for_iphone(title):
    """До памяти указывается линейка телефона"""
    pattern = r'(.+?)\s+(\d+\s*(ТБ|ГБ|Тб|tb|Гб|Gb|gb|Tb|GB|TB))'
    match = re.search(pattern, title)
    if match:
        line = match.group(1).strip()
    else:
        input(title, 'define_line_for_iphone')
    return line


def define_color(color):

    color = color.strip().lower()
    if color in ['сияющая звезда', 'starlight']:
        color = 'Starlight'
        color_rus = 'Сияющая Звезда'
        color_filter = 'white'
    elif color in ['тёмная ночь', 'темная ночь', 'midnight']:
        color = 'Midnight'
        color_rus = 'Тёмная Ночь'
        color_filter = 'black'
    elif color in ['синий', 'blue', 'голубой']:
        color = 'Blue'
        color_rus = 'Синий'
        color_filter = 'blue'
    elif color in ['розовый', 'pink']:
        color = 'Pink'
        color_rus = 'Розовый'
        color_filter = 'pink'
    elif color in ['(product)red', 'красный']:
        color = '(PRODUCT)RED'
        color_rus = 'Красный'
        color_filter = 'red'
    elif color in ['золотой', 'gold']:
        color = 'Gold'
        color_rus = 'Золотой'
        color_filter = 'yellow'
    elif color in ['желтый', 'yellow']:
        color = 'Yellow'
        color_rus = 'Жёлтый'
        color_filter = 'yellow'
    elif color in ['глубокий фиолетовый', 'deep purple']:
        color = 'Deep Purple'
        color_rus = 'Глубокий Фиолетовый'
        color_filter = 'purple'
    elif color in ['space gray', 'космический серый', 'серый космос']:
        color = 'Space Gray'
        color_rus = 'Космический серый'
        color_filter = 'Gray'
    elif color in ['космический черный', 'космический чёрный', 'space black']:
        color = 'Space Black'
        color_rus = 'Космический Чёрный'
        color_filter = 'black'
    elif color in ['титан', 'натуральный титан', 'natural titanium', 'серый титан']:
        color = 'Natural Titanium'
        color_rus = 'Натуральный Титан'
        color_filter = 'white'
    elif color in ['черный титан', 'black titanium']:
        color = 'Black Titanium'
        color_rus = 'Чёрный Титан'
        color_filter = 'black'
    elif color in ['белый титан', 'white titanium']:
        color = 'White Titanium'
        color_rus = 'Белый Титан'
        color_filter = 'white'
    elif color in ['синий титан', 'blue titanium']:
        color = 'Blue Titanium'
        color_rus = 'Синий Титан'
        color_filter = 'blue'
    elif color in ['purple', 'фиолетовый']:
        color = 'Purple'
        color_rus = 'Фиолетовый'
        color_filter = 'purple'
    elif color in ['серебристый', 'silver']:
        color = 'Silver'
        color_rus = 'Серебристый'
        color_filter = 'white'
    elif color in ['черный', 'чёрный', 'black']:
        color = 'Black'
        color_rus = 'Чёрный'
        color_filter = 'black'
    elif color in ['белый', 'white']:
        color = 'White'
        color_rus = 'Белый'
        color_filter = 'white'
    elif color in ['зелeный', 'зелёный', 'green', 'зеленый']:
        color = 'Green'
        color_rus = 'Зелёный'
        color_filter = 'green'
    elif color in ['белый', 'white']:
        color = 'White'
        color_rus = 'Белый'
        color_filter = 'white'
    elif color in ['альпийский зелёный', 'альпийский зеленый', 'alpine green']:
        color = 'Alpine Green'
        color_rus = 'Альпийский Зелёный'
        color_filter = 'green'
    elif color in ['пустынный титан']:
        color = 'Desert Titanium'
        color_rus = 'Пустынный титан'
        color_filter = 'yellow'
    elif color in ['ультрамарин']:
        color = 'Ultramarine'
        color_rus = 'Ультрамарин'
        color_filter = 'blue'
    elif color in ['бирюзовый']:
        color = 'Teal'
        color_rus = 'Бирюзовый'
        color_filter = 'green'
    else:
        # update_name(sku, name)
        return '', '', ''
        sys.exit(color + ' <- Не обнаружен. Программа Завершена')

    return color, color_rus, color_filter


def define_year(title):
    pattern = r'(\d{4})'
    match = re.search(pattern, title)
    if match:
        year = match.group(1)
    else:
        year = 0000

    return int(year)


def define_sceen_diagonal(title):
    """Определяет диагональ для iphone и mac"""
    title = title.lower()
    if 'ipad' in title:
        year = define_year(title)
        # берём значение указанное перед годом
        title = title.replace(',', '', title.count(','))
        try:
            index = title.split().index(str(year))
            diagonal = title.split()[index - 1].replace(',', '.')
            diagonal = float(diagonal)
            return diagonal
        except:
            print('Пробуем определить диагональ по другому')

        if 'mini' in title:
            diagonal = 6.0
        elif 'air' in title:
            if year == 2022:
                diagonal = 10.9

        return diagonal

    elif 'iphone' in title:
        line = define_line_for_iphone(title).lower()

        if line in ['iphone se 2022', 'iphone se 2020']:
            screen_diagonal = '4.7'
        elif line in ['iphone 12 mini', 'iphone 13 mini']:
            screen_diagonal = '5.4'
        elif line in ['iphone 11', 'iphone 12', 'iphone 13', 'iphone 13 pro', 'iphone 14', 'iphone 14 pro', 'iphone 15',
                      'iphone 15 pro', 'iphone 16']:
            screen_diagonal = '6.1'
        elif line in ['iphone 13 pro max', 'iphone 14 plus', 'iphone 14 pro max', 'iphone 15 plus',
                      'iphone 15 pro max', 'iphone 16 plus']:
            screen_diagonal = '6.7'
        elif line in ['iphone 16 pro']:
            screen_diagonal = '6.3'
        elif line in ['iphone 16 pro max']:
            screen_diagonal = '6.9'

        return float(screen_diagonal)


def define_memory(title):
    """

    :param title:
    :return: 128 Gb или 1 Tb
    """
    title = title.replace(',', '', title.count(','))
    # если до букв не стоит пробел, добавляем пробел
    if title[title.find('Gb') - 1] != ' ':
        title = title.replace('Gb', ' Gb')
    if 'Gb' in title:
        memory = title.split()[title.split().index('Gb') - 1] + ' Gb'
    elif 'Tb' in title:
        memory = title.split()[title.split().index('Tb') - 1] + ' Tb'

    if 'memory' in locals():
        return memory
    else:
        print(title)


def define_sim_for_iphone(title):
    title = title.lower().replace('е', 'e')
    if any(substring in title for substring in ('nano sim + esim',)):
        return 'nanoSIM + eSIM'
    if any(substring in title for substring in ('nano sim', 'nano-sim')):
        return 'nanoSIM + nanoSIM'
    elif any(substring in title for substring in('esim', 'еsim')):
        return 'eSIM'
    else:
        input(title)


# Форматные функции для ipad
def create_norm_title_for_ipad(title: str):
    title = title.replace('Планшет ', '')
    title = title.replace('Apple ', '')

    index = title.find('"', 0, 10)
    if index >= 0:
        title = title[index+1:None].strip()

    title = replace_letter_of_memory(title)

    title = title.replace('iPadOS, ', '')

    return title


def define_line_for_ipad(title: str):
    title = title.lower()
    if 'pro' in title:
        line = 'iPad Pro'
    elif 'air' in title:
        line = 'iPad Air'
    elif 'mini' in title:
        line = 'iPad mini'
    else:
        line = 'iPad'

    return line


def define_processor(title):
    if 'ipad' in title.lower():
        pattern = r'(M\d)'
        match = re.match(pattern, title)
        if match:
            processor = match.group(1)
            return processor

        year = define_year(title)
        if ('mini' in title.lower()) and (year == 2021):
            return 'A15 Bionic'
        elif ('air' in title.lower()) and (year == 2024):
            return 'M2'
        elif ('air' in title.lower()) and (year == 2022):
            return 'M1'
        elif ('pro' in title.lower()) and (year == 2024):
            return 'M4'
        elif ('pro' in title.lower()) and (year == 2022):
            return 'M2'
        elif ('ipad' in title.lower()) and (year == 2022):
            return 'A14 Bionic'
        elif ('ipad' in title.lower()) and (year == 2021):
            return 'A13 Bionic'
        else:
            input('Не обнаружен процессор')

# конец Форматные функции


def parsing_list_of_product_as_iphone(list_of_products):
    """

    """
    products = []
    counter = 1
    for item in list_of_products:
        sku = item['offer']['offerId']
        title = item['mapping']['marketSkuName']
        if title == 'Смартфон Apple iPhone 16 256 Gb nanoSIM+esim белый white':
            print(title)
        title = title.replace('Смартфон Apple ', '')
        price = int(item['offer']['basicPrice']['value'])

        title = replace_letter_of_memory(title)  # пишем нормальные буквы для памяти и заменяем цвет RED в названии

        line = define_line_for_iphone(title)
        pictures = item['offer']['pictures']
        color_in_product = title.split(',')[-1]  # цвет в названии обязательно должен отделяться запятой
        color, color_ru, color_filter = define_color(color_in_product)
        if not color:
            print('Не удалось определить цвет')
            input()
            continue
        title = title.replace(color_in_product, ' '+color_ru) + ' | ' + color  # заменяем английский цвет на русский

        if 'description' in item['offer']:
            description = item['offer']['description']
        else:
            description = ''
            print('!!! Нет описания')

        screen_diagonal = define_sceen_diagonal(title)
        if title == '  | ':
            print(title)
        memory = define_memory(title)
        sim = define_sim_for_iphone(title)

        print(counter, end=' - ')
        counter += 1
        title = ', '.join([line, memory, sim, color]) + ' | ' + color_ru
        print('-------------------------')
        print('title', title, sep=': ')
        print('sku', sku, sep=': ')
        print('line', line, sep=': ')
        print('memory', memory, sep=': ')
        print('sim', sim, sep=': ')
        print('color', color, color_ru, color_filter, sep=': ')
        print('price', price, sep=': ')
        print('diagonal', screen_diagonal, sep=': ')
        print('description', description, sep=': ')

        print('-------------', end='\n\n')
        full_name = 'Смартфон Apple ' + title
        sku_ya_shop = ('SM', sku)
        colors = (color, color_ru, color_filter)
        print('------')

        product_id = query_to_db.add_iphone(title, full_name, line, memory, sim, colors, screen_diagonal, description, sku_ya_shop)
        query_to_db.update_price(product_id, price)


def parsing_list_of_product_as_ipad(list_of_products):
    products = []
    counter = 1
    for item in list_of_products:
        sku = item['offer']['offerId']
        title = item['mapping']['marketSkuName']

        title = create_norm_title_for_ipad(title)

        line = item['mapping']['marketModelName']
        pictures = item['offer']['pictures']
        color_in_product = title.split(',')[-1].strip()
        color, color_ru, color_filter = define_color(color_in_product)
        title = title.replace(color_in_product, color_ru) + ' | ' + color  # заменяем английский цвет на русский

        line = define_line_for_ipad(title)

        price = int(item['offer']['basicPrice']['value'])
        if 'description' in item['offer']:
            description = item['offer']['description']
        else:
            # print('!!! Нет описания')
            description = ''

        # special characteristic
        year = define_year(title)
        screen_diagonal = define_sceen_diagonal(title)
        processor = define_processor(title)
        memory = define_memory(title)
        has_cellular = 'cellular' in title.lower()
        cellular = 'Wi-Fi + Cellular' if has_cellular else 'Wi-Fi'

        colors = (color, color_ru, color_filter)

        title = f'{line} {screen_diagonal}", {year}, {processor}, {memory}, {cellular}, {color}'
        full_name = 'Планшет Apple ' + title + ' | ' + color_ru

        # printing
        print(counter, end=' - ')
        counter += 1
        print('title', title, sep=': ')
        print('full_name', full_name, sep=': ')
        print('sku', sku, sep=': ')
        print('line', line, sep=': ')
        print('year', year, sep=': ')
        print('color', color, sep=': ')
        print('price', price, sep=': ')
        print('cellular', has_cellular, sep=': ')
        print('diagonal', screen_diagonal, sep=': ')
        print('memory', memory, sep=': ')

        print('-------------', end='\n\n')

        sku_ya_shop = ('SM', sku)
        query_to_db.add_iphone(title, full_name, line, memory, '', colors, screen_diagonal, description, sku_ya_shop)
        # input()


def get_goods_from_ya(category_id: str):
    """
    Получает товары айфоны или айпады с Ямаркета и вызывает функцию для заполнения этими товарами БД.
    Сначала получаем самую старую страницу с товарами (потому-что не передан идентификатор страницы)
     и извлекаем из неё next_page_token. Получаем последующие страницы, до тех пор пока есть next_page_token.
    :return:
    """
    business_id = 96421931
    url = f'https://api.partner.market.yandex.ru/businesses/{business_id}/offer-mappings'

    # Формируем параметры для получения необходимой выборки
    body = {
        "vendorNames": ["Apple"],
        "categoryIds": [category_id],  # Мобильные телефоны
    }

    params = {
        'page_token': None,
        'limit': 200
    }
    response = requests.post(url, params=params, headers=headers, json=body)

    if response.status_code == 200:
        data = response.json()
        list_of_products = data['result']['offerMappings']
        # Если нет токена следующей страницы, значит достигли конца котолога
        next_page_token = data['result']['paging']['nextPageToken'] if data['result']['paging'] else None

        # форматируем список для получения нужных данных и записи их в БД
        if category_id == '91491':  # мобильные телефоны
            parsing_list_of_product_as_iphone(list_of_products)
        elif category_id == '6427100':  # планшеты
            parsing_list_of_product_as_ipad(list_of_products)

    else:
        print(f'Ошибка запроса к серверу yandex-market: {response.status_code}')
        print(response.text)
        return

    while next_page_token:  # нельзя просто так взять и установить next_page_token = 1
        params = {
            'page_token': next_page_token,
            'limit': 200
        }

        response = requests.post(url, params=params, headers=headers, json=body)
        if response.status_code == 200:
            data = response.json()
            list_of_products = data['result']['offerMappings']
            next_page_token = data['result']['paging']['nextPageToken'] if data['result']['paging'] else None

            # форматируем список для получения нужных данных и записи их в БД
            if category_id == '91491':  # мобильные телефоны
                parsing_list_of_product_as_iphone(list_of_products)
            elif category_id == '6427100':  # планшеты
                parsing_list_of_product_as_ipad(list_of_products)

        else:
            print(f'Ошибка запроса к серверу yandex-market: {response.status_code}')
            print(response.text)
            return

        answer = input('Жмакни enter или q')
        if answer == 'q':
            break


def main():
    get_goods_from_ya("91491")  # мобильные телефоны
    get_goods_from_ya("6427100")  # планшеты


if __name__ == '__main__':
    main()
