#!/home/jakewharton/bin/python vendor/pyy/pyy/cgi.py

import sys, os
sys.path.append('vendor/pyy')

from pyy.request      import request
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
    rkeyval = re.compile(r'\s+:\s')
    d = {}
    
    #TODO: come up with a better newline solution than this
    for category in text.replace('\r\n', '\n').replace('\r', '\n').strip().split('\n\n'):
        pairs = map(str.strip, category.split('\n'))
        if pairs:
            name = pairs.pop(0)
            d[name] = dict(rkeyval.split(pair, 1) for pair in pairs)
    
    if video in d and encoding_settings in d[video]:
        d[video][encoding_settings] = dict(pair.split('=', 1) for pair in map(str.strip, filter(None, d[video][encoding_settings].split('/'))))
    
    return d


def get_status_class(status):
    if status >= FAIL:
        return 'fail'
    if status == WARN:
        return 'warn'
    return 'pass'


def tdvalue(value, status=PASS):
    v = td(value, _class='got ')
    if status == PASS:
        v['class'] += 'pass'
    elif status == WARN:
        v['class'] += 'warn'
    else:
        v['class'] += 'fail'
    return v

def trrow(test, attribute, requirement):
    return tr(td(test), td(attribute), td(requirement))


awesome = 'Awesome'
dxva    = 'DXVA'


