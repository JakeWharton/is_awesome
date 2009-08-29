#!/home/jakewharton/bin/python vendor/pyy/pyy/cgi.py

import sys, os
sys.path.append('vendor/pyy')

from pyy.url_resolver import resolve
from pyy.xhtml11      import *

#Test Statuses
PASS = 0
WARN = 1
FAIL = 2


def MediaInfo2Dict(text, video='Video', encoding_settings='Encoding settings'):
    '''
    This method takes the text output from the program MediaInfo and parses it
    into a dictionary heirarchy.
    '''
    import re
    rkeyval   = re.compile(r'\s*:\s')
    rnewline1 = re.compile('\r|\n')
    rnewline2 = re.compile('\r{2}|\n{2}')
    
    text = text.replace('\r\n', '\n').strip()
    d = {}
    
    #TODO: come up with a better newline solution than this
    for category in rnewline2.split(text):
        pairs = map(str.strip, rnewline1.split(category))
        if pairs:
            name = pairs.pop(0)
            d[name] = dict(rkeyval.split(pair, 1) for pair in pairs)
    
    if video in d and encoding_settings in d[video]:
        d[video][encoding_settings] = dict(pair.split('=', 1) for pair in map(str.strip, filter(None, d[video][encoding_settings].split('/'))))
    
    return d


awesome = 'Awesome'
dxva    = 'DXVA'


