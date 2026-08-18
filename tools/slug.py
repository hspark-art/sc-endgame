# -*- coding: utf-8 -*-
"""한글 이름 → URL 슬러그. 국어의 로마자 표기법(음절 단위) + 흔한 성씨 관용 표기."""

CHO = ['g','kk','n','d','tt','r','m','b','pp','s','ss','','j','jj','ch','k','t','p','h']
JUNG = ['a','ae','ya','yae','eo','e','yeo','ye','o','wa','wae','oe','yo',
        'u','wo','we','wi','yu','eu','ui','i']
JONG = ['','k','k','k','n','n','n','t','l','k','m','p','l','l','p','l','m','p',
        'p','t','t','ng','t','t','k','t','p','t']

# 여권·언론에서 굳어진 성씨 표기 (엄격한 로마자 표기법보다 이쪽이 읽기 쉽습니다)
SURNAME = {
    '김':'kim','이':'lee','박':'park','최':'choi','정':'jung','강':'kang','조':'cho',
    '윤':'yoon','장':'jang','임':'lim','한':'han','오':'oh','서':'seo','신':'shin',
    '권':'kwon','황':'hwang','안':'ahn','송':'song','류':'ryu','전':'jeon','홍':'hong',
    '고':'ko','문':'moon','양':'yang','손':'son','배':'bae','백':'baek','허':'heo',
    '유':'yoo','남':'nam','심':'shim','노':'noh','하':'ha','곽':'kwak','성':'sung',
    '차':'cha','주':'joo','우':'woo','구':'koo','민':'min','진':'jin','지':'ji',
    '엄':'eom','채':'chae','원':'won','천':'chun','방':'bang','공':'kong','현':'hyun',
    '함':'ham','변':'byun','염':'yeom','여':'yeo','추':'chu','도':'do','소':'so',
    '석':'seok','선':'sun','설':'seol','马':'ma','마':'ma','길':'gil','연':'yeon',
    '위':'wi','표':'pyo','명':'myung','기':'ki','반':'ban','왕':'wang','금':'keum',
    '옥':'ok','육':'yook','인':'in','맹':'maeng','제':'je','모':'mo','탁':'tak',
    '국':'kook','어':'eo','은':'eun','편':'pyun','용':'yong','예':'ye','경':'kyung',
    '봉':'bong','사':'sa','부':'boo','피':'pi','설':'seol','감':'kam','호':'ho',
}


def romanize(text):
    """한글 문자열을 로마자로 옮깁니다. 한글이 아닌 글자는 그대로 둡니다."""
    out = []
    for ch in text:
        code = ord(ch) - 0xAC00
        if 0 <= code < 11172:
            out.append(CHO[code // 588] + JUNG[(code % 588) // 28] + JONG[code % 28])
        else:
            out.append(ch)
    return ''.join(out)


def name_slug(name):
    """'박상현' → 'park-sanghyeon'. 성(첫 글자)은 관용 표기를 우선합니다."""
    name = (name or '').strip()
    if not name:
        return ''
    head, rest = name[0], name[1:]
    if '가' <= head <= '힣' and rest:
        first = SURNAME.get(head) or romanize(head)
        return (first + '-' + romanize(rest)).lower()
    slug = romanize(name).lower()
    return ''.join(c if (c.isalnum() or c == '-') else '-' for c in slug).strip('-')


def unique_slugs(names):
    """이름 목록 → {이름: 슬러그}. 충돌하면 -2, -3 을 붙입니다."""
    seen, out = {}, {}
    for n in names:
        base = name_slug(n) or 'player'
        s, i = base, 1
        while s in seen:
            i += 1
            s = '%s-%d' % (base, i)
        seen[s] = n
        out[n] = s
    return out
