import os
import re

from zhihu.conf import config
from zhihu.document import markdown, html
from zhihu.spider.core import Crawler


class Meta:
    intact = 0
    simple = 1
    __slots__ = ('author', 'author_avatar_url', 'author_homepage', 'title', 'original_url',
                 'created_date', 'voteup', 'background', 'pattern')

    def __init__(self, author: str = None, author_avatar_url: str = None,
                 author_homepage: str = None, title: str = None, original_url: str = None,
                 created_date: str = None, voteup: int = None, background: str = None, pattern=0
                 ):
        self.author = author
        self.author_avatar_url = author_avatar_url
        self.author_homepage = author_homepage
        self.title = title
        self.original_url = original_url
        self.created_date = created_date
        self.voteup = voteup
        self.background = background
        self.pattern = pattern


class Document:
    index = 1
    page_index = 1
    DOC_TYPES = {'html': 0, 'md': 1, 'markdown': 1}
    DEFAULT_TYPE = DOC_TYPES.get('html', 0)

    @classmethod
    def download_image(cls, doc):
        cra = Crawler()
        index = 1
        for image_url in doc.image_list:
            file_name = os.path.basename(image_url)
            path = os.path.join(config.wh(), 'image')
            if not os.path.exists(path):
                os.makedirs(path)
            with open(os.path.join(path, file_name), 'wb') as foo:
                foo.write(cra.download(image_url).content)
                print('{:<8}\t{}'.format(str(cls.index) + '-' + str(index), file_name))
                index += 1

    @classmethod
    def item2html(cls, idx, cont, meta):
        mushroom = html.Mushroom(cont, meta, css_output=config.get_setting('running/css_output'))
        with open(format_file_name('html', meta.title, str(idx), str(meta.voteup), meta.author), 'w',
                  encoding='utf8') as foo:
            # 写入文件
            mushroom.write_down(foo)
        if config.get_setting('running/css_output'):
            stylesheets = mushroom.output_css_code()
            for css in stylesheets:
                with open(format_file_name('css', css['file_name']), 'w',
                          encoding='utf8') as foo:
                    foo.write(css['code'])
        return mushroom

    @classmethod
    def item2md(cls, cont, meta):
        md = markdown.Markdown(cont, meta)
        with open(format_file_name('md', meta.title, str(meta.voteup), meta.author, ),
                  'w', encoding='utf8') as foo:
            md.write_down(foo)
        return md

    @classmethod
    def make_document(cls, meta, cont):
        """根据所给的cont和meta生成html或markdown文件"""
        if cont is None or cont == '':
            return

        if config.get_setting('running/file_type') == cls.DEFAULT_TYPE:
            doc = cls.item2html(cls.page_index, cont, meta)
        else:
            doc = cls.item2md(cont, meta)
        cls.page_index += 1
        cls.show_info(meta)

        if config.get_setting('running/download_image'):
            cls.download_image(doc)
            print('-'*53 + '\n')
        cls.index += 1

    @classmethod
    def show_info(cls, meta):
        print('{:<8}\t{:<5}\t{}\t{}'.format(cls.index, meta.voteup, meta.title, meta.author))


def format_path(path):
    def stg(r):
        return {':': '：', '?': '？'}.get(r.group(0), '+')

    return re.sub(r'[\\/:*?"<>|]', stg, path)


def format_file_name(suffix, *part_name):
    """返回正确的文件名"""
    names = format_path('-'.join(part_name))
    if (suffix is not None) and (suffix != ''):
        file = os.path.join(config.wh(), '%s.%s' % (names, suffix))
    else:
        file = os.path.join(config.wh(), names)
    if not config.get_setting('running/cover'):
        return file

    REPETITION = 1
    while os.path.exists(file):
        file = os.path.join(
            config.wh(),
            '%s-%d.%s' % (names, REPETITION, suffix)
        )
        REPETITION += 1
    return file
