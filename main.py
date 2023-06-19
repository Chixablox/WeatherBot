import telebot
import os
import requests
import typing
import dotenv

dotenv.load_dotenv()
TOKEN = os.getenv('TOKEN', '')
YANDEX_TOKEN = os.getenv('YANDEX_TOKEN', '')
GEO_TOKEN = os.getenv('GEO_TOKEN', '')

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start_message(message: telebot.types.Message) -> None:
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("Узнать погоду")
    markup.add(btn1)
    bot.send_message(message.chat.id, 'Нажми на кнопку ниже\n', reply_markup=markup)


@bot.message_handler(content_types=["text"])
def get_message_from_chat(message: telebot.types.Message) -> None:
    if message.text == 'Привет':
        bot.send_message(message.chat.id, 'И тебе привет')
    elif message.text == 'Пока':
        bot.send_message(message.chat.id, "ББ")
    elif message.text == 'Узнать погоду':
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = telebot.types.KeyboardButton("Омск")
        btn2 = telebot.types.KeyboardButton("Новосибирск")
        btn3 = telebot.types.KeyboardButton("Москва")
        btn4 = telebot.types.KeyboardButton("Другой населённый пункт")
        btn5 = telebot.types.KeyboardButton("Вернуться в меню")
        markup.add(btn1, btn2, btn3, btn4, btn5)
        bot.send_message(message.chat.id, text="Выберите населённый пункт", reply_markup=markup)
    elif message.text == 'Омск':
        weather_in_city(54.983006700000004, 73.37452243916528, 'Омск', message)
    elif message.text == 'Новосибирск':
        weather_in_city(55.0415, 82.9346, 'Новосибирск', message)
    elif message.text == 'Москва':
        weather_in_city(55.7522, 37.6156, 'Москва', message)
    elif message.text == 'Другой населённый пункт':
        msg = bot.send_message(message.chat.id, f"Введите название населённого пункта")
        bot.register_next_step_handler(msg, get_city)
    elif message.text == 'Вернуться в меню':
        start_message(message)
    else:
        bot.send_message(message.chat.id, "Моя твоя не понимать")
        message.text = 'Узнать погоду'
        get_message_from_chat(message)


@bot.message_handler(content_types=["text"])
def get_city(message: telebot.types.Message) -> None:
    try:
        city = message.text
        geo_req = requests.get(
            f'https://api.geoapify.com/v1/geocode/search?city={city}&type=city&apiKey={GEO_TOKEN}&lang=ru')
        geo_response = geo_req.json()
        replays = []
        for i in range(0, len(geo_response['features']) - 1):
            if (round(geo_response['features'][i]['properties']['lat'], 1) == round(
                    geo_response['features'][i + 1]['properties']['lat'], 1)
                    and round(geo_response['features'][i]['properties']['lon'], 1) == round(
                        geo_response['features'][i + 1]['properties']['lon'], 1)):
                replays.append(i + 1)
    except:
        bot.send_message(message.chat.id, f"Я не могу найти такой город")
    for i in range(0, len(replays)):
        geo_response['features'].pop(i)
    if len(geo_response['features']) > 1:
        for i in range(0, len(geo_response['features'])):
            try:
                geo_city = geo_response['features'][i]['properties']['city']
                country = geo_response['features'][i]['properties']['country']
                if 'state' in geo_response['features'][i]['properties'] and 'county' in geo_response['features'][i][
                    'properties']:
                    county = geo_response['features'][i]['properties']['county']
                    state = geo_response['features'][i]['properties']['state']
                    bot.send_message(message.chat.id, f'{i + 1} - {city}, {county}, {state}, {country}\n')
                elif 'state' in geo_response['features'][i]['properties']:
                    state = geo_response['features'][i]['properties']['state']
                    bot.send_message(message.chat.id, f'{i + 1} - {geo_city}, {state}, {country}\n')
                else:
                    bot.send_message(message.chat.id, f'{i + 1} - {geo_city}, {country}\n')
            except:
                print('Прикол')
        msg = bot.send_message(message.chat.id, f"Введите номер населённого пункта")
        bot.register_next_step_handler(msg, get_coord, geo_response, city)
    elif len(geo_response['features']) == 1:
        message.text = 1
        get_coord(message, geo_response, city)
    else:
        bot.send_message(message.chat.id, f"Я не могу найти такой город")