def check_compliance(text, is_animation, lang):
    info = MediaInfo2Dict(text)
    is_awesome = is_dxva = PASS
    
    check_table  = table(cellspacing=0)
    check_table += thead(tr(th(lang.s_compliance), th(lang.s_attribute), th(lang.s_requirement), th(lang.s_value)))
    tbdy         = check_table.add(tbody())
    
    ###################
    ### VIDEO TESTS ###
    ###################
    
    if lang.s_video in info:
        video = info[lang.s_video]
        
        #Check 1: 720p/1080p
        row = tbdy.add(trrow(dxva, lang.s_att_resolution, ['1080p ', lang.s_or, ' 720p']))
        is_1080p = is_720p = False
        width  = int(video[lang.s_width ].replace(lang.s_pixels, '').replace(' ', '').strip())
        height = int(video[lang.s_height].replace(lang.s_pixels, '').replace(' ', '').strip())
        dar    = float(video[lang.s_dar])
        res    = '%sx%s' % (width, height)
        if dar >= (16.0/9.0):
            #Wider than high (compared to 16:9), check width
            if width == 1920:
                is_1080p = True
                row += tdvalue('1080p (%s)' % res)
            elif width == 1280:
                is_720p = True
                row += tdvalue('720p (%s)' % res)
            else:
                row += tdvalue(res, FAIL)
                is_dxva |= FAIL
        else:
            #Taller than wide (compared to 16:9), check height
            if height == 1080:
                is_1080p = True
                row += tdvalue('1080p (%s)' % res)
            elif height == 720:
                is_720p = True
                row += tdvalue('720p (%s)' % res)
            else:
                row += tdvalue(res, FAIL)
                is_dxva |= FAIL
        
        #Check 2: is x264
        row = tbdy.add(trrow(awesome, lang.s_att_vcodec, 'V_MPEG4/ISO/AVC (x264)'))
        if lang.s_codecid not in video:
            row += tdvalue(lang.s_missing, FAIL)
            is_awesome |= FAIL
        else:
            codec = video[lang.s_codecid]
            if codec == 'V_MPEG4/ISO/AVC':
                row += tdvalue(codec)
            else:
                row += tdvalue(codec, FAIL)
                is_awesome |= FAIL
        
        ###############################
        ### ENCODING SETTINGS TESTS ###
        ###############################
        
        #Check 'Encoding settings' are in 'Video' section
        if lang.s_att_encoding in video:
            encoding = video[lang.s_att_encoding]
            
            #Check 5: cabac = 1
            row = tbdy.add(trrow(awesome, code('cabac'), lang.s_req_cabac))
            if 'cabac' not in encoding:
                row += tdvalue(lang.s_missing, FAIL)
                is_awesome |= FAIL
            else:
                cabac = encoding['cabac']
                if cabac == '1':
                    row += tdvalue(cabac)
                else:
                    row += tdvalue(cabac, FAIL)
                    is_awesome |= FAIL
            
            #Check 6: Reference frames
            refs = [
                [(540, 12), (588, 11), (648, 10), (720, 9)], #720p
                [(720, 6) , (864, 5) , (1080, 4)          ], #1080p
            ]
            ref_low = 3 if is_1080p else 5
            for allowed_height, allowed_ref_high in refs[int(is_1080p)]:
                if height <= allowed_height:
                    ref_high = allowed_ref_high
                    break
            
            row = tbdy.add(trrow(dxva, lang.s_att_ref, lang.s_req_ref % (ref_low, ref_high)))
            if 'ref' not in encoding:
                row += tdvalue(lang.s_missing, FAIL)
                is_dxva |= FAIL
            elif 'ref_high' not in locals():
                row += tdvalue(lang.s_invalidh, FAIL)
                is_dxva |= FAIL
            else:
                ref = int(encoding['ref'])
                
                if not is_1080p and not is_720p:
                    row += tdvalue(lang.s_invalidres, FAIL)
                    is_dxva |= FAIL
                else: #is_1080p or is_720p
                  if ref_low <= ref <= ref_high:
                      row += tdvalue(ref)
                  else:
                      row += tdvalue(ref, FAIL)
                      is_dxva |= FAIL
            
            #Check 7: vbv_maxrate <= 50000
            row = tbdy.add(trrow(dxva, code('vbv_maxrate'), lang.s_req_vbvmaxrate))
            if 'vbv_maxrate' not in encoding:
                row += tdvalue(lang.s_missing, WARN)
                is_dxva |= WARN
            else:
                vbv_maxrate = int(encoding['vbv_maxrate'])
                if vbv_maxrate <= 50000:
                    row += tdvalue(vbv_maxrate)
                else:
                    row += tdvalue(vbv_maxrate, FAIL)
                    is_dxva |= FAIL
            
            #Check 8: vbv_bufsize <= 50000
            row = tbdy.add(trrow(dxva, code('vbv_bufsize'), lang.s_req_vbvbufsize))
            if 'vbv_bufsize' not in encoding:
                row += tdvalue(lang.s_missing, WARN)
                is_dxva |= WARN
            else:
                vbv_bufsize = int(encoding['vbv_bufsize'])
                if vbv_bufsize <= 50000:
                    row += tdvalue(vbv_bufsize)
                else:
                    row += tdvalue(vbv_bufsize, FAIL)
                    is_dxva |= FAIL
            
            #Check 9: analyse = 0x3:0x113
            row = tbdy.add(trrow(dxva, code('analyse'), lang.s_req_analyse))
            if 'analyse' not in encoding:
                row += tdvalue(lang.s_missing, FAIL)
                is_dxva |= FAIL
            else:
                analyse = encoding['analyse']
                if analyse == '0x3:0x113':
                    row += tdvalue(analyse)
                else:
                    row += tdvalue(analyse, FAIL)
                    is_dxva |= FAIL
            
            #Check 10: rc = crf or 2pass
            row = tbdy.add(trrow(awesome, code('rc'), ['"crf" ', lang.s_or, ' "2pass"']))
            if 'rc' not in encoding:
                row += tdvalue(lang.s_missing, FAIL)
                is_awesome |= FAIL
            else:
                rc = encoding['rc']
                if rc == 'crf' or rc == '2pass':
                    row += tdvalue(rc)
                else:
                    row += tdvalue(rc, FAIL)
                    is_awesome |= FAIL
            
            #Check 11: me_range >= 16
            row = tbdy.add(trrow(awesome, code('me_range'), lang.s_req_merange))
            if 'me_range' not in encoding:
                row += tdvalue(lang.s_missing, FAIL)
                is_awesome |= FAIL
            else:
                me_range = int(encoding['me_range'])
                if me_range >= 16:
                    row += tdvalue(me_range)
                else:
                    row += tdvalue(me_range, FAIL)
                    is_awesome |= FAIL
            
            #Check 12: trellis = 1 or 2 or deadzone <= 10
            row = tbdy.add(trrow(awesome, [code('trellis'), br(), em(lang.s_or), br(), code('deadzone')], [lang.s_req_trellis, br(), em(lang.s_or), br(), lang.s_req_deadzone]))
            if 'trellis' not in encoding and 'deadzone' not in encoding:
                row += tdvalue(lang.s_missing, FAIL)
                is_awesome |= FAIL
            else:
                if 'trellis' in encoding:
                    trellis = int(encoding['trellis'])
                    if 1 <= trellis <= 2:
                        row += tdvalue([trellis, br(), em(lang.s_and), br(), lang.s_skipped])
                    else:
                        if 'deadzone' in encoding:
                            deadzone = tuple(map(int, encoding['deadzone'].split(',')))
                            if deadzone <= (10,10):
                                row += tdvalue([trellis, br(), lang.s_and, br(), deadzone])
                            else:
                                row += tdvalue([trellis, br(), lang.s_and, br(), deadzone], FAIL)
                                is_awesome |= FAIL
                        else:
                            row += tdvalue([trellis, br(), lang.s_and, br(), lang.s_missing.lower()], FAIL)
                            is_awesome |= FAIL
                else: #if 'trellis' not in encoding ('deadzone' in encoding)
                    deadzone = tuple(map(int, encoding['deadzone'].split(',')))
                    if deadzone <= (10,10):
                        row += tdvalue([lang.s_missing, br(), lang.s_and, br(), deadzone])
                    else:
                        row += tdvalue([lang.s_missing, br(), lang.s_and, br(), deadzone], FAIL)
                        is_awesome |= FAIL
            
            #Check 13: bframe >= 3
            row = tbdy.add(trrow(awesome, code('bframes'), lang.s_req_bframe))
            if 'bframes' not in encoding:
                row += tdvalue(lang.s_missing, FAIL)
                is_awesome |= FAIL
            else:
                bframes = int(encoding['bframes'])
                if bframes >= 3:
                    row += tdvalue(bframes)
                else:
                    row += tdvalue(bframes, FAIL)
                    is_awesome |= FAIL
            
            #Check 14: deblock
            deblock = lang.s_req_deblock_a if is_animation else lang.s_req_deblock_na
            row = tbdy.add(trrow(awesome, code('deblock'), deblock))
            if 'deblock' not in encoding:
                row += tdvalue(lang.s_missing, FAIL)
                is_awesome |= FAIL
            else:
                deblock = tuple(map(int, encoding['deblock'].split(':')[1:]))
                low  = 0 if is_animation else -3
                high = 2 if is_animation else -1
                
                if (low,low) <= deblock <= (high,high):
                    row += tdvalue(deblock[0])
                else:
                    row += tdvalue(deblock[0], FAIL)
                    is_awesome |= FAIL
            
            #Check 15: me != dia or hex
            row = tbdy.add(trrow(awesome, code('me'), lang.s_req_me % ('dia', 'hex')))
            if 'me' not in encoding:
                row += tdvalue(lang.s_missing, FAIL)
                is_awesome |= FAIL
            else:
                me = encoding['me']
                if me != 'dia' and me != 'hex':
                    row += tdvalue(me)
                else:
                    row += tdvalue(me, FAIL)
                    is_awesome |= FAIL
            
            #Check 16: subme >= 7
            row = tbdy.add(trrow(awesome, code('subme'), lang.s_req_subme))
            if 'subme' not in encoding:
                row += tdvalue(lang.s_missing, FAIL)
                is_awesome |= FAIL
            else:
                subme = int(encoding['subme'])
                if subme >= 7:
                    row += tdvalue(subme)
                else:
                    row += tdvalue(subme, FAIL)
                    is_awesome |= FAIL
            
        else: #if lang.s_att_encoding not in video
            row  = tbdy.add(trrow(dxva, lang.s_att_encoding, lang.s_req_encoding))
            row += tdvalue(lang.s_missing, FAIL)
            is_awesome |= FAIL
            is_dxva    |= FAIL
        
    else: #if lang.s_video not in info
        row  = tbdy.add(trrow(dxva, lang.s_att_video, lang.s_req_video))
        row += tdvalue(lang.s_missing, FAIL)
        is_awesome |= FAIL
        is_dxva    |= FAIL
    
    ###################
    ### AUDIO TESTS ###
    ###################
    
    if lang.s_audio in info:
        audio = info[lang.s_audio]
        
        row = tbdy.add(trrow(awesome, lang.s_att_acodec, ['A_DTS ', lang.s_or, ' A_AC3']))
        if lang.s_codecid not in audio:
            row += tdvalue(lang.s_missing, FAIL)
            is_awesome |= FAIL
        else:
            acodec = audio[lang.s_codecid]
            if acodec == 'A_DTS' or acodec == 'A_AC3':
                row += tdvalue(acodec)
            else:
                row += tdvalue(acodec, FAIL)
                is_awesome |= FAIL
        
        row = tbdy.add(trrow(awesome, lang.s_att_alang, lang.s_req_alang))
        if lang.s_language not in audio:
            row += tdvalue(lang.s_missing, FAIL)
            is_awesome |= FAIL
        else:
            alang = audio[lang.s_language]
            if alang == lang.s_english:
                row += tdvalue(alang)
            else:
                row += tdvalue(alang, FAIL)
                is_awesome |= FAIL
    else: #if lang.s_audio not in info
        if lang.s_audio_n % 1 not in info:
            row  = tbdy.add(trrow(awesome, lang.s_att_audio, lang.s_req_audio))
            row += tdvalue(lang.s_missing, FAIL)
            is_awesome |= FAIL
        else:
            i = 1
            codec_ids = []
            language_ids = []
            while True:
                if lang.s_audio_n % i not in info:
                    break
                
                audio = info[lang.s_audio_n % i]
                if lang.s_codecid in audio and (audio[lang.s_codecid] == 'A_DTS' or audio[lang.s_codecid] == 'A_AC3'):
                    codec_ids.append(i)
                if lang.s_language in audio and audio[lang.s_language] == s.english:
                    language_ids.append(i)
                
                i += 1
            
            union = set(codec_ids) & set(language_ids)
            if union:
                valid = []
                for id in union:
                    valid_id = union[0]
                    valid.append(audio[lang.s_audio_n % valid_id][lang.s_codecid][2:] + ' ' + audio[lang.s_audio_n % valid_id][lang.s_language])
                row  = tbdy.add(trrow(awesome, lang.s_att_audio, lang.s_req_aboth))
                row += tdvalue(' ,'.join(valid))
            elif codec_ids and not language_ids:
                row  = tbdy.add(trrow(awesome, lang.s_att_acodec, ['A_DTS ', lang.s_or, ' A_AC3']))
                #TODO: get codecs for codec_ids
                row += tdvalue('TODO')
                row  = tbdy.add(trrow(awesome, lang.s_att_alang, lang.s_req_alang))
                #TODO: if all language values for codec_ids are missing then WARN, otherwise FAIL
                row += tdvalue('Multiple', WARN)
                is_awesome |= WARN
            elif language_ids and not codec_ids:
                row  = tbdy.add(trrow(awesome, lang.s_att_acodec, lang.s_req_acodec))
                row += tdvalue('Not DTS or AC3', FAIL)
                row  = tbdy.add(trrow(awesome, lang.s_att_alang, lang.s_req_alang))
                row += tdvalue(lang.s_english)
                is_awesome |= FAIL
            else:
                row  = tbdy.add(trrow(awesome, lang.s_att_audio, lang.s_req_both))
                #TODO: lookup codec/language pairs
                row += tdvalue('Multiple', FAIL)
                is_awesome |= FAIL
    
    ######################
    ### SUBTITLE TESTS ###
    ######################
    
    #Check 4: English subtitles
    if lang.s_text in info:
        row = tbdy.add(trrow(awesome, lang.s_att_tlang, lang.s_req_tlang))
        tlang = info[lang.s_text][lang.s_language]
        if tlang == lang.s_english:
            row += tdvalue(tlang)
        else:
            row += tdvalue(lang.s_missing, FAIL)
            is_awesome |= FAIL
    else:
        if lang.s_text_n % 1 not in info:
            row  = tbdy.add(trrow(awesome, lang.s_att_text, lang.s_req_text))
            row += tdvalue(lang.s_missing, FAIL)
            is_awesome |= FAIL
        else:
            row = tbdy.add(trrow(awesome, lang.s_att_tlang, lang.s_req_tlang))
            
            i = 1
            langs = []
            while True:
                if lang.s_text_n % i not in info:
                    row += tdvalue(', '.join(langs), FAIL)
                    is_awesome |= FAIL
                    break
                
                tlang = info[lang.s_text_n % i][lang.s_language]
                if tlang == lang.s_english:
                    row += tdvalue(tlang)
                    break
                
                langs.append(tlang)
                i += 1
    
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
        self.lang.s_req_tlang      = self.lang.s_req_alang
        self.lang.s_content_2b    %= self.lang.s_check
        
        self.is_post = 'mediainfo' in self.request.post
        if self.is_post:
            self.is_animation = 'is_animation' in self.request.post
            self.is_awesome, self.is_dxva, self.check_table = check_compliance(self.request.post['mediainfo'], self.is_animation, self.lang)

