import re

from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from zhihu.conf import config

__all__ = ['Tag', 'Parsing', 'TagGenerate', 'Mushroom', 'Formatter']


def highlight_code(code, language, theme='default'):
    html_formatter = HtmlFormatter(style=theme, nowrap=True)
    return highlight(code, get_lexer_by_name(language, stripall=True), html_formatter)


def wrapper_handle_attrs(func):
    """转化html的标签属性为字典"""

    # 这是一个装饰Parsing.handle_attrs_tmp、Parsing.handle_attrs_tag的装饰器
    def handle_attrs(self, attrs_str):
        attrs = dict()
        if attrs_str == '/':
            return attrs
        attrs_list = re.findall(self.attr_reg, attrs_str)
        for attr in attrs_list:
            attrs[attr[0]] = func(self, attr)
        return attrs

    return handle_attrs


def except_handle_string(func):
    """处理字符串"""

    # 捕获stg != '' 的断言装饰器
    def handle_string(self, stg):
        try:
            return func(self, stg)
        except AssertionError:
            pass

    return handle_string


class TagParseError(ValueError):
    def __init__(self):
        super(TagParseError, self).__init__('can not parse the tag, maybe self-close tag was met.')


class Tag:
    """
    html标签的抽象：
    <div class="box"><p>我们都是<strong>好孩子</strong></p></div>

    观察上面的div标签，发现它由三部分构成：
        start:    起始标签，含属性
        end:      尾标签
        contents: 内容，起止标签包围的内容，字符串或其他标签

    进一步观察发现p和strong标签也是由上述三部分构成，只是它们倆没有属性。
    为了统一化，把字符串也抽象成为一个没有名字和属性的特殊标签。
    """
    SELF_CLOSING = ['img', 'link', 'br', 'hr', 'meta']

    def __init__(self, name, attrs: dict = None, contents: list = None, string: str = None,
                 indent: bool = True):
        """
        :param name: 标签名称，如div
        :param attrs: 标签属性
        :param contents: 标签内容，一般通过.push()添加
        :param string: 字符串，用于创建名字为None的字符串标签，或者普通标签的字符串content
        :param indent: .write（）时是否缩进，默认True，主要用于<code><pre>
        """
        # 如果标签的内容只有一个string，可以在创建标签时传入string，这样做是没有问题的。
        # 但如果标签含有标签内容，同时传入string，string会被添加到content的末尾，可能会导致次序混乱。
        # 所以建议标签只含有string时传入string
        self.name = name
        self.attrs = dict() if attrs is None else attrs
        self.contents = list()
        if contents is not None:
            self.push(*contents)
        if name is None:
            self._string = string
        elif string is not None:
            self.push(Tag(None, string=string, indent=indent))
        self.to_indent = indent

    def write_down(self, outfile, indent=0):
        padding = ' ' * 4 * indent if self.to_indent else ''
        if self.name is None:
            outfile.write('%s%s\n' % (padding, self.string))
            return
        attrs = self._str_attrs() if len(self.attrs) != 0 else ''
        outfile.write('%s<%s%s>\n' % (padding, self.name, attrs))
        for c in self.contents:
            c.write_down(outfile, indent + 1)
        if self.name not in self.SELF_CLOSING:
            outfile.write('%s</%s>\n' % (padding, self.name))
        return outfile

    def push(self, *items):
        # 在Compile过程中由于Compile.a()的需要，
        # 它返回的是None，这里做一个对象检测也是可以的
        for item in items:
            if isinstance(item, Tag):
                self.contents.append(item)
            elif item is not None:
                raise TypeError(
                    'Tag type is needed, but %s type is given.' % item.__class__.__name__)

    @property
    def string(self):
        return self.get_text(split='')

    def get_text(self, split='', strip=True):
        """返回self包含地所有文本，用split分隔不同标签之间的文本
        :param strip: True
        :type split: str
        """
        """这里有一个隐含的递归算法，能得到所有contents的string，不论嵌套多少层"""
        if self.name is None:
            return self._string
        else:
            s = list()
            for c in self.contents:
                s.append(c.string.strip() if strip else c.string)
            return split.join(s)

    def search_tags(self, name, limit, **kwargs):
        found_list = list()
        if self.name == name and self._attrs_match(kwargs):
            found_list.append(self)
        else:
            for _tag in self.contents:
                if len(found_list) == limit:
                    return found_list
                found_list.extend(_tag.search_tags(name, limit, **kwargs))
        return found_list

    def find_all(self, name, attrs=None, limit=-1, **kwargs):
        try:
            attrs.update(kwargs)
        except AttributeError:
            attrs = kwargs

        for key in attrs.keys():
            if re.match('_[^_]+|[^_]+_', key):
                attrs[key.strip('_')] = attrs[key]
                del attrs[key]

        return self.search_tags(name, limit, **attrs)

    def find(self, name, attrs=None, **kwargs):
        try:
            attrs.update(kwargs)
        except AttributeError:
            attrs = kwargs

        for key in list(attrs.keys()):
            if re.match('_[^_]+|[^_]+_', key):
                attrs[key.strip('_')] = attrs[key]
                del attrs[key]

        try:
            return self.search_tags(name, limit=1, **attrs)[0]
        except IndexError:
            return None

    def get_attrs(self, item, default=None, error=False):
        # 使用get_attrs方法得到所需的属性值，没有则应该返回默认值
        # 实现__getitem__方法仍然有必要。
        try:
            return self.attrs[item]
        except KeyError:
            if error:
                raise AttributeError(
                    '%s tag no attribute named "%s".' % (self.name, item)
                )
            return default

    def _attrs_match(self, attrs):
        """多值匹配法检查属性值是否匹配（包含）"""
        for attr, value in attrs.items():
            attr_val = self.attrs.get(attr, None)
            try:
                attr_vas = re.split(r'\s+', attr_val)
                vas = re.split(r'\s+', value) if isinstance(value, str) else value
                for v in vas:
                    if v not in attr_vas:
                        return False
            except (AttributeError, TypeError):
                return False
        return True

    def _str_attrs(self):
        return ' ' + ' '.join(
            ['%s="%s"' % (key, value) for key, value in self.attrs.items()]
        )

    def __str__(self):
        from io import StringIO
        stg = StringIO()
        self.write_down(stg)
        return stg.getvalue()

    def __repr__(self):
        k = 'class'
        v = self.attrs.get(k, None)
        if v is None:
            k, v = self.attrs.popitem()
        return 'Tag: %s, %s=%s' % (self.name or 'string', k, v)


