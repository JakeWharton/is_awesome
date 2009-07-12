#!/usr/bin/python vendor/pyy/cgi.py

from vendor.pyy          import web
from vendor.pyy.htmlpage import xhtmlpage
from vendor.pyy.xhtml11  import *


def MediaInfo2Dict(text):
    """
    This method takes the text output from the program MediaInfo and parses it
    into a dictionary heirarchy.
    """
    import re
    rkeyval = re.compile(r'\s+:\s')
    res = {}
    
    for category in text.replace('\r\n', '\n').strip().split('\n\n'):
        pairs = map(str.strip, category.split('\n'))
        if pairs:
            name = pairs.pop(0).replace(' ', '_').lower()
            res[name] = dict(rkeyval.split(pair, 2) for pair in pairs)
    if 'Encoding settings' in res['video']:
        res['video']['Encoding settings'] = dict(pair.split('=', 1) for pair in map(str.strip, filter(None, res['video']['Encoding settings'].split('/'))))
    return res


def is_awesome(text, is_animation):
    info = MediaInfo2Dict(text)
    
    is_a = True
    is_d = True
    warnings = []
    errors = []
    
    def warn_d(message):
        warnings.append(strong('DXVA: ')+message)
    def error_a(message, value=None):
        is_a = False
        if value:
            errors.append(strong('Awesome: '), '%s Got: %s' % (message, value))
        else:
            errors.append(strong('Awesome: '), message)
    def error_d(message, value=None):
        is_d = False
        if value:
            errors.append(strong('DXVA: '), '%s Got: %s' % (message, value))
        else:
            errors.append(strong('DXVA: '), message)
    
    is_1080p = (info['video']['Width'] == '1 920 pixels')
    is_720p  = (info['video']['Width'] == '1 280 pixels')
    
    #Check 1: 720p/1080p
    if not is_720p and not is_1080p:
        error_a('Must be 1920 or 1280 pixels wide.', info['video']['Width'])
    
    #Check 2: is x264
    if info['video']['Codec ID'] != 'V_MPEG4/ISO/AVC':
        error_a('Not MPEG4/ISO/AVC (x264) codec.', info['video']['Codec ID'])
    
    #Check 3: DTS or AC3 track
    if 'audio' in info:
        a_codec = info['audio']['Format']
        if not a_codec == 'DTS' and not a_codec == 'AC3':
            error_a('Audio track not DTS or AC3.', info['audio']['Format'])
    elif 'audio_#1' in info:
        a_codec = info['audio_#1']['Format']
        if not a_codec == 'DTS' and not a_codec == 'AC3':
            error_a('Audio track not DTS or AC3.', info['audio_#1']['Format'])
    else:
        error_a('No audio tracks.')
    
    #Check 4: English subtitles
    if 'text' in info:
        if info['text']['Language'] != 'English':
            error_a('Subtitle track not English.', info['text']['Language'])
    elif 'text_#1' in info:
        if info['text_#1']['Language'] != 'English':
            error_a('Subtitle track not English.', info['text_#1']['Language'])
    else:
        error_a('No subtitle tracks.')
    
    height = int(info['video']['Height'].replace('pixels', '').replace(' ', '').strip())
    ref = int(info['video']['Encoding settings']['ref'])
    if is_1080p:
        if height <= 720:
            #Check 6: 3<=ref<=6
            if ref < 3 or ref > 6:
                error_d('Reference frames not between 3 and 6.', ref)
        elif height <= 864:
            #Check 6: 3<=ref<=5
            if ref < 3 or ref > 5:
                error_d('Reference frames not between 3 and 5.', ref)
        else:
            #Check 6: 3<=ref<=4
            if ref < 3 or ref > 4:
                error_d('Reference frames not between 3 and 4.', ref)
    else:
        if height <= 540:
            #Check 6: 5<=ref<=12
            if ref < 5 or ref > 12:
                error_d('Reference frames not between 5 and 12.', ref)
        elif height <= 588:
            #Check 6: 5<=ref<=11
            if ref < 5 or ref > 11:
                error_d('Reference frames not between 5 and 11.', ref)
        elif height <= 648:
            #Check 6: 5<=ref<=10
            if ref < 5 or ref > 10:
                error_d('Reference frames not between 5 and 10.', ref)
        else:
            #Check 6: 5<=ref<=9
            if ref < 5 or ref > 9:
                error_d('Reference frames not between 5 and 9.', ref)
    
    #Check 5: cabac = 1
    if info['video']['Encoding settings']['cabac'] != '1':
        error_a(code('cabac')+' must be 1.', info['video']['Encoding settings']['cabac'])
    
    #Check 7: vbv_maxrate <= 50000
    if 'vbv_maxrate' in info['video']['Encoding settings']:
        if int(info['video']['Encoding settings']['vbv_maxrate']) > 50000:
            error_d(code('vbv_maxrate'), ' must be less than or equal to 50,000.', info['video']['Encoding settings']['vbv_maxrate'])
    else:
        warn_d(code('vbv_maxrate')+' can not be determined. Assuming a value lower than 50,000.')
    
    #Check 8: vbv_bufsize <= 50000
    if 'vbv_bufsize' in info['video']['Encoding settings']:
        if int(info['video']['Encoding settings']['vbv_bufsize']) > 50000:
            error_d(code('vbv_bufsize')+' must be less than or equal to 50,000.', info['video']['Encoding settings']['vbv_bufsize'])
    else:
        warn_d(code('vbv_bufsize')+' can not be determined. Assuming a value lower than 50,000.')
    
    #Check 9: analyse = 0x3:0x113
    if info['video']['Encoding settings']['analyse'] != '0x3:0x113':
        error_d(code('analyse')+' must be 0x3:0x113.', info['video']['Encoding settings']['analyse'])
    
    #Check 10: rc = crf or 2-pass
    rc = info['video']['Encoding settings']['rc']
    if rc != 'crf' and rc != '2pass':
        error_a(code('rc')+' must be CRF or 2pass.', info['video']['Encoding settings']['rc'])
    
    #Check 11: me_range >= 16
    if int(info['video']['Encoding settings']['me_range']) < 16:
        error_a(code('me_range')+' must be greater than or equal to 16.', info['video']['Encoding settings']['me_range'])
    
    #Check 12: trellis = 1 or 2 or deadzone <= 10
    trellis = info['video']['Encoding settings']['trellis']
    if trellis != '1' and trellis != 2:
        deadzone = map(int, info['video']['Encoding settings']['deadzone'].split(','))
        if deadzone[0] > 10 or deadzone[1] > 10:
            error_a(code('trellis')+' must be 1 or 2 or ', code('deadzone'), ' values need to be less than 10.', info['video']['Encoding settings']['trellis'] + ' and ' + info['video']['Encoding settings']['deadzone'])
    
    #Check 13: bframe >= 3
    if int(info['video']['Encoding settings']['bframes']) < 3:
        error_a(code('bframes')+' must be greater than or equal to 3.', info['video']['Encoding settings']['bframes'])
    
    deblock = int(info['video']['Encoding settings']['deblock'].split(':')[2])
    if is_animation:
        #Check 14: 0<=deblock<=2
        if deblock < 0 or deblock > 2:
            error_a(code('deblock')+' must be between 0 and 2.', deblock)
    else:
        #Check 14: -3<=deblock<=-1
        if deblock < -3 or deblock > -1:
            error_a(code('deblock')+' must be between -3 and -1.', deblock)
    
    #Check 15: me != dia or hex
    me = info['video']['Encoding settings']['me']
    if me == 'dia' or me == 'hex':
        error_a(code('me')+' must not be "dia" or "hex".', me)
    
    #Check 16: subme >= 7
    if int(info['video']['Encoding settings']['subme']) < 7:
        error_a(code('subme')+' must be greater than or equal to 7.', info['video']['Encoding settings']['subme'])
    
    #AWESOME!
    return (is_a and is_d, is_d, errors, warnings)