def check_compliance(text, is_animation, lang):
    info = MediaInfo2Dict(text)
    is_awesome = is_dxva = PASS
    check_table = []
    
    def pyyjoin(*args):
        return ''.join(map(str, args))
    
    ###################
    ### VIDEO TESTS ###
    ###################
    
    if lang.s_video in info:
        video = info[lang.s_video]
        
        #Check 1: 720p/1080p
        is_1080p = is_720p = False
        row    = [1, dxva, lang.s_att_resolution, '1080p ' + lang.s_or + ' 720p']
        width  = int(video[lang.s_width ].replace(lang.s_pixels, '').replace(' ', '').strip())
        height = int(video[lang.s_height].replace(lang.s_pixels, '').replace(' ', '').strip())
        res    = '%sx%s' % (width, height)
        
        dar = video[lang.s_dar]
        if ':' in dar or '/' in dar:
            dar = reduce(lambda x,y: x/y, map(float, dar.split(':' if ':' in dar else '/' )))
        else:
            dar = float(dar)
        
        if dar >= (16.0/9.0):
            #Wider than high (compared to 16:9), check width
            if width == 1920:
                is_1080p = True
                row += ['1080p (%s)' % res, PASS]
            elif width == 1280:
                is_720p = True
                row += ['720p (%s)' % res, PASS]
            else:
                row += [res, FAIL]
                is_dxva |= FAIL
        else:
            #Taller than wide (compared to 16:9), check height
            if height == 1080:
                is_1080p = True
                row += ['1080p (%s)' % res, PASS]
            elif height == 720:
                is_720p = True
                row += ['720p (%s)' % res, PASS]
            else:
                row += [res, FAIL]
                is_dxva |= FAIL
        check_table.append(row)
        
        #Check 2: is x264
        row = [2, awesome, lang.s_att_vcodec, 'V_MPEG4/ISO/AVC']
        if lang.s_codecid not in video:
            row += [lang.s_missing, FAIL]
            is_awesome |= FAIL
        else:
            codec = video[lang.s_codecid]
            if codec == 'V_MPEG4/ISO/AVC':
                row += [codec, PASS]
            else:
                row += [codec, FAIL]
                is_awesome |= FAIL
        check_table.append(row)
        
        ###############################
        ### ENCODING SETTINGS TESTS ###
        ###############################
        
        #Check 'Encoding settings' are in 'Video' section
        if lang.s_att_encoding in video:
            encoding = video[lang.s_att_encoding]
            
            #Check 5: cabac = 1
            row = [5, awesome, code('cabac'), lang.s_req_cabac]
            if 'cabac' not in encoding:
                row += [lang.s_missing, FAIL]
                is_awesome |= FAIL
            else:
                cabac = encoding['cabac']
                if cabac == '1':
                    row += [cabac, PASS]
                else:
                    row += [cabac, FAIL]
                    is_awesome |= FAIL
            check_table.append(row)
            
            #Check 6: Reference frames
            if not is_1080p and not is_720p:
                row = [6, dxva, lang.s_att_ref, lang.s_req_ref % ('?', '?'), lang.s_invalidres, FAIL]
                is_dxva |= FAIL
            else:
                refs = [
                    [(540, 12), (588, 11), (648, 10), (720, 9)], #720p
                    [(720, 6) , (864, 5) , (1080, 4)          ], #1080p
                ]
                ref_low = 3 if is_1080p else 5
                for allowed_height, allowed_ref_high in refs[int(is_1080p)]:
                    if height <= allowed_height:
                        ref_high = allowed_ref_high
                        break
                
                row = [6, dxva, lang.s_att_ref, lang.s_req_ref % (ref_low, ref_high)]
                if 'ref' not in encoding:
                    row += [lang.s_missing, FAIL]
                    is_dxva |= FAIL
                else:
                    ref = int(encoding['ref'])
                    
                    if ref_low <= ref <= ref_high:
                        row += [ref, PASS]
                    else:
                        row += [ref, FAIL]
                        is_dxva |= FAIL
            check_table.append(row)
            
            #Check 7: vbv_maxrate <= 50000
            row = [7, dxva, code('vbv_maxrate'), lang.s_req_vbvmaxrate]
            if 'vbv_maxrate' not in encoding:
                row += [lang.s_missing, WARN]
                is_dxva |= WARN
            else:
                vbv_maxrate = int(encoding['vbv_maxrate'])
                if vbv_maxrate <= 50000:
                    row += [vbv_maxrate, PASS]
                else:
                    row += [vbv_maxrate, FAIL]
                    is_dxva |= FAIL
            check_table.append(row)
            
            #Check 8: vbv_bufsize <= 50000
            row = [8, dxva, code('vbv_bufsize'), lang.s_req_vbvbufsize]
            if 'vbv_bufsize' not in encoding:
                row += [lang.s_missing, WARN]
                is_dxva |= WARN
            else:
                vbv_bufsize = int(encoding['vbv_bufsize'])
                if vbv_bufsize <= 50000:
                    row += [vbv_bufsize, PASS]
                else:
                    row += [vbv_bufsize, FAIL]
                    is_dxva |= FAIL
            check_table.append(row)
            
            #Check 9: analyse = 0x3:0x113
            row = [9, dxva, code('analyse'), lang.s_req_analyse]
            if 'analyse' not in encoding:
                row += [lang.s_missing, FAIL]
                is_dxva |= FAIL
            else:
                analyse = encoding['analyse']
                if analyse == '0x3:0x113':
                    row += [analyse, PASS]
                else:
                    row += [analyse, FAIL]
                    is_dxva |= FAIL
            check_table.append(row)
            
            #Check 10: rc = crf or 2pass
            row = [10, awesome, code('rc'), '"crf" ' + lang.s_or + ' "2pass"']
            if 'rc' not in encoding:
                row += [lang.s_missing, FAIL]
                is_awesome |= FAIL
            else:
                rc = encoding['rc']
                if rc == 'crf' or rc == '2pass':
                    row += [rc, PASS]
                else:
                    row += [rc, FAIL]
                    is_awesome |= FAIL
            check_table.append(row)
            
            #Check 11: me_range >= 16
            row = [11, awesome, code('me_range'), lang.s_req_merange]
            if 'me_range' not in encoding:
                row += [lang.s_missing, FAIL]
                is_awesome |= FAIL
            else:
                me_range = int(encoding['me_range'])
                if me_range >= 16:
                    row += [me_range, PASS]
                else:
                    row += [me_range, FAIL]
                    is_awesome |= FAIL
            check_table.append(row)
            
            #Check 12: trellis = 1 or 2 or deadzone <= 10
            row = [12, awesome, pyyjoin(code('trellis'), br(), em(lang.s_or), br(), code('deadzone')), pyyjoin(lang.s_req_trellis, br(), em(lang.s_or), br(), lang.s_req_deadzone)]
            if 'trellis' not in encoding and 'deadzone' not in encoding:
                row += [lang.s_missing, FAIL]
                is_awesome |= FAIL
            else:
                if 'trellis' in encoding:
                    trellis = int(encoding['trellis'])
                    if 1 <= trellis <= 2:
                        row += [pyyjoin(trellis, br(), em(lang.s_and), br(), lang.s_skipped), PASS]
                    else:
                        if 'deadzone' in encoding:
                            deadzone = tuple(map(int, encoding['deadzone'].split(',')))
                            if deadzone <= (10,10):
                                row += [pyyjoin(trellis, br(), em(lang.s_and), br(), encoding['deadzone']), PASS]
                            else:
                                row += [pyyjoin(trellis, br(), em(lang.s_and), br(), encoding['deadzone']), FAIL]
                                is_awesome |= FAIL
                        else:
                            row += [pyyjoin(trellis, br(), em(lang.s_and), br(), lang.s_missing.lower()), FAIL]
                            is_awesome |= FAIL
                else: #if 'trellis' not in encoding ('deadzone' in encoding)
                    deadzone = tuple(map(int, encoding['deadzone'].split(',')))
                    if deadzone <= (10,10):
                        row += [pyyjoin(lang.s_missing, br(), em(lang.s_and), br(), encoding['deadzone']), PASS]
                    else:
                        row += [pyyjoin(lang.s_missing, br(), em(lang.s_and), br(), encoding['deadzone']), FAIL]
                        is_awesome |= FAIL
            check_table.append(row)
            
            #Check 13: bframe >= 3
            row = [13, awesome, code('bframes'), lang.s_req_bframe]
            if 'bframes' not in encoding:
                row += [lang.s_missing, FAIL]
                is_awesome |= FAIL
            else:
                bframes = int(encoding['bframes'])
                if bframes >= 3:
                    row += [bframes, PASS]
                else:
                    row += [bframes, FAIL]
                    is_awesome |= FAIL
            check_table.append(row)
            
            #Check 14: deblock
            deblock = lang.s_req_deblock_a if is_animation else lang.s_req_deblock_na
            row     = [14, awesome, code('deblock'), deblock]
            if 'deblock' not in encoding:
                row += [lang.s_missing, FAIL]
                is_awesome |= FAIL
            else:
                deblock = tuple(map(int, encoding['deblock'].split(':')[1:]))
                low     = 0 if is_animation else -3
                high    = 2 if is_animation else -1
                
                if (low,low) <= deblock <= (high,high):
                    row += [deblock[0], PASS]
                else:
                    row += [deblock[0], FAIL]
                    is_awesome |= FAIL
            check_table.append(row)
            
            #Check 15: me != dia or hex
            row = [15, awesome, code('me'), lang.s_req_me % ('dia', 'hex')]
            if 'me' not in encoding:
                row += [lang.s_missing, FAIL]
                is_awesome |= FAIL
            else:
                me = encoding['me']
                if me != 'dia' and me != 'hex':
                    row += [me, PASS]
                else:
                    row += [me, FAIL]
                    is_awesome |= FAIL
            check_table.append(row)
            
            #Check 16: subme >= 7
            row = [16, awesome, code('subme'), lang.s_req_subme]
            if 'subme' not in encoding:
                row += [lang.s_missing, FAIL]
                is_awesome |= FAIL
            else:
                subme = int(encoding['subme'])
                if subme >= 7:
                    row += [subme, PASS]
                else:
                    row += [subme, FAIL]
                    is_awesome |= FAIL
            check_table.append(row)
            
        else: #if lang.s_att_encoding not in video
            check_table.append([0, dxva, lang.s_att_encoding, lang.s_req_encoding, lang.s_missing, FAIL])
            is_awesome |= FAIL
            is_dxva    |= FAIL
        
    else: #if lang.s_video not in info
        check_table.append([0, dxva, lang.s_att_video, lang.s_req_video, lang.s_missing, FAIL])
        is_awesome |= FAIL
        is_dxva    |= FAIL
    
    ###################
    ### AUDIO TESTS ###
    ###################
    
    if lang.s_audio in info:
        audio = info[lang.s_audio]
        
        row = [3, awesome, lang.s_att_acodec, ''.join(['A_DTS ', lang.s_or, ' A_AC3'])]
        if lang.s_codecid not in audio:
            row += [lang.s_missing, FAIL]
            is_awesome |= FAIL
        else:
            acodec = audio[lang.s_codecid]
            if acodec == 'A_DTS' or acodec == 'A_AC3':
                row += [acodec, PASS]
            else:
                row += [acodec, FAIL]
                is_awesome |= FAIL
    else: #if lang.s_audio not in info
        if lang.s_audio_n % 1 not in info:
            row = [3, awesome, lang.s_att_audio, lang.s_req_audio, lang.s_missing, FAIL]
            is_awesome |= FAIL
        else:
            row = [3, awesome, lang.s_att_acodec, ''.join(['A_DTS ', lang.s_or, ' A_AC3'])]
            i = 1
            codec_ids = []
            language_ids = []
            while True:
                if lang.s_audio_n % i not in info:
                    row += [lang.s_missing, FAIL]
                    is_awesome |= FAIL
                    break
                
                audio = info[lang.s_audio_n % i]
                if lang.s_codecid in audio and (audio[lang.s_codecid] == 'A_DTS' or audio[lang.s_codecid] == 'A_AC3'):
                    row += [audio[lang.s_codecid], PASS]
                    break
                
                i += 1
    check_table.append(row)
    
    
    ######################
    ### SUBTITLE TESTS ###
    ######################
    
    #Check 4: English subtitles
    if lang.s_text in info:
        row = [4, awesome, lang.s_att_tlang, lang.s_req_tlang]
        tlang = info[lang.s_text][lang.s_language]
        if tlang == lang.s_english:
            row += [tlang, PASS]
        else:
            row += [lang.s_missing, FAIL]
            is_awesome |= FAIL
    else:
        if lang.s_text_n % 1 not in info:
            row = [4, awesome, lang.s_att_text, lang.s_req_text, lang.s_missing, FAIL]
            is_awesome |= FAIL
        else:
            row = [4, awesome, lang.s_att_tlang, lang.s_req_tlang]
            
            i = 1
            langs = []
            while True:
                if lang.s_text_n % i not in info:
                    row += [', '.join(langs), FAIL]
                    is_awesome |= FAIL
                    break
                
                tlang = info[lang.s_text_n % i][lang.s_language]
                if tlang == lang.s_english:
                    row += [tlang, PASS]
                    break
                
                langs.append(tlang)
                i += 1
    check_table.append(row)
    
    return is_awesome, is_dxva, check_table