class Parsing:
    """解析HTML生成Tag，返回由Tags组成的contents_list"""
    # #########实现原理#########
    # <div class="header">
    #     <div class="title">
    #         <a href="__ar-or__" target="_blank">文章标题</a>
    #     </div>
    #     <a class="UserLink-link" target="_blank" href="__us-li__">
    #         <div class="AuthorInfo">
    #             <div class="Popover">
    #                 <img class="Avatar" width="50" height="50" src="__us-av__" alt="__us-na__"/>
    #             </div>
    #             <div class="AuthorInfo-content">
    #                 <div class="AuthorInfo-name"><span>用户名</span></div>
    #                 <div class="AuthorInfo-detail"><span>发表日期和点赞数量</span></div>
    #             </div>
    #         </div>
    #     </a>
    # </div>
    #
    #     html标签一般由起始标签、尾标签和内容三部分共同构成，起止标签包围的内容都归它所有，被它“接收”。
    # 同样，它包含的子标签也需要“接收”自身的内容，直到出现尾标签。因此需要一个栈来暂时存放标签，往后的内容
    # 都归处于栈顶的标签“接收”，直到尾标签出现，栈顶出栈，栈顶的后继元素成为新栈顶继续“接收”它的内容。
    #     创建一个栈（stack），从左向右扫描html，一旦发现是起始标签（start）就创建这个标签(Tag)，并让它
    # 入栈（append）“接收”内容（content），继续向下扫描，如果发现新的标签就add到栈顶contents，同时让它入栈，
    # 如果是字符串，它必定被栈顶标签包围，直接add到栈顶contents。每扫描到一个尾标签，就让栈顶出栈（pop）。
    #     这种解析方式要求html标签必须拥有完整起止标签，缺失起止标签都将导致内容“接收”出现混乱（结构混乱），
    # 过多或过少接收。没有起始标签，它的尾标签将导致栈顶标签提前弹出；缺失尾标签，其将滞后甚至不弹出栈顶。

    # Questions：
    # 如何处理传入的是并列标签的情况？
    # 它可能有contents，先入栈，出栈时append到contents_list
    # 每发现一个尾标签栈顶就出栈，起止标签两两成对，所以不存在并列标签滞留在stack中导致出错的情况

    # append内容到stack时有两种情况：直接append或先add到栈顶contents再append到stack
    # 前者，说明它是一个父级标签，将与前后标签构成兄弟关系（并列标签），出栈后要append到contents_list；
    # 后者，说明它只是一个content（子级标签），入栈是为了“接收”它的contents，出栈后不需要append到contents_list.
    # 所以要对两种情况进行区分，方法是入栈时添加一个状态码：
    # 前者，状态码为 1
    # 后者，状态码为 0

    # 如何匹配代码？
    # 观察到<pre>或<code>标签就使用正则表达式做最小闭合匹配，把匹配内容当成字符串（string）
    # 针对知乎Spider可能观察到<div class="highlight">就对<pre>做闭合匹配比较好
    # 如果匹配到<pre>或<code>，ofs回退r.end()，用code_reg匹配，作为字符串add到栈顶contents或append到contents_list（栈空）
    # 也可以将<pre>或<code>做成标签(Tag)，它的content就是去除起止标签后剩余的元素，ofs要减去len('</%s>' % Tag.name)
    # 如果匹配到<div class="highlight">，构造div标签，然后用code_reg匹配，作为字符串add到div,然后将整个div，add或append
    # 需要特殊处理ofs

    # 匹配起始标签和属性
    start = re.compile(r'<(\w+)([^<>]*?)(/?)>')

    # 从start的匹配结果中匹配属性和属性值（re.findall()）
    attr_reg = re.compile(r"""([a-zA-Z-]+)\s*=\s*["']([^<>"']*)["']""")

    # 匹配字符串
    string = re.compile(r'([^<>]+)|(<!DOCTYPE html>)')

    # 匹配尾标签
    end = re.compile(r'</(\w+)>')

    # 匹配注释
    comment = re.compile(r'<!--[\s\S]*?-->')

    # 匹配code或pre标签内的代码，包括给代码添加样式的span标签
    code_reg = re.compile(r'(<code[^<>]*?>[\s\S]+?</code>)|(<pre[^<>]*?>[\s\S]*?</pre>)')

    # 匹配标识符的名称，关于标识符见marks.py
    mark = re.compile(r'__#([a-zA-Z0-9\-]+)#__')  # 下划线 _ 属于 \w，在这里不能用

    SELF_CLOSING = ['img', 'link', 'br', 'hr', 'meta', 'input']

    def __init__(self):
        self._ofs = 0
        self._marks_value = dict()
        self._contents_list = list()
        self._stack = list()
        self._tag = ''

    def restore(self):
        """还原Parsing到初始状态"""
        self._ofs = 0
        self._marks_value = dict()
        self._contents_list = list()
        self._stack = list()
        self._tag = ''

    def arouse_error(self, max_loop):
        """检查解析过程是否正常，不正常将引发ValueError"""
        if max_loop == 0:
            w = 'While loop go beyond the max_loop(%d). ' \
                'The following words is showed below line.' % len(self._tag)
            raise ValueError('%s\n%s\n\n%s' % (w, '-' * (len(w) + 12), self._tag[self._ofs:]))
        if len(self._stack) != 0:
            raise TagParseError()

    def replace(self, stg):
        """处理html模板中的字符串并替换标识符的值"""
        mark = re.search(self.mark, stg)
        while mark:
            value = self._marks_value.get(mark.group(1), '##')
            stg = re.sub(self.mark, value, stg, 1)
            mark = re.search(self.mark, stg)
        return stg

    def parse_tag(self, tag):
        """解析html标签生成Tag并返回由Tags构成的列表"""
        self._tag = tag
        return self.parsing(funcs=(
            self.handle_start_tag, self.handle_string_tag, self.handle_end, self.handle_comment))

    def parse_tmp(self, tmp, marks_val):
        """解析html模板生成Tag，并在解析过程中将模板上的占位符替换成marks_val提供的对应值"""
        self._tag = tmp
        self._marks_value = marks_val
        return self.parsing(funcs=(
            self.handle_start_tmp, self.handle_string_tmp, self.handle_end, self.handle_comment))

    def parsing(self, funcs):
        """解析html标签"""
        regs = (self.start, self.string, self.end, self.comment)
        max_loop = len(self._tag)
        # 可以预见html的标签（元素）数量不可能等于或超过它本身的字符数量
        # 设定max_loop可以避免遇到无法匹配的情况时，进度停滞不前，程序陷入死循环
        while self._ofs < len(self._tag) and max_loop > 0:
            max_loop -= 1
            for reg, func in zip(regs, funcs):
                # 循环匹配tag文本直到匹配成功并调用相关的处理方法func
                r = re.match(reg, self._tag[self._ofs:])
                if bool(r):
                    self._ofs += r.end()
                    func(r)
                    break
        # 检查htm是否解析完全，如果没有，将引起错误
        self.arouse_error(max_loop)
        # 这个类有点像加工厂，来料加工，加工完之后要还原到原来的状态，等料加工
        ct = self._contents_list
        self.restore()
        return ct

    def handle_start_tag(self, r):
        """处理起始标签"""
        self.handle_start(r, make_attrs=self.handle_attrs_val_tag)

    def handle_start_tmp(self, r):
        """处理起始标签（模板）"""
        self.handle_start(r, self.handle_attrs_val_tmp)

    def handle_string_tag(self, r):
        """处理html中的字符串"""
        self.handle_string(r.group().strip())

    def handle_string_tmp(self, r):
        """处理html模板中的字符串并替换标识符的值"""
        self.handle_string(
            self.replace(
                r.group().strip()
            )
        )

    def handle_end(self, r):
        """处理html标签的尾标签，涉及栈顶元素的弹出"""
        n, status_code = self._stack.pop()
        # 如果n是顶层父级标签则需要将其加入到内容列表
        if status_code == 1:
            self._contents_list.append(n)

    def handle_comment(self, r):
        """html中的注释，不处理"""
        pass

    def handle_code(self, n, r):
        """处理代码标签"""
        if n.name == 'div' and n.attrs.get('class', None) == 'highlight':
            cd = re.match(self.code_reg, self._tag[self._ofs:])
            if bool(cd):
                self._ofs += cd.end()
                n.push(Tag(None, string=cd.group(), indent=False))
        elif n.name in ('code', 'pre'):
            cof = self._ofs - r.end()
            cd = re.match(self.code_reg, self._tag[cof:])
            if bool(cd):
                self._ofs = cof + cd.end() - len('</%s>' % n.name)
                stg = re.sub('</?%s[^<>]*?>' % n.name, '', cd.group())
                n.push(Tag(None, string=stg, indent=False))

    def handle_start(self, r, make_attrs):
        """处理起始标签"""
        if r.group(3) == '/':
            if r.group(1) not in self.SELF_CLOSING:
                self.SELF_CLOSING.append(r.group(1))

        if r.group(1) in self.SELF_CLOSING:
            n = Tag(r.group(1), attrs=make_attrs(r.group(2) if len(r.groups()) != 1 else '/'))
            # 可以确定它没有contents，直接append到content_list或add到stack
            if len(self._stack) == 0:
                self._contents_list.append(n)
            else:
                self._stack[-1][0].push(n)
        else:
            n = Tag(r.group(1), attrs=make_attrs(r.group(2)))
            self.handle_code(n, r)
            # 如果栈为空，直接append到栈顶，
            # 否则就是栈顶有元素，n是栈顶的content，
            # 先add到栈顶contents再append到栈顶，成为新的栈顶
            if len(self._stack) == 0:
                self._stack.append((n, 1))
            else:
                self._stack[-1][0].push(n)
                self._stack.append((n, 0))

    @except_handle_string
    def handle_string(self, stg):
        """根据传入的字符串构造Tag，并将其添加到（栈顶）内容列表"""
        assert stg != ''
        n = Tag(None, string=stg)
        if len(self._stack) == 0:
            self._contents_list.append(n)
        else:
            self._stack[-1][0].push(n)

    @wrapper_handle_attrs
    def handle_attrs_val_tmp(self, attrs_val):
        """"转化html的标签属性为字典，并替换标识符的值"""
        return self.replace(attrs_val[1])

    @wrapper_handle_attrs
    def handle_attrs_val_tag(self, attrs_val):
        """"转化html的标签属性为字典"""
        return attrs_val[1].strip()