@bot.message_handler(content_types=["text"])
def get_coord(message: telebot.types.Message, geo_response: dict, city: str) -> None:
    try:
        numb = message.text
        lat = geo_response['features'][int(numb) - 1]['properties']['lat']
        lon = geo_response['features'][int(numb) - 1]['properties']['lon']
        weather_in_city(lat, lon, city, message)
    except:
        bot.send_message(message.chat.id, f"Что-то пошло не так")


def weather_in_city(lat: float, lon: float, city: str, message: telebot.types.Message) -> None:
    try:
        url = f'https://api.weather.yandex.ru/v2/forecast?lat={lat}&lon={lon}&lang=ru_RU&hours=false&limit=3'
        yandex_response = requests.get(url, headers={'X-Yandex-API-Key': YANDEX_TOKEN})
        jsonweather = yandex_response.json()

        cond = jsonweather['fact']['condition']
        cur_temp = jsonweather['fact']['temp']
        feels_like = jsonweather['fact']['feels_like']
        hum = jsonweather['fact']['humidity']
        pressure = jsonweather['fact']['pressure_mm']
        speed = jsonweather['fact']['wind_speed']
        direction = jsonweather['fact']['wind_dir']
        prec_type = jsonweather['fact']['prec_type']
        direction = dir_trans(direction)
        cond = cond_trans(cond)
        rec = recommendations(feels_like, prec_type)

        bot.send_message(message.chat.id, f'В населённом пункте {city} сейчас следующая погода:\n'
                                          f'Погода: {cond}\n'
                                          f'Температура: {cur_temp}℃\n'
                                          f'Ощущается как: {feels_like}℃\n'
                                          f'Влажность: {hum}%\n'
                                          f'Давление: {pressure} мм рт. ст.\n'
                                          f'Скорость ветра: {speed}м/с, направление: {direction}\n\n'
                                          f'Рекомендации по одежде:\n{rec}')
    except:
        bot.send_message(message.chat.id, "К сожалению, я не могу определить погоду в данном населённом пункте")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("Погода завтра")
    btn2 = telebot.types.KeyboardButton("Погода сегодня")
    btn3 = telebot.types.KeyboardButton("Узнать погоду")
    markup.add(btn1, btn2, btn3)
    msg = bot.send_message(message.chat.id, text="Что дальше?", reply_markup=markup)
    bot.register_next_step_handler(msg, get_weather_tomorrow_or_today, jsonweather, city)


def get_weather_tomorrow_or_today(message: telebot.types.Message, jsonweather: dict, city: str) -> None:
    if message.text == 'Погода завтра':
        forecasts(jsonweather, message, city, 1)
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = telebot.types.KeyboardButton("Погода сегодня")
        btn2 = telebot.types.KeyboardButton("Узнать погоду")
        markup.add(btn1, btn2)
        msg = bot.send_message(message.chat.id, text="Что дальше?", reply_markup=markup)
        bot.register_next_step_handler(msg, get_weather_tomorrow_or_today, jsonweather, city)
    elif message.text == 'Погода сегодня':
        forecasts(jsonweather, message, city, 0)
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = telebot.types.KeyboardButton("Погода завтра")
        btn2 = telebot.types.KeyboardButton("Узнать погоду")
        markup.add(btn1, btn2)
        msg = bot.send_message(message.chat.id, text="Что дальше?", reply_markup=markup)
        bot.register_next_step_handler(msg, get_weather_tomorrow_or_today, jsonweather, city)
    elif message.text == 'Узнать погоду':
        get_message_from_chat(message)
    else:
        message.text = 'jajaja'
        get_message_from_chat(message)


