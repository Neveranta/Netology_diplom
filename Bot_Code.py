from Config import access_token, community_token, db_url_object
from Core import VkTools
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from Data_Base import add_user, check_user, exact_lists
from sqlalchemy import create_engine, MetaData


engine = create_engine(db_url_object)
metadata = MetaData()

class Test_Bot:
    def __init__(self, community_token, access_token):
        self.vk = vk_api.VkApi(token=community_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(access_token)
        self.params = {}
        self.searches = []
        self.offset = 0


# Отправка сообщений
    def write_msg(self,user_id, message, attachment=None):
        self.vk.method('messages.send',
                  {'user_id': user_id,
                   'message': message,
                   'attachment': attachment,
                   'random_id': get_random_id(),
                   })

    def check_info(self,user_id, info):
        for item in info.keys():
            if info[item] is None:
                self.write_msg(user_id,
                               f'В профиле отсутствует информация о: {item}\n'
                               f'Необходимо предоставить данные в формате "{item} данные"')
                self.await_user_answer(user_id)

    def await_user_answer(self, user_id, *search):
        for reply in self.longpoll.listen():
            if reply.type == VkEventType.MESSAGE_NEW and reply.to_me:
                if reply.text.lower().split(' ')[0] == 'city':
                    self.params['city'] = self.vk_tools.get_city(reply.text.lower().split(' ')[1:])
                    self.write_msg(user_id, 'Данные о городе изменены')
                    break

                elif reply.text.lower() == 'избранное':
                    add_user(engine,user_id, search[0]['id'], search[0]['name'], False, True)
                    self.write_msg(user_id, 'Пользователь добавлен в избранное')
                    break

                elif reply.text.lower() == 'исключить из поиска':
                    add_user(engine, user_id, search[0]['id'], search[0]['name'], True, False)
                    self.write_msg(user_id, 'Пользователь добавлен в черный список')
                    break

                elif reply.text.lower() == 'просмотрено':
                    add_user(engine, user_id, search[0]['id'], search[0]['name'], False, False)
                    self.write_msg(user_id, 'Анкета добавлена в список просмотренных')
                    break

                elif reply.text.lower() == 'список избранного':
                    for user in exact_lists(engine,user_id,'favorites'):
                        self.write_msg(
                            user_id,
                            f'имя:{user.name} ссылка: https://vk.com/id{user.worksheet_id}')
                    break

                elif reply.text.lower() == 'список просмотренных анкет':
                    for user in exact_lists(engine, user_id, 'viewed'):
                        self.write_msg(
                            user_id,
                            f'имя:{user.name} ссылка: https://vk.com/id{user.worksheet_id}')
                    break

                elif reply.text.lower() == 'чёрный список':
                    for user in exact_lists(engine, user_id, 'black_list'):
                        self.write_msg(
                            user_id,
                            f'имя:{user.name} ссылка: https://vk.com/id{user.worksheet_id}')
                    break
                else:
                    break

    def send_photos(self, user_id, search):
        photos = self.vk_tools.get_photos(search['id'])
        photo_string = ' '
        for photo in photos:
            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'

        self.write_msg(
            user_id,
            f'имя:{search["name"]} ссылка: https://vk.com/id{search["id"]}',
            attachment=photo_string)

        self.write_msg(
            user_id,
            f'Добавить в избранное или исключить из поиска?\n'
            f'Если затрудняетесь с выбором - отправьте команду "Просмотрено" и анкета будет отмечена как просмотреная, а позже Вы сможете к ней вернуться')

        self.await_user_answer(user_id, search)


# Общение с пользователем
    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                # Основные команды для взаимодействия с пользователем
                if event.text.lower() == 'начать работу':
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.write_msg(event.user_id, f'Приветствую Вас {self.params["name"]}')
                    # Проверка данных пользователя для начала работы
                    self.check_info(event.user_id, self.params)

                elif event.text.lower() == 'поиск':
                    self.write_msg(
                        event.user_id, 'Начинаем поиск')
                    self.searches = self.vk_tools.search_users(self.params, self.offset)
                    lenght = len(self.searches)
                    search = self.searches.pop()

                    while check_user(engine, event.user_id, search['id']) is True or self.vk_tools.get_photos(search['id']) is None:
                        if self.searches:
                            search = self.searches.pop()

                        else:
                            self.offset += lenght
                            self.searches = self.vk_tools.search_users(self.params, self.offset)
                            search = self.searches.pop()

                    self.send_photos(event.user_id, search)

                elif event.text.lower() == 'просмотреть списки':
                    self.write_msg(
                        event.user_id, f'Уточните, какой именно список желаете просмотреть?\n'
                                        f'список избранного\n'
                                        f'чёрный список\n'
                                        f'список просмотренных анкет')
                    self.await_user_answer(event.user_id)

                elif event.text.lower() == 'пока' or event.text.lower() == 'до свиданья':
                    self.write_msg(event.user_id, 'До новых встреч')

                else:
                    self.write_msg(event.user_id, f'Не знаю, как ответить на Ваш вопрос \n'
                                   f'В настоящее время доступны команды: "начать работу", "поиск", "просмотреть списки", "пока"')


if __name__ == '__main__':

    test_bot = Test_Bot(community_token, access_token)
    test_bot.event_handler()