class TagGenerate(Parsing):
    """依据模板和数据生成html标签"""

    def __init__(self):
        super(TagGenerate, self).__init__()

    @classmethod
    def template(cls, name):
        try:
            return config.get_setting('tag/%s' % name)
        except KeyError:
            raise KeyError('not find template named %s.' % name)

    def generate_tag_by_template(self, template, marks_value=None):
        return self.parse_tmp(template, marks_value)[0]

    def link_card(self, url, title, img=None):
        try:
            domain = re.search('target=https?%3A//([^/]+)', url).group(1)
        except AttributeError:
            domain = re.search('https?://([^/]+)', url).group(1)
        mas_val = {
            'domain': domain,
            'link-card-image': img if img is not None else '',
            'link-card-url': url,
            'link-card-title': title
        }
        name = 'lc_img' if img is not None else 'lc_svg'
        return self.generate_tag_by_template(self.template(name), marks_value=mas_val)

    @classmethod
    def article_text(cls, *contents):
        return Tag('div', attrs={'class': 'text'}, contents=list(contents))

    def article_tile(self, meta):

        mas_val = {'article-origin': meta.original_url,
                   'user-avatar': meta.author_avatar_url,
                   'user-name': meta.author,
                   'user-link': meta.author_homepage,
                   'created-date': meta.created_date,
                   'title': meta.title,
                   'background-image': meta.background
                   }
        header = ['header', 'header_simple'][meta.pattern]
        title = self.generate_tag_by_template(self.template(header), marks_value=mas_val)
        if not (meta.background is None or meta.background == ''):
            title.contents.insert(
                0,
                self.generate_tag_by_template(
                    self.template('bgg'), marks_value=mas_val)
            )
        return title

    def video_box(self, video_link, cover_link, tip=None):
        # TODO 针对有无视频标题做两套video box
        mas_val = {'video-link': video_link,
                   'video-cover': cover_link,
                   'video-tip': '点击封面可观看视频!' if tip is None else '%s，%s' % (tip, '点击封面可观看视频!')
                   }
        return self.generate_tag_by_template(self.template('video'), marks_value=mas_val)

    def reference_index(self, index):
        return self.generate_tag_by_template(self.template('ref_ind'), {'index': index})

    def reference_table(self, ref_title_url):
        table = Tag('table', attrs={'class': 'reference'})
        for ref in ref_title_url:
            mas_val = {
                'index': ref.get('index'),
                'ref-url': ref.get('url'),
                'ref-title': ref.get('text')
            }
            table.push(self.generate_tag_by_template(self.template('quo'), mas_val))
        return table


