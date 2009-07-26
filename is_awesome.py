#!/usr/bin/python vendor/pyy/cgi.py

from vendor.pyy          import web
from vendor.pyy.htmlpage import xhtmlpage
from vendor.pyy.xhtml11  import *
import re

def MediaInfo2Dict(text):
    """
    This method takes the text output from the program MediaInfo and parses it
    into a dictionary heirarchy.
    """
    import re
    rkeyval = re.compile(r'\s+:\s')
    res = {}
    
    for category in text.replace('\r\n', '\n').replace('\r', '\n').strip().split('\n\n'):
        pairs = map(str.strip, category.split('\n'))
        if pairs:
            name = pairs.pop(0).replace(' ', '_').lower()
            res[name] = dict(rkeyval.split(pair, 1) for pair in pairs)
    if 'video' in res and 'Encoding settings' in res['video']:
        res['video']['Encoding settings'] = dict(pair.split('=', 1) for pair in map(str.strip, filter(None, res['video']['Encoding settings'].split('/'))))
    return res


def is_awesome(text, is_animation):
    info = MediaInfo2Dict(text)
    
    is_a = True
    is_d = True
    warnings = ul()
    errors = ul()
    
    a = strong('Awesome: ')
    d = strong('DXVA: ')
    
    is_1080p = (info['video']['Width'] == '1 920 pixels')
    is_720p  = (info['video']['Width'] == '1 280 pixels')
    
    #Check 1: 720p/1080p
    if not is_720p and not is_1080p:
        is_a = False
        errors += li(a, 'Must be 1920 or 1280 pixels wide. Got: ', info['video']['Width'])
    
    #Check 2: is x264
    if info['video']['Codec ID'] != 'V_MPEG4/ISO/AVC':
        is_a = False
        errors += li(a, 'Not MPEG4/ISO/AVC (x264) codec. Got: ', info['video']['Codec ID'])
    
    #Check 3: English DTS or AC3 track
    if 'audio' in info:
        a_codec = info['audio']['Format']
        if a_codec != 'DTS' and a_codec != 'AC3':
            is_a = False
            errors += li(a, 'Audio track not DTS or AC3. Got: ', info['audio']['Format'])
        elif info['audio']['Language'] != 'English':
            is_a = False
            errors += li(a, 'Audio track not English. Got: ', info['audio']['Language'])
    else:
        i = 1
        while True:
            if 'audio_#%i' % i not in info:
                is_a = False
                errors += li(a, 'No English DTS or AC3 audio tracks.')
                break
            else:
                a_codec = info['audio_#%i' % i]['Format']
                if (a_codec == 'DTS' or a_codec == 'AC3') and info['audio_#%s' % i]['Language'] == 'English':
                    break
            i += 1
    
    #Check 4: English subtitles
    if 'text' in info:
        if info['text']['Language'] != 'English':
            is_a = False
            errors += li(a, 'Subtitle track not English. Got: ', info['text']['Language'])
    else:
        i = 1
        while True:
            if 'text_#%s' % i not in info:
                is_a = False
                errors += li(a, 'No English subtitle tracks.')
                break
            elif info['text_#%s' % i]['Language'] == 'English':
                break
            i += 1
    
    height = int(info['video']['Height'].replace('pixels', '').replace(' ', '').strip())
    ref = int(info['video']['Encoding settings']['ref'])
    if is_1080p:
        if height <= 720:
            #Check 6: Reference frames between 3 and 6
            if 3 <= ref <= 6:
                is_d = False
                errors += li(d, 'Reference frames not between 3 and 6. Got: ', ref)
        elif height <= 864:
            #Check 6: Reference frames between 3 and 5
            if 3 <= ref <= 5:
                is_d = False
                errors += li(d, 'Reference frames not between 3 and 5. Got: ', ref)
        else:
            #Check 6: Reference frames between 3 and 4
            if 3 <= ref <= 4:
                is_d = False
                errors += li(d, 'Reference frames not between 3 and 4. Got: ', ref)
    else:
        if height <= 540:
            #Check 6: Reference frames between 5 and 12
            if 5 <= ref <= 12:
                is_d = False
                errors += li(d, 'Reference frames not between 5 and 12. Got: ', ref)
        elif height <= 588:
            #Check 6: Reference frames between 5 and 11
            if 5 <= ref <= 11:
                is_d = False
                errors += li(d, 'Reference frames not between 5 and 11. Got: ', ref)
        elif height <= 648:
            #Check 6: Reference frames between 5 and 10
            if 5 <= ref <= 10:
                is_d = False
                errors += li(d, 'Reference frames not between 5 and 10. Got: ', ref)
        else:
            #Check 6: Reference frames between 5 and 9
            if 5 <= ref <= 9:
                is_d = False
                errors += li(d, 'Reference frames not between 5 and 9. Got: ', ref)
    
    #Check 5: cabac = 1
    if info['video']['Encoding settings']['cabac'] != '1':
        is_a = False
        errors += li(a, code('cabac'), ' must be 1. Got: ', info['video']['Encoding settings']['cabac'])
    
    #Check 7: vbv_maxrate <= 50000
    if 'vbv_maxrate' in info['video']['Encoding settings']:
        if int(info['video']['Encoding settings']['vbv_maxrate']) > 50000:
            is_d = False
            errors += li(d, code('vbv_maxrate'), ' must be less than or equal to 50,000. Got: ', info['video']['Encoding settings']['vbv_maxrate'])
    else:
        warnings += li(d, code('vbv_maxrate'), ' can not be determined. Assuming a value lower than 50,000.')
    
    #Check 8: vbv_bufsize <= 50000
    if 'vbv_bufsize' in info['video']['Encoding settings']:
        if int(info['video']['Encoding settings']['vbv_bufsize']) > 50000:
            is_d = False
            errors += li(d, code('vbv_bufsize'), ' must be less than or equal to 50,000.', info['video']['Encoding settings']['vbv_bufsize'])
    else:
        warnings += li(d, code('vbv_bufsize'), ' can not be determined. Assuming a value lower than 50,000.')
    
    #Check 9: analyse = 0x3:0x113
    if info['video']['Encoding settings']['analyse'] != '0x3:0x113':
        is_d = False
        errors += li(d, code('analyse'), ' must be 0x3:0x113. Got: ', info['video']['Encoding settings']['analyse'])
    
    #Check 10: rc = crf or 2-pass
    rc = info['video']['Encoding settings']['rc']
    if rc != 'crf' and rc != '2pass':
        is_a = False
        errors += li(a, code('rc'), ' must be CRF or 2pass. Got: ', info['video']['Encoding settings']['rc'])
    
    #Check 11: me_range >= 16
    if int(info['video']['Encoding settings']['me_range']) < 16:
        is_a = False
        errors += li(a, code('me_range'), ' must be greater than or equal to 16. Got: ', info['video']['Encoding settings']['me_range'])
    
    #Check 12: trellis = 1 or 2 or deadzone <= 10
    trellis = info['video']['Encoding settings']['trellis']
    if trellis != '1' and trellis != '2':
        deadzone = map(int, info['video']['Encoding settings']['deadzone'].split(','))
        if deadzone[0] > 10 or deadzone[1] > 10:
            is_a = False
            errors += li(a, code('trellis')+' must be 1 or 2 or ', code('deadzone'), ' values need to be less than 10. Got: ', info['video']['Encoding settings']['trellis'], ' and ', info['video']['Encoding settings']['deadzone'])
    
    #Check 13: bframe >= 3
    if int(info['video']['Encoding settings']['bframes']) < 3:
        is_a = False
        errors += li(a, code('bframes'), ' must be greater than or equal to 3. Got: ', info['video']['Encoding settings']['bframes'])
    
    deblock = int(info['video']['Encoding settings']['deblock'].split(':')[2])
    if is_animation:
        #Check 14: Deblock between 0 and 2
        if 0 <= deblock <= 2:
            id_a = False
            errors += li(a, code('deblock'), ' must be between 0 and 2. Got: ', deblock)
    else:
        #Check 14: Deblock between -3 and -1
        if -3 <= deblock <= -1:
            is_a = False
            errors += li(a, code('deblock'), ' must be between -3 and -1. Got: ', deblock)
    
    #Check 15: me != dia or hex
    me = info['video']['Encoding settings']['me']
    if me == 'dia' or me == 'hex':
        is_a = False
        errors += li(a, code('me'), ' must not be "dia" or "hex". Got: ', me)
    
    #Check 16: subme >= 7
    if int(info['video']['Encoding settings']['subme']) < 7:
        is_a = False
        errors += li(a, code('subme'), ' must be greater than or equal to 7. Got: ', info['video']['Encoding settings']['subme'])
    
    #AWESOME!
    return (is_a and is_d, is_d, errors, warnings)


