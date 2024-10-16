import mysql.connector
from mysql.connector import Error

import settings


def create_schema(cursor):
    # СПРАВОЧНИКИ
    # продукты
    query = '''CREATE TABLE IF NOT EXISTS product(
                    id INT UNSIGNED AUTO_INCREMENT,
                    title CHAR(255) NOT NULL UNIQUE,
                    slug char(255) NOT NULL UNIQUE,
                    full_name char(255),
                    is_available TINYINT(1) NOT NULL DEFAULT 1,
                    PRIMARY KEY (id)
                );
    '''
    cursor.execute(query)

    # Создание функции create-slug
    # Данная функция оставляет только английские буквы и пробелы заменяет на -
    query = 'DROP FUNCTION IF EXISTS `create-slug`;'
    cursor.execute(query)
    query = '''
    CREATE FUNCTION `create-slug`(input VARCHAR(255)) RETURNS VARCHAR(255) CHARSET utf8mb4
    BEGIN
        DECLARE output VARCHAR(255) DEFAULT '';
        DECLARE i INT DEFAULT 1;
        DECLARE c CHAR(1);
        DECLARE prev_char CHAR(1) DEFAULT '';  -- переменная для хранения предыдущего символа
        
        WHILE i <= CHAR_LENGTH(input) DO
            SET c = SUBSTRING(input, i, 1);
            
            -- Добавляем символ, если это буква или цифра
            IF c REGEXP '[a-zA-Z0-9]' THEN
                SET output = CONCAT(output, c);
                SET prev_char = c;  -- Обновляем предыдущий символ
            -- Если это пробел, добавляем дефис, только если предыдущий символ не дефис
            ELSEIF c = ' ' AND prev_char != '-' THEN
                SET output = CONCAT(output, '-');
                SET prev_char = '-';  -- Обновляем предыдущий символ как дефис
            END IF;
            
            SET i = i + 1;
        END WHILE;
        
        -- Удаляем дефисы в начале и конце строки
        RETURN TRIM(BOTH '-' FROM output);
    END
    '''
    cursor.execute(query)

    query = 'DROP TRIGGER IF EXISTS before_insert_product;'
    cursor.execute(query)

    query = 'DROP TRIGGER IF EXISTS before_update_product;'
    cursor.execute(query)

    # Создание триггера before_insert_product
    # формирование и обновление slug
    query = '''
    CREATE TRIGGER before_insert_product
    BEFORE INSERT ON product
    FOR EACH ROW
    BEGIN
      SET NEW.slug = LOWER(REPLACE(`create-slug`(NEW.title), ' ', '-'));
    END;
    '''
    cursor.execute(query)

    # Создание триггера before_update_product
    # - формирование и обновление slug
    query = '''
    CREATE TRIGGER before_update_product
    BEFORE UPDATE ON product
    FOR EACH ROW
    BEGIN
        SET NEW.slug = LOWER(REPLACE(`create-slug`(NEW.title), ' ', '-'));
    END;
    '''
    cursor.execute(query)

    # справочник категория
    query = '''CREATE TABLE IF NOT EXISTS category(
                title CHAR(255),	
                position INT,
                PRIMARY KEY (title)			
        )
    '''

    cursor.execute(query)


    # справочник группа товаров
    # query = '''CREATE TABLE IF NOT EXISTS group_of_product(
    #                             id INT,
    #                             title CHAR(255),
    #                             PRIMARY KEY (id)
    #                     )
    #                 '''
    # cursor.execute(query)

    # справочник тип характеристики
    query = '''CREATE TABLE IF NOT EXISTS type_of_characteristic(
                        characteristic CHAR(255),
                        PRIMARY KEY (characteristic)
                )
            '''
    cursor.execute(query)

    # справочник значения для характеристик
    query = '''CREATE TABLE IF NOT EXISTS value_for_characteristic(
                title CHAR(255),
                PRIMARY KEY (title)
            );
    '''
    cursor.execute(query)

    # //////////// РЕГИСТРЫ СВЕДЕНИЙ ////////////
    # регистр сведений значений характеристик
    query = '''CREATE TABLE IF NOT EXISTS value_of_characteristic(
                        characteristic CHAR(255),
                        `value` CHAR(255),
                        PRIMARY KEY (characteristic, value),
                        FOREIGN KEY (`value`) REFERENCES original_gadget.value_for_characteristic(title)
                            ON DELETE CASCADE
                            ON UPDATE CASCADE,
                        FOREIGN KEY (characteristic) REFERENCES original_gadget.type_of_characteristic(characteristic) 
                            ON DELETE CASCADE
                            ON UPDATE CASCADE
                )
            '''
    cursor.execute(query)

    # регистр сведений характеристики продукта
    query = '''CREATE TABLE IF NOT EXISTS characteristic_of_product(
                    product_id INT UNSIGNED,
                    characteristic CHAR(255),
                    `value` CHAR(255),
                    PRIMARY KEY (product_id, characteristic),
                    FOREIGN KEY (product_id) REFERENCES original_gadget.product(id) 
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    FOREIGN KEY (characteristic) REFERENCES original_gadget.type_of_characteristic(characteristic)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    FOREIGN KEY (`value`) REFERENCES original_gadget.value_for_characteristic(title) 
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                )
            '''
    cursor.execute(query)

    # регистр сведений основные характеристики категории
    query = '''CREATE TABLE IF NOT EXISTS basic_of_characteristic(
            category CHAR(255),
            characteristic CHAR(255),
            PRIMARY KEY (category, characteristic),
            FOREIGN KEY (category) REFERENCES original_gadget.category(title) 
                ON DELETE CASCADE 
                ON UPDATE CASCADE,
            FOREIGN KEY (characteristic) REFERENCES original_gadget.type_of_characteristic(characteristic)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
    '''
    cursor.execute(query)

    # регистр сведений линейка(поколение) продукта в разрезе категории
    query = '''CREATE TABLE IF NOT EXISTS product_line(
                category CHAR(255) NOT NULL,
                line CHAR(255) NOT NULL UNIQUE,
                line_position INT,
                PRIMARY KEY (category, line),
                FOREIGN KEY (category) REFERENCES original_gadget.category(title) 
                    ON DELETE CASCADE 
                    ON UPDATE CASCADE
                -- INDEX idx_line (line)  -- индексация поля line для внешнего ключа для таблицы product_in_line
            );
    '''
    cursor.execute(query)

    # регистр сведений продукты в линейке
    query = '''CREATE TABLE IF NOT EXISTS product_in_line(
                    line CHAR(255) NOT NULL ,
                    product_id INT UNSIGNED UNIQUE,
                    PRIMARY KEY (line, product_id),
                    FOREIGN KEY (line) REFERENCES original_gadget.product_line(line)
                        ON DELETE CASCADE 
                        ON UPDATE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES original_gadget.product(id) 
                        ON DELETE CASCADE
                        ON UPDATE CASCADE		
                );
    '''
    cursor.execute(query)

    # регистр сведений продукты в группе
    # query = '''CREATE TABLE IF NOT EXISTS product_in_group(
    #                     `group` CHAR(255),
    #                     product_id INT UNSIGNED,
    #                     PRIMARY KEY (`group`, product_id),
    #                     FOREIGN KEY (product_id) REFERENCES original_gadget.product(id) ON DELETE CASCADE
    #                 )
    #         '''
    # cursor.execute(query)

    # регистр сведений стоимость продукты
    query = '''
    CREATE TABLE IF NOT EXISTS price_of_product(
        product_id INT UNSIGNED,
        `date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        price INT(10) UNSIGNED NOT NULL,
        PRIMARY KEY (product_id, `date`),
        FOREIGN KEY (product_id) REFERENCES original_gadget.product(id) ON DELETE CASCADE ON UPDATE CASCADE		
    )
    '''
    cursor.execute(query)

    # регистр сведений изображение продукта
    query = '''
    CREATE TABLE IF NOT EXISTS img_of_product(
        product_id INT UNSIGNED,
        number_of_image INT NOT NULL,
        name_of_img CHAR(255),
        PRIMARY KEY (product_id, number_of_image),
        FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    '''
    cursor.execute(query)

    # Дополнительные таблицы
    # Таблица с описанием продукта
    query = '''
    CREATE TABLE IF NOT EXISTS description_of_product(
        product_id INT UNSIGNED,
        description TEXT,
        PRIMARY KEY (product_id),
        FOREIGN KEY (product_id) REFERENCES original_gadget.product(id) ON DELETE CASCADE ON UPDATE CASCADE
    );
    '''
    cursor.execute(query)

    query = '''
        CREATE TABLE IF NOT EXISTS sku_of_product(
            product_id INT UNSIGNED,
            sm_sku CHAR(255) UNIQUE,
            og_sku CHAR(255) UNIQUE,
            pd_sku CHAR(255) UNIQUE,
            PRIMARY KEY (product_id),
            FOREIGN KEY (product_id) REFERENCES original_gadget.product(id) ON DELETE CASCADE ON UPDATE CASCADE
        );
        '''
    cursor.execute(query)


