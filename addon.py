import xbmcplugin, xbmcgui, xbmcaddon
import cookielib
import re, os, time
import urllib, urllib2
import sys
import json
import HTMLParser
import calendar
from datetime import datetime, timedelta
import time
import cookielib
import base64
import requests
import xmltodict
import m3u8
import xbmcvfs

settings = xbmcaddon.Addon(id='plugin.video.plp')
APP_CONFIG_URL = settings.getSetting(id="config_url")
APP_USER_AGENT_STRING = settings.getSetting(id="user_agent")
ROOTDIR = xbmcaddon.Addon(id='plugin.video.plp').getAddonInfo('path')
ADDON_PROFILE = xbmc.translatePath(xbmcaddon.Addon(id='plugin.video.plp').getAddonInfo('profile'))
ADDON_HANDLE = int(sys.argv[1])
teams = []

import urlparse

if not xbmcvfs.exists(ADDON_PROFILE):
    xbmcvfs.mkdir(ADDON_PROFILE)

cookie_file = os.path.join(ADDON_PROFILE, 'cookie_file')
http_session = requests.Session()
cookie_jar = cookielib.LWPCookieJar(cookie_file)

try:
    cookie_jar.load(ignore_discard=True, ignore_expires=True)
except IOError:
    pass

http_session.cookies = cookie_jar

#Get settings if stored on file
if not xbmcvfs.exists(ADDON_PROFILE+'urls.xml'):
    req = http_session.get(APP_CONFIG_URL, params=None, headers=None, allow_redirects=False)
    s_w_data = req.content
    text_file = open(ADDON_PROFILE+"urls.xml", "w")
    text_file.write(s_w_data)
    text_file.close()
        
#Ensure file isn't corrupt

try:
    text_file = open(ADDON_PROFILE+"urls.xml", "r")
    s_w_data = text_file.read()
    text_file.close()
    s_w_data_dict = xmltodict.parse(s_w_data)
except:
    s_w_data = ''
    xbmcvfs.delete(ADDON_PROFILE+'urls.xml')
    req = http_session.get(APP_CONFIG_URL, params=None, headers=None, allow_redirects=False)
    s_w_data = req.content
    print('##############' + s_w_data)
    text_file = open(ADDON_PROFILE+"urls.xml", "w")
    text_file.write(s_w_data)
    text_file.close()
    s_w_data_dict = xmltodict.parse(s_w_data)
    pass

ROOT_URL = s_w_data_dict['result']['appURL']['locDLServer'].replace('/home','/')
SCHEDULE_URL = s_w_data_dict['result']['appURL']['locSchedule'] + '?format=json'
HIGHLIGHT_URL = s_w_data_dict['result']['appURL']['locHighlights'] + '?format=json&ps=19&pn='
PUBLISH_POINT_URL = ROOT_URL+'publishpoint'
LOGOUT_URL = ROOT_URL+'logout'
LOGIN_URL = 'https://www.premierleaguepass.com/plp/secure/login'
IMG_URL = s_w_data_dict['result']['appURL']['locImgServer'] + '/'
QUALITY = int(settings.getSetting(id="quality"))
USERNAME = str(settings.getSetting(id="username"))
PASSWORD = str(settings.getSetting(id="password"))
FANART = ROOTDIR+"/fanart.jpg"
ICON = ROOTDIR+"/icon.png"
VS_ICON = ROOTDIR+"/vs.png"

def CATEGORIES():           
        
    addDir('Live/Full Replays & Upcoming','live',1,ICON,FANART)
    addDir('Highlights & Shows',HIGHLIGHT_URL + '1',2,ICON,FANART)

def LIVE_AND_UPCOMING():      
    GET_LIVE_VIDEOS(SCHEDULE_URL)

def HIGHLIGHTS(url):
    #Highlights and Videos
    GET_HIGHLIGHTS(url)

def addLink(name,url,title,iconimage,fanart,info=None):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=VS_ICON,)
    liz.setProperty('fanart_image',fanart)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info) 
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok
    