class XHTML(AwesomeChecker):
    def __init__(self, **kwargs):
        AwesomeChecker.__init__(self, **kwargs)
        
        self.html.head += link(rel='stylesheet', type='text/css', href='/static/is_awesome.css')
        
        wrapper  = self.html.body.add(div(id='wrapper'))
        wrapper += div(h1(a('Is Awesome?', href='/')), id='header', __inline=True)
        content  = wrapper.add(div(id='content'))
        footer   = wrapper.add(div(id='footer'))
        langs    = footer.add(ul(id='langs'))
        for name in filter(lambda x: x.endswith('.py'), os.listdir('./languages/')):
            if name != '__init__.py':
               name = name[:-3]
               langs += li(a(img(src='/static/%s.png' % name, alt=name), href='/%s/' % name))
        footer  += div(self.lang.s_designed, ' ', a('Jake Wharton', href='http://jakewharton.com'), '. ', a(self.lang.s_source, href='http://github.com/JakeWharton/is_awesome/'), '.', id='about', __inline=True)
        
        #Google Analytics
        self.html += script('''
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
''', type='text/javascript')
        self.html += script('''
try {
var pageTracker = _gat._getTracker("UA-3637749-9");
pageTracker._trackPageview();
} catch(err) {}
''', type='text/javascript')
        
        if self.is_post:
            content += div(h1('DXVA'), p(self.lang.s_dxva_desc), _class='compliance %s' % get_status_class(self.is_dxva))
            content += div(h1('Awesome'), p(self.lang.s_awesome_desc), _class='compliance %s' % get_status_class(self.is_awesome))
            content += self.check_table
            
            content += div(a(self.lang.s_tryagain, ' &raquo;', href='/%s/' % self.locale), __inline=True)
        else:
            content += p(self.lang.s_content_1)
            content += p(self.lang.s_content_2a, ' ', a('MediaInfo', href='http://mediainfo.sf.net'), ' ', self.lang.s_content_2b, __inline=True)
            frm  = content.add(form(method='post', action=''))
            frm += label(self.lang.s_is_anim, ':', _for='is_animation')
            frm += input_(type='checkbox', name='is_animation')
            frm += br()
            frm += textarea(name='mediainfo')
            frm += br()
            frm += input_(type='submit', name='submit', value=self.lang.s_check)