def forecasts(jsonweather: dict, message: telebot.types.Message, city: str, number: int) -> None:
    mor_cond = jsonweather['forecasts'][number]['parts']['morning']['condition']
    mor_temp_max = jsonweather['forecasts'][number]['parts']['morning']['temp_max']
    mor_temp_min = jsonweather['forecasts'][number]['parts']['morning']['temp_min']
    mor_feels_like = jsonweather['forecasts'][number]['parts']['morning']['feels_like']
    mor_hum = jsonweather['forecasts'][number]['parts']['morning']['humidity']
    mor_pressure = jsonweather['forecasts'][number]['parts']['morning']['pressure_mm']
    mor_speed = jsonweather['forecasts'][number]['parts']['morning']['wind_speed']
    mor_dir = jsonweather['forecasts'][number]['parts']['morning']['wind_dir']
    mor_prec_type = jsonweather['forecasts'][number]['parts']['day']['prec_type']
    mor_dir = dir_trans(mor_dir)
    mor_cond = cond_trans(mor_cond)
    m_rec = recommendations(mor_feels_like, mor_prec_type)

    cond = jsonweather['forecasts'][number]['parts']['morning']['condition']
    temp_max = jsonweather['forecasts'][number]['parts']['day']['temp_max']
    temp_min = jsonweather['forecasts'][number]['parts']['day']['temp_min']
    feels_like = jsonweather['forecasts'][number]['parts']['day']['feels_like']
    hum = jsonweather['forecasts'][number]['parts']['day']['humidity']
    pressure = jsonweather['forecasts'][number]['parts']['day']['pressure_mm']
    speed = jsonweather['forecasts'][number]['parts']['day']['wind_speed']
    direction = jsonweather['forecasts'][number]['parts']['day']['wind_dir']
    prec_type = jsonweather['forecasts'][number]['parts']['day']['prec_type']
    direction = dir_trans(direction)
    cond = cond_trans(cond)
    rec = recommendations(feels_like, prec_type)

    ev_cond = jsonweather['forecasts'][number]['parts']['morning']['condition']
    ev_temp_max = jsonweather['forecasts'][number]['parts']['evening']['temp_max']
    ev_temp_min = jsonweather['forecasts'][number]['parts']['evening']['temp_min']
    ev_feels_like = jsonweather['forecasts'][number]['parts']['evening']['feels_like']
    ev_hum = jsonweather['forecasts'][number]['parts']['evening']['humidity']
    ev_pressure = jsonweather['forecasts'][number]['parts']['evening']['pressure_mm']
    ev_speed = jsonweather['forecasts'][number]['parts']['evening']['wind_speed']
    ev_dir = jsonweather['forecasts'][number]['parts']['evening']['wind_dir']
    ev_prec_type = jsonweather['forecasts'][number]['parts']['evening']['prec_type']
    ev_dir = dir_trans(ev_dir)
    ev_cond = cond_trans(ev_cond)
    ev_rec = recommendations(ev_feels_like, ev_prec_type)

    n_cond = jsonweather['forecasts'][number]['parts']['morning']['condition']
    n_temp_max = jsonweather['forecasts'][number + 1]['parts']['night']['temp_max']
    n_temp_min = jsonweather['forecasts'][number + 1]['parts']['night']['temp_min']
    n_feels_like = jsonweather['forecasts'][number + 1]['parts']['night']['feels_like']
    n_hum = jsonweather['forecasts'][number + 1]['parts']['night']['humidity']
    n_pressure = jsonweather['forecasts'][number + 1]['parts']['night']['pressure_mm']
    n_speed = jsonweather['forecasts'][number + 1]['parts']['night']['wind_speed']
    n_dir = jsonweather['forecasts'][number + 1]['parts']['night']['wind_dir']
    n_prec_type = jsonweather['forecasts'][number + 1]['parts']['night']['prec_type']
    n_dir = dir_trans(n_dir)
    n_cond = cond_trans(n_cond)
    n_rec = recommendations(n_feels_like, n_prec_type)

    bot.send_message(message.chat.id, f'Погода в населённом пункте {city} сегодня:\n'
                                      f'Утро(6-11):\n\n'
                                      f'Погода: {mor_cond}\n'
                                      f'Температура: {mor_temp_min}℃...{mor_temp_max}℃\n'
                                      f'Ощущается как: {mor_feels_like}℃\n'
                                      f'Влажность: {mor_hum}%\n'
                                      f'Давление: {mor_pressure} мм рт. ст.\n'
                                      f'Скорость ветра: {mor_speed}м/с, направление: {mor_dir}\n\n'
                                      f'Рекомендации по одежде:\n{m_rec}\n\n'
                                      f'День(12-17):\n\n'
                                      f'Погода: {cond}\n'
                                      f'Температура: {temp_min}℃...{temp_max}℃\n'
                                      f'Ощущается как: {feels_like}℃\n'
                                      f'Влажность: {hum}%\n'
                                      f'Давление: {pressure} мм рт. ст.\n'
                                      f'Скорость ветра: {speed}м/с, направление: {direction}\n\n'
                                      f'Рекомендации по одежде:\n{rec}\n\n'
                                      f'Вечер(18-21):\n\n'
                                      f'Погода: {ev_cond}\n'
                                      f'Температура: {ev_temp_min}℃...{ev_temp_max}℃\n'
                                      f'Ощущается как: {ev_feels_like}℃\n'
                                      f'Влажность: {ev_hum}%\n'
                                      f'Давление: {ev_pressure} мм рт. ст.\n'
                                      f'Скорость ветра: {ev_speed}м/с, направление: {ev_dir}\n\n'
                                      f'Рекомендации по одежде:\n{ev_rec}\n\n'
                                      f'Ночь(22-5):\n\n'
                                      f'Погода: {n_cond}\n'
                                      f'Температура: {n_temp_min}℃...{n_temp_max}℃\n'
                                      f'Ощущается как: {n_feels_like}℃\n'
                                      f'Влажность: {n_hum}%\n'
                                      f'Давление: {n_pressure} мм рт. ст.\n'
                                      f'Скорость ветра: {n_speed}м/с, направление: {n_dir}\n\n'
                                      f'Рекомендации по одежде:\n{n_rec}\n\n')