class AwesomeChecker(htmlpage):
    def __init__(self, **kwargs):
        htmlpage.__init__(self, **kwargs)
        self.title = 'Is Awesome?'
        
        #Import locale strings
        self.locale = self.request.get['locale']
        name   = 'languages.%s' % self.locale
        try:
            __import__(name)
        except ImportError:
            self.error = True
            name = 'languages.en_US'
            __import__(name)
        self.lang = sys.modules[name]
        
        #Copy equal string values
        self.lang.s_req_vbvbufsize = self.lang.s_req_vbvmaxrate
        self.lang.s_req_audio      = self.lang.s_req_video
        self.lang.s_req_text       = self.lang.s_req_video
        self.lang.s_req_encoding   = self.lang.s_req_video
        self.lang.s_req_tlang      = self.lang.s_req_alang
        self.lang.s_content_2b    %= self.lang.s_check
        
        self.is_post = 'mediainfo' in self.request.post
        self.error   = None
        if self.is_post:
            self.is_animation = 'is_animation' in self.request.post
            try:
                self.is_awesome, self.is_dxva, self.check_table = check_compliance(self.request.post['mediainfo'], self.is_animation, self.lang)
            except StandardError, e:
                import traceback
                self.error = traceback.format_exc()

def get_status_class(status):
    if status >= FAIL:
        return 'fail'
    if status == WARN:
        return 'warn'
    return 'pass'
            
