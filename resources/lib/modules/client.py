# -*- coding: utf-8 -*-

import re,sys,random
from resources.lib.modules import cache

if sys.version_info[0] == 3:
    import urllib.request as urllib2
    import urllib.parse as urlparse
    import html
    from urllib.error import HTTPError as HTTPError
else:
    import urllib2
    import urlparse
    import HTMLParser
    from urllib2 import HTTPError as HTTPError

def request(url, close=True, error=False, proxy=None, post=None, headers=None, mobile=False, safe=False, referer=None, cookie=None, output='', timeout='30'):
    try:
        handlers = []
        if not proxy == None:
            handlers += [urllib2.ProxyHandler({'http':'%s' % (proxy)}), urllib2.HTTPHandler]
            opener = urllib2.build_opener(*handlers)
            opener = urllib2.install_opener(opener)
        if output == 'cookie' or output == 'extended' or not close == True:
            if sys.version_info[0] == 3:
                import http.cookiejar as cookielib
            else:
                import cookielib
            cookies = cookielib.LWPCookieJar()
            handlers += [urllib2.HTTPHandler(), urllib2.HTTPSHandler(), urllib2.HTTPCookieProcessor(cookies)]
            opener = urllib2.build_opener(*handlers)
            opener = urllib2.install_opener(opener)
        try:
            if sys.version_info < (2, 7, 9): raise Exception()
            import ssl; ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            handlers += [urllib2.HTTPSHandler(context=ssl_context)]
            opener = urllib2.build_opener(*handlers)
            opener = urllib2.install_opener(opener)
        except:
            pass

        try: headers.update(headers)
        except: headers = {}
        if 'User-Agent' in headers:
            pass
        elif not mobile == True:
            #headers['User-Agent'] = agent()
            headers['User-Agent'] = cache.get(randomagent, 1)
        else:
            headers['User-Agent'] = 'Apple-iPhone/701.341'
        if 'Referer' in headers:
            pass
        elif referer == None:
            headers['Referer'] = '%s://%s/' % (urlparse.urlparse(url).scheme, urlparse.urlparse(url).netloc)
        else:
            headers['Referer'] = referer
        if not 'Accept-Language' in headers:
            headers['Accept-Language'] = 'hu-HU,hu;q=0.8,en-US;q=0.6,en;q=0.4,de;q=0.2'
        if 'Cookie' in headers:
            pass
        elif not cookie == None:
            headers['Cookie'] = cookie


        if sys.version_info[0] == 3:
            request = urllib2.Request(url, data=(post.encode('utf-8') if post != None else post), headers=headers)
        else:
            request = urllib2.Request(url, data=post, headers=headers)

        try:
            response = urllib2.urlopen(request, timeout=int(timeout))
        except HTTPError as response:
            if error == False: return

        if output == 'cookie':
            result = []
            for c in cookies: result.append('%s=%s' % (c.name, c.value))
            result = "; ".join(result)
        elif output == 'response':
            if safe == True:
                result = (str(response.code), response.read(224 * 1024))
            else:
                result = (str(response.code), response.read())
        elif output == 'chunk':
            try: content = int(response.headers['Content-Length'])
            except: content = (2049 * 1024)
            if content < (2048 * 1024): return
            result = response.read(16 * 1024)
        elif output == 'title':
            result = response.read(1 * 1024)
            result = parseDOM(result, 'title')[0]
        elif output == 'extended':
            cookie = []
            for c in cookies: cookie.append('%s=%s' % (c.name, c.value))
            cookie = "; ".join(cookie)
            content = response.headers
            result = response.read()
            return (result, headers, content, cookie)
        elif output == 'geturl':
            result = response.geturl()
        elif output == 'headers':
            content = response.headers
            return content
        else:
            if safe == True:
                result = response.read(224 * 1024)
            else:
                result = response.read()
        if close == True:
            response.close()

        if (sys.version_info[0] == 3 and not isinstance(result, str)):
            return result.decode('utf-8')
        else:
            return result
    except:
        return


def source(url, close=True, error=False, proxy=None, post=None, headers=None, mobile=False, safe=False, referer=None, cookie=None, output='', timeout='30'):
    return request(url, close, error, proxy, post, headers, mobile, safe, referer, cookie, output, timeout)


