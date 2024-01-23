from aiogram import Bot, types
from aiogram import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
import re
import requests
import threading
import datetime
import asyncio
import time
import numpy as np
import ast
import math

import Buttons
import DataBase


#region Начальное
BOT_TOKEN = None
AVAILABLE_CURRENCIES = None
CURRENCY_UPDATE_PERIOD = None
START_BALANCE = None
ROUND_PRECISION = None
ORDER_COMMANDS = [
    'Рыночный ордер на покупку', 
    'Рыночный ордер на продажу', 
    'Лимитный ордер на покупку', 
    'Лимитный ордер на продажу']
order_command_len = len(ORDER_COMMANDS[0].split(' '))
TOURNAMENT_END_DATE = None

def ConvertStringToType(string):
    # Try to parse the string as a literal
    try:
        return ast.literal_eval(string)
    except:
        # If it fails, it means the string is a date
        return datetime.datetime.strptime(string, '%Y-%m-%d %H:%M')
def LoadParametersFromFile():
    # Open the constants file
    with open('constants.txt') as f:
        # Read the contents of the file
        contents = f.read()

    # Split the contents into lines
    lines = contents.split('\n')

    # Iterate over the lines
    for line in lines:
        # Split the line into the constant name and value
        name, value = line.split(' = ')

        # Parse the value as the appropriate data type
        value = ConvertStringToType(value)

        # Assign the value to a variable with the name of the constant
        globals()[name] = value
LoadParametersFromFile()

# Объявление бота
bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

# Создание БД
if not DataBase.CheckIfDBExists():
    DataBase.CreateDB()
    DataBase.CreateTables()

# Глобальные переменные
currency_rates = []
tournamentTimeLeftInSec = 99999

# Добавить начальный баланс
DataBase.SetBalanceToExistingUsers(START_BALANCE)

# Регистрация
@dp.message_handler(commands='start')
async def TryRegUser(message:types.Message):
    keyboard = types.ReplyKeyboardMarkup(keyboard=Buttons.main, resize_keyboard=True)

    if DataBase.UserRegCheck(message.from_user.id):
        await message.answer('Вы уже есть среди пользователей.' , reply_markup=keyboard)
    else:
        DataBase.InsertUser(message.from_user.id, message.from_user.full_name, START_BALANCE)
        await message.answer('Добро пожаловать, ' + message.from_user.full_name + '!' + 
                            '\nТеперь вы наш пользователь, ваш баланс пополнен на 100 $!!!' , reply_markup=keyboard)
#endregion


#region Админ-панель
# Сообщение всем админам
async def send_message_to_admins(message):
    for admin in DataBase.GetAdminsList():
        await bot.send_message(admin, message)

# Очистка БД
@dp.message_handler(commands='clear')
async def CleanDB(message:types.Message):
    if message.from_user.id in DataBase.GetAdminsList():
        DataBase.ClearDB()
        await message.answer('ВСЁ УДАЛЕНО!!!')

# Экспорт в Эксель
@dp.message_handler(commands='export')
async def ExportDB(message:types.Message):
    if message.from_user.id in DataBase.GetAdminsList():
        DataBase.UpdateUsersTotalBalance(GetUsersTotalBalances())
        DataBase.ExportDB()
        await message.answer(f'Файлы экспортированы.')

# Добавить админа
@dp.message_handler(commands='add_admin')
async def AddAdminHandler(message:types.Message):
    if message.from_user.id in DataBase.GetAdminsList():
        newAdmin = int(message.text.split()[1])
        DataBase.AddNewAdmin(newAdmin)
        await message.answer(f'{newAdmin} добавлен в качестве администратора.')

# Запросить список админов
@dp.message_handler(commands='admins')
async def AdminsHandler(message:types.Message):
    if message.from_user.id in DataBase.GetAdminsList():
        await message.answer(DataBase.GetAdminsList())

# Добавить баланс
@dp.message_handler(commands='add_balance')
async def AddbalanceHandler(message:types.Message):
    if message.from_user.id in DataBase.GetAdminsList():
        amount = int(message.text.split()[1])
        DataBase.AddUserMoney(message.from_user.id, amount)
        await message.answer(f'На ваш баланс зачислено {amount} $')
    else:
        await message.answer('Вы не админ. Зарабатывайте сами.')