class XHTML(AwesomeChecker):
    def __init__(self, **kwargs):
        AwesomeChecker.__init__(self, **kwargs)
        
        self.html.head += link(rel='stylesheet', type='text/css', href='/static/is_awesome.css')
        
        wrapper  = self.html.body.add(div(id='wrapper'))
        wrapper += div(h1(a('Is Awesome?', href='/')), id='header', __inline=True)
        content  = wrapper.add(div(id='content'))
        footer   = wrapper.add(div(id='footer'))
        langs    = footer.add(ul(id='langs'))
        for name in filter(lambda x: x.endswith('.py') and x[0] != '_', os.listdir('./languages/')):
            name = name[:-3]
            langs += li(a(img(src='/static/%s.png' % name, alt=name), href='/%s/' % name), __inline=True)
        footer  += div(self.lang.s_designed, ' ', a('Jake Wharton', href='http://jakewharton.com'), '. ', a(self.lang.s_source, href='http://github.com/JakeWharton/is_awesome/'), '.', id='about', __inline=True)
        
        #Google Analytics
        self.html.body += script('''
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
''', type='text/javascript')
        self.html.body += script('''
try {
var pageTracker = _gat._getTracker("UA-3637749-9");
pageTracker._trackPageview();
} catch(err) {}
''', type='text/javascript')
        
        if self.error:
            content += h1('An Error Has Occured')
            content += p('A fatal error has occured processing your request.')
            content += p(pre(self.error))
            content += p('Please post the above traceback along with your MediaInfo input ', a('here', href='https://awesome-hd.com/forums.php?action=viewthread&threadid=508'), '.' )
        elif self.is_post:
            content += div(h1('DXVA'), p(self.lang.s_dxva_desc), _class='compliance %s' % get_status_class(self.is_dxva))
            content += div(h1('Awesome'), p(self.lang.s_awesome_desc), _class='compliance %s' % get_status_class(self.is_awesome))
            
            tbl  = content.add(table(cellspacing=0))
            tbl += thead(tr(th(self.lang.s_compliance), th(self.lang.s_attribute), th(self.lang.s_requirement), th(self.lang.s_value), __inline=True))
            tbdy = tbl.add(tbody())
            for check in self.check_table:
                t = tr(map(td, check[1:5]), id='check%s' % check[0], __inline=True)
                t.children[-1]['class'] = get_status_class(check[5])
                tbdy += t
            
            content += div(a(self.lang.s_tryagain, ' &raquo;', href='/%s/' % self.locale), __inline=True)
        else:
            content += p(self.lang.s_content_1)
            content += p(self.lang.s_content_2a, ' ', a('MediaInfo', href='http://mediainfo.sf.net'), ' ', self.lang.s_content_2b, __inline=True)
            frm  = content.add(form(method='post', action=''))
            frm += label(self.lang.s_is_anim, ':', _for='is_animation')
            frm += _input(type='checkbox', name='is_animation')
            frm += br()
            frm += textarea(name='mediainfo')
            frm += br()
            frm += _input(type='submit', name='submit', value=self.lang.s_check)


