import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

conn = sqlite3.connect('online_store.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY ,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        photo TEXT
    )
''')


TOKEN = '6978665646:AAET_gCNCZkQj5-EM6lxQYvDYeJkHSJvoKg'
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
ADMINS = [1042223756]


async def set_default_commands(dp):
    await bot.set_my_commands(
        [
            types.BotCommand('menu', 'Меню'),
            types.BotCommand('products', 'Подивитися товари'),
            
            types.BotCommand('add_product', 'Додати новий товар.')
        ]
    )

@dp.message_handler(commands='products')
async def product(message: types.Message):
    product_choice = InlineKeyboardMarkup()
    cursor.execute('SELECT name FROM products')
    products_data = cursor.fetchall()
    
    for product_data in products_data:
        product_name = product_data[0]
        button = InlineKeyboardButton(text=product_name, callback_data=product_name)
        product_choice.add(button)
    
    await message.answer(text='Обери продукт, про який ти хочеш дізнатися.', reply_markup=product_choice)

# ______________________________________________________________________________________________________________________________-


@dp.callback_query_handler()
async def get_product_info(callback_query: types.CallbackQuery):
    cursor.execute(f"""SELECT name, price, description, photo FROM products WHERE name = '{callback_query.data}'""")
    product_data = cursor.fetchone()

    if product_data:
        product_name, product_price, product_description, photo = product_data
        await bot.send_photo(callback_query.message.chat.id, photo)

        message = f"<b>Назва товару:</b> {product_name}\n\n<b>Опис:</b> \n{product_description}\n\n<b>Ціна:</b> {product_price}\n"

        
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton('Повернутись до всіх товарів', callback_data='Повернутись до всіх товарів'))

        await bot.send_message(callback_query.message.chat.id, message, parse_mode='html', reply_markup=keyboard)
    elif callback_query.data == 'Товари':
        await product(callback_query.message)
    elif callback_query.data == 'Повернутись до всіх товарів':
        await product(callback_query.message) 
    else:
        await bot.send_message(callback_query.message.chat.id, 'Товар не знайдено')

# ______________________________________________________________________________________________________________________________-

@dp.message_handler(commands='add_product')
async def add_new_film(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in ADMINS:
        await message.answer(text='Введи назву товару, який ти хочеш додати.')
        await state.set_state('set_product_name')


@dp.message_handler(state='set_product_name')
async def set_film_name(message: types.Message, state: FSMContext):
    product_name = message.text
    
    if len(product_name) > 64:
        message.answer(text='На жаль, я не можу додати цей товар, адже довжина його назви не має перевищувати 64 символи.')
    else:
        await state.update_data(product_name=product_name)  
        await state.set_state('set_price')
        await message.answer(text='Надай ціну цьому товару.')

@dp.message_handler(state='set_price')
async def set_description(message: types.Message, state: FSMContext):
    product_price = message.text
    await state.update_data(product_price=product_price)  
    await state.set_state('set_description')
    await message.answer(text='Тепер дай опис товару')

@dp.message_handler(state='set_description')
async def set_description(message: types.Message, state: FSMContext):
    product_description = message.text
    await state.update_data(product_description=product_description)  
    await state.set_state('set_photo')
    await message.answer(text='Тепер дай посилання на банер цього товару')

@dp.message_handler(state='set_photo')
async def set_photo(message: types.Message, state: FSMContext):
    product_photo = message.text
    
    product_name = await state.get_data()
    product_description = await state.get_data()
    product_price = await state.get_data()
    product_name = product_name['product_name']
    product_description = product_description['product_description']
    product_price = product_price['product_price']

    cursor.execute('''
        INSERT INTO products (name, price, description, photo)
        VALUES (?, ?, ?, ?)
    ''', (product_name, product_price, product_description, product_photo))
    
    conn.commit()
    
    await state.finish()
    await message.answer(text='Супер! Новий товар успішно додано до бібліотеки.')

@dp.message_handler(commands='menu')
async def menu(message: types.Message):
    menu = InlineKeyboardMarkup()
    name_button = ('Товари')
    button = InlineKeyboardButton(text=name_button, callback_data=name_button)
    menu.add(button)
    await message.answer(text='Меню:', reply_markup=menu)


async def on_shutdown(dp):
    conn.close()

async def on_startup(dp):
    await set_default_commands(dp)

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)