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
    
    for category in text.strip().split('\n\n'):
        pairs = map(str.strip, category.split('\n'))
        if pairs:
            name = pairs.pop(0).replace(' ', '_').lower()
            res[name] = dict(rkeyval.split(pair, 1) for pair in pairs)
    if 'Encoding settings' in res['video']:
        res['video']['Encoding settings'] = dict(pair.split('=', 1) for pair in map(str.strip, filter(None, res['video']['Encoding settings'].split('/'))))
    return res


def is_awesome(text, is_animation):
    info = MediaInfo2Dict(text)
    
    is_1080p = (info['video']['Width'] == '1 920 pixels')
    is_720p  = (info['video']['Width'] == '1 280 pixels')
    
    #Check 1: 720p/1080p
    if not is_720p and not is_1080p:
        raise ValueError("Not 1080p or 720p")
    
    #Check 2: is x264
    if info['video']['Codec ID'] != 'V_MPEG4/ISO/AVC':
        raise ValueError("Not x264.")
    
    #Check 3: DTS or AC3 track
    if 'audio_#1' not in info:
        raise ValueError("No audio tracks.")
    a_codec = info['audio_#1']['Format']
    if not a_codec == 'DTS' and not a_codec == 'AC3':
        raise ValueError("Audio track not DTS or AC3")
    
    #Check 4: English subtitles
    if 'text_#1' not in info:
        raise ValueError("No subtitle tracks.")
    if info['text_#1']['Language'] != 'English':
        raise ValueError("Subtitle track not English.")
    
    height = int(info['video']['Height'].replace('pixels', '').strip())
    ref = int(info['video']['Encoding settings']['ref'])
    if is_1080p:
        if height <= 720:
            #Check 6: 3<=ref<=6
            if ref < 3 or ref > 6:
                raise ValueError("Reference frames not between 3 and 6.")
        elif height <= 864:
            #Check 6: 3<=ref<=5
            if ref < 3 or ref > 5:
                raise ValueError("Reference frames not between 3 and 5.")
        else:
            #Check 6: 3<=ref<=4
            if ref < 3 or ref > 4:
                raise ValueError("Reference frames not between 3 and 4.")
    else:
        if height <= 540:
            #Check 6: 5<=ref<=12
            if ref < 5 or ref > 12:
                raise ValueError("Reference frames not between 5 and 12.")
        elif height <= 588:
            #Check 6: 5<=ref<=11
            if ref < 5 or ref > 11:
                raise ValueError("Reference frames not between 5 and 11.")
        elif height <= 648:
            #Check 6: 5<=ref<=10
            if ref < 5 or ref > 10:
                raise ValueError("Reference frames not between 5 and 10.")
        else:
            #Check 6: 5<=ref<=9
            if ref < 5 or ref > 9:
                raise ValueError("Reference frames not between 5 and 9.")
    
    #Check 5: cabac = 1
    if info['video']['Encoding settings']['cabac'] != '1':
        raise ValueError("Cabac must be 1.")
    
    #Check 7: vbv_maxrate <= 50000
    if int(info['video']['Encoding settings']['vbv_maxrate']) > 50000:
        raise ValueError("Vbv_maxrate must be less than or equal to 50,000.")
    
    #Check 8: vbv_bufsize <= 50000
    if int(info['video']['Encoding settings']['vbv_bufsize']) > 50000:
        raise ValueError("Vbv_bufsize must be less than or equal to 50,000.")
    
    #Check 9: analyse = 0x3:0x113
    if info['video']['Encoding settings']['analyse'] != '0x3:0x113':
        raise ValueError("Analyse must be 0x3:0x113")
    
    #Check 10: rc = crf or 2-pass
    rc = info['video']['Encoding settings']['rc']
    if rc != 'crf' and rc != '2pass':
        raise ValueError("Rc must be CRF or 2pass.")
    
    #Check 11: me_range >= 16
    if int(info['video']['Encoding settings']['me_range']) < 16:
        raise ValueError("Me_range must be greater than or equal to 16.")
    
    if 'trellis' in info['video']['Encoding settings']:
        #Check 12: trellis = 1 or 2
        trellis = info['video']['Encoding settings']['trellis']
        if trellis != '1' and trellis != 2:
            raise ValueError("Trellis must be 1 or 2.")
    else:
        #Check 12: deadzone < 10
        if int(info['video']['Encoding settings']['deadzone']) >= 10:
            raise ValueError("Deadzone must be less than 10.")
    
    #Check 13: bframe >= 3
    if int(info['video']['Encoding settings']['bframes']) < 3:
        raise ValueError("Bframes must be greater than or equal to 3.")
    
    deblock = int(info['video']['Encoding settings']['deblock'].split(':')[2])
    if is_animation:
        #Check 14: 0<=deblock<=2
        if deblock < 0 or deblock > 2:
            raise ValueError("Deblock must be between 0 and 2.")
    else:
        #Check 14: -3<=deblock<=-1
        if deblock < -3 or deblock > -1:
            raise ValueError("Deblock must be between -3 and -1.")
    
    #Check 15: me != dia or hex
    me = info['video']['Encoding settings']['me']
    if me == 'dia' or me == 'hex':
        raise ValueError("Me must not be DIA or HEX.")
    
    #Check 16: subme >= 7
    if int(info['video']['Encoding settings']['subme']) < 7:
        raise ValueError("Subme must be greater than or equal to 7.")
    
    #AWESOME!
    return True

page = xhtmlpage('Is Awesome?')
page.html.head += link(rel='stylesheet', src='isawesome.css')

wrapper = page.html.body.add(div(id='wrapper'))
header  = wrapper.add(div(id='header'))
content = wrapper.add(div(id='content'))
footer  = wrapper.add(div(id='footer'))

header += h1('Is Awesome?')
footer += div('Designed and developed by ', a('Jake Wharton', href='http://jakewharton.com'))    

if 'mediainfo' in web.post:
    is_d, is_a = is_awesome(web.post['mediainfo'])
    
    dxva = div(h1('DXVA'), p('Direct X Video Acceleration (DXVA) is ...'))
    awsm = div(h1('Awesome'), p('"Awesome" is a standard higher than DXVA. It is used to determine the highest quality encodes by certain individuals. If you are unaware of it, then you most likely do not need to concern yourself with its compliance.'))
    
    if is_d:
        dxva['class'] = 'good'
    else:
        dxva['class'] = 'bad'
    if is_a:
        awsm['class'] = 'good'
    else:
        awsm['class'] = 'bad'
    content += dxva
    content += awsm
else:
    content += p('The requirements for testing DXVA compliance are straight forward but tedious to check. The rules for "awesome"-ness are even more strict.')
    content += p('Paste the text output of the ', a('MediaInfo', href='http://mediainfo.sf.net'), ' below and press "Check".')
    form = content.add(form(method='post', action=''))
    form += textarea(name='mediainfo')
    form += input(type='button', name='submit', value='Check')

page.render()
