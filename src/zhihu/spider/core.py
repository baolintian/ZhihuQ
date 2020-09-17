# coding=utf-8
import os
import re
from http import cookiejar

import requests
from requests import HTTPError
from requests.exceptions import MissingSchema

from zhihu import timer
from zhihu.conf import config

__all__ = ['VerityError', 'HandleError', 'API', 'Crawler', 'format_path', 'format_file_name']


class VerityError(ValueError):
    """网络数据验证异常"""

    def __init__(self, **kwargs):
        self.status_code = kwargs.get('status_code', 'None')
        self.url = kwargs.get('url', 'None')
        super(VerityError, self).__init__(
            '网络错误，错误码: %s, url: %s' % (self.status_code, self.url))


class HandleError:

    @classmethod
    def verity(cls, func):
        """验证网络请求结果"""

        def verity_deco(self, *args, **kwargs):
            """验证返回的网络数据是否正确，确保输入到核心库数据的正确性"""
            # 验证不通过就引发VerityError
            rs = None
            try:
                rs = func(self, *args, **kwargs)
                rs.raise_for_status()
            except HTTPError:
                raise VerityError(status_code=rs.status_code, url=rs.url)
            except MissingSchema:
                raise ValueError('url error: ', args, kwargs)
            return rs

        return verity_deco

    @classmethod
    def catch_error(cls, func):
        """捕获VerityError并处理，装饰普通函数"""

        def catch(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except VerityError as e:
                cls.handle_error(e)
                return False

        return catch

    @classmethod
    def handle_error(cls, error):
        """网络返回错误数据时应做的处理"""
        if error.status_code == 400:
            print('网络错误，url无法解析，400！%s' % error.url)
        elif error.status_code == 401:
            print('网络错误，可能需要cookie，401！%s' % error.url)
        elif error.status_code == 404:
            print('网络错误，可能没有访问权限，404！%s' % error.url)


class API:
    """获得有关数据的链接类"""

    SORT_BY_DEF = config.get_setting('API/SORT_BY_DEF')
    SORT_BY_VOT = config.get_setting('API/SORT_BY_VOT')
    SORT_BY_DAT = config.get_setting('API/SORT_BY_DAT')
    PLATFORM = config.get_setting('API/PLATFORM')

    api = {
        'question': config.get_setting('API/question'),
        'question_meta': config.get_setting('API/question_meta'),
        'answer': config.get_setting('API/answer'),
        'article': config.get_setting('API/article'),
        'column': config.get_setting('API/column'),
        'column_meta': config.get_setting('API/column_meta'),
        'answer_link': config.get_setting('API/answer_link'),
        'article_link': config.get_setting('API/article_link'),
        'author_homepage': config.get_setting('API/author_homepage'),
        'user_answers': config.get_setting('API/user_answers'),
        'user_articles': config.get_setting('API/user_articles'),
        'user_meta': config.get_setting('API/user_meta'),
        'collection': config.get_setting('API/collection'),
        'collection_meta': config.get_setting('API/collection_meta'),
    }

    @classmethod
    def get_url(cls, item_name, item_id, **kwargs):
        """
        :param item_name: question, answer, column, ...
        :param item_id: question_id, answer_id, ...
        :param kwargs: offset, limit, sort_by
        :return: str, url
        """
        
        if kwargs['sort_method'] == 0:
            sort_by = cls.SORT_BY_VOT
        elif kwargs['sort_method'] == 1:
            sort_by =  cls.SORT_BY_DAT
        else:
            sort_by = cls.SORT_BY_DEF

        params = {
            'item_id': item_id,
            'offset': 0,
            'limit': 20,
            'sort_by': sort_by
        }
        params.update(kwargs) # 讲kwargs中的变量全部都映射给params
        return cls.api.get(item_name, '').format(**params)

    @classmethod
    def format_url(cls, item_name, **kwargs):
        return cls.get_url(item_name, None, **kwargs)


class Crawler(API):
    UA = config.get_setting('Crawler/user-agent')

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': Crawler.UA})
        try:
            mod = __import__('zhihu.spider.login', None, None, ['__all__'])
            ckf = getattr(mod, 'cookies_file')
            self.session.cookies = cookiejar.LWPCookieJar(filename=ckf)
            self.session.cookies.load()
        except (FileNotFoundError, ImportError, AttributeError) as e:
            pass

    def __del__(self):
        self.session.close()

    def get_network_data_package(self, item_name, item_id, **kwargs):
        resp = self.session.get(self.get_url(item_name, item_id, **kwargs), timeout=30)
        try:
            resp.raise_for_status()
        except HTTPError:
            raise VerityError(status_code=resp.status_code, url=resp.url)
        except MissingSchema:
            raise ValueError('url error: ', item_name, item_id, kwargs)
        if config.get_setting('running/cached'):
            self.cached_network_data(resp, item_name, item_id, **kwargs)
        return resp

    def download(self, url, **kwargs):
        return self.session.get(url, timeout=30, **kwargs)

    @classmethod
    def cached_network_data(cls, data, item_name, item_id, **kwargs):
        """缓存原始数据"""
        ofs = kwargs.get('offset', None) or kwargs.get('page', None) or timer.timestamp_str()
        file = os.path.join(config.cached_warehouse(), '%s-%s-%s.json' % (item_name, item_id, ofs))
        with open(file, 'w', encoding='utf8') as foo:
            foo.write(data.text)
        return file


def format_path(path):
    return re.sub(r'[\\/:*?"<>|]', '#', path)


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