class Mushroom(Tag):

    def __init__(self, content, meta, css_output=False, printing=True):
        Tag.__init__(self, 'html', attrs={'lang': 'zh'})
        self.content = content
        self.meta = meta
        self.head = Tag('head')
        self.body = Tag('body')
        self.feed2head(Tag('meta', attrs={'charset': 'UTF-8'}))
        self.feed2head(Tag('title', string=meta.title))
        self.push(self.head, self.body)
        self.title = None
        self.text = None
        self.new_article()
        self.css_output = css_output
        self.stylesheets = list()
        self.image_list = list()

        if printing:
            self.feed2head(
                Tag('link', attrs={'rel': 'stylesheet', 'type': 'text/css',
                                   'media': 'print'})
            )

    @property
    def article(self):
        try:
            return self.body.contents[-1]
        except IndexError:
            self.new_article()
            return self.article

    def feed2head(self, tag: Tag):
        self.head.push(tag)

    def feed2body(self, tag: Tag):
        self.body.push(tag)

    def link_css_file(self):
        """link stylesheet file in html link tag"""
        for stylesheet in self.stylesheets:
            self.feed2head(
                Tag('link', attrs={'rel': 'stylesheet', 'type': 'text/css',
                                   'href': stylesheet['file_name']}))

    def insert_css_code(self):
        """insert stylesheet code in html style tag"""
        for stylesheet in self.stylesheets:
            self.feed2head(
                Tag('style', attrs={'type': 'text/css'}, string=stylesheet['format_code']))

    def output_css_code(self):
        """return stylesheets for output or other else"""
        return self.stylesheets

    def insert_article_text(self, text):
        self.text = text

    def insert_article_title(self, title):
        self.title = title

    def new_article(self):
        if self.title or self.text:
            self.commit_article()
        if len(self.body.contents) >= 1:
            self.feed2body(Tag('div', attrs={'class': 'divide'}))
        self.feed2body(Tag('div', attrs={'class': 'article'}))

    def commit_article(self):
        self.article.push(self.title)
        self.article.push(self.text)

    def write_down(self, outfile, indent=0):
        Formatter(self.content).formatter(self.meta, self)
        self.commit_article()
        if self.css_output:
            self.link_css_file()
        else:
            self.insert_css_code()
        outfile.write('<!DOCTYPE html>\n')
        return super(Mushroom, self).write_down(outfile)


