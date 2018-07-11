#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import errno
import os, sys
import tempfile
from bs4 import BeautifulSoup
from argparse import ArgumentParser
import urllib, urllib2, urlparse
from urllib import urlopen
from urllib import quote
from kbbi import KBBI
from googletrans import Translator
import requests
import time, json, random
import wikipedia

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageTemplateAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URITemplateAction,
    PostbackTemplateAction, DatetimePickerTemplateAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    VideoSendMessage, AudioSendMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent
)

translator = Translator()
wiki_settings = {}


app = Flask(__name__)

line_bot_api = LineBotApi('3Qkr3SNlqPpzhZ0FYrPZupD/TcYAxK0+Kdh7J0u3JzH2qQkzZVGVjivLQ32olTcPIWOPg/jSaRvyekXU3gsLRs5BLHgCZEw1sHcTZoEy8yMOnTuXGvqh+27/RHYrQHVjTibPpU/YsK+qDXR+mrgEEQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('2aeccaa784bd1a4d7f86f6516d91851a')

# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):

    text=event.message.text
    groupId = event.source.group_id
    userId = event.source.user_id
    profile = line_bot_api.get_profile(userId)
    profile_name = profile.display_name
    profile_picture = profile.picture_url
    profile_sm = profile.status_message
    
    if isinstance(event.source, SourceGroup):
        subject = line_bot_api.get_group_member_profile(event.source.group_id,
                                                        event.source.user_id)
        set_id = event.source.group_id
    elif isinstance(event.source, SourceRoom):
        subject = line_bot_api.get_room_member_profile(event.source.room_id,
                                                   event.source.user_id)
        set_id = event.source.room_id
    else:
        subject = line_bot_api.get_profile(event.source.user_id)
        set_id = event.source.user_id
    
    def split1(text):
        return text.split('/wolfram ', 1)[-1]
        
    def split2(text):
        return text.split('/kbbi ', 1)[-1]
        
    def split3(text):
        return text.split('/echo ', 1)[-1]

    def split4(text):
        return text.split('/wolframs ', 1)[-1]
    
    def split5(text):
        return text.split('/trans ', 1)[-1]
    
    def split6(text):
        return text.split('/wiki ', 1)[-1]
    
    def split7(text):
        return text.split('/wikilang ', 1)[-1]
        
    def split8(text):
        return text.split('/urban ', 1)[-1]

    def split9(text):
        return text.split('/ox ', 1)[-1]
        
    def trans(word):
        sc = 'en'
        to = 'id'
        
        if word[0:].lower().strip().startswith('sc='):
            sc = word.split(', ', 1)[0]
            sc = sc.split('sc=', 1)[-1]
            word = word.split(', ', 1)[1]
    
        if word[0:].lower().strip().startswith('to='):
            to = word.split(', ', 1)[0]
            to = to.split('to=', 1)[-1]
            word = word.split(', ', 1)[1]
            
        if word[0:].lower().strip().startswith('sc='):
            sc = word.split(', ', 1)[0]
            sc = sc.split('sc=', 1)[-1]
            word = word.split(', ', 1)[1]
            
        return translator.translate(word, src=sc, dest=to).text
        
    def wiki_get(keyword, set_id, trim=True):
    
        try:
            wikipedia.set_lang(wiki_settings[set_id])
        except KeyError:
            wikipedia.set_lang('en')

        try:
            result = wikipedia.summary(keyword)

        except wikipedia.exceptions.DisambiguationError:
            articles = wikipedia.search(keyword)
            result = "{} disambiguation:".format(keyword)
            for item in articles:
                result += "\n{}".format(item)
        except wikipedia.exceptions.PageError:
            result = "{} not found!".format(keyword)

        else:
            if trim:
                result = result[:2000]
                if not result.endswith('.'):
                    result = result[:result.rfind('.')+1]
        return result
        
    def wiki_lang(lang, set_id):
    
        langs_dict = wikipedia.languages()
        if lang in langs_dict.keys():
            wiki_settings[set_id] = lang
            return ("Language has been changed to {} successfully."
                    .format(langs_dict[lang]))

        return ("{} not available!\n"
                "See meta.wikimedia.org/wiki/List_of_Wikipedias for "
                "a list of available languages, and use the prefix "
                "in the Wiki column to set the language."
                .format(lang))  
    
    def find_kbbi(keyword, ex=True):

        try:
            entry = KBBI(keyword)
        except KBBI.TidakDitemukan as e:
            result = str(e)
        else:
            result = "Definisi {}:\n".format(keyword)
            if ex:
                result += '\n'.join(entry.arti_contoh)
            else:
                result += str(entry)
        return result
    
    if text == '/help':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage('Hai kak..ketik /cmd untuk menu lainnya.'))

    elif text == '/cmd':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("Menu \n"
                            "/about\n/help\n/profilku\n/bye\n/ppku\n/idku\n/samehadaku\n/sp\n"
                            "/echo {teks}\n/kbbi {teks}\n/gambar {teks}\n/lokasi {teks}\n"
                            "/trans {teks}\n/wiki {teks}\n/wikilang {teks}\n/lagu {teks}\n"
                            "/hitung {teks}\n/cariyoutube {teks}\n/zodiak {teks}\n"))
    elif text == '/about':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("Hai kak..nama saya Shin Chan \n"
                                "saya akan membuat obrolan kamu jadi makin seru."))

    elif text == '/bye':
        if (userId != 'Uf12a33117e93064e553855f6a4ce80eb'):
            line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="Gak mau ah, Kamu kan bukan Abangku!"))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Hai kak "+profile_name+" Aku keluar dulu ya..!"))
            line_bot_api.leave_group(groupId)

    elif text=='/kbbi':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('Ketik /kbbi {input}'))

    elif text=='/trans':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('Ketik /trans sc={}, to={}, {text}'))
    
    elif text=='/wiki':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('Ketik /wiki {text}'))
                
    elif text=='/wikilang':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('Ketik /wikilang {language_id}'))

    elif text == '/idku':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Hai "+profile_name+", ini adalah id kamu: "+userId))


    elif text == '/profilku':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="~ [ R E S U L T ] ~\n\n Nama: "+profile_name+"\n Foto Profil: "+profile_picture+"\n Pesan Status: "+profile_sm))

    elif text == "/ppku":
        profile = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
        url = profile.picture_url
        image_message = ImageSendMessage(
            original_content_url=url,
            preview_image_url=url
        )
        line_bot_api.reply_message(
            event.reply_token, image_message)

    elif '/apakah ' in text:
        rep = text.replace("/apakah ","")
        txt = ["Ya","Tidak","Bisa Jadi","Mungkin","Hoax","Coba tanya lagi"]

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=random.choice(txt)))


    elif '/gambar' in text:
        separate = text.split(" ")
        search = text.replace(separate[0] + " ","")
        r = requests.get("http://rahandiapi.herokuapp.com/imageapi?key=betakey&q={}".format(search))
        data = r.text
        data = json.loads(data)

        if data["result"] != []:
            items = data["result"]
            path = random.choice(items)
            a = items.index(path)
            b = len(items)

        image_message = ImageSendMessage(
            original_content_url=path,
            preview_image_url=path
        )

        line_bot_api.reply_message(
            event.reply_token,
            image_message
        )


    elif '/zodiak ' in text:
        tanggal = text.replace("/zodiak ","")
        r = requests.get('https://script.google.com/macros/exec?service=AKfycbw7gKzP-WYV2F5mc9RaR7yE3Ve1yN91Tjs91hp_jHSE02dSv9w&nama=siapa&tanggal='+tanggal)
        data = r.text
        data = json.loads(data)
        lahir = data["data"]["lahir"]
        usia = data["data"]["usia"]
        ultah = data["data"]["ultah"]
        zodiak = data["data"]["zodiak"]

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="== I N F O R M A S I ==\n"+"Date Of Birth : "+lahir+"\nAge : "+usia+"\nUltah : "+ultah+"\nZodiak : "+zodiak+"\n== I N F O R M A S I =="))

    elif '/lokasi' in text:
        separate = text.split(" ")
        search = text.replace(separate[0] + " ","")
        req = requests.get("https://time.siswadi.com/pray/{}".format(search))
        data = req.text
        data = json.loads(data)
        add = data['location']['address']
        lat = data['location']['latitude']
        lon = data['location']['longitude']

        location_message = LocationSendMessage(
            title='Lokasi',
            address=add,
            latitude=lat,
            longitude=lon
        )

        line_bot_api.reply_message(
            event.reply_token,
            location_message
        )


    if 'meet?' in text:
        sticker_message = StickerSendMessage(
            package_id='1',
            sticker_id='1'
        )

        line_bot_api.reply_message(
            event.reply_token,
            sticker_message
        )


    elif '/hitung' in text:
        separate = text.split(" ")
        search = text.replace(separate[0] + " ","")
        if search == None:
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Untuk cara menggunakan kalkulator, ketik /hitung 'nominal'\n\nContoh: /hitung (3e+2i)*(2e-3i)\n\nSelamat mencoba (((o(*ﾟ▽ﾟ*)o)))"))
        else:
            with requests.session() as web:
                web.headers["user-agent"] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
            r = web.get("http://api.mathjs.org/v4/?expr={}".format(urllib2.quote(search)))
            data=r.text
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=str(data)))


    elif text == '/sp':
        start = time.time()
        elapsed_time = time.time() - start
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=format(elapsed_time)))


    elif '/cariyoutube ' in text:
        query = text.replace("/cariyoutube ","")
        with requests.session() as s:
            s.headers['user-agent'] = 'Mozilla/5.0'
            url = 'http://www.youtube.com/results'
            params = {'search_query': query}
            r = s.get(url, params=params)
            soup = BeautifulSoup(r.content, 'html5lib')
            num = 0
            hasil = ""
            for a in soup.select('.yt-lockup-title > a[title]'):
                num += 1
                if '&list=' not in a['href']:
                    hasil += "".join((a["title"],"\nhttps://www.youtube.com" + a["href"],"\n\n"))
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=hasil))


    elif '/lagu ' in text:
        query = text.replace("/lagu ","")
        cond = query.split("|")
        search = cond[0]
        result = requests.get("http://api.ntcorp.us/joox/search?q={}".format(search))
        data = result.text
        data = json.loads(data)
        if len(cond) == 1:
            num = 0
            ret_ = "╔══[ Result Music ]"
            for music in data["result"]:
                num += 1
                ret_ += "\n╠ {}. {}".format(num, music["single"])
            ret_ += "\n╚══[ Total {} Music ]".format(len(data["result"]))
            ret_ += "\n\nUntuk Melihat Details Music, silahkan gunakan command /lagu {}|「number」".format(search)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=ret_))
        elif len(cond) == 2:
            num = int(cond[1])
            if num <= len(data["result"]):
                music = data["result"][num - 1]
                result = requests.get("http://api.ntcorp.us/joox/song_info?sid={}".format(music["sid"]))
                data = result.text
                data = json.loads(data)
                if data["result"] != []:
                    ret_ = "╔══[ Music ]"
                    ret_ += "\n╠ Title : {}".format(data["result"]["song"])
                    ret_ += "\n╠ Album : {}".format(data["result"]["album"])
                    ret_ += "\n╠ Size : {}".format(data["result"]["size"])
                    ret_ += "\n╠ Link : {}".format(data["result"]["mp3"][0])
                    ret_ += "\n╚══[ Finish ]"
                    image_message = ImageSendMessage(
                        original_content_url=data["result"]["img"],
                        preview_image_url=data["result"]["img"]
                    )
 #                   line_bot_api.reply_message(
 #                       event.reply_token,
 #                       TextSendMessage(text=ret_))
 #                   return

                    
                    line_bot_api.reply_message(
                        event.reply_token,
                        image_message
                    )
                    return
    
    elif text[0:].lower().strip().startswith('/kbbi '):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(find_kbbi(split2(text))))
            
    elif text[0:].lower().strip().startswith('/echo ') :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(split3(text)))
            
    elif text[0:].lower().strip().startswith('/trans ') :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(trans(split5(text))))
    
    elif text[0:].lower().strip().startswith('/wiki ') :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(wiki_get(split6(text), set_id=set_id)))
            
    elif text[0:].lower().strip().startswith('/wikilang ') :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(wiki_lang(split7(text), set_id=set_id)))
            
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        LocationSendMessage(
            title=event.message.title, address=event.message.address,
            latitude=event.message.latitude, longitude=event.message.longitude
        )
    )

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=event.message.package_id,
            sticker_id=event.message.sticker_id)
    )
    
# Other Message Type
@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_content_message(event):
    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    elif isinstance(event.message, VideoMessage):
        ext = 'mp4'
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
    else:
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '.' + ext
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save content.'),
            TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
        ])
        
@handler.add(MessageEvent, message=FileMessage)
def handle_file_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix='file-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '-' + event.message.file_name
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save file.'),
            TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
        ])
        
@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text='Got follow event'))


@handler.add(UnfollowEvent)
def handle_unfollow():
    app.logger.info("Got Unfollow event")


@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='Hi, Aku Shin Chan jangan lupa ADD aku dan jadikan obrolanmu jadi tambah seru 􀄃􀆀sparkling eyes􏿿 '))
        
@handler.add(LeaveEvent)
def handle_leave():
    app.logger.info("Bye")


@handler.add(PostbackEvent)
def handle_postback(event):
    if event.postback.data == 'ping':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text='pong'))
    elif event.postback.data == 'datetime_postback':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.params['datetime']))
    elif event.postback.data == 'date_postback':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.params['date']))


@handler.add(BeaconEvent)
def handle_beacon(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text='Got beacon event. hwid={}, device_message(hex string)={}'.format(
                event.beacon.hwid, event.beacon.dm)))
    
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
