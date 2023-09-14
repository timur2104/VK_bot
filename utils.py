from selenium import webdriver
from selenium.webdriver.common.by import By

import requests
import json
from bs4 import BeautifulSoup
from tabulate import tabulate


def create_exchange_str(data):
    exc_str = f"Курс рубля к востребованным валютам:\nДоллар США: {data['USD']:.4}₽\nЕвро: {data['EUR']:.4}₽\nЙена: {data['CNY']:.4}₽"
    return exc_str


def create_weather_str(data):
    weather_str = f'Температура: {data["temp"]}°C (ощущается как {data["feels_like"]}°C)\nДавление: {data["pressure_mm"]} мм.рт.ст.\nВлажность: {data["humidity"]}%\nУльтрафиолетовый индекс: {data["uv_index"]}\n'
    return weather_str


def get_afisha_str(data):
    print(data)
    event_str = "Меропроятие: {}\nЦена: {}\nСсылка: {}\n\n"
    output = ""
    for event in data:
        output += event_str.format(*(event.values()))

    return output
    # return tabulate(data, headers=['Название', 'Цена', 'Ссылка'], tablefmt="github")


def find_coordinate(token, data):
    # Finding coordinates of city
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": data['city'],
        "apikey": token,
        "format": "json",
    })
    coordinates = [c.split(' ') for c in list(
        json.loads(response.text)['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['boundedBy'][
            'Envelope'].values())]
    # Given coordinates are upper-left and down-right coordinates -> finding their middle
    data['coord'] = (float(coordinates[0][0]) + float(coordinates[1][0])) / 2, (float(coordinates[0][1]) + float(coordinates[1][1])) / 2


def get_traffic_level(token, data):
    if "coord" not in data.keys():
        find_coordinate(token, data)
    if 'traffic_level' not in data.keys():
        url = f"https://yandex.ru/maps/probki/?from=api-maps&ll={data['coord'][0]}%2C{data['coord'][1]:.6}&origin=jsapi_2_1_79&z=12"

        op = webdriver.ChromeOptions()
        op.add_argument('--headless')
        driver = webdriver.Chrome(op)
        driver.get(url)
        max_iter, traffic_level = 1000, ""
        for i in range(max_iter):
            traffic_level = driver.find_element(By.CLASS_NAME, 'traffic-raw-icon__text').text
            if traffic_level != "":
                break
        if traffic_level == "":
            traffic_level = 0
        data['traffic_level'] = traffic_level
    return data['traffic_level']


def get_weather_forecast(geo_token, weather_token, data):
    if "coord" not in data.keys():
        find_coordinate(geo_token, data)
    if 'weather' not in data.keys():
        base_url = "https://api.weather.yandex.ru/v2/forecast?"
        response = requests.get(base_url,
                                params={
                                    "lat": data['coord'][1],
                                    "lon": data['coord'][0],
                                    "lang": "ru_RU"},
                                headers={
                                    "X-Yandex-API-Key": weather_token}
                                )
        resp_dict = json.loads(response.text)
        data['weather'] = {'today': resp_dict['fact'],
                           'tomorrow': resp_dict['forecasts'][1]['parts']['day_short']}


def get_afisha_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    top_5 = soup.find_all('div', class_='wsXlA pZeTF SUiYd')[:5]
    afisha = []
    for event in top_5:
        try:
            price = event.find('span', class_='Ef2IR jEnBm MDhmt ouqW6').find('span').text
        except:
            price = '-'
        afisha.append({'title': event.find('div', class_='mQ7Bh').text,
                       'price': price,
                       'link': 'https://www.afisha.ru' + event.find('a', class_='vcSoT b6DKO jkBWH f5gWK')['href']
         })
    for event in afisha:
        if event['price'] == 'Билеты':
            event['price'] = '-'
    return afisha


def get_exchange_rates(data):
    if 'exchange_rates' not in data.keys():
        base_url = 'http://api.exchangeratesapi.io/v1/latest'
        response = requests.get(base_url,
                                params={
                                    'access_key': 'a2849c719f9c0e3abd4cd246c0848ff7'
                                }).json()
        data['exchange_rates'] = {
            'EUR': response['rates']['RUB'],
            'USD': response['rates']['RUB'] / response['rates']["USD"],
            'GBP': response['rates']['RUB'] / response['rates']["GBP"],
            'CNY': response['rates']['RUB'] / response['rates']["CNY"],
        }