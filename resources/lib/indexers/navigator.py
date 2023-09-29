# -*- coding: utf-8 -*-

'''
    dmdamedia Addon
    Copyright (C) 2020

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import os,sys,re,xbmc,xbmcgui,xbmcplugin,xbmcaddon, time, locale, json
import resolveurl as urlresolver
from resources.lib.modules import client, control
from resources.lib.modules.utils import py2_encode, py2_decode, safeopen
from datetime import date

if sys.version_info[0] == 3:
    import urllib.parse as urlparse
    from urllib.parse import quote_plus
else:   
    import urlparse
    from urllib import quote_plus

sysaddon = sys.argv[0] ; syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

base_url = 'https://filmpapa.filmadatbazis.site/'
series_url = 'series-category/sorozat-online/'
years_url = 'release/%d/'
start_year = 1938
login_url = 'wp-login.php'
notmember_url = 'ugy-tunik-meg-nem-filmpapa-tag'

class navigator:
    def __init__(self):
        self.loggedin = None
        self.logincookiename = None
        self.logincookievalue = None
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        try:
            self.infoPreload = xbmcaddon.Addon().getSettingBool('infopreload')
            self.downloadsubtitles = xbmcaddon.Addon().getSettingBool('downloadsubtitles')
        except:
            self.infoPreload = xbmcaddon.Addon().getSetting('infopreload').lower() == 'true'
            self.downloadsubtitles = xbmcaddon.Addon().getSetting('downloadsubtitles').lower() == 'true'
        self.base_path = py2_decode(control.dataPath)
        self.searchFileName = os.path.join(self.base_path, "search.history")
        if not (control.setting('username') and control.setting('password')):
            if xbmcgui.Dialog().ok('FilmPapa HD', 'A kiegészítő használatához add meg a bejelentkezési adataidat!'):
                xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
                control.openSettings()
        self.loggedin = control.setting('loggedin')
        self.logincookiename = control.setting('logincookiename')
        self.logincookievalue = control.setting('logincookievalue')

        self.login()


    def getRoot(self):
        self.addDirectoryItem('Keresés', 'search', '', 'DefaultFolder.png')
        self.addDirectoryItem('Legújabb filmek és sorozatok', 'items&page=1', '', 'DefaultFolder.png')
        self.addDirectoryItem('Premier filmek', 'sorts&url=category/kiemelt/', '', 'DefaultFolder.png')
        self.addDirectoryItem('Sorozatok', 'sorts&url=category/sorozatok/', '', 'DefaultFolder.png')
        self.addDirectoryItem('Kollekciók', 'sorts&url=category/online-hd-film-sorozat/', '', 'DefaultFolder.png')
        self.addDirectoryItem('Műfajok', 'categories', '', 'DefaultFolder.png')
        self.addDirectoryItem('Megjelenés éve szerint', 'years', '', 'DefaultFolder.png');
        self.endDirectory()

    def getYears(self):
        for year in range(date.today().year, start_year-1, -1):
            self.addDirectoryItem(str(year), 'items&url=%s' % (years_url % year), '', 'DefaultFolder.png')
        self.endDirectory()

    def getCategories(self):
        url_content = client.request(base_url)
        categories = client.parseDOM(url_content, 'div', attrs={'class': '[^\'"]*widget_categories'})[0]
        mainMenu = client.parseDOM(categories, 'ul')[0]
        menuItems = client.parseDOM(mainMenu, 'li')
        for menuItem in menuItems:
            text = py2_encode(client.replaceHTMLCodes(client.parseDOM(menuItem, 'a')[0]))
            url = client.parseDOM(menuItem, 'a', ret='href')[0]
            self.addDirectoryItem(text.replace('🎄', '').strip(), 'sorts&url=%s' % url[len(base_url):], '', 'DefaultFolder.png')
        self.endDirectory()
    
    def getSorts(self, url):
        self.addDirectoryItem('Legfrissebb', 'items&&url=%s&sort=date' % url, '', 'DefaultFolder.png')
        self.addDirectoryItem('Legnézettebb', 'items&url=%s&sort=views' % url, '', 'DefaultFolder.png')
        self.addDirectoryItem('Legtöbb komment', 'items&url=%s&sort=comments' % url, '', 'DefaultFolder.png')
        self.addDirectoryItem('IMDB szerint', 'items&url=%s&sort=imdb' % url, '', 'DefaultFolder.png')
        self.endDirectory()

    def getItems(self, url, page, sort, search):
        url = url or ""
        sort = sort or ""
        searchparam = "" if search == None else "&s=%s" % quote_plus(search)
        page = page or "1"
        url_content = client.request("%s%spage/%s/?sort=%s%s" % (base_url, url, page, sort, searchparam))
        try:
            listItems = client.parseDOM(url_content, 'div', attrs={'class': '[^\'"]*list_items.*?'})[0]
            items = client.parseDOM(listItems, 'div', attrs={'class': 'movie-preview-content'})
            for item in items:
                details = client.parseDOM(item, 'div', attrs={'class': 'movie-details'})[0]
                span = client.parseDOM(details, 'span', attrs={'class': 'movie-title'})[0]
                title = client.replaceHTMLCodes(client.parseDOM(span, 'a', ret='title')[0])
                try:
                    title = "%s - [COLOR green]%s[/COLOR]" % (client.parseDOM(item, 'span', attrs={'class': 'serietitle'})[0], client.parseDOM(item, 'span', attrs={'class': 'episodetitle'})[0].replace(' <b>', ', ').replace('</b>', ''))
                except:
                    pass
                newurl = client.parseDOM(span, 'a', ret='href')[0]
                felirat = 0
                if self.infoPreload:
                    detail_content = self.requestWithLoginCookie(newurl)
                    info_left = client.parseDOM(detail_content, 'div', attrs={'class': 'info-left'})[0]
                    info_right = client.parseDOM(detail_content, 'div', attrs={'class': 'info-right'})[0]
                    poster = client.parseDOM(info_left, 'div', attrs={'class': 'poster'})[0]
                    thumb = client.parseDOM(poster, 'img', ret='src')[0]
                    try:
                        release = client.parseDOM(info_right, 'div', attrs={'class': 'release'})[0]
                        year = client.parseDOM(release, 'a')[0]
                    except:
                        year = "ismeretlen"
                    try:
                        time = client.parseDOM(movieData, 'li', attrs={'class': 'time'})[0]
                        time = client.parseDOM(time, 'span')[0].replace('min', '').strip()
                        time = int(time)
                    except:
                        time = 0
                    try:
                        plot = client.replaceHTMLCodes(client.parseDOM(info_right, 'div', attrs={'class': 'excerpt'})[0])
                    except:
                        plot = ""
                    try:
                        fullimdb = client.parseDOM(detail_content, 'span', attrs={'class': 'imdb-rating'})[0]
                        imdb = re.search(r"([^<]*)(<|$)", fullimdb)[1].strip()
                        if "felirat" in fullimdb.lower():
                            felirat = 1
                    except:
                        imdb = None
                else:
                    try:
                        plot = client.replaceHTMLCodes(client.parseDOM(details, 'p', attrs={'class': 'story'})[0])
                    except:
                        plot = ""
                    poster = client.parseDOM(item, 'div', attrs={'class': 'movie-poster'})[0]
                    thumb = client.parseDOM(poster, 'img', ret='src')[0]
                    release = client.parseDOM(details, 'span', attrs={'class': 'movie-release'})[0]
                    time = 0
                    year = ""
                    try:
                        year = re.search(r"([^<]*)(<|$)", release)[1].strip()
                    except:
                        pass
                    imdb = None
                    try:
                        imdb = client.parseDOM(release, 'span', attrs={'title': 'IMDB'})[0]
                        if "felirat" in imdb.lower():
                            felirat = 1
                    except:
                        pass
                if 'sorozatok' in url or client.parseDOM(item, 'span', attrs={'class': 'bilgi-icon'}) and client.parseDOM(item, 'span', attrs={'class': 'bilgi-icon'})[0] == 'Sorozat':
                    self.addDirectoryItem('%s%s%s%s' % (title, "" if len(year) == 0 else " ([COLOR red]%s[/COLOR])" % year, "" if imdb == None else " | [COLOR yellow]IMDB: %s[/COLOR]" % imdb, "" if felirat == 0 else " | [COLOR lime]Feliratos[/COLOR]"), 'episodes&url=%s' % (quote_plus(newurl)), thumb, 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': plot, 'duration': time*60}, banner=thumb)
                else:
                    self.addDirectoryItem('%s%s%s%s' % (title, "" if len(year) == 0 else " ([COLOR red]%s[/COLOR])" % year, "" if imdb == None else " | [COLOR yellow]IMDB: %s[/COLOR]" % imdb, "" if felirat == 0 else " | [COLOR lime]Feliratos[/COLOR]"), 'playmovie&url=%s' % quote_plus(newurl), thumb, 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'duration': time*60}, banner=thumb)
            try:
                navicenter = client.parseDOM(url_content, 'div', attrs={'class': 'navicenter'})[0]
                last = client.parseDOM(navicenter, 'a')[-1]
                if int(last)>int(page):
                    self.addDirectoryItem(u'[I]K\u00F6vetkez\u0151 oldal  (%d/%s)>>[/I]' % (int(page)+1, last), 'items&url=%s&page=%d%s%s' % (url, int(page)+1, "" if sort == "" else "&sort=%s" % sort, "" if search == "" or search == None else "&search=%s" % search), '', 'DefaultFolder.png')
            except:
                pass
        except:
            pass
        self.endDirectory('movies')

    def getEpisodes(self, url):
        url_content = self.requestWithLoginCookie(url)
        info_left = client.parseDOM(url_content, 'div', attrs={'class': 'info-left'})[0]
        info_right = client.parseDOM(url_content, 'div', attrs={'class': 'info-right'})[0]
        title = client.parseDOM(info_right, 'div', attrs={'class': 'title'})[0]
        title = client.parseDOM(title, 'h1')[0]
        poster = client.parseDOM(info_left, 'div', attrs={'class': 'poster'})[0]
        thumb = client.parseDOM(poster, 'img', ret='src')[0]
        release = client.parseDOM(info_right, 'div', attrs={'class': 'release'})[0]
        year = client.parseDOM(release, 'a')[0]
        try:
            time = client.parseDOM(info_right, 'li', attrs={'class': 'time'})[0]
            time = client.parseDOM(time, 'span')[0].replace('min', '').strip()
        except:
            time = 0
        try:
            plot = client.replaceHTMLCodes(client.parseDOM(info_right, 'div', attrs={'class': 'excerpt'})[0])
        except:
            plot = ""
        try:
            imdb = client.parseDOM(detail_content, 'span', attrs={'class': 'imdb-rating'})[0]
            imdb = re.search(r"([^<]*)(<|$)", imdb)[1].strip()
        except:
            imdb = None
        parts_middle = client.parseDOM(url_content, 'div', attrs={'class': 'parts-middle'})[0]
        part_names = client.parseDOM(parts_middle, 'div', attrs={'class': 'part-name'})
        links = client.parseDOM(parts_middle, 'a', ret = 'href')
        for idx in range(len(part_names)):
            self.addDirectoryItem(part_names[idx], 'playmovie&url=%s' % quote_plus(url if idx == 0 else links[idx-1]), thumb, 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'duration': int(time)*60}, banner=thumb)
        self.endDirectory('episodes')

    def getSearches(self):
        self.addDirectoryItem('[COLOR lightgreen]Új keresés[/COLOR]', 'newsearch', '', 'DefaultFolder.png')
        try:
            file = safeopen(self.searchFileName, "r")
            olditems = file.read().splitlines()
            file.close()
            items = list(set(olditems))
            items.sort(key=locale.strxfrm)
            if len(items) != len(olditems):
                file = safeopen(self.searchFileName, "w")
                file.write("\n".join(items))
                file.close()
            for item in items:
                self.addDirectoryItem(item, 'historysearch&search=%s' % (quote_plus(item)), '', 'DefaultFolder.png')
            if len(items) > 0:
                self.addDirectoryItem('[COLOR red]Keresési előzmények törlése[/COLOR]', 'deletesearchhistory', '', 'DefaultFolder.png') 
        except:
            pass   
        self.endDirectory()

    def deleteSearchHistory(self):
        if os.path.exists(self.searchFileName):
            os.remove(self.searchFileName)

    def doSearch(self):
        search_text = self.getText(u'Add meg a keresend\xF5 film c\xEDm\xE9t')
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)
            file = safeopen(self.searchFileName, "a")
            file.write("%s\n" % search_text)
            file.close()
            self.getItems(None, 1, None, search_text)


    def playMovie(self, url, subtitled):
        url_content = self.requestWithLoginCookie(url)
        try:
            src = client.parseDOM(url_content, 'iframe', ret='src')[0]
        except:
            try:
                src = client.parseDOM(url_content, 'IFRAME', ret='SRC')[0]
            except:
                src = client.parseDOM(url_content, 'source', ret='src')[0]
        if "http" not in src:
            src = ("https:%s" % src)
        if 'feltotesek.xyz' in src:
            videoID = src.split("/v/")[1]
            xbmc.log('FilmPapa: downloading feltotesek json. URL: https://feltotesek.xyz/api/source/%s' % videoID, xbmc.LOGINFO)
            url_content = client.request("https://feltotesek.xyz/api/source/%s" % videoID, post=b"")
            try:
                jsonData = json.loads(url_content)
                maxRes = 0
                for data in jsonData["data"]:
                    if int(data["label"].replace("p", "")) > maxRes:
                        maxRes = int(data["label"].replace("p", ""))
                        src = data["file"]
            except:
                pass

        direct_url = None
        pattern = r'(.*?://|\.)((?:filemoon|cinegrab|moonmov)\.(?:sx|to|in|link|nl|wf|com|eu|art|pro))/(?:e|d)/([0-9a-zA-Z]+)'
        match = re.search(pattern, src)
        if match:
            src = match.group(0)
        if "filemoon" in src or "streamwish" in src:
            src = "%s$$%s" % (src, base_url)
        try:
            xbmc.log('FilmPapa: resolving URL %s with ResolveURL' % src, xbmc.LOGINFO)
            direct_url = urlresolver.resolve(src)
            if direct_url:
                direct_url = py2_encode(direct_url)
            else:
                direct_url = src
        except Exception as e:
            xbmcgui.Dialog().notification(urlparse.urlparse(url).hostname, str(e))
            return
        if direct_url:
            xbmc.log('FilmPapa: playing URL: %s, subtitled: %s' % (direct_url, subtitled), xbmc.LOGINFO)
            play_item = xbmcgui.ListItem(path=direct_url)
            if 'm3u8' in direct_url:
                from inputstreamhelper import Helper
                is_helper = Helper('hls')
                if is_helper.check_inputstream():
                    if sys.version_info < (3, 0):  # if python version < 3 is safe to assume we are running on Kodi 18
                        play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')   # compatible with Kodi 18 API
                    else:
                        play_item.setProperty('inputstream', 'inputstream.adaptive')  # compatible with recent builds Kodi 19 API
                    play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
            elif subtitled == '1' and self.downloadsubtitles:
                errMsg = ""
                try:
                    if not os.path.exists("%s/subtitles" % self.base_path):
                        errMsg = "Hiba a felirat könyvtár létrehozásakor!"
                        os.mkdir("%s/subtitles" % self.base_path)
                    for f in os.listdir("%s/subtitles" % self.base_path):
                        errMsg = "Hiba a korábbi feliratok törlésekor!"
                        os.remove("%s/subtitles/%s" % (self.base_path, f))
                    finalsubtitles=[]
                    if ("mxdcontent" in direct_url or "mxcontent" in direct_url):
                        errMsg = "Hiba a sorozat felirat letöltésekor!"
                        parsed_uri = urlparse.urlparse(direct_url)
                        parsed_uri2 = urlparse.urlparse(src)
                        subtitle = client.request("%s://%s/subs/%s_en.vtt" % (parsed_uri.scheme, parsed_uri.netloc, src.split("/")[-1]))
                        if len(subtitle) > 0:
                            errMsg = "Hiba a sorozat felirat file kiírásakor!"
                            file = safeopen("%s/subtitles/hu.srt" % self.base_path, "w")
                            file.write(subtitle)
                            file.close()
                            errMsg = "Hiba a sorozat felirat file hozzáadásakor!"
                            finalsubtitles.append("%s/subtitles/hu.srt" % self.base_path)
                    if len(finalsubtitles)>0:
                        errMsg = "Hiba a feliratok beállításakor!"
                        play_item.setSubtitles(finalsubtitles)
                except:
                    xbmcgui.Dialog().notification("FilmPapa hiba", errMsg, xbmcgui.NOTIFICATION_ERROR)
                    xbmc.log("Hiba a %s URL-hez tartozó felirat letöltésekor, hiba: %s" % (py2_encode(src), py2_encode(errMsg)), xbmc.LOGERROR)
            xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = '%s?action=%s' % (sysaddon, query) if isAction == True else query
        if thumb == '': thumb = icon
        cm = []
        if queue == True: cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))
        if not context == None: cm.append((py2_encode(context[0]), 'RunPlugin(%s?action=%s)' % (sysaddon, context[1])))
        item = xbmcgui.ListItem(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb, 'banner': banner})
        if Fanart == None: Fanart = addonFanart
        item.setProperty('Fanart_Image', Fanart)
        if isFolder == False: item.setProperty('IsPlayable', 'true')
        if not meta == None: item.setInfo(type='Video', infoLabels = meta)
        xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)


    def endDirectory(self, type='addons'):
        xbmcplugin.setContent(syshandle, type)
        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=True)

    def getText(self, title, hidden=False):
        search_text = ''
        keyb = xbmc.Keyboard('', title, hidden)
        keyb.doModal()

        if (keyb.isConfirmed()):
            search_text = keyb.getText()

        return search_text

    def logout(self):
        dialog = xbmcgui.Dialog()
        if 1 == dialog.yesno('FilmPapa HD kijelentkezés', 'Valóban ki szeretnél jelentkezni?', '', ''):
            control.setSetting('username', '')
            control.setSetting('password', '')
            control.setSetting('logincookiename', '')
            control.setSetting('logincookievalue', '')
            control.setSetting('loggedin', 'false')
            dialog.ok('Filmpapa HD', u'Sikeresen kijelentkeztél.\nAz adataid törlésre kerültek a kiegészítőből.')

    def login(self):
        if self.loggedin != "true":
            xbmc.log('FilmPapa: Trying to login.', xbmc.LOGINFO)
            data = "log=%s&pwd=%s" % (quote_plus(control.setting("username")), quote_plus(control.setting("password")))
            cookies = client.request("%s%s" % (base_url, login_url), post=data, output="cookie")
            if cookies:
                cookies = dict(i.split('=', 1) for i in cookies.split('; '))
                for cookie in cookies:
                    if "logged_in" in cookie:
                        control.setSetting('logincookiename', cookie)
                        control.setSetting('logincookievalue', cookies[cookie])
                        control.setSetting('loggedin', 'true')
                        xbmc.log('FilmPapa: logged in successfully', xbmc.LOGINFO)
                        self.loggedin = 'true'
                        self.logincookiename = cookie
                        self.logincookievalue = cookies[cookie]
                        break
            if self.loggedin != "true":
                xbmc.log('FilmPapa: Login failed.', xbmc.LOGINFO)
                xbmcgui.Dialog().ok("FilmPapa HD", "Sikertelen bejelentkezés!\nHibás felhasználónév, vagy jelszó!")

    def requestWithLoginCookie(self, url):
        url_content = None
        if self.loggedin == "true":
            cookie = "%s=%s" % (self.logincookiename, self.logincookievalue)
            url_content = client.request(url, cookie=cookie)
        if not url_content or ("%s%s" % (base_url, notmember_url)) in url_content:
            control.setSetting('loggedin', 'false')
            self.loggedin = 'false'
            xbmc.log('FilmPapa: Not member page received. Cookie expired?', xbmc.LOGINFO)
            self.login()
            cookie = "%s=%s" % (self.logincookiename, self.logincookievalue)
            url_content = client.request(url, cookie=cookie)
        return url_content