class JSON(AwesomeChecker):
    def render(self):
        print 'Content-type: application/json'
        print
        if self.is_post:
            print '{"dxva": %s, "awesome": %s, "error_count": %s, "errors": "%s", "warning_count": %s, "warnings": "%s"}' % (is_d and 'true' or 'false', is_a and 'true' or 'false', len(errors.children), str(errors), len(warnings.children), str(warnings))
        else:
            print '{}'

class XML(AwesomeChecker):
    def render(self):
        print 'Content-type: application/xml'
        print
        print '<?xml version="1.0" encoding="UTF-8"?>'
        print
        if self.is_post:
            print '<compliant dxva="%s" awesome="%s">' % (is_d and 'true' or 'false', is_a and 'true' or 'false')
            if len(errors.children) > 0:
                print '\t<errors count="%s">%s\n\t</errors>' % (len(errors.children), errors.render_children(2, True))
            else:
                print '\t<errors count="0"/>'
            if len(warnings.children) > 0:
                print '\t<warnings count="%s">%s\n\t</warnings>' % (len(warnings.children), warnings.render_children(2, True))
            else:
                print '\t<warnings count="0"/>'
            print '</compliant>'
        else:
            print '<compliant />'




#URL mapping
urls = (
    (r'^/(?P<locale>[a-z]{2}_[A-Z]{2})/$', XHTML),
    (r'^/json/$', JSON),
    (r'^/xml/$', XML),
)

print resolve(urls).render()
