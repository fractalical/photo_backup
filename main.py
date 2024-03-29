from classes import VK, Yandex
import datetime
import json
import logging
import string
import configparser

logging.basicConfig(
    level=logging.INFO,
    filename="py_log.log",
    filemode="a",
    format="%(asctime)s %(levelname)s %(message)s"
)


def get_photo(token_vk, user_id_vk, photo_album_vk, photo_count):
    vk = VK(token_vk, user_id_vk)
    photos = vk.get_photo(photo_album_vk, photo_count)
    return photos


def get_data(photos):
    photos_json = []
    links = {}
    for photo in photos['response']['items']:
        likes = str(photo['likes']['count'])
        date = photo['date']
        date = datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d')
        photo_list = sorted(photo['sizes'], reverse=True, key=lambda x: x['height'])
        url = photo_list[0]['url']
        name = f'{likes}.jpg'
        if name in links:
            name = f'{likes}_{date}.jpg'
            if name in links:
                count = list(links.keys()).count(name)
                name = f'{likes}_{date}_({count}).jpg'
        links[name] = url
        photo_data = {"file_name": name, "size": photo_list[0]['type']}
        photos_json.append(photo_data)
    return photos_json, links


def data_upload(token_yandex, path, photos_json, links):
    ya_uploader = Yandex(token_yandex)
    disk_path = path
    folder = ya_uploader.get_upload_link(disk_path)
    image = ''
    if folder == 201:
        logging.info(f'Folder "{disk_path}" created.')
    elif folder == 409:
        logging.info(f'Folder "{disk_path}" exist.')
    for name, link in links.items():
        image = ya_uploader.upload_file_to_disk(disk_path, name, link)
    if image == 202:
        logging.info(f'Images was uploaded to yandex.disk.')
    else:
        logging.error(f'Images was NOT uploaded to yandex.disk.')

    with open("photo_data.json", mode="w") as json_file:
        json.dump(photos_json, json_file, indent=4, ensure_ascii=False)


def backup(path, user_id_vk, photo_album_vk,
           token_vk, token_yandex, photo_count):
    logging.info(f'Backup starting.')
    photos = get_photo(token_vk, user_id_vk, photo_album_vk, photo_count)
    if photos.get('response', 'error') == 'error':
        logging.error(f'Images was NOT gotten.')
        print('Фотографии не были скопированы.\nПроверьте введённые данные!')
    else:
        photos_json, links = get_data(photos)
        if len(photos_json) > 0:
            logging.info(f'Images was gotten.')
            data_upload(token_yandex, path, photos_json, links)
            print('Фотографии успешно скопированы.')
        else:
            logging.error(f'Images was NOT gotten.')
            print('Фотографии не были скопированы.\nПроверьте введённые данные!')


def main():
    config = configparser.ConfigParser()
    config.read("tokens.ini")
    ya_token = config['TOKENS']['ya_token']
    access_token = config['TOKENS']['access_token']
    letters = set(string.ascii_letters) | set(string.digits) | set('_')
    user_id = input('Введите id или username пользователя VK:\n')
    albums = {1: 'profile', 2: 'wall'}
    disk_path = input('Введите название папки (латиницей) для копирования фотографий:\n'
                      'Или нажмите "enter" для выбора папки по умолчанию ("netology")\n')
    while True:
        if disk_path == "":
            disk_path = 'netology'
        elif all([char in letters for char in disk_path]):
            break
        else:
            disk_path = input(
                'Введено недопустимое название папки.\n'
                'Введите название папки (латиницей) для копирования фотографий:\n')
    count = input('Введите количество фотографик для копирования:\n'
                  'Или нажмите "enter" для выбора количества по умолчанию (5)\n')
    while True:
        if count.isdigit():
            count = int(count)
            break
        elif count == "":
            count = '5'
        else:
            count = input('Введено не число.\nВведите количество фотографий для копирования:\n')
    run = True
    while run:
        number_photo_album = input('Выберите альбов для копирования фотографий:\n'
                                   '1 - Фото из профиля\n'
                                   '2 - Фото со стены\n')
        if number_photo_album in ('1', '2'):
            photo_album = albums[int(number_photo_album)]
            run = False
        else:
            print('Неверный номер альбома.')
    backup(path=disk_path, user_id_vk=user_id, photo_album_vk=photo_album,
           token_vk=access_token, token_yandex=ya_token, photo_count=count)


if __name__ == '__main__':
    main()