def dir_trans(direction: dict) -> str:
    dir_dict = {'n': "C",
                'ne': "СВ",
                'e': 'В',
                'se': 'ЮВ',
                's': 'Ю',
                'sw': 'ЮЗ',
                'w': 'З',
                'nw': 'СЗ',
                'c': 'Штиль'
                }
    return dir_dict[direction]


def cond_trans(condition: dict) -> str:
    cond_dict = {'clear': "Ясно",
                 'partly-cloudy': "Малооблачно",
                 'cloudy': 'Облачно с прояснениями',
                 'overcast': 'Пасмурно',
                 'drizzle': 'Морось',
                 'light-rain': 'Небольшой дождь',
                 'rain': 'Дождь',
                 'moderate-rain': 'Умеренно сильный дождь',
                 'heavy-rain': 'Сильный дождь',
                 'continuous-heavy-rain': 'Длительный сильный дождь',
                 'showers': 'Ливень',
                 'wet-snow': 'Дождь со снегом',
                 'light-snow': 'Небольшой снег',
                 'snow': 'Снег',
                 'snow-showers': 'Снегопад',
                 'hail': 'Град',
                 'thunderstorm ': 'Гроза',
                 'thunderstorm-with-rain': 'Дождь с грозой',
                 'thunderstorm-with-hail': 'Гроза с градом',
                 }
    return cond_dict[condition]


def recommendations(feels_like: float, prec_type: float) -> str:
    if feels_like < -30:
        rec = f'Головной убор: теплая шапка\n' \
              f'Одежда:	подштаники, штаны, тёплые носки, теплая кофта, пуховик, шарф, варежки (перчатки)\n' \
              f'Обувь: зимние ботинки'
    elif -30 <= feels_like < -20:
        rec = f'Головной убор: теплая шапка\n' \
              f'Одежда:	подштаники,	 штаны, теплые носки, свитер/теплая кофта, пуховик, шарф, варежки (перчатки)\n' \
              f'Обувь: зимние ботинки'
    elif -20 <= feels_like < -10:
        rec = f'Головной убор: теплая шапка\n' \
              f'Одежда:	подштаники, штаны, свитер/кофта, пуховик, шарф, варежки (перчатки)\n' \
              f'Обувь: зимние ботинки'
    elif -10 <= feels_like < 0:
        rec = f'Головной убор: легкая шапка/кепка\n' \
              f'Одежда: подштаники, штаны, свитер/кофта, демисезонная куртка, перчатки\n' \
              f'Обувь: ботинки'
    elif 0 <= feels_like < 10:
        rec = f'Головной убор: кепка\n' \
              f'Одежда:	штаны/брюки, футболка/водолазка, пальто/ветровка\n' \
              f'Обувь: ботинки'
    elif 10 <= feels_like < 20:
        rec = f'Головной убор: кепка\n' \
              f'Одежда:	штаны/брюки/юбка/платье, футболка/легкая кофта, рубаха/кожанка/джинсовка\n' \
              f'Обувь: кроссовки'
    elif 20 <= feels_like < 30:
        rec = f'Головной убор: кепка/панама\n' \
              f'Одежда:	футболка/майка, юбка/шорты/брюки, платье\n' \
              f'Обувь: кроссовки, сандалии '
    elif feels_like >= 30:
        rec = f'Головной убор: кепка/панама\n' \
              f'Одежда: майка/футболка, шорты/юбка, платье, тканевый комбинезон\n' \
              f'Обувь: сланцы, сандалии'

    if 0 < prec_type < 3:
        rec = rec + f'\nБудет дождь, возьмите плащ/зонтик'
    return rec


bot.infinity_polling()