# Апдейт полного баланса пользователей
@dp.message_handler(commands='update_totals')
async def UpdateTotalsHandler(message:types.Message):
    if message.from_user.id in DataBase.GetAdminsList():
        DataBase.UpdateUsersTotalBalance(GetUsersTotalBalances())

# Суперкоманда
@dp.message_handler(commands='execute')
async def ExecuteQueryHandler(message:types.Message):
    if message.from_user.id in DataBase.GetAdminsList():
        text = message.text
        text = re.sub('/execute ', '', text)
        result = DataBase.ExecuteQuery(text)
        
        restext = ''
        for element in result:
            restext += str(element)
            restext += '\n'

        await message.answer(restext)
#endregion


#region Цикл апдейта валют
def smart_round(x):
    if np.abs(x) < 0.1:
        return np.format_float_positional(x, precision=ROUND_PRECISION, fractional=False)
    else:
        x = np.format_float_positional(x, precision=ROUND_PRECISION, fractional=True)
        x = float(x)

        if math.modf(x)[0] == 0:
            return int(x)
        else:
            return x

def get_curr_string_date():
    current_date = datetime.datetime.now().date()
    current_time = datetime.datetime.now().time()
    current_date_string = current_date.strftime('%Y-%m-%d')
    current_time_string = current_time.strftime('%H:%M:%S')
    current_datetime_string = current_date_string + ' ' + current_time_string
    return current_datetime_string


def GetCurrencyPrice(currency):
    idx = AVAILABLE_CURRENCIES.index(currency)
    return currency_rates[idx]
def ParseCurrencyPrice(currency):
    symbol = currency + 'USDT'
    url = "https://api.binance.com/api/v3/ticker/price?symbol=" + symbol
    response = requests.get(url)
    data = response.json()
    return float(data['price'])

def UpdateCurrencyRates():
    rates = []
    for i in range (len(AVAILABLE_CURRENCIES)):
        rates.append(ParseCurrencyPrice(AVAILABLE_CURRENCIES[i]))
    global currency_rates
    currency_rates = rates
def CheckUsersLimitOrders():
    limitOrdersTuple = DataBase.GetOpenLimitOrders()
    telegramIdsList = [x[0] for x in limitOrdersTuple]
    currenciesList = [x[1] for x in limitOrdersTuple]
    amountList = [x[2] for x in limitOrdersTuple]
    moneyList = [x[3] for x in limitOrdersTuple]
    linesList = [x[4] for x in limitOrdersTuple]
    actionsList = [x[5] for x in limitOrdersTuple]

    for i in range(len(telegramIdsList)):
        
        currencyPrice = GetCurrencyPrice(currenciesList[i])

        def close_limit_order(amount):
            closeDate = get_curr_string_date()
            DataBase.CloseLimitOrder(telegramIdsList[i], currenciesList[i], closeDate, actionsList[i])
            bot_event_loop.create_task(TryBuyOrSellCurrency(telegramIdsList[i], currenciesList[i], amount, actionsList[i], price=linesList[i]))

        if actionsList[i] == 'buy' and currencyPrice - linesList[i] <= 0:
            amount = moneyList[i]
            close_limit_order(amount)
        elif actionsList[i] == 'sell' and currencyPrice - linesList[i] >= 0:
            amount = amountList[i]
            close_limit_order(amount)
        else:
            continue
def CheckIfTournamentEnded():
    if TOURNAMENT_END_DATE < datetime.datetime.now():
        DataBase.ExportDB()
        print('Данные экспортированы.')
        print('Турнир окончен. Для старта нового измените дату его окончания в constants.txt.')
        bot_event_loop.stop()
def CurrencyUpdateCycle():    
    while True:
        # Обновление курсов валют
        UpdateCurrencyRates()

        # Проверка окончания турнира
        CheckIfTournamentEnded()

        # Проверка ордеров
        CheckUsersLimitOrders()

        # Уходим на цикл
        time.sleep(CURRENCY_UPDATE_PERIOD)
#endregion


#region Ордеры
for command in ORDER_COMMANDS:
    @dp.message_handler(Text(contains=command))
    async def handle_command(message: types.Message):
        await StartOrderCommand(message)
