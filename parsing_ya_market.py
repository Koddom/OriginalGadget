import requests
import json
import csv
import re
import sys

'''
{
    [
        "id": 91491,
        "name": "Мобильные телефоны"
    ],
    [
        
    ]
}
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

    return memory


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

# конец Форматные функции


def parsing_list_of_product_as_iphone(list_of_products):
    """

    """
    products = []
    counter = 1
    for item in list_of_products:
        sku = item['offer']['offerId']
        title = item['mapping']['marketSkuName']
        title = title.replace('Смартфон Apple ', '')
        price = int(item['offer']['basicPrice']['value'])

        title = replace_letter_of_memory(title)  # пишем нормальные буквы для памяти и заменяем цвет RED в названии

        line = define_line_for_iphone(title)
        pictures = item['offer']['pictures']
        color_in_product = title.split(',')[-1]
        color, color_ru, color_filter = define_color(color_in_product)
        title = title.replace(color_in_product, ' '+color_ru) + ' | ' + color  # заменяем английский цвет на русский

        if 'description' in item['offer']:
            description = item['offer']['description']
        else:
            description = ''
            print('!!! Нет описания')

        screen_diagonal = define_sceen_diagonal(title)
        memory = define_memory(title)
        sim = define_sim_for_iphone(title)

        print(counter, end=' - ')
        counter += 1
        title = ', '.join([line, memory, sim, color]) + ' | ' + color_ru
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


def get_goods_iphones():
    """
    Сначала получаем самую старую страницу с товарами (потому-что не передан идентификатор страницы)
     и извлекаем из неё next_page_token. Получаем последующие страницы, до тех пор пока есть next_page_token.
    :return:
    """
    business_id = 96421931
    url = f'https://api.partner.market.yandex.ru/businesses/{business_id}/offer-mappings'

    # Формируем параметры для получения необходимой выборки
    body = {
        "vendorNames": ["Apple"],
        "categoryIds": ["91491"],  # Мобильные телефоны
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

        parsing_list_of_product_as_iphone(list_of_products)  # форматируем список для получения нужных данных

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

            parsing_list_of_product_as_iphone(list_of_products)

        else:
            print(f'Ошибка запроса к серверу yandex-market: {response.status_code}')
            print(response.text)
            return

        answer = input('Жмакни enter или q')
        if answer == 'q':
            break


def main():
    get_goods_iphones()


if __name__ == '__main__':
    main()
