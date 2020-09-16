import re

from zhihu.document.html import Parsing


class Markdown:
    def __init__(self, content, meta):
        self.meta = meta
        self.content = content
        self.image_list = list()

    def write_down(self, outfile):
        background = ''
        if self.meta.background is not None and self.meta.background != '':
            background = '![背景大图](%s)\n\n' % self.meta.background

        title = '# [%s](%s)\n\n' % (self.meta.title, self.meta.original_url)

        split_line = '-' * len(title) + '\n\n'

        if self.meta.author_avatar_url is not None or self.meta.author_avatar_url != '':
            head_img = '![%s](%s "%s")&emsp;' % (
                self.meta.author, self.meta.author_avatar_url, self.meta.author)
        else:
            head_img = ''

        if self.meta.created_date is not None or self.meta.created_date != '':
            author = '**[%s](%s) / %s**\n\n' % (
                self.meta.author, self.meta.author_homepage, self.meta.created_date)
        else:
            author = '**[%s](%s)\n\n' % (self.meta.author, self.meta.author_homepage)

        outfile.write(background + title + split_line + head_img + author)

        outfile.write(Formatter(self.content).formatter(self))


class Formatter:
    functions = {
        'div': 'code',
        'figure': 'figure',
        'a': 'url',
        'img': 'math',
        'br': 'newline',
        'hr': 'horizontal',
        'sup': 'superscript',
        'blockquote': 'quote',
        'p': 'paragraph',
        'ol': 'table',
        'ul': 'table',
        'hx': 'font_style',
        'em': 'font_style',
        'strong': 'font_style',
        'b': 'font_style',
        'i': 'font_style',
        'u': 'font_style',
        'li': 'font_style'
    }

    warp = (None, 'sup', 'img', 'a', 'div', 'figure', 'br', 'hr', 'blockquote', 'ol', 'ul')
    emphasize = ('em', 'strong', 'b', 'i')
    split = ('p' 'br', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6')

    def __init__(self, content):
        self.tags = Parsing().parse_tag(content)
        self.image_list = list()
        self.reference_list = list()

    def formatter(self, opt):
        formatter = self.format(self.tags, self.reference_list, self.image_list)
        opt.image_list = self.image_list
        content = list()
        for ref in self.reference_list:
            content.append('[%s] [%s](%s)\n\n' % (ref.get('index'), ref.get('text'), ref.get('url')))
        return formatter + ''.join(content)

    @classmethod
    def format(cls, tags, reference_list, image_list, level=1):
        content = list()
        for tag in tags:
            warp = cls.format_tag(
                tag=tag, reference_list=reference_list, image_list=image_list, level=level)
            inner = None
            if tag.name not in cls.warp:
                inner = cls.format(tag.contents, reference_list, image_list, level+1)
            content.append(cls._warp_inner(warp, inner))

        return ''.join(content)

    @classmethod
    def format_tag(cls, **kwargs):
        handle = cls.find_handle_func_by_name(kwargs.get('tag').name)
        return handle(**kwargs)

    @classmethod
    def _warp_inner(cls, warp, inner):
        if inner is None:
            return warp
        return warp.format(inner=inner)

    @classmethod
    def find_handle_func_by_name(cls, name):
        if name is None:
            return cls.string

        if re.match('h\d', name):
            name = 'hx'

        return getattr(cls, cls.functions.get(name, 'unsupported'))

    @classmethod
    def string(cls, **kwargs):
        return kwargs.get('tag').string

    @classmethod
    def superscript(cls, **kwargs):
        """处理sup标签，知乎标准的文献引用样式"""

        data_url = kwargs.get('tag').get_attrs('data-url')
        index = kwargs.get('tag').get_attrs('data-numero')
        data_text = kwargs.get('tag').get_attrs('data-text')

        kwargs.get('reference_list').append(
            {'text': data_text or data_url, 'url': data_url, 'index': index})

        return ' ^[%s]^ ' % index

    @classmethod
    def math(cls, **kwargs):
        if kwargs.get('level') == 1:
            return '$$\n%s\n$$\n\n' % kwargs.get('tag').get_attrs('alt')
        else:
            return ' $%s$ ' % kwargs.get('tag').get_attrs('alt')

    @classmethod
    def link(cls, **kwargs):
        url = kwargs.get('tag').get_attrs('href')
        try:
            assert isinstance(url, str)
        except AssertionError:
            print(kwargs.get('tag'))
            raise AssertionError
        if not bool(re.match(r'http', url)):
            url = 'https://www.zhihu.com' + url
        link_title = kwargs.get('tag').string

        if kwargs.get('tag').find('a', **{'type': 'link-card'}) is not None:
            length = 85

            ascii_reg = '[{ascii32}-{ascii126}]'.format(ascii32=chr(32), ascii126=chr(126))
            one_grid = len(re.findall(ascii_reg, link_title))
            two_grid = 2 * (len(link_title) - one_grid)

            if one_grid + two_grid < length:
                line = '-' * ((length - one_grid - two_grid) // 2)
                return f'***\n+%s+|%s|+%s+\n***\n\n' % (line, link_title, line)

        return '[%s](%s)' % (link_title, url)

    @classmethod
    def code(cls, **kwargs):
        if kwargs.get('tag').get_attrs('class', None) != 'highlight':
            return ''
        try:
            lang = re.sub(
                r'[+\d\s]+', '',
                re.search(r'"language-([^()]+)">', kwargs.get('tag').string).group(1)
            )
        except AttributeError:
            lang = 'text'

        def stg(r):
            return {'&quot;': '"', '&#39;': "'", '&lt;': '<', '&gt;': '>'}.get(r.group(0), '')

        code = re.sub(r'(</?(\w+)[^<>]*>)|(&quot;)|(&[\w#]+;)', stg, kwargs.get('tag').string)

        return '```%s\n%s\n```\n\n' % (lang, code)

    @classmethod
    def figure(cls, **kwargs):
        img = kwargs.get('tag').find('img')
        url = img.get_attrs('data-original') or img.get_attrs('src')

        kwargs.get('image_list').append(url)

        try:
            title = kwargs.get('tag').find('figcaption').string
        except AttributeError:
            title = ''

        return '![%s](%s)%s\n***\n\n' % (title, url, title)

    @classmethod
    def url(cls, **kwargs):
        """处理a标签，视频、卡片链接、广告、普通链接"""
        if kwargs.get('tag').find('a', _class='video-box') is not None:
            return cls.video(**kwargs)
        elif kwargs.get('tag').find('a', attrs={'data-draft-type': 'mcn-link-card'}) is not None:
            # 广告，tag自动过滤None
            return ''
        else:
            return cls.link(**kwargs)

    @classmethod
    def video(cls, **kwargs):
        video_link = kwargs.get('tag').find('span', _class='url').string
        cover_link = kwargs.get('tag').find('img').get_attrs('src')
        video_title = kwargs.get('tag').find('span', _class='title').string or '视频'

        return '![](%s)\n[%s](%s): %s\n\n' % (cover_link, video_title, video_link, video_link)

    @classmethod
    def newline(cls, **kwargs):
        return '\n'

    @classmethod
    def horizontal(cls, **kwargs):
        return '***\n\n'

    @classmethod
    def quote(cls, **kwargs):
        quote_tag = kwargs.pop('tag')
        content = list()
        quote_span = '> '
        content.append(quote_span)
        for tag in quote_tag.contents:
            warp = cls.format_tag(tag=tag, **kwargs)
            inner = None
            if tag.name not in cls.warp:
                inner = cls.format(tag.contents, **kwargs)
            content.append(cls._warp_inner(warp, inner))
            if tag.name in cls.split:
                content.append(quote_span)
        if content[-1] == quote_span:
            content.pop()
        return ''.join(content) + '\n\n'

    @classmethod
    def table(cls, **kwargs):
        def index(t):
            if t == 'ul':
                while True:
                    yield '- '
            else:
                i = 1
                while True:
                    yield str(i) + '. '
                    i += 1

        table_tag = kwargs.pop('tag')
        content = list()
        ind = index(table_tag.name)
        for tag in table_tag.contents:
            content.append(next(ind) + cls.format(tag.contents, **kwargs) + '\n')

        return ''.join(content) + '\n\n'

    # ----------------{inner}---------------- #

    @classmethod
    def font_style(cls, **kwargs):
        if re.match('h\d', kwargs.get('tag').name):
            return '%s {inner}\n\n' % ('#' * int(re.search('\d', kwargs.get('tag').name).group()))
        elif kwargs.get('tag').name in cls.emphasize:
            return ' **{inner}** '
        else:
            return ' *{inner}* '

    @classmethod
    def unsupported(cls, **kwargs):
        return '[unsupported, %s: {inner}]' % kwargs.get('tag').name

    @classmethod
    def paragraph(cls, **kwargs):
        if kwargs.get('tag').get_attrs('class') == 'ztext-empty-paragraph':
            return '{inner}'
        else:
            return '{inner}\n\n'


if __name__ == '__main__':
    pass