async def StartOrderCommand(message:types.Message):
    splitted_message = message.text.split()

    if ORDER_COMMANDS[0] in message.text:
        keyboard = Buttons.buyCurrency
        reply_2 = 'Введите количество $ на которое вы хотите купить валюту'
        sell = False
    if ORDER_COMMANDS[1] in message.text:
        keyboard = Buttons.sellCurrency
        reply_2 = 'Введите количество валюты на продажу'
        sell = True
    if ORDER_COMMANDS[2] in message.text:
        keyboard = Buttons.limitBuyCurrency
        reply_2 = 'Введите количество $ на которое вы хотите отложенно купить валюту'
        sell = False
    if ORDER_COMMANDS[3] in message.text:
        keyboard = Buttons.limitSellCurrency
        sell = True
        reply_2 = 'Введите количество валюты на продажу'

    reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    all_markup = types.ReplyKeyboardMarkup(keyboard=Buttons.all, resize_keyboard=True)

    if len(splitted_message) == order_command_len:
        if sell:
            # Вывести валюты что есть
            values = DataBase.CurrencyBalance(message.from_user.id)
            restext = 'Содержание портфеля:\n'
            for currency, amount in values:
                restext += f'   {currency}: {smart_round(amount)} \n'
            await message.answer(restext)

        # Спросить о валюте
        await message.answer('Выберите валюту (Через кнопку)', reply_markup=reply_markup)
    if len(splitted_message) == order_command_len + 1:        
        # Спросить о сумме
        await message.answer(reply_2, reply_markup=all_markup)
    if len(splitted_message) >= order_command_len + 2:
        await message.answer('Однострочная подача аргументов не поддерживается')

    DataBase.AddLastMessage(message.from_user.id, message.text)
async def AppendAmountToLimitOrderCommand(telegramId, currency, lastMessage, amount, action):

    if action == 'buy':
        await bot.send_message(telegramId, 'Введите, по какому курсу требуется купить валюту')
    if action == 'sell':
        await bot.send_message(telegramId, 'Введите, по какому курсу требуется продать валюту')

    currencyPrice = GetCurrencyPrice(currency)
    await bot.send_message(telegramId, f'Текущий курс {currency}: \n{smart_round(currencyPrice)}')
    
    newMessage = lastMessage + ' ' + str(amount)
    return newMessage
async def CompileMarketOrder(telegramId, currency, amount, action):
    if currency not in AVAILABLE_CURRENCIES:
        return

    try:
        currencyAmount, moneyAmount = await TryBuyOrSellCurrency(telegramId, currency, amount, action)
    except:
        return

    date = get_curr_string_date()
    DataBase.LogMarketOrderInHistory(telegramId, currency, currencyAmount, moneyAmount, action, date)
    await send_message_to_admins(f'{DataBase.GetUsernameById(telegramId)} создал рыночный ордер:\n'
    f'{action} {currency} на ${smart_round(moneyAmount)}')
async def CompileLimitOrder(telegramId, currency, amount, limit, action):
    if currency not in AVAILABLE_CURRENCIES:
        return
    if DataBase.CheckIfLimitOrderExists(telegramId, currency):
        await bot.send_message(telegramId, f'У вас уже есть лимитный ордер на {currency} - {action}')
        return

    if action == 'buy':
        moneyAmount = amount
        currencyAmount = moneyAmount / GetCurrencyPrice(currency)
    if action == 'sell':
        currencyAmount = amount
        moneyAmount = currencyAmount * GetCurrencyPrice(currency)

    openDate = get_curr_string_date()
    closeDate = 'ACTIVE'

    reply_markup = types.ReplyKeyboardMarkup(keyboard=Buttons.market, resize_keyboard=True)

    DataBase.LogLimitOrderInHistory(telegramId, currency, currencyAmount, moneyAmount, limit, action, openDate, closeDate)
    await send_message_to_admins(f'{DataBase.GetUsernameById(telegramId)} создал лимитный ордер:\n'
    f'{action} {currency} на {smart_round(moneyAmount)} $ по курсу {limit} $')    

    await bot.send_message(telegramId, 
    f'Вы успешно создали лимитный ордер: \n' + \
        f'{action} {currency} на {smart_round(moneyAmount)} $ по курсу {limit} $', 
    reply_markup=reply_markup)

