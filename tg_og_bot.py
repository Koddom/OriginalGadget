from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler, ConversationHandler, CallbackQueryHandler
import re
from pathlib import Path

from settings import TOKEN, ADMIN_LIST

import query_to_db


START_STATE, DOWNLOAD_COST, UPLOAD_COST, CATEGORY_SELECTED, LINE_SELECTED, PRODUCT_SELECTED, EDIT_ITEM = range(7)
CART, NEXT = range(7, 9)

STATIC = './original_gadget/shop/static/img/product-img/'


def slugify(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = re.sub(r'[^a-z0-9-/.]+', '', text)  # Убираем все символы, кроме латинских букв, цифр и дефисов
    text = re.sub(r'-+', '-', text)  # Удаляем возможные подряд идущие дефисы
    text = text.strip('-')
    return text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает стартовое меню
    """
    text = 'Привет! Я официальный бот сайта www.OriginalGadget.ru .\n'
    keyboard = [
        [InlineKeyboardButton('В магазин 🏪', callback_data='shop')],
    ]
    if 'cart' in context.user_data.keys():
        keyboard.append([InlineKeyboardButton('моя корзина 🛒', callback_data='go_to_cart')])

    if update.message.from_user.id in ADMIN_LIST:
        admin_keyboard = [
            [InlineKeyboardButton('Скачать файл с ценами', callback_data='download_cost')],
            [InlineKeyboardButton('Загрузить файл с ценами', callback_data='upload_cost')],
        ]
        keyboard.extend(admin_keyboard)

    reply_markup = InlineKeyboardMarkup(keyboard)
    path_to_photo = './tg_bot/logo.png'
    await update.message.reply_photo(photo=path_to_photo, caption=text, reply_markup=reply_markup)
    # await update.message.reply_text(text=text, reply_markup=reply_markup)

    return START_STATE


async def start_copy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает стартовое меню
    """
    query = update.callback_query
    await query.answer()

    text = 'Привет! Я официальный бот сайта www.OriginalGadget.ru .\n'
    keyboard = [[InlineKeyboardButton('В магазин 🏪', callback_data='shop')]]

    if 'cart' in context.user_data.keys():
        keyboard.append([InlineKeyboardButton('моя корзина 🛒', callback_data='go_to_cart')])

    if query.from_user.id in ADMIN_LIST:
        admin_keyboard = [
            [InlineKeyboardButton('Скачать файл с ценами', callback_data='download_cost')],
            [InlineKeyboardButton('Загрузить файл с ценами', callback_data='upload_cost')],
        ]
        keyboard.extend(admin_keyboard)

    reply_markup = InlineKeyboardMarkup(keyboard)
    path_to_photo = './tg_bot/logo.png'
    with open(path_to_photo, 'rb') as file:
        input_media = InputMediaPhoto(media=file, caption=text)

    await query.edit_message_media(media=input_media, reply_markup=reply_markup)
    return START_STATE


async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    text = 'Выберите категорию.'
    categories = query_to_db.get_all_categories()
    keyboard = [[InlineKeyboardButton(category, callback_data='category=' + category)] for category in categories]
    keyboard.append([InlineKeyboardButton('MAIN MENU', callback_data='home')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    # await query.edit_message_text(text=text, reply_markup=reply_markup)
    path_to_photo = './tg_bot/logo.png'
    with open(path_to_photo, 'rb') as file:
        input_media = InputMediaPhoto(media=file,  caption=text)

    await query.edit_message_media(media=input_media, reply_markup=reply_markup)

    return CATEGORY_SELECTED


async def select_line(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == 'back':
        category = context.user_data['current_category']
    else:
        category = query.data.split('=')[1]
        context.user_data['current_category'] = category

    lines = query_to_db.get_lines_in_category(category)

    text = 'Выберите линейку.'
    keyboard = [[InlineKeyboardButton(line, callback_data='line=' + line)] for line in lines]
    keyboard.append([InlineKeyboardButton('< Назад', callback_data='back')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    path_to_photo = './tg_bot/logo.png'
    with open(path_to_photo, 'rb') as file:
        input_media = InputMediaPhoto(media=file, caption=text)

    # await query.edit_message_text(text=text, reply_markup=reply_markup)
    await query.edit_message_media(media=input_media, reply_markup=reply_markup)

    return LINE_SELECTED


async def show_item_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()
    if query.data == 'back':
        line = context.user_data['current_line']
    else:
        line = query.data.split('=')[1]
        context.user_data['current_line'] = line

    products = query_to_db.get_products_in_line(line)  # {id:, title:, slug:, price:, 'images': [], 'category'}, ...]

    products_id = [product['id'] for product in products]
    context.user_data['products_id'] = products_id

    text = f'Твой {line} на OriginalGadget'

    keyboard = [[InlineKeyboardButton(product['title'].replace(line, '').strip(','), callback_data=product['id'])] for product in products]
    keyboard.append([InlineKeyboardButton('< Назад', callback_data='back')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    path_to_photo = './tg_bot/logo.png'
    with open(path_to_photo, 'rb') as file:
        input_media = InputMediaPhoto(media=file, caption=text)

    # await query.edit_message_text(text=text, reply_markup=reply_markup)
    await query.edit_message_media(media=input_media, reply_markup=reply_markup)

    return PRODUCT_SELECTED


async def show_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает карточку товара
    """

    query = update.callback_query
    await query.answer()

    user_data = context.user_data
    if query.data in ['back', 'add_to_cart', 'remove_from_cart']:
        product_id = user_data['product_id']
    else:
        product_id = int(query.data)
        user_data['product_id'] = product_id

    product = query_to_db.get_info_product(product_id=product_id)

    user_data['price'] = product['price']
    user_data['title'] = product['title']
    user_data['product_images'] = product['images']
    if product['images']:  # если есть изображения
        user_data['current_image'] = product['images'][0]

    text = (f"{product['title']}\n"
            f"цена: {product['price']}\n"
            f"--------------------\n"
            f"{product['description']}")
    try:
        path_to_photo = product['category'] + '/' + product['line']
        path_to_photo = STATIC + '/' + slugify(path_to_photo) + '/' + user_data['current_image']
        with open(path_to_photo, 'rb') as file:
            input_media = InputMediaPhoto(media=file, caption=text)
    except:  # если не получилось открыть файл
        path_to_photo = './tg_bot/no_image.jpg'
        with open(path_to_photo, 'rb') as file:
            input_media = InputMediaPhoto(media=file, caption=text)

    products_id = user_data['products_id']  # список id продуктов в одной линейке ()
    current_index = products_id.index(product_id)
    next_id = products_id[(current_index + 1) % len(products_id)]
    prew_id = products_id[current_index - 1]
    keyboard = [[
        InlineKeyboardButton('Сюда', callback_data=next_id),
        InlineKeyboardButton('🖼', callback_data='next_image',),
        InlineKeyboardButton('Туда', callback_data=prew_id),
    ]]

    if 'cart' in user_data.keys() and product_id in user_data['cart'].keys():
        # if product_id in user_data['cart'].keys():
        keyboard.append([InlineKeyboardButton('🛍 Go to cart', callback_data='go_to_cart')])
        keyboard.append([InlineKeyboardButton('⛔️ Remove from cart', callback_data=f'remove_from_cart')])
    else:
        keyboard.append([InlineKeyboardButton('Add to cart', callback_data='add_to_cart')])

    if query.from_user.id in ADMIN_LIST:
        admin_keyboard = [
            [InlineKeyboardButton('⚙️ Редактировать', callback_data=f'edit_{product_id}')]
        ]
        keyboard.extend(admin_keyboard)

    keyboard.append([InlineKeyboardButton('Назад', callback_data='back')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_media(media=input_media, reply_markup=reply_markup)

    return PRODUCT_SELECTED


async def next_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает следующее изображение товара"""
    query = update.callback_query
    await query.answer()

    if 'product_images' not in context.user_data.keys():  # Если для продукта нет картинок
        return PRODUCT_SELECTED

    current_image = context.user_data['current_image']
    images = context.user_data['product_images']
    index = (images.index(current_image) + 1) % len(images)
    context.user_data['current_image'] = images[index]
    # Получаем текущие caption и клавиатуру
    caption = query.message.caption
    reply_markup = query.message.reply_markup

    try:
        path_to_photo = context.user_data['current_category'] + '/' + context.user_data['current_line']
        path_to_photo = STATIC + '/' + slugify(path_to_photo) + '/' + context.user_data['current_image']
        with open(path_to_photo, 'rb') as file:
            input_media = InputMediaPhoto(media=file, caption=caption)
    except:  # если не получилось открыть файл
        path_to_photo = './tg_bot/no_image.jpg'
        with open(path_to_photo, 'rb') as file:
            input_media = InputMediaPhoto(media=file, caption=caption)

    await query.edit_message_media(media=input_media, reply_markup=reply_markup)

    return PRODUCT_SELECTED


async def show_edit_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data['message_for_update'] = query.message.message_id

    keyboard = [
        [InlineKeyboardButton('Картинка', callback_data='image')],
        [InlineKeyboardButton('Описание', callback_data='description')],
        [InlineKeyboardButton('Цена', callback_data='price')],
        [InlineKeyboardButton('Назад', callback_data='back')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_reply_markup(reply_markup=reply_markup)

    return EDIT_ITEM


async def awaiting_value_for_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    editing_property = query.data
    context.user_data['editing_property'] = editing_property
    if editing_property == 'description':
        text = 'Отправьте новое описание'
    elif editing_property == 'price':
        text = 'Введите новую цену. Можно использовать пробелы.'
    elif editing_property == 'image':
        text = 'Отправьте новое изображение.'

    keyboard = [[InlineKeyboardButton('Отмена', callback_data='delete')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # await query.edit_message_caption(caption=text)
    message = await context.bot.send_message(chat_id=query.from_user.id, text=text, reply_markup=reply_markup)
    context.user_data['message_for_delete'] = message.id

    return EDIT_ITEM


async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

    await update.callback_query.delete_message()


async def set_new_item_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Устанавливает для выбранного свойства значение, которое ввел пользователь"""
    user_data = context.user_data
    current_product_id = user_data['product_id']
    editing_property = user_data['editing_property']

    data = update.message.text
    if editing_property == 'description':
        query_to_db.update_description(current_product_id, description=data)
    elif editing_property == 'price':
        price = re.sub(r"\D", "", data)
        query_to_db.update_price(current_product_id, new_price=price)
    elif editing_property == 'image':
        document = update.message.document
        # Проверяем MIME-тип документа (только изображения)
        if not document.mime_type.startswith("image/"):
            await update.message.reply_text("Это не изображение.")

        file_id = document.file_id  # Получаем file_id документа
        new_file = await context.bot.get_file(file_id)  # Получаем сам файл

        file_name = document.file_name
        path = Path(file_name)
        name = path.stem  # имя файла без расширения
        extension = path.suffix  # расширение файла (с точкой)

        if user_data['product_images']:  # если у продукта есть изображения
            # Сохраняем старое имя файла, но расширение берём у нового.
            number_of_img = user_data['product_images'].index(user_data['current_image']) + 1
            old_name_file = Path(user_data['current_image'])
            name_of_img = old_name_file.stem + extension
        else:  # если у продукта до этого не было изображений
            # Имя файла берём из новых данных добавляем к нему порядковый номер
            number_of_img = 1
            name_of_img = name + '-1' + extension

        category = slugify(user_data['current_category'])
        line = slugify(user_data['current_line'])
        path_to_file = Path(STATIC) / category / line / name_of_img
        await new_file.download_to_drive(path_to_file)  # Скачиваем файл на локальную машину
        query_to_db.update_image(current_product_id, number_of_img, name_of_img)

    else:
        await update.message.reply_text('Что-то пошло не так в set_new_item_value.')

    # удаляем сообщения
    user_id = update.message.from_user.id
    message_for_delete = user_data.pop('message_for_delete')
    await context.bot.delete_message(user_id, message_id=message_for_delete)
    await update.message.delete()


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    product_id = context.user_data.get('product_id')
    title = context.user_data.get('title')
    price = context.user_data.get('price')
    if 'cart' in context.user_data.keys():
        cart = context.user_data['cart']
    else:
        cart = {}
        context.user_data['cart'] = cart  # первый элемент

    cart[product_id] = {
        "title": title,
        "price": price
    }

    state = await show_item(update, context)
    return state


async def remove_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    product_id = context.user_data.get('product_id')
    context.user_data['cart'].pop(product_id)

    state = await show_item(update, context)
    return state


async def show_cart_item_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if 'cart' in context.user_data.keys():
        text = 'Товары готовые к упаковке'

        keyboard = [[InlineKeyboardButton(value['title'], callback_data=product_id)] for product_id, value in context.user_data['cart'].items()]
        keyboard.append([InlineKeyboardButton('MAIN MENU', callback_data='home')])
        keyboard.append([InlineKeyboardButton('🧾 Оформить заказ', callback_data='create_order')])
    else:
        text = 'Ваша корзина пуста'
        keyboard = [[InlineKeyboardButton('MAIN MENU', callback_data='home')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    path_to_photo = './tg_bot/logo.png'
    with open(path_to_photo, 'rb') as file:
        input_media = InputMediaPhoto(media=file, caption=text)

    # await query.edit_message_text(text=text, reply_markup=reply_markup)
    await query.edit_message_media(media=input_media, reply_markup=reply_markup)

    return CART


async def create_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user.username
    user_id = update.effective_user.id

    text = f"@{user} сделал заказ\n"
    n = 1
    full_price = 0
    for product_id, title_and_price in context.user_data['cart'].items():
        text += f"{n}-{title_and_price['title']} - {title_and_price['price']}\n"
        full_price += int(title_and_price['price'])
        n += 1

    text += f'\n-----------------\nИТОГО: {full_price}'

    chat_id = ADMIN_LIST[0]

    await context.bot.send_message(chat_id, text)

    text = ('Ваш заказ отправлен нашему менеджеру @OriginalGadgetMSK. Скоро он с вами свяжется ☺️.'
            'Магазин техники Apple OriginalGadget - 🌇 Из Москвы с любовью ❤️')
    keyboard = [
        [InlineKeyboardButton('OriginalGadget.ru', url='https://originalgadget.ru')],
        [InlineKeyboardButton('YandexMarket', url='https://market.yandex.ru/business--original-gadget/115386042')],
        [InlineKeyboardButton('MAIN MENU', callback_data='home')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_caption(caption=text, reply_markup=reply_markup)
    # await context.bot.send_message(user_id, text, reply_markup=reply_markup)

    context.user_data.pop('cart')


# Функции менеджера
async def get_table_with_cost_from_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает необходимые данные. Формирует файл на сервере и отправляет его."""
    query = update.callback_query
    await query.answer()

    category = query.data.split('=')[1]
    only_available = context.chat_data.pop('only_available')

    # формируем файл с ценами
    file_name = query_to_db.create_file_with_cost(category, only_available)

    # отправляем файл с ценами админу
    chat_id = update.effective_chat.id
    with open(file_name, 'rb') as document:
        await context.bot.send_document(chat_id=chat_id, document=document)

    # удаляем файл с ценами
    # Или не удаляем

    await query.delete_message()

    return ConversationHandler.END


async def select_category_for_table_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список категорий для выбора, на какую необходимо получить таблицу стоимости товаров"""
    query = update.callback_query
    await query.answer()

    categories = query_to_db.get_all_categories()
    keyboard = [[InlineKeyboardButton(category, callback_data='category='+category)] for category in categories]

    if query.data == 'only_available=False':
        context.chat_data['only_available'] = False
        button_availability = [InlineKeyboardButton('🚫 все', callback_data='only_available=True')]
    else:
        context.chat_data['only_available'] = True
        button_availability = [InlineKeyboardButton('✅ только доступные', callback_data='only_available=False')]

    keyboard.append(button_availability)
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = 'Выберите категорию на которую хотите получить таблицу со стоимостью'

    await query.edit_message_caption(caption=text, reply_markup=reply_markup)

    return DOWNLOAD_COST


async def waiting_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.edit_message_caption(caption='Пришлите файл в формате .csv')

    return UPLOAD_COST


async def parse_document(update: Update, context: ContextTypes.DEFAULT_TYPE):

    document = update.message.document
    if not document.mime_type == 'text/csv':
        await update.message.reply_text('Нужна csv таблица')
        return UPLOAD_COST

    # Загружаем файл
    file_id = document.file_id
    new_file = await context.bot.get_file(file_id)
    await new_file.download_to_drive(f'{document.file_name}')  # Сохраняем файл

    # обрабатываем документ
    query_to_db.parsing_file_with_new_cost(file_name=document.file_name)

    await update.message.reply_text('Файл успешно обработан. Цены и наличие обновлены.')

    return ConversationHandler.END


def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START_STATE: [
                CallbackQueryHandler(select_category, 'shop'),  # перейти в магазин из главного меню
                CallbackQueryHandler(select_category_for_table_cost, 'download_cost',),
                CallbackQueryHandler(waiting_file, 'upload_cost'),
            ],
            CATEGORY_SELECTED: [
                CallbackQueryHandler(select_line, pattern='^category='),
                CallbackQueryHandler(select_category, pattern='back'),
            ],
            LINE_SELECTED: [
                CallbackQueryHandler(show_item_list, pattern='^line='),
                CallbackQueryHandler(select_category, pattern='back'),
            ],
            PRODUCT_SELECTED: [
                CallbackQueryHandler(show_item, pattern=r'\d+'),
                CallbackQueryHandler(next_image, pattern='next_image'),
                CallbackQueryHandler(show_edit_button, pattern=r'^edit_'),
                CallbackQueryHandler(select_line, pattern='back'),
                CallbackQueryHandler(add_to_cart, pattern='add_to_cart'),
                CallbackQueryHandler(remove_from_cart, pattern='remove_from_cart'),
            ],
            EDIT_ITEM: [
                CallbackQueryHandler(awaiting_value_for_edit, pattern='description|price|image'),
                MessageHandler(filters.Document.ALL, set_new_item_value),
                MessageHandler(filters.TEXT & ~filters.COMMAND, callback=set_new_item_value),
                CallbackQueryHandler(show_item, pattern='back'),
                CallbackQueryHandler(delete_message, pattern='delete'),
            ],
            CART: [
                CallbackQueryHandler(show_item, pattern=r'\d+'),
                CallbackQueryHandler(create_order, pattern='create_order'),
            ],
            DOWNLOAD_COST: [
                CallbackQueryHandler(get_table_with_cost_from_server, pattern='^category='),
                CallbackQueryHandler(select_category_for_table_cost, pattern='^only_available='),
            ],
            UPLOAD_COST: [
                MessageHandler(filters.Document.ALL, parse_document),
                # MessageHandler()
            ]
        },
        fallbacks=[
            CommandHandler('start', start),
            CallbackQueryHandler(start_copy, pattern='home'),
            CallbackQueryHandler(show_cart_item_list, 'go_to_cart'),
        ],
    )

    # application.add_handler(CommandHandler('start', start))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_to_html))
    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
