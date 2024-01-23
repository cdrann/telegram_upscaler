from aiogram.types import KeyboardButton

ORDER_COMMANDS = [
    'Рыночный ордер на покупку', 
    'Рыночный ордер на продажу', 
    'Лимитный ордер на покупку', 
    'Лимитный ордер на продажу']

main = [
    [KeyboardButton(text='Рынок 💰')],
    [KeyboardButton(text='Курсы валют 📈')],
    [KeyboardButton(text='Баланс 💵')],
    [KeyboardButton(text='Статистика 📄')],
    ]

market = [
    [KeyboardButton(text='Назад  🔙')],
    [KeyboardButton(text=ORDER_COMMANDS[0])],
    [KeyboardButton(text=ORDER_COMMANDS[1])],
    [KeyboardButton(text=ORDER_COMMANDS[2])],
    [KeyboardButton(text=ORDER_COMMANDS[3])],
    [KeyboardButton(text='Активные лимитные ордеры 📊')],
    [KeyboardButton(text='Отменить активные лимитные ордеры ❌')],
    ]


all = [
    [KeyboardButton(text='Назад  🔙')],
    [KeyboardButton(text='Всё')],
    ]

statistics = [
    [KeyboardButton(text='Назад  🔙')],
    [KeyboardButton(text='Время до окончания турнира 📅')],
    [KeyboardButton(text='История операций 📕')], 
    [KeyboardButton(text='Доходы-расходы 🧮')],
    ]

buyCurrency = [
    [KeyboardButton(text='Назад  🔙')],
    [KeyboardButton(text=ORDER_COMMANDS[0]+' BTC')],
    [KeyboardButton(text=ORDER_COMMANDS[0]+' ETH')],
    [KeyboardButton(text=ORDER_COMMANDS[0]+' BNB')],
    [KeyboardButton(text=ORDER_COMMANDS[0]+' XRP')],
    [KeyboardButton(text=ORDER_COMMANDS[0]+' DOGE')],
    ]

sellCurrency = [
    [KeyboardButton(text='Назад  🔙')],
    [KeyboardButton(text=ORDER_COMMANDS[1]+' BTC')],
    [KeyboardButton(text=ORDER_COMMANDS[1]+' ETH')],
    [KeyboardButton(text=ORDER_COMMANDS[1]+' BNB')],
    [KeyboardButton(text=ORDER_COMMANDS[1]+' XRP')],
    [KeyboardButton(text=ORDER_COMMANDS[1]+' DOGE')],
    ]

limitBuyCurrency = [
    [KeyboardButton(text='Назад  🔙')],
    [KeyboardButton(text=ORDER_COMMANDS[2]+' BTC')],
    [KeyboardButton(text=ORDER_COMMANDS[2]+' ETH')],
    [KeyboardButton(text=ORDER_COMMANDS[2]+' BNB')],
    [KeyboardButton(text=ORDER_COMMANDS[2]+' XRP')],
    [KeyboardButton(text=ORDER_COMMANDS[2]+' DOGE')],
    ]

limitSellCurrency = [
    [KeyboardButton(text='Назад  🔙')],
    [KeyboardButton(text=ORDER_COMMANDS[3]+' BTC')],
    [KeyboardButton(text=ORDER_COMMANDS[3]+' ETH')],
    [KeyboardButton(text=ORDER_COMMANDS[3]+' BNB')],
    [KeyboardButton(text=ORDER_COMMANDS[3]+' XRP')],
    [KeyboardButton(text=ORDER_COMMANDS[3]+' DOGE')],
    ]