async def TryBuyOrSellCurrency(telegramId, currency, amount, action, price=None):

    reply_markup = types.ReplyKeyboardMarkup(keyboard=Buttons.market, resize_keyboard=True)

    if action == "buy":
        currencyAmount = None
        moneyAmount = amount

        if moneyAmount <= 0:
            await bot.send_message(telegramId, 'Невозможно купить на отрицательную/нулевую сумму')
            DataBase.MarkLimitOrderAsError(telegramId, currency, currencyAmount, moneyAmount, action)
            return

        successfullyTransacted = DataBase.TrySpendUserMoney(telegramId, moneyAmount)
        if successfullyTransacted:
            if price == None:
                price = GetCurrencyPrice(currency)
            purchasedAmount = moneyAmount / price
            currentAmount = DataBase.GetUserCurrency(telegramId, currency)
            if currentAmount:
                newAmount = currentAmount + purchasedAmount
                DataBase.UpdateCurrency(currency, newAmount, telegramId)
                await bot.send_message(telegramId, f'''Ваш пакет с {currency} обновлён на : {smart_round(purchasedAmount)} по курсу {price}.
                                                    На вашем счёте осталось {smart_round(DataBase.GetUserBalance(telegramId))} $.
                                                    И теперь вы имеете {smart_round(newAmount)} {currency}''', reply_markup=reply_markup)
            else:
                DataBase.AddCurrency(currency, purchasedAmount, telegramId)
                await bot.send_message(telegramId, f'В ваш пакет добавлен {currency} в количестве : {smart_round(purchasedAmount)} по курсу {price}. \n' +\
                                                f'На вашем счёте осталось {smart_round(DataBase.GetUserBalance(telegramId))} $.', 
                                                reply_markup=reply_markup)
            return purchasedAmount, amount
        
        if not successfullyTransacted:
            await bot.send_message(telegramId,'Недостаточно денег на счёте.')
            DataBase.MarkLimitOrderAsError(telegramId, currency, currencyAmount, moneyAmount, action)
            return

    elif action == "sell":
        currencyAmount = amount
        moneyAmount = None

        if currencyAmount <= 0:
            await bot.send_message(telegramId, 'Невозможно продать на отрицательное/нулевое количество валюты')
            DataBase.MarkLimitOrderAsError(telegramId, currency, currencyAmount, moneyAmount, action)
            return

        successfullyTransacted = DataBase.TrySellUserCurrency(telegramId, currency, currencyAmount)
        if successfullyTransacted:
            if price == None:
                price = GetCurrencyPrice(currency)
            soldAmount = currencyAmount * price
            DataBase.AddUserMoney(telegramId, soldAmount)
            await bot.send_message(telegramId, 
                f'Вы успешно продали {currency} в количестве {smart_round(amount)} по курсу {price} $.' + \
                f'На данной операции вы заработали {smart_round(soldAmount)} $', 
                reply_markup=reply_markup)
            return amount, soldAmount
        
        if not successfullyTransacted:
            await bot.send_message(telegramId,f'У вас нет столько {currency}.')
            DataBase.MarkLimitOrderAsError(telegramId, currency, currencyAmount, moneyAmount, action)
            return

@dp.message_handler(Text(equals='Активные лимитные ордеры 📊'))
async def ShowMyOpenLimitOrders(message:types.Message):
    active_orders = DataBase.GetUserActiveLimitOrders(message.from_user.id)

    reply = "Активные лимитные ордеры:\n\n"
    for i, trade in enumerate(active_orders):
        reply += f"Ордер {i+1}:\n"
        reply += f"  {trade[3]} {trade[0]}\n"
        reply += f"  В количестве {smart_round(trade[1])}\n"
        reply += f"  Лимит: {trade[6]} $\n"
        reply += f"  Стоимостью {smart_round(trade[2])} $\n"
        reply += f"  Дата открытия: {trade[4]}\n"
        reply += "\n"
    await message.reply(reply)
@dp.message_handler(Text(equals='Отменить активные лимитные ордеры ❌'))
async def CancelMyOpenLimitOrders(message:types.Message):
    DataBase.CancellOpenLimitOrdersOfUser(message.from_id)
    await message.reply('Ваши лимитные ордеры были отменены.')
# endregion