class JSON(AwesomeChecker):
    def render(self):
        r = 'Content-type: application/json\n\n'
        if self.is_post:
            checks = ', '.join('"%s": {"compliance": "%s", "attribute": "%s", "requirement": "%s", "value": "%s", "level": "%s"}' % (check[0], check[1], check[2], check[3].replace('"', r'\"'), check[4], get_status_class(check[5])) for check in self.check_table)
            r += '{"dxva": "%s", "awesome": "%s", "checks": {%s}}' % (get_status_class(self.is_dxva), get_status_class(self.is_awesome), checks)
        else:
            r += '{}'
        return r

class XML(AwesomeChecker):
    def render(self):
        r =  'Content-type: application/xml\n\n<?xml version="1.0" encoding="UTF-8"?>\n\n'
        if self.is_post:
            r += '<compliant dxva="%s" awesome="%s">\n' % (get_status_class(self.is_dxva), get_status_class(self.is_awesome))
            for check in self.check_table:
                r += '  <check id="%s">\n' % check[0]
                r += '    <compliance>%s</compliance>\n' % check[1]
                r += '    <attribute>%s</attribute>\n' % check[2]
                r += '    <requirement>%s</requirement>\n' % check[3]
                r += '    <value>%s</value>\n' % check[4]
                r += '    <level>%s</level>\n' % get_status_class(check[5])
                r += '  </check>\n'
            r += '</compliant>'
        else:
            r += '<compliant />'
        return r



urls = (
    (r'^/(?P<locale>[a-z]{2}_[A-Z]{2})/$'     , XHTML),
    (r'^/(?P<locale>[a-z]{2}_[A-Z]{2})/json/$', JSON ),
    (r'^/(?P<locale>[a-z]{2}_[A-Z]{2})/xml/$' , XML  ),
)

print resolve(urls)
