import json
import os

import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from handlers import Router


class Server:
    def __init__(self, api_token, weather_token, geo_token, group_id, exchange_token):
        session = vk_api.VkApi(token=api_token)

        self.weather_token = weather_token
        self.geo_token = geo_token
        self.exchange_token = exchange_token

        self.api = session.get_api()
        self.longPool = VkBotLongPoll(session, group_id)
        self.router = Router(self.api, self.longPool)
        self.database = {}

    def start_server(self):
        for event in self.longPool.listen():
            if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
                if event.obj.message['text'] == 'Начать':
                    self.last_msg = self.router.start_handler(event.obj.message['from_id'], self.database)
                # Bot main functionality only accessible after starting command
                else:
                    self.router.default_msg(event.obj.message['from_id'])
            elif event.type == VkBotEventType.MESSAGE_EVENT:
                print(self.database)

                if event.obj.payload.get('value') == 'Погода':
                    self.router.weather_handler(user_id=event.obj.get('user_id'),
                                                geo_token=self.geo_token,
                                                weather_token=self.weather_token,
                                                data=self.database[event.obj.get('user_id')],
                                                event=event)
                elif event.obj.payload.get('value') == 'Пробка':
                    self.router.traffic_handler(user_id=event.obj.get('user_id'),
                                                token=self.geo_token,
                                                data=self.database[event.obj.get('user_id')],
                                                event=event)
                elif event.obj.payload.get('value') == 'Афиша':
                    self.router.afisha_handler(user_id=event.obj.get('user_id'),
                                               data=self.database[event.obj.get('user_id')],
                                               event=event)
                elif event.obj.payload.get('value') == 'Валюта':
                    self.router.exchange_handler(user_id=event.obj.get('user_id'),
                                                 data=self.database[event.obj.get('user_id')])



if __name__ == '__main__':
    BOT_API_KEY = os.getenv('BOT_API_KEY')
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    GEO_API_KEY = os.getenv('GEO_API_KEY')
    GROUP_ID = os.getenv('GROUP_ID')
    EXCHANGE_API_KEY = os.getenv('EXCHANGE_API_KEY')
    Server(BOT_API_KEY, WEATHER_API_KEY, GEO_API_KEY, GROUP_ID, EXCHANGE_API_KEY).start_server()
