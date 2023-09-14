import json
from transliterate import translit

import vk_api
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

import keyboards
import utils


class Router:
    def __init__(self, api: vk_api.vk_api.VkApiMethod, pool: VkBotLongPoll):
        self.longPool = pool
        self.api = api

    def ask_to_start(self, user_id):
        return self.api.messages.send(user_id=user_id,
                                      message='Для доступа к функционалу бота отправьте "Начать"',
                                      random_id=get_random_id(),
                                      keyboard=keyboards.main_keyboard.get_keyboard())

    def default_msg(self, user_id):
        return self.api.messages.send(user_id=user_id,
                                      message='Функционал бота доступен с помощью клавиатуры, если у Вас ее нет, отправьте "Начать"',
                                      random_id=get_random_id())

    def main_menu(self, user_id):
        return self.api.messages.send(user_id=user_id,
                                      message=f'Добро пожаловать!\n Функционал бота доступен с помощью кнопок, ты можешь посмотреть погоду, пробки, афишу и курс валют',
                                      random_id=get_random_id(),
                                      keyboard=keyboards.main_keyboard.get_keyboard())

    def start_handler(self, user_id: int, db: dict):
        # Check if user is in db
        if user_id in db.keys():
            message_id = self.api.messages.send(user_id=user_id,
                                                message=f'Мы уже знакомы!\nВаш город:{db[user_id]["city"]}\nХотите его поменять?',
                                                random_id=get_random_id(),
                                                keyboard=keyboards.confirmation_keyboard.get_keyboard())
            for event in self.longPool.listen():
                if event.type == VkBotEventType.MESSAGE_EVENT:
                    if not event.obj.payload.get('value'):
                        # If user doesn't want to change his city, move to main menu
                        self.api.messages.delete(message_ids=[message_id],
                                                 delete_for_all=True)
                        return self.main_menu(user_id)
                    self.api.messages.delete(message_ids=[message_id],
                                             delete_for_all=True)
                    break
        else:
            # If user is not in db, trying to get his city info
            response = self.api.users.get(user_id=user_id,
                                          fields='city')[0]
            try:
                city = response['city']['title']
            except:
                print('Cannot retrieve city')
                city = None

            # If city successfully retrieved
            if city:
                message_id = self.api.messages.send(user_id=user_id,
                                                    message=f'Привет!\nВаш город:{city}?',
                                                    random_id=get_random_id(),
                                                    keyboard=keyboards.confirmation_keyboard.get_keyboard())
                for event in self.longPool.listen():
                    if event.type == VkBotEventType.MESSAGE_EVENT:
                        self.api.messages.delete(message_ids=[message_id],
                                                 delete_for_all=True)
                        if event.obj.payload.get('value'):
                            # If user confirmed that city info is right, add it to db, move to main menu
                            db[user_id] = {'city': city}
                            return self.main_menu(user_id)
                        break
        # Reachable in 3 scenarios:
        # 1. Saved user wants to change his city
        # 2. Cannot retrieve city info
        # 3. Retrieved city is not correct (according to user)
        self.api.messages.send(user_id=user_id,
                               message='Пожалуйста, введите свой город.',
                               random_id=get_random_id())
        for event in self.longPool.listen():
            if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
                db[user_id] = {'city': event.obj.message['text']}
                return self.main_menu(user_id)

    def traffic_handler(self, user_id, token, data, event):
        message_id = self.api.messages.send(user_id=user_id,
                                            message=f"Узнаем ситуацию на дорогах..(может занять время)",
                                            random_id=get_random_id())
        level = utils.get_traffic_level(token, data)
        self.api.messages.delete(message_ids=[message_id],
                                 delete_for_all=True)
        self.api.messages.send(user_id=user_id,
                               message=f'Баллов пробки сейчас: {level}',
                               random_id=get_random_id())

    def weather_handler(self, user_id, geo_token, weather_token, data, event):
        self.api.messages.sendMessageEventAnswer(
            event_id=event.object.event_id,
            user_id=event.object.user_id,
            peer_id=event.object.peer_id,
            event_data=json.dumps({"type": "show_snackbar", "text": "Вы в меню погоды"})
        )
        utils.get_weather_forecast(geo_token=geo_token,
                                   weather_token=weather_token,
                                   data=data)
        message_id = self.api.messages.send(user_id=user_id,
                                            message=f'Выберите день прогноза погоды:',
                                            random_id=get_random_id(),
                                            keyboard=keyboards.day_keyboard.get_keyboard())
        for event in self.longPool.listen():
            if event.type == VkBotEventType.MESSAGE_EVENT:
                self.api.messages.delete(message_ids=[message_id],
                                         delete_for_all=True)
                if event.obj.payload.get('value') == "Today":
                    return self.api.messages.send(user_id=user_id,
                                                  message=utils.create_weather_str(data['weather']['today']),
                                                  random_id=get_random_id())
                else:
                    return self.api.messages.send(user_id=user_id,
                                                  message=utils.create_weather_str(data['weather']['tomorrow']),
                                                  random_id=get_random_id())

    def afisha_handler(self, user_id, data, event):
        self.api.messages.sendMessageEventAnswer(
            event_id=event.object.event_id,
            user_id=event.object.user_id,
            peer_id=event.object.peer_id,
            event_data=json.dumps({"type": "show_snackbar", "text": "Вы в меню афиши"})
        )
        if 'afisha' not in data.keys():
            if data['city'] == "Москва":
                city = 'msk'
            elif data['city'] == 'Санкт-Петербург':
                city = 'spb'
            else:
                city = translit(data['city'].lower(), language_code='ru', reversed=True).replace(' ', '_').replace("'", "").replace('y', 'i')
            data['afisha'] = {'today': utils.get_afisha_info(f'https://www.afisha.ru/{city}/events/na-segodnya/'),
                              'tomorrow': utils.get_afisha_info(f'https://www.afisha.ru/{city}/events/na-zavtra/')
                              }
        message_id = self.api.messages.send(user_id=user_id,
                                            message=f'Выберите день показа афиши:',
                                            random_id=get_random_id(),
                                            keyboard=keyboards.day_keyboard.get_keyboard())
        for event in self.longPool.listen():
            if event.type == VkBotEventType.MESSAGE_EVENT:
                self.api.messages.delete(message_ids=[message_id],
                                         delete_for_all=True)
                if event.obj.payload.get('value') == "Today":
                    return self.api.messages.send(user_id=user_id,
                                                  message=utils.get_afisha_str(data['afisha']['today']),
                                                  random_id=get_random_id())
                else:
                    return self.api.messages.send(user_id=user_id,
                                                  message=utils.get_afisha_str(data['afisha']['tomorrow']),
                                                  random_id=get_random_id())

    def exchange_handler(self, user_id, data):
        utils.get_exchange_rates(data)
        return self.api.messages.send(user_id=user_id,
                                      message=utils.create_exchange_str(data['exchange_rates']),
                                      random_id=get_random_id())