#region Статистика
@dp.message_handler(Text(equals='Баланс 💵'))
async def GetUserBalance(message:types.Message):
    # Get the user's balance in $
    balance = DataBase.GetUserBalance(message.from_user.id)

    # Calculate the total $ equivalent of the user's portfolio
    portfolio_value = 0
    values = DataBase.CurrencyBalance(message.from_user.id)
    for currency, amount in values:
        price = GetCurrencyPrice(currency)
        portfolio_value += amount * price
        
    # Display the total balance (balance + portfolio value)
    total_balance = balance + portfolio_value
    await message.answer(f'Общая ценность ваших средств составляет {smart_round(total_balance)} $\n'
                         f'Ваш баланс составляет {smart_round(balance)} $\n'
                         f'Ценность портфеля составляет {smart_round(portfolio_value)} $')

    # Get the user's balances in different currencies
    values = DataBase.CurrencyBalance(message.from_user.id)
    restext = 'Содержание портфеля:\n'
    for currency, amount in values:
        restext += f'   {currency}: {smart_round(amount)} \n'
    await message.answer(restext) 

@dp.message_handler(Text(equals='Курсы валют 📈'))
async def ExchangeRates(message:types.Message):
    rates = currency_rates
    answer = ''

    # Заполняем ответ прайсами
    for i in range(len(AVAILABLE_CURRENCIES)):
        answer += f'{AVAILABLE_CURRENCIES[i]}: {rates[i]}\n'

    await message.answer(answer)

