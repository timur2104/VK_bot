from vk_api.keyboard import VkKeyboard, VkKeyboardColor

main_keyboard = VkKeyboard(inline=False)
main_kb_buttons = ['Погода', 'Пробка', 'Афиша', 'Валюта']

for button in main_kb_buttons:
    main_keyboard.add_callback_button(button, payload={"value": button})

confirmation_keyboard = VkKeyboard(inline=True)
confirmation_keyboard.add_callback_button('Да', color=VkKeyboardColor.POSITIVE, payload={'value': True})
confirmation_keyboard.add_callback_button('Нет', color=VkKeyboardColor.NEGATIVE, payload={'value': False})

empty_keyboard = {'keyboard': {
    "one_time": False,
    "buttons": []
}}

day_keyboard = VkKeyboard(inline=True)
day_keyboard.add_callback_button('Сегодня', payload={'value': "Today"})
day_keyboard.add_callback_button('Завтра', payload={'value': "Tomorrow"})
