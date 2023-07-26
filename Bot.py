import aiogram as aio # Для тг бота
import asyncio # Асинкио. Обычно использую для асинхронных задержек, и для создание асинхронных потоков
import json # Для загрузки json файлов
import requests as req # Для запросов к API
from pytube import YouTube, exceptions # Для скачивания видео с ютуб
import subprocess as subp
import os
import shutil

CACHENAME = "cache"
DEFTYPE = "webm"
DEFISVID = False

CFGf = open("sp_bot_data.spbconfig", 'r')
CFG = json.load(CFGf)
CFGf.close()

shutil.rmtree(CACHENAME, ignore_errors = True)

b = aio.Bot(token=CFG['token'])
dp = aio.Dispatcher(b)

def song_link_request(link: str): # Отдельная функция запроса к song.link
    resp = req.get("https://api.song.link/v1-alpha.1/links", params={'url': link}).json() # Реквест
    if not "youtube" in resp['linksByPlatform'].keys(): return False # Возвращает False если song.link не нашел нужный ролик на ютуб
    return resp['linksByPlatform']['youtube']['entityUniqueId'].split('::')[1] # Возвращаем id ролика на youtube

def download_youtube(yt_id: str, is_video = DEFISVID, _type=DEFTYPE):
    vid = YouTube("https://www.youtube.com/watch?v=" + yt_id)
    if is_video:
        stream = vid.streams.filter(file_extension = _type)[0]
        stream.download(f"{CACHENAME}", f"{yt_id}.{_type}")
    if not is_video:
        stream = vid.streams.filter(file_extension = _type, only_audio=True)[0]
        stream.download(f"{CACHENAME}", f"{yt_id}.{_type}")
    return vid.title

def convert_to_mp3(fid: str, _type='webm'):
    subp.run(f"ffmpeg -i {CACHENAME}/{fid}.{_type} {CACHENAME}/{fid}.mp3", shell=True)


@dp.message_handler(commands=['start'])
async def c_start(msg):
    await msg.answer("Привет! Я бот который может скачивать музыку из спотифай в формате mp3\n\
Но, я не скачиваю песню на прямую со спотифая, я использую сервис который ищет подобную песню на ютубе, и скачивает её\n\n\
Для того что бы начать работу, отправь мне ссылку на трек")

@dp.message_handler(content_types=aio.types.ContentType.TEXT)
async def _text(msg):
    if msg.text.startswith("https://"):
        pass
    else:
        await msg.reply("Кажется ты отправил не ссылку на трек")
        return
    _msg = await msg.reply("Начал работать над песней...")
    _id = song_link_request(msg.text)
    if not _id:
        await _msg.delete()
        await msg.reply("Сторонний сервис не нашел похожее видео на ютуб")
        return
    _msg = await _msg.edit_text(_msg.text + f"\nВидео на ютуб найдено ( https://youtu.be/{_id} ), начинаю скачивать")
    try: title = download_youtube(_id)
    except exceptions.VideoUnavailable:
        await _msg.delete()
        await msg.reply("Видео недоступно")
        return
    _msg = await _msg.edit_text(_msg.text + "\nВидео скачано, преобразовываю в .mp3")
    convert_to_mp3(_id)
    os.mkdir(f"{CACHENAME}/"+_id)
    os.replace(f"{CACHENAME}/{_id}.mp3", f"{CACHENAME}/{_id}/{title}.mp3")
    os.remove(f"{CACHENAME}/{_id}.webm")
    _msg = await _msg.edit_text(_msg.text + "\nПесня готова!")
    await b.send_audio(msg.chat.id, aio.types.InputFile(f"{CACHENAME}/{_id}/{title}.mp3"), reply_to_message_id=msg.message_id)
    os.remove(f"{CACHENAME}/{_id}/{title}.mp3")
    os.removedirs(f"{CACHENAME}/{_id}")
    


def start_bot_Alright():
    aio.executor.start_polling(dp)

if __name__ == "__main__":
    start_bot_Alright()


def example():
    _id = song_link_request(input())
    title = download_youtube(_id)
    convert_to_mp3(_id)
    os.mkdir("cache/"+_id)
    os.replace(f"cache/{_id}.mp3", f"cache/{_id}/{title}.mp3")
    os.remove(f"cache/{_id}.webm")
