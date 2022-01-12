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
import os,sys,re,xbmc,xbmcgui,xbmcplugin,xbmcaddon, time, locale
import resolveurl as urlresolver
from resources.lib.modules import client
from resources.lib.modules.utils import py2_encode, py2_decode, safeopen

if sys.version_info[0] == 3:
    import urllib.parse as urlparse
    from urllib.parse import quote_plus
else:   
    import urlparse
    from urllib import quote_plus

sysaddon = sys.argv[0] ; syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

base_url = 'https://plusz.club/'
series_url = 'series-category/sorozat-online/'

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            pass
        self.infoPreload = xbmcaddon.Addon().getSettingBool('infopreload')
        self.downloadsubtitles = xbmcaddon.Addon().getSettingBool('downloadsubtitles')
        self.base_path = py2_decode(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
        self.searchFileName = os.path.join(self.base_path, "search.history")

    def getRoot(self):
        self.addDirectoryItem('Keresés', 'search', '', 'DefaultFolder.png')
        self.addDirectoryItem('Legújabb HD filmek', 'items&page=1', '', 'DefaultFolder.png')
        self.addDirectoryItem('Műfajok', 'categories', '', 'DefaultFolder.png')
        self.addDirectoryItem('Sorozatok', 'sorts&url=series-category/sorozat-online/', '', 'DefaultFolder.png')
        self.addDirectoryItem('Legújabb sorozat epizódok', 'items&itemlistnr=1', '', 'DefaultFolder.png')
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

    def getItems(self, url, page, itemlistNr, sort, search):
        url = url or ""
        itemlistNr = itemlistNr or '0'
        sort = sort or ""
        searchparam = "" if search == None else "&s=%s" % search
        page = page or "1"
        url_content = client.request("%s%spage/%s?sort=%s%s" % (base_url, url, page, sort, searchparam))
        try:
            listItems = client.parseDOM(url_content, 'div', attrs={'class': '[^\'"]*list_items.*?'})[int(itemlistNr)]
            items = client.parseDOM(listItems, 'div', attrs={'class': 'movie-box|episode-box'})
            for item in items:
                details = client.parseDOM(item, 'div', attrs={'class': '[^\'"]*existing-details.*?'})[0]
                name = client.parseDOM(details, 'div', attrs={'class': 'name'})[0]
                title = client.replaceHTMLCodes(client.parseDOM(name, 'a', ret='title')[0])
                try:
                    title = "%s - [COLOR green]%s[/COLOR]" % (client.parseDOM(item, 'span', attrs={'class': 'serietitle'})[0], client.parseDOM(item, 'span', attrs={'class': 'episodetitle'})[0].replace(' <b>', ', ').replace('</b>', ''))
                except:
                    pass
                newurl = client.parseDOM(name, 'a', ret='href')[0]
                felirat = 0
                if itemlistNr == '0' and self.infoPreload:
                    detail_content = client.request(newurl)
                    movieLeft = client.parseDOM(detail_content, 'div', attrs={'class': 'movie-left'})[0]
                    movieData = client.parseDOM(detail_content, 'div', attrs={'class': 'movies-data'})[0]
                    poster = client.parseDOM(movieLeft, 'div', attrs={'class': 'poster'})[0]
                    img = client.parseDOM(poster, 'div', attrs={'class': 'img'})[0]
                    thumb = client.parseDOM(img, 'img', ret='src')[0]
                    release = client.parseDOM(movieData, 'li', attrs={'class': 'release'})[0]
                    year = client.parseDOM(release, 'a')[0]
                    try:
                        time = client.parseDOM(movieData, 'li', attrs={'class': 'time'})[0]
                        time = client.parseDOM(time, 'span')[0].replace('min', '').strip()
                    except:
                        time = 0
                    plot = client.replaceHTMLCodes(client.parseDOM(movieData, 'div', attrs={'class': 'description'})[0])
                    try:
                        fullimdb = client.parseDOM(movieData, 'div', attrs={'class': 'imdb-count'})[0]
                        imdb = fullimdb.split(" ")[0]
                        if "felirat" in fullimdb.lower():
                            felirat = 1
                    except:
                        imdb = None
                else:
                    plot = ""
                    try:
                        plot = client.replaceHTMLCodes(client.parseDOM(details, 'p', attrs={'class': 'story'})[0])
                    except:
                        pass
                    poster = client.parseDOM(item, 'div', attrs={'class': 'poster'})[0]
                    img = client.parseDOM(poster, 'div', attrs={'class': 'img'})[0]
                    thumb = client.parseDOM(img, 'img', ret='src')[0]
                    time = 0
                    year = 0
                    try:
                        year = client.parseDOM(details, 'div', attrs={'class': 'category'})[0].strip()
                    except:
                        pass
                    imdb = None
                    try:
                        imdbdiv = client.parseDOM(item, 'div', attrs={'class': 'rating'})[0]
                        fullimdb = client.parseDOM(imdbdiv, 'span')[0]
                        imdb = fullimdb.split(" ")[0].strip()
                        if "felirat" in fullimdb.lower():
                            felirat = 1
                    except:
                        pass
                if newurl.startswith("%sseries" % base_url):
                    self.addDirectoryItem('%s%s%s%s' % (title, "" if year == 0 else " ([COLOR red]%s[/COLOR])" % year, "" if imdb == None else " | [COLOR yellow]IMDB: %s[/COLOR]" % imdb, "" if felirat == 0 else " | [COLOR lime]Feliratos[/COLOR]"), 'series&url=%s' % (quote_plus(newurl)), thumb, 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': plot, 'duration': int(time)*60}, banner=thumb)
                else:
                    self.addDirectoryItem('%s%s%s%s' % (title, "" if year == 0 else " ([COLOR red]%s[/COLOR])" % year, "" if imdb == None else " | [COLOR yellow]IMDB: %s[/COLOR]" % imdb, "" if felirat == 0 else " | [COLOR lime]Feliratos[/COLOR]"), 'playmovie&url=%s' % quote_plus(newurl), thumb, 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'duration': int(time)*60}, banner=thumb)
            try:
                navicenter = client.parseDOM(url_content, 'div', attrs={'class': 'navicenter'})[int(itemlistNr)]
                last = client.parseDOM(navicenter, 'a')[-1]
                if int(last)>int(page):
                    self.addDirectoryItem(u'[I]K\u00F6vetkez\u0151 oldal  (%d/%s)>>[/I]' % (int(page)+1, last), 'items&url=%s&page=%d%s%s%s' % (url, int(page)+1, "" if itemlistNr == 0 else "&itemlistnr=%s" % itemlistNr, "" if sort == "" else "&sort=%s" % sort, "" if search == "" or search == None else "&search=%s" % search), '', 'DefaultFolder.png')
            except:
                pass
        except:
            pass
        self.endDirectory('movies')

    def getSeries(self, url):
        url_content = client.request(url)
        seriesButtons = client.parseDOM(url_content, 'div', attrs={'class': 'tab-buttons.*?'})[0]
        movieLeft = client.parseDOM(url_content, 'div', attrs={'class': 'movie-left'})[0]
        movieData = client.parseDOM(url_content, 'div', attrs={'class': 'movies-data'})[0]
        info = client.parseDOM(movieData, 'div', attrs={'class': 'info'})[0]
        title = client.parseDOM(info, 'h1', attrs={'class': 'film'})[0]
        poster = client.parseDOM(movieLeft, 'div', attrs={'class': 'poster'})[0]
        img = client.parseDOM(poster, 'div', attrs={'class': 'img'})[0]
        thumb = client.parseDOM(img, 'img', ret='src')[0]
        release = client.parseDOM(movieData, 'li', attrs={'class': 'release'})[0]
        year = client.parseDOM(release, 'a')[0]
        try:
            time = client.parseDOM(movieData, 'li', attrs={'class': 'time'})[0]
            time = client.parseDOM(time, 'span')[0].replace('min', '').strip()
        except:
            time = 0
        plot = client.replaceHTMLCodes(client.parseDOM(movieData, 'div', attrs={'class': 'description'})[0])
        try:
            imdb = client.parseDOM(movieData, 'div', attrs={'class': 'imdb-count'})[0].split(" ")[0]
        except:
            imdb = None
        series = client.parseDOM(seriesButtons, 'li')
        seriesDataIds = client.parseDOM(seriesButtons, 'li', ret='data-id')
        for idx in range(len(series)):
            self.addDirectoryItem(series[idx], 'episodes&url=%s&serieid=%s' % (quote_plus(url), seriesDataIds[idx]), thumb, 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': plot, 'duration': int(time)*60}, banner=thumb)     
        self.endDirectory('tvshows')
    
    def getEpisodes(self, url, serieID):
        url_content = client.request(url)
        seasons = client.parseDOM(url_content, 'div', attrs={'id': 'seasons'})[0]
        season = client.parseDOM(seasons, 'div', attrs={'id': serieID})[0]
        movieLeft = client.parseDOM(url_content, 'div', attrs={'class': 'movie-left'})[0]
        movieData = client.parseDOM(url_content, 'div', attrs={'class': 'movies-data'})[0]
        info = client.parseDOM(movieData, 'div', attrs={'class': 'info'})[0]
        title = client.parseDOM(info, 'h1', attrs={'class': 'film'})[0]
        poster = client.parseDOM(movieLeft, 'div', attrs={'class': 'poster'})[0]
        img = client.parseDOM(poster, 'div', attrs={'class': 'img'})[0]
        thumb = client.parseDOM(img, 'img', ret='src')[0]
        release = client.parseDOM(movieData, 'li', attrs={'class': 'release'})[0]
        year = client.parseDOM(release, 'a')[0]
        try:
            time = client.parseDOM(movieData, 'li', attrs={'class': 'time'})[0]
            time = client.parseDOM(time, 'span')[0].replace('min', '').strip()
        except:
            time = 0
        plot = client.replaceHTMLCodes(client.parseDOM(movieData, 'div', attrs={'class': 'description'})[0])
        subtitled = 0
        try:
            fullimdb = client.parseDOM(movieData, 'div', attrs={'class': 'imdb-count'})[0]
            imdb= fullimdb.split(" ")[0]
            if "Feliratos" in fullimdb:
                subtitled = 1
        except:
            imdb = None
        items = client.parseDOM(season, 'div', attrs={'class': 'movie-box|episode-box'})
        for item in items:
            details = client.parseDOM(item, 'div', attrs={'class': '[^\'"]*existing-details.*?'})[0]
            name = client.parseDOM(details, 'div', attrs={'class': 'name'})[0]
            title = client.replaceHTMLCodes(client.parseDOM(name, 'a', ret='title')[0])
            try:
                title = "%s - [COLOR green]%s[/COLOR]" % (client.parseDOM(item, 'span', attrs={'class': 'serietitle'})[0], client.parseDOM(item, 'span', attrs={'class': 'episodetitle'})[0].replace(' <b>', ', ').replace('</b>', ''))
            except:
                pass
            newurl = client.parseDOM(name, 'a', ret='href')[0]
            self.addDirectoryItem('%s%s%s' % (title, "" if year == 0 else " ([COLOR red]%s[/COLOR])" % year, "" if imdb == None else " | [COLOR yellow]IMDB: %s[/COLOR]" % imdb), 'playmovie&url=%s&subtitled=%d' % (quote_plus(newurl), subtitled), thumb, 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'duration': int(time)*60}, banner=thumb)
        self.endDirectory('episodes')


    def getSearches(self):
        self.addDirectoryItem('Új keresés', 'newsearch', '', 'DefaultFolder.png')
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
                self.addDirectoryItem('Keresési előzmények törlése', 'deletesearchhistory', '', 'DefaultFolder.png') 
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
            self.getItems(None, 1, None, None, search_text)


    def playMovie(self, url, subtitled):
        url_content = client.request(url)
        try:
            src = client.parseDOM(url_content, 'iframe', ret='src')[0]
        except:
            src = client.parseDOM(url_content, 'source', ret='src')[0]
        if "http" not in src:
            src = ("https:%s" % src)
        xbmc.log('FilmPapa: resolving url: %s' % src, xbmc.LOGINFO)
        try:
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
            if subtitled == '1' and self.downloadsubtitles:
                errMsg = ""
                try:
                    if not os.path.exists("%s/subtitles" % self.base_path):
                        errMsg = "Hiba a felirat könyvtár létrehozásakor!"
                        os.mkdir("%s/subtitles" % self.base_path)
                    for f in os.listdir("%s/subtitles" % self.base_path):
                        errMsg = "Hiba a korábbi feliratok törlésekor!"
                        os.remove("%s/subtitles/%s" % (self.base_path, f))
                    finalsubtitles=[]
                    if "mxdcontent" in direct_url:
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
