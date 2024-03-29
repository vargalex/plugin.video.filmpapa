# -*- coding: utf-8 -*-

'''
    dmdamedia Add-on
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


import sys, xbmcgui
from resources.lib.indexers import navigator

if sys.version_info[0] == 3:
    from urllib.parse import parse_qsl
else:
    from urlparse import parse_qsl


params = dict(parse_qsl(sys.argv[2].replace('?','')))

action = params.get('action')

url = params.get('url')

search = params.get('search')

page = params.get('page')

sort = params.get('sort')

subtitled = params.get('subtitled')

dataID = params.get('dataid')

listtype = params.get('listtype')

if action == None:
    navigator.navigator().getRoot()

if action == 'categories':
    navigator.navigator().getCategories()

if action == 'years':
    navigator.navigator().getYears()

elif action == 'sorts':
    navigator.navigator().getSorts(url)

elif action == 'items':
    navigator.navigator().getItems(url, page, sort, search)

elif action == 'episodes':
    navigator.navigator().getEpisodes(url)

elif action == 'playmovie':
    navigator.navigator().playMovie(url, subtitled)

elif action == 'search':
    navigator.navigator().getSearches()

elif action == 'historysearch':
    navigator.navigator().getItems(None, 1, None, search)

elif action == 'newsearch':
    navigator.navigator().doSearch()

elif action == 'deletesearchhistory':
    navigator.navigator().deleteSearchHistory()

elif action == 'inputStreamSettings':
    import xbmcaddon
    xbmcaddon.Addon(id='inputstream.adaptive').openSettings()

elif action == 'watchlist':
    navigator.navigator().getWatchList(url)

elif action == 'logout':
    navigator.navigator().logout()

elif action == 'adddeletelist':
    navigator.navigator().addDeleteList(listtype, dataID)