def addDir(name,url,mode,iconimage,fanart=None,scrape_type=None,isFolder=True,info=None): 
    params = get_params()      
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&scrape_type="+urllib.quote_plus(str(scrape_type))+"&icon_image="+urllib.quote_plus(str(iconimage))
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)        

    liz.setProperty('fanart_image', fanart)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isFolder) 
    print(u)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok
    
def GET_LIVE_VIDEOS(url,scrape_type=None):
    #print url
    req = urllib2.Request(url)
    req.add_header('Connection', 'keep-alive')
    req.add_header('Accept', '*/*')
    req.add_header('User-Agent', APP_USER_AGENT_STRING)
    req.add_header('Accept-Language', 'en-us')
    req.add_header('Accept-Encoding', 'gzip, deflate')
    
    response = urllib2.urlopen(req)    
    json_source = json.load(response)                           
    response.close()                
    
    for item in json_source['schedule']:
            Home_Team = item['home_team']
            Away_Team = item['away_team']
            channelId = item['programId']
            #addDir(Home_Team+' vs '+Away_Team,channelId,3,VS_ICON,fanart=None,scrape_type=None,isFolder=False,info=None)
            addDir('[COLOR=FF00B7EB]'+Home_Team+' vs '+Away_Team+'[/COLOR]',channelId,3,VS_ICON,fanart=None,scrape_type=None,isFolder=False,info=None)

def GET_HIGHLIGHTS(url,scrape_type=None):
    req = urllib2.Request(url)
    req.add_header('Connection', 'keep-alive')
    req.add_header('Accept', '*/*')
    req.add_header('User-Agent', APP_USER_AGENT_STRING)
    req.add_header('Accept-Language', 'en-us')
    req.add_header('Accept-Encoding', 'gzip, deflate')
    
    response = urllib2.urlopen(req)    
    json_source = json.load(response)                           
    response.close()                
    
    for item in json_source['programs']:
            Home_Team = item['name']
            Away_Team = item['releaseDate']
            channelId = item['id']
            image_name = item['image']
            addDir(Home_Team+' - '+Away_Team,channelId,3,IMG_URL+image_name,fanart=None,scrape_type=None,isFolder=False,info=None)

    current_page_number = int(json_source['paging']['pageNumber'])
    total_page_number = int(json_source['paging']['totalPages'])
    next_page = current_page_number+1
    
    if(current_page_number<total_page_number):
        addDir('('+str(current_page_number)+'/'+str(total_page_number)+') Next Page -->',HIGHLIGHT_URL+str(next_page),2,VS_ICON,fanart=None)

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
                params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
                splitparams={}
                splitparams=pairsofparams[i].split('=')
                if (len(splitparams))==2:
                        param[splitparams[0]]=splitparams[1]
                        
    return param  

def login(username=None, password=None):
    if check_for_subscription():
        print('Already logged in')
    else:
        if username and password:
            print('Not (yet) logged in')
            login_to_account(username, password)
            if not check_for_subscription():
                print('login failed')
        else:
            print('No username and password supplied.')
        
def login_to_account(username, password):
    url = ROOT_URL + 'login'
    post_data = {
       'username': username,
       'password': password
    }
    make_request(url=url, method='post', payload=post_data)
     
def check_for_subscription():
    url = ROOT_URL + 'simpleconsole'
    sc_data = make_request(url=url, method='post', payload='')

    if '</userName>' not in sc_data:
        print('No user name detected.')
        return False
    elif '</hasSubscription>' not in sc_data:
        print('No subscription detected.')
        return False
    else:
        print('Subscription and user name detected.')
        return True    
       
def make_request(url, method, payload=None, headers=None):
    try:
        if method == 'get':
            req = http_session.get(url, params=payload, headers=headers, allow_redirects=False)
        else: # post
            req = http_session.post(url, data=payload, headers=headers, allow_redirects=False)
        cookie_jar.save(ignore_discard=True, ignore_expires=False)
        return req.content
    except requests.exceptions.RequestException as error:
        print(error)    

def logout():
    make_request(url=LOGOUT_URL, method='post', payload='')

