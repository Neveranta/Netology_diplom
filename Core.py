from Config import access_token
import vk_api
from vk_api.exceptions import ApiError
from datetime import datetime


class VkTools:
    def __init__(self, access_token):
        self.vkapi = vk_api.VkApi(token=access_token)

    def bdate_to_age(self,bdate):
        if bdate is not None:
            user_year = bdate.split('.')[2]
            now = datetime.now().year
            return now - int(user_year)
        else:
            return 'Возраст не указан'

    def get_profile_info(self, user_id):
        try:
            info, = self.vkapi.method('users.get',
                                     {'user_id': user_id,
                                      'fields': 'city,sex,bdate,relation,home_town'
                                      }
                                     )
        except ApiError as e:
            info = {}
            print(f'Ошибка = {e}')
        result = {
            'name': (info['first_name'] + ' ' + info['last_name']),
            'sex': info.get('sex'),
            'city': info.get('city')['id'] if info.get('city') is not None else None,
            'age': self.bdate_to_age(info.get('bdate')),
            'relation': info.get('relation')
                }
        return result

    def search_users(self,params,offset):
        try:
            users = self.vkapi.method('users.search',
                                      {
                                        'count': 20,
                                        'offset': offset,
                                        'city': params['city'],
                                        'sex': 1 if params['sex'] == 2 else 2,
                                        'has_photo': 1,
                                        'age_from': params['age']-3,
                                        'age_to': params['age']+3,
                                        'is_closed': False,
                                        'relation': 6
                                      }
                                      )

        except ApiError as e:
            print(f'Ошибка = {e}')

        result = []

        for user in users['items']:
            if user['is_closed'] is False:
                result.append({'id': user['id'],
                               'name': user['first_name'] + ' ' + user['last_name']})

        return result

    def get_photos(self, id):
        try:
            photos = self.vkapi.method('photos.get',
                                      {'owner_id': id,
                                       'album_id': 'profile',
                                       'extended': 1})
        except ApiError as e:
            photos={}
            print(f'Ошибка = {e}')

        result = [{'owner_id': item['owner_id'],
                'id': item['id'],
                'likes': item['likes']['count'],
                'comments': item['comments']['count']}
                for item in photos['items']]

        # сортировка по лайкам и комментам
        result.sort(key=lambda x: x['likes'] + x['comments'], reverse=True)
        if len(result) >= 3:
            return result[:3]
        else:
            return None

    def get_city(self, city_title):
        try:
            city_id = self.vkapi.method('database.getCities',
                                      {
                                        'q': city_title,
                                        }
                                      )

        except ApiError as e:
            print(f'Ошибка = {e}')
        result = city_id['items'][0]['id']
        return result


if __name__ == '__main__':
    user_id = ' '
    tools = VkTools(access_token)
    params = tools.get_profile_info(user_id)
    search = tools.search_users(params,10)
    search_result=search.pop()
    photos=tools.get_photos(search_result['id'])
    city = tools.get_city('Екатеринбург')