class Formatter(TagGenerate):

    def __init__(self, content):
        TagGenerate.__init__(self)
        self.tag_list = self.parse_tag(content)
        self.reference_list = list()
        self.ref_ind = 1
        self.style_meta = set()
        self.style_meta.add('styleText')
        self.style_meta.add('styleMod')
        self.image_list = list()

    def formatter(self, meta, otp: Mushroom):
        """处理Tags，修改属性、生成视频标签等"""
        r = self.format(self.tag_list)

        if len(self.reference_list) != 0:
            r.append(Tag('span', attrs={'style': 'font-size:24px'}, string='参考资料'))
            n = self.reference_table(self.reference_list)
            r.append(n)

        otp.insert_article_title(self.article_tile(meta))
        otp.insert_article_text(self.article_text(*r))

        for stylesheet in self.style_meta:
            otp.stylesheets.append(config.get_setting('head/style/%s' % stylesheet))
        otp.image_list = self.image_list

        return otp

    def format(self, contents):
        """处理Tags"""
        contents_list = list()
        for tag in contents:
            if tag.name in ('a', 'div', 'figure', 'img', 'sup'):
                contents_list.append(getattr(self, tag.name)(tag))
                continue
            tag.contents = self.format(tag.contents)
            self._remove_attrs(tag)
            contents_list.append(tag)
        return contents_list

    def figure(self, tag):
        """处理figure标签，图片"""

        img = tag.find('img')
        url = img.get_attrs('data-original') or img.get_attrs('src')

        self.image_list.append(url)

        return Tag('figure', contents=[Tag('img', attrs={'src': url}), tag.find('figcaption')])

    def img(self, tag):
        """处理数学公式"""
        return tag

    def div(self, tag):
        """处理div标签，代码"""
        if tag.get_attrs('class', None) != 'highlight':
            return None

        self.style_meta.add('styleCode')

        try:
            language = re.search('language-([^"]+)', tag.string).group(1)
        except AttributeError:
            language = 'text'

        code = self.highlight_code(tag.string, language)
        return Tag('div', attrs={'class': 'highlight'}, string=code)

    def a(self, tag):
        """处理a标签，视频、卡片链接、广告、普通链接"""
        if tag.find('a', attrs={'class': 'video-box'}) is not None:
            return self._make_video_box(tag)
        elif tag.find('a', attrs={'data-draft-type': 'link-card'}) is not None:
            return self._make_link_card(tag)
        elif tag.find('a', attrs={'data-draft-type': 'mcn-link-card'}) is not None:
            # 广告，tag自动过滤None
            return None
        else:
            return tag

    def sup(self, tag):
        """处理sup标签，知乎标准的文献引用样式"""
        data_url = tag.get_attrs('data-url')
        index = tag.get_attrs('data-numero')
        data_text = tag.get_attrs('data-text')

        self.reference_list.append(
            {'text': data_text or data_url, 'url': data_url, 'index': index})

        return self.reference_index(index)

    def _make_video_box(self, tag):
        """生成视频标签"""
        try:
            return self.video_box(
                video_link=tag.find('span', _class='url').string,
                cover_link=tag.find('img').get_attrs('src'),
                tip=tag.find('span', **{'class': 'title'}).string
            )
        except AttributeError as e:
            print(tag)
            raise e

    def _make_link_card(self, tag):
        """生成卡片链接标签"""
        url = tag.get_attrs('href')
        img = tag.get_attrs('image')
        if re.search('zhihu', url) and img is None:
            img = config.get_setting('Formatter/link_card_default_image')
        return self.link_card(
            url=url,
            title=tag.string,
            img=img
        )

    @staticmethod
    def _remove_attrs(tag):
        """移除标签的属性"""
        tag.attrs = dict()
        return tag

    @classmethod
    def highlight_code(cls, code_text, language, theme='default'):
        def stg(r):
            return {'&quot;': '"', '&#34;': '"', '&amp;': '&', '&#38': '&',
                    '&lt;': '<', '&#60': '<', '&gt;': '>', '&gt': '>'}.get(r.group(0), '')

        return '<pre>%s</pre>' % highlight(
            re.sub(r'(</?(\w+)[^<>]*>)|(&quot;)|(&[\w#]+;)', stg, code_text),
            get_lexer_by_name(language, stripall=True),
            HtmlFormatter(style=theme, nowrap=True))

    @classmethod
    def code_css_sheet(cls, theme):
        return HtmlFormatter(style=theme, nowrap=True, cssclass='highlight').get_style_defs()