def parseDOM(html, name=u"", attrs={}, ret=False):
    # Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

    if isinstance(html, str):
        try:
            html = [html.decode("utf-8")] # Replace with chardet thingy
        except:
            html = [html]
    elif isinstance(html, str if sys.version_info[0] == 3 else unicode):
        html = [html]
    elif not isinstance(html, list):
        return u""

    if not name.strip():
        return u""

    ret_lst = []
    for item in html:
        temp_item = re.compile('(<[^>]*?\n[^>]*?>)').findall(item)
        for match in temp_item:
            item = item.replace(match, match.replace("\n", " "))

        lst = []
        for key in attrs:
            lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"].*?>))', re.M | re.S).findall(item)
            if len(lst2) == 0 and attrs[key].find(" ") == -1:  # Try matching without quotation marks
                lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=' + attrs[key] + '.*?>))', re.M | re.S).findall(item)

            if len(lst) == 0:
                lst = lst2
                lst2 = []
            else:
                test = list(range(len(lst)))
                test.reverse()
                for i in test:  # Delete anything missing from the next list.
                    if not lst[i] in lst2:
                        del(lst[i])

        if len(lst) == 0 and attrs == {}:
            lst = re.compile('(<' + name + '>)', re.M | re.S).findall(item)
            if len(lst) == 0:
                lst = re.compile('(<' + name + ' .*?>)', re.M | re.S).findall(item)

        if isinstance(ret, str):
            lst2 = []
            for match in lst:
                attr_lst = re.compile('<' + name + '.*?' + ret + '=([\'"].[^>]*?[\'"])>', re.M | re.S).findall(match)
                if len(attr_lst) == 0:
                    attr_lst = re.compile('<' + name + '.*?' + ret + '=(.[^>]*?)>', re.M | re.S).findall(match)
                for tmp in attr_lst:
                    cont_char = tmp[0]
                    if cont_char in "'\"":
                        # Limit down to next variable.
                        if tmp.find('=' + cont_char, tmp.find(cont_char, 1)) > -1:
                            tmp = tmp[:tmp.find('=' + cont_char, tmp.find(cont_char, 1))]

                        # Limit to the last quotation mark
                        if tmp.rfind(cont_char, 1) > -1:
                            tmp = tmp[1:tmp.rfind(cont_char)]
                    else:
                        if tmp.find(" ") > 0:
                            tmp = tmp[:tmp.find(" ")]
                        elif tmp.find("/") > 0:
                            tmp = tmp[:tmp.find("/")]
                        elif tmp.find(">") > 0:
                            tmp = tmp[:tmp.find(">")]

                    lst2.append(tmp.strip())
            lst = lst2
        else:
            lst2 = []
            for match in lst:
                endstr = u"</" + name

                start = item.find(match)
                end = item.find(endstr, start)
                pos = item.find("<" + name, start + 1 )

                while pos < end and pos != -1:
                    tend = item.find(endstr, end + len(endstr))
                    if tend != -1:
                        end = tend
                    pos = item.find("<" + name, pos + 1)

                if start == -1 and end == -1:
                    temp = u""
                elif start > -1 and end > -1:
                    temp = item[start + len(match):end]
                elif end > -1:
                    temp = item[:end]
                elif start > -1:
                    temp = item[start + len(match):]

                if ret:
                    endstr = item[end:item.find(">", item.find(endstr)) + 1]
                    temp = match + temp + endstr

                item = item[item.find(temp, item.find(match)) + len(temp):]
                lst2.append(temp)
            lst = lst2
        ret_lst += lst

    return ret_lst


def replaceHTMLCodes(txt):
    txt = re.sub("(&#[0-9]+)([^;^0-9]+)", "\\1;\\2", txt)
    if sys.version_info[0] == 3:
        txt = html.unescape(txt)
    else:
        txt = HTMLParser.HTMLParser().unescape(txt)
    txt = txt.replace("&quot;", "\"")
    txt = txt.replace("&amp;", "&")
    txt = txt.replace("<br>", "\n")
    txt = txt.replace("<br/>", "\n")
    txt = txt.replace("<br />", "\n")
    return txt


def randomagent():
    BR_VERS = [
        ['%s.0' % i for i in range(18, 43)],
        ['61.0.3163.79', '61.0.3163.100', '62.0.3202.89', '62.0.3202.94', '63.0.3239.83', '63.0.3239.84', '64.0.3282.186', '65.0.3325.162', '65.0.3325.181', '66.0.3359.117', '66.0.3359.139',
         '67.0.3396.99', '68.0.3440.84', '68.0.3440.106', '68.0.3440.1805', '69.0.3497.100', '70.0.3538.67', '70.0.3538.77', '70.0.3538.110', '70.0.3538.102', '71.0.3578.80', '71.0.3578.98',
         '72.0.3626.109', '72.0.3626.121', '73.0.3683.103', '74.0.3729.131'],
        ['11.0']]
    WIN_VERS = ['Windows NT 10.0', 'Windows NT 7.0', 'Windows NT 6.3', 'Windows NT 6.2', 'Windows NT 6.1']
    FEATURES = ['; WOW64', '; Win64; IA64', '; Win64; x64', '']
    RAND_UAS = ['Mozilla/5.0 ({win_ver}{feature}; rv:{br_ver}) Gecko/20100101 Firefox/{br_ver}',
                'Mozilla/5.0 ({win_ver}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{br_ver} Safari/537.36',
                'Mozilla/5.0 ({win_ver}{feature}; Trident/7.0; rv:{br_ver}) like Gecko']
    index = random.randrange(len(RAND_UAS))
    return RAND_UAS[index].format(win_ver=random.choice(WIN_VERS), feature=random.choice(FEATURES), br_ver=random.choice(BR_VERS[index]))