#Output types
XHTML = 0
JSON  = 1
XML = 2

#URL mapping
urls = (
    (r'^/$', XHTML),
    (r'^/json/$', JSON),
    (r'^/xml/$', XML),
)

#Determine output format
output = XHTML
for regex, url_output in urls:
    if re.match(regex, web.env['REQUEST_URI']):
        output = url_output
        break

#Parse POSTed data (if any)
is_post = 'mediainfo' in web.post
if is_post:
    try:
        (is_a, is_d, errors, warnings) = is_awesome(web.post['mediainfo'], 'is_animation' in web.post and web.post['is_animation'])
    except (ValueError, KeyError), e:
        is_a = is_d = False
        errors = ul(li(strong('Fatal %s: ' % type(e).__name__), str(e)))
        warnings = ul()
else:
    is_a = is_d = False
    errors = ul(li(strong('Fatal Error: '), 'No MediaInfo text POSTed.'))
    warnings = ul()

#Output in specified format
if output == JSON:
    print 'Content-type: application/json'
    print
    print '{"dxva": %s, "awesome": %s, "error_count": %s, "errors": "%s", "warning_count": %s, "warnings": "%s"}' % (is_d and 'true' or 'false', is_a and 'true' or 'false', len(errors.children), str(errors), len(warnings.children), str(warnings))