def get_team_names():
    url = ROOT_URL+'simpleconsole'
    s_w_data = make_request(url=url, method='get')
    s_w_data_dict = xmltodict.parse(s_w_data)
    items = s_w_data_dict['result']['lsids']['lsid']
    teams.append('Dummy')
    try:
        for lsid in items:
            teams.append(lsid['@feed'])
            
    except KeyError:
        print('Parsing team data failed.')
        raise

def set_cookies():
    url = ROOT_URL+'simpleconsole'
    sc_data = make_request(url=url, method='post', payload='')
    
def PlayVideo(video_id):
    progress = xbmcgui.DialogProgress()
    progress.create('Launching Stream', 'Please wait ..')
    
    QUALITY = int(settings.getSetting(id="quality"))
    if QUALITY == 0:
        bitrate_to_use = "240"
    elif QUALITY == 1:
        bitrate_to_use = "400"
    elif QUALITY == 2:
        bitrate_to_use = "800"
    elif QUALITY == 3:
        bitrate_to_use = "1200"
    elif QUALITY == 4:
        bitrate_to_use = "1600"
    elif QUALITY == 5:
        bitrate_to_use = "3000"
    else:
        bitrate_to_use = "4500"
 
    video_streams = get_publishpoint_streams(video_id)
    
    if bitrate_to_use == '4500':
        try:
            video_url = video_streams[bitrate_to_use] + '|User-Agent=' + APP_USER_AGENT_STRING
            #Quick way to check if it is a highlight video as they max out at 3000Kbps
        except KeyError:
            video_url = video_streams['3000'] + '|User-Agent=' + APP_USER_AGENT_STRING
    else:
        video_url = video_streams[bitrate_to_use] + '|User-Agent=' + APP_USER_AGENT_STRING
        
    login(USERNAME,PASSWORD) #Check if we are logged in
    
    if progress.iscanceled():
        progress.close()
        return
    
    p = xbmc.Player()
    p.play(video_url)
    
def get_publishpoint_streams(video_id):
    """Return the URL for a stream."""
    streams = {}
    set_cookies()  # set cookies

    post_data = {'id': video_id, 'type': 'video', 'nt': '1', 'gt': '0'}
    headers = {'User-Agent': APP_USER_AGENT_STRING}
    m3u8_data = make_request(url=PUBLISH_POINT_URL, method='post', payload=post_data, headers=headers)
    m3u8_dict = xmltodict.parse(m3u8_data)['result']
    print('PLP Dict %s' % m3u8_dict)
    m3u8_url = m3u8_dict['path'].replace('_ipad','')
    m3u8_param = m3u8_url.split('?', 1)[-1]
    m3u8_header = {'Cookie': 'nlqptid=' + m3u8_param}
    m3u8_obj = m3u8.load(m3u8_url)
    if m3u8_obj.is_variant:
        for playlist in m3u8_obj.playlists:
            print(m3u8_url)
            bitrate = str(int(playlist.stream_info.bandwidth[:playlist.stream_info.bandwidth.find(' ')])/100)
            streams[bitrate] = m3u8_url
    else:
        streams['only available'] = m3u8_url
        
    return streams

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]
                            
    return param

params=get_params()
url=None
name=None
mode=None
scrape_type=None
icon_image = None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    scrape_type=urllib.unquote_plus(params["scrape_type"])
except:
    pass
try:
    icon_image=urllib.unquote_plus(params["icon_image"])
except:
    pass


print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)
print "Video Id"
print "scrape_type:"+str(scrape_type)
#get_team_names() Will Implement later.

if mode==None or url==None or len(url)<1:        
        CATEGORIES()        
elif mode==1:        
        LIVE_AND_UPCOMING()                     
elif mode==2:
        HIGHLIGHTS(url)
elif mode==3:        
        if USERNAME != '' and PASSWORD != '':
            PlayVideo(url)
        else:
            msg = "A valid username and password is required to view anything with this addon"
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Credentials Missing', msg)

#Don't cache live and upcoming list
if mode==1:
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)
else:
    xbmcplugin.endOfDirectory(ADDON_HANDLE)