def create_basic_data(cursor):
    # Заполняем справочник категорий товаров
    categories = [
        (0, 'Mac'),
        (1, 'iPad'),
        (2, 'iPhone'),
        (3, 'Watch'),
        (4, 'AirPods'),
        (5, 'TV & Home')
    ]
    query = '''INSERT IGNORE INTO category (position, title) VALUES (%s, %s)
    '''
    cursor.executemany(query, categories)

    # Создаём линейки(поколения) продуктов в категориях
    # Упорядочивание элементов происходит по уменьшению
    product_line = [
        (200, 'Mac', 'MacBook Air'),
        (201, 'Mac', 'MacBook Air'),
        (202, 'Mac', 'MacBook Pro'),
        (203, 'Mac', 'iMac'),
        (204, 'Mac', 'Mac mini'),
        (205, 'Mac', 'Mac Studio'),
        (206, 'Mac', 'Mac Pro'),

        (0, 'iPhone', 'iPhone SE',),
        (1, 'iPhone', 'iPhone 12',),
        (2, 'iPhone', 'iPhone 12 mini',),
        (3, 'iPhone', 'iPhone 13',),
        (4, 'iPhone', 'iPhone 13 Pro',),
        (5, 'iPhone', 'iPhone 13 Pro Max',),
        (6, 'iPhone', 'iPhone 14',),
        (7, 'iPhone', 'iPhone 14 plus',),
        (8, 'iPhone', 'iPhone 14 Pro',),
        (9, 'iPhone', 'iPhone 14 Pro Max',),
        (10, 'iPhone', 'iPhone 15',),
        (11, 'iPhone', 'iPhone 15 Plus',),
        (12, 'iPhone', 'iPhone 15 Pro',),
        (13, 'iPhone', 'iPhone 15 Pro Max',),
        (14, 'iPhone', 'iPhone 16',),
        (15, 'iPhone', 'iPhone 16 Plus',),
        (16, 'iPhone', 'iPhone 16 Pro',),
        (17, 'iPhone', 'iPhone 16 Pro Max',),

        (101, 'iPad', 'iPad mini'),
        (102, 'iPad', 'iPad'),
        (103, 'iPad', 'iPad Air'),
        (104, 'iPad', 'iPad Pro'),

    ]

    query = ''' INSERT IGNORE INTO product_line (line_position, category, line) VALUES (%s, %s, %s)'''
    cursor.executemany(query, product_line)

    # Заполняем таблицу тип характеристики
    characteristics = [
        ('color',),
        ('sim',),
        ('memory_ssd',),
        ('memory_ram',),
        ('screen_diagonal',),
        ('cellular_slot',)
    ]
    query = ''' INSERT IGNORE INTO type_of_characteristic VALUES (%s)
    '''
    cursor.executemany(query, characteristics)

    # Указываем какими значениями могут обладать каждая из характеристик
    values_of_characteristics = {
        'color': 'white, black, red, green, blue, yellow, silver, pink'.split(', '),
        'sim': 'nanoSIM + eSIM, nanoSIM + nanoSIM, eSIM'.split(', '),
        'memory_ssd': '64 Gb, 128 Gb, 256 Gb, 512 Gb, 1 Tb'.split(', '),
        'screen_diagonal': '4.7, 5.4, 6.1, 6.7, 12, 13, 14, 15'.split(', '),
        'cellular_slot': 'wi-fi, wi-fi + cellular'.split(', ')
    }

    # Формируем список всех возможных значений характеристик
    values_for_characteristic = []
    for characteristic in values_of_characteristics:
        for value in values_of_characteristics[characteristic]:
            values_for_characteristic.append((value,))

    # Сначала записываем все возможные значения характеристик
    query = '''INSERT IGNORE INTO value_for_characteristic (title) VALUES (%s)'''
    cursor.executemany(query, values_for_characteristic)


    values = []
    for characteristic in values_of_characteristics:
        for value in values_of_characteristics[characteristic]:
            text = f"('{characteristic}', '{value}')"
            values.append(text)

    # Заполняем возможные значения для каждой характеристики
    query = 'INSERT IGNORE INTO value_of_characteristic VALUES ' + ', '.join(values)

    cursor.execute(query)

    # Заполняем таблицу базовые характеристики для категории товаров
    lines = {
        'iphone': 'color memory_ssd screen_diagonal'.split(),
        'ipad': 'color memory cpu screen_diagonal cellular_slot year'.split(),
        'mac': 'color memory_ssd memory_ram screen_diagonal cpu year'.split(),
    }

    values = []
    for line in lines:
        for characteristic in lines[line]:
            text = f"('{line}', '{characteristic}')"
            values.append(text)

    query = 'INSERT IGNORE INTO basic_of_characteristic VALUES ' + ', '.join(values)

    cursor.execute(query)


def main():
    config = settings.connection_config_to_db
    connect = mysql.connector.connect(**config)
    cursor = connect.cursor()
    cursor.execute('CREATE DATABASE IF NOT EXISTS original_gadget CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;')
    cursor.execute('USE original_gadget')

    create_schema(cursor)
    create_basic_data(cursor)
    connect.close()


if __name__ == '__main__':
    main()