page = xhtmlpage('Is Awesome?')
page.html.head += link(rel='stylesheet', type='text/css', href='is_awesome.css')

wrapper = page.html.body.add(div(id='wrapper'))
header  = wrapper.add(div(id='header'))
content = wrapper.add(div(id='content'))
footer  = wrapper.add(div(id='footer'))

header += h1(a('Is Awesome?', href='/'))
footer += div('Designed and developed by ', a('Jake Wharton', href='http://jakewharton.com'), '. ', a('Source code', href='http://github.com/JakeWharton/is_awesome/'), '.')

if 'mediainfo' in web.post:
    try:
        (is_a, is_d, errors, warnings) = is_awesome(web.post['mediainfo'], 'is_animation' in web.post)
        
        dxva = div(h1('DXVA'), p('DirectX Video Acceleration (DXVA) is a Microsoft API specification for the Microsoft Windows and Xbox 360 platforms that allows video decoding to be hardware accelerated.'))
        awsm = div(h1('Awesome'), p('"Awesome" is a standard higher than DXVA. It is used to determine the highest quality encodes by certain individuals. If you are unaware of it, then you most likely do not need to concern yourself with its compliance.'))
        
        dxva['class'] = is_d and 'good' or 'bad'
        awsm['class'] = is_a and 'good' or 'bad'
        content += dxva
        content += awsm
        
        if len(warnings) > 0:
            content += h3('Warnings')
            e = content.add(ul())
            for warning in warnings:
                e += li(warning)
        
        if not is_a or not is_d:
            content += h3('Errors')
            e = content.add(ul())
            for error in errors:
                e += li(error)
    except (ValueError, KeyError), e:
        content += div(h1('Fatal Error'), p(e.__class__.__name__, ': ', e), _class='bad')
        
    content += p(a('Try Again &raquo;', href='/'))
else:
    content += p('The requirements for testing DXVA compliance are straight forward but tedious to check. The rules for "awesome"-ness are even more strict.')
    content += p('Paste the text output of the ', a('MediaInfo', href='http://mediainfo.sf.net'), ' program below and press "Check".')
    form = content.add(form(method='post', action=''))
    form += label('Is Animation?:', _for='is_animation')
    form += input(type='checkbox', name='is_animation')
    form += br()
    form += textarea(name='mediainfo')
    form += br()
    form += input(type='submit', name='submit', value='Check')

page.render()