@dp.message_handler(Text(equals='Время до окончания турнира 📅'))
async def CheckTimer(message:types.Message):
    # Get time left
    seconds = TOURNAMENT_END_DATE - datetime.datetime.now()
    
    # Convert the time left to days and hours
    days, seconds = divmod(seconds.total_seconds(), 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days == 0 and hours == 0:
        await message.answer(f'Осталось времени турнира: {int(minutes)} мин. {int(seconds)} сек.')
    else:
        await message.answer(f'Осталось времени турнира: {int(days)} д. {int(hours)} ч.')

@dp.message_handler(Text(equals='История операций 📕'))
async def HistoryHandler(message:types.Message):
    market_history = DataBase.GetUserMarketOrdersHistory(message.from_user.id)
    limit_history = DataBase.GetUserLimitOrdersHistory(message.from_user.id)

    reply = "Рыночные ордеры:\n\n"
    for i, trade in enumerate(market_history):
        reply += f"Trade {i+1}:\n"
        reply += f"  {trade[3]} {trade[0]}\n"
        reply += f"  В количестве {smart_round(trade[1])}\n"
        reply += f"  Стоимостью {smart_round(trade[2])} $\n"
        reply += f"  Дата: {trade[4]}\n"
        reply += "\n"
    await message.reply(reply)

    reply = "Лимитные ордеры:\n\n"
    for i, trade in enumerate(limit_history):
        reply += f"Trade {i+1}:\n"
        reply += f"  {trade[3]} {trade[0]}\n"
        reply += f"  В количестве {smart_round(trade[1])}\n"
        reply += f"  Лимит: {trade[6]} $\n"
        reply += f"  Стоимостью {smart_round(trade[2])} $\n"
        reply += f"  Дата открытия: {trade[4]}\n"
        reply += f"  Дата закрытия: {trade[5]}\n"
        reply += "\n"
    await message.reply(reply)

@dp.message_handler(Text(equals='Доходы-расходы 🧮'))
async def SumsHandler(message:types.Message):

    # Calculate the total $ equivalent of the user's portfolio
    portfolio_value = 0
    values = DataBase.CurrencyBalance(message.from_user.id)
    for currency, amount in values:
        price = GetCurrencyPrice(currency)
        portfolio_value += amount * price

    balance = DataBase.GetUserBalance(message.from_id)
    total_money_buy, total_money_sell = DataBase.GetUserTotalMoney(message.from_user.id)

    reply = f'Куплено на: {smart_round(total_money_buy)} $\n' + \
            f'Продано на: {smart_round(total_money_sell)} $\n' + \
            f'Вы заработали: {smart_round(balance + portfolio_value - START_BALANCE)} $\n' + \
            f'В активах: {smart_round(portfolio_value)} $'
    await message.reply(reply)

def GetUserTotalBalance(telegramId):
    portfolio_value = 0
    values = DataBase.CurrencyBalance(telegramId)
    for currency, amount in values:
        price = GetCurrencyPrice(currency)
        portfolio_value += amount * price
    balance = DataBase.GetUserBalance(telegramId)
    return balance + portfolio_value
def GetUsersTotalBalances():
    users = DataBase.GetUsers()
    totalBalances = []
    for user in users:
        totalBalance = GetUserTotalBalance(user)
        totalBalances.append(totalBalance)
    return totalBalances
#endregion


#region Кнопки
@dp.message_handler(Text(equals='Назад  🔙'))
async def Back(message:types.Message):    
    keyboard = types.ReplyKeyboardMarkup(keyboard=Buttons.main, resize_keyboard = True)
    await message.answer('Основная страница', reply_markup=keyboard)

@dp.message_handler(Text(equals='Рынок 💰'))
async def MarketPage(message:types.Message):
    keyboard = types.ReplyKeyboardMarkup(keyboard=Buttons.market, resize_keyboard = True)
    await message.answer('Страница рынка', reply_markup=keyboard)

@dp.message_handler(Text(equals='Статистика 📄'))
async def StatPage(message:types.Message):
    keyboard = types.ReplyKeyboardMarkup(keyboard=Buttons.statistics, resize_keyboard = True)
    await message.answer('Страница статистики', reply_markup=keyboard)
#endregion


@dp.message_handler(content_types=['text'])
async def EmptyMessageHandler(message:types.Message):
    # Взяли из БД последнее сообщение зареганного пользователя
    lastMessage = DataBase.GetLastMessage(message.from_user.id)
    if lastMessage == None:
        await message.answer('Вы не зарегистрированы. Зарегистрируйтесь, написав /start.')
        return

    # Выходим если не выполняются команды рынка
    if not any(substring in lastMessage   for substring in ORDER_COMMANDS):
        DataBase.AddLastMessage(message.from_user.id, message.text)
        return

    # Сплит последнего сообщения
    lastMessageSplit = lastMessage.split(' ')

    # Достали полезную инфу
    telegramId = message.from_user.id
    try:
        message_float = float(message.text)
    except:
        message_float =  None

    # Уточняем order и action и currency
    order_rus, action_rus = lastMessageSplit[0], lastMessageSplit[3]
    order = 'market' if 'ыночн' in order_rus else 'limit'
    action = 'buy' if 'окупк' in action_rus else 'sell'
    currency = lastMessageSplit[order_command_len + 0]

    all = message.text in ['all', 'a', 'Всё', 'Все']  # если сообщение содержит ключевые слова 
                                                        # для продажи всей валюты / покупки на всю сумму
    
    def get_actual_amount(telegramId, currency, action, all, message_float):
        if action == 'buy' and all:
            balance = DataBase.GetUserBalance(telegramId)
            return balance if balance else 0
        elif action == 'sell' and all:
            currencyAmount = DataBase.GetUserCurrency(telegramId, currency)
            return currencyAmount if currencyAmount else 0
        else:
            return message_float

    if order == 'market':
        amount = get_actual_amount(telegramId, currency, action, all, message_float)
        await CompileMarketOrder(telegramId, currency, amount, action)
        DataBase.AddLastMessage(telegramId, 'NULL')
        return 

    if order == 'limit':

            if len(lastMessageSplit) == (order_command_len + 1):
                amount = get_actual_amount(telegramId, currency, action, all, message_float)
                
                success = False
                if action == 'buy':
                    success = DataBase.GetUserBalance(telegramId) >= amount
                if action == 'sell':
                    currencyAmount = DataBase.GetUserCurrency(telegramId, currency)
                    if currencyAmount:
                        success = DataBase.GetUserCurrency(telegramId, currency) >= amount
                    else:
                        success = False
                if amount <= 0:
                    success = False

                if success:
                    newMessage = await AppendAmountToLimitOrderCommand(telegramId, currency, lastMessage, amount, action)
                    DataBase.AddLastMessage(telegramId, newMessage)
                else:
                    await message.answer('Некорректное создание ордера. \nПроверьте наличие валют и баланс.')
                    DataBase.AddLastMessage(telegramId, 'NULL')
                
                return

            if len(lastMessageSplit) == (order_command_len + 2):
                amount = float(lastMessageSplit[order_command_len + 1])
                limit = message_float
                await CompileLimitOrder(telegramId, currency, amount, limit, action)
                DataBase.AddLastMessage(telegramId, 'NULL')
                return


thread = threading.Thread(target=CurrencyUpdateCycle, name='CurrencyUpdateCycle', daemon=True)
thread.start()

bot_event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(bot_event_loop)
bot_event_loop.run_until_complete(executor.start_polling(dp, skip_updates=True))