elif output == XML:
    print 'Content-type: application/xml'
    print
    print '<?xml version="1.0" encoding="UTF-8"?>'
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

elif output == XHTML:
    page = xhtmlpage('Is Awesome?')
    page.html.head += link(rel='stylesheet', type='text/css', href='is_awesome.css')
    
    wrapper = page.html.body.add(div(id='wrapper'))
    wrapper += div(h1(a('Is Awesome?', href='/')), id='header', __inline=True)
    content = wrapper.add(div(id='content'))
    wrapper += div('Designed and developed by ', a('Jake Wharton', href='http://jakewharton.com'), '. ', a('Source code', href='http://github.com/JakeWharton/is_awesome/'), '.', id='footer', __inline=True)
    
    if is_post:
        dxva = div(h1('DXVA'), p('DirectX Video Acceleration (DXVA) is a Microsoft API specification for the Microsoft Windows and Xbox 360 platforms that allows video decoding to be hardware accelerated. It is also useful for determining playback compatability with Sigma Designs, Inc.-based hardware media players.'))
        awsm = div(h1('Awesome'), p('"Awesome" is a standard higher than DXVA. It is used to determine the highest quality encodes by certain individuals. If you are unaware of it, then you most likely do not need to concern yourself with compliance.'))
        
        dxva['class'] = is_d and 'good' or 'bad'
        awsm['class'] = is_a and 'good' or 'bad'
        content += dxva
        content += awsm
        
        if len(warnings.children) > 0:
            content += h3('Warnings')
            content += warnings
        
        if len(errors.children) > 0:
            content += h3('Errors')
            content += errors
            
        content += p(a('Try Again &raquo;', href='/'), __inline=True)
    else:
        content += p('The requirements for testing DXVA compliance are straight forward but tedious to check. The rules for "awesome"-ness are even more strict.')
        content += p('Paste the text output of the ', a('MediaInfo', href='http://mediainfo.sf.net'), ' program below and press "Check".', __inline=True)
        form = content.add(form(method='post', action=''))
        form += label('Is Animation?:', _for='is_animation')
        form += input(type='checkbox', name='is_animation') + br()
        form += textarea(name='mediainfo') + br()
        form += input(type='submit', name='submit', value='Check')

    #Google Analytics
    page.html += script('''
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
''', type='text/javascript')
    page.html += script('''
try {
var pageTracker = _gat._getTracker("UA-3637749-9");
pageTracker._trackPageview();
} catch(err) {}
''', type='text/javascript')

    page.render()
