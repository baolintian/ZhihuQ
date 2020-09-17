# coding=utf-8
import codecs
import re

import zhihu.timer as timer
from zhihu.conf import config
from zhihu.document import Meta, Document
from zhihu.spider.core import *
from zhihu.spider.core import Crawler

current_dir = ''

__all__ = ['question', 'answer', 'column', 'article', 'user_answers', 'user_articles',
           'collection']


class ItemManage(Crawler):
    item_name = 'item'
    def __init__(self, item_id):
        super(ItemManage, self).__init__()
        self.item_id = item_id
        # self.sort_method = 0

    def network_data_packages(self, size, func=None, **kwargs):
        """
        :param size:
        :param func: 初步处理response数据的函数。
        :return: dict
        """
        offset = 0
        if size == 0:
            return

        if func is None or type(func).__name__ != 'function':
            def f(x, **kw):
                return x

            func = f

        def get_json_data(ofs, sort_method):
            resp = self.get_network_data_package(self.item_name, self.item_id, offset=ofs, sort_method=sort_method)
            resp.encoding = 'utf8'
            return resp.json()

        jsd = get_json_data(offset, sort_method = self.sort_method)
        offset += len(jsd.get('data', {}))
        totals = jsd.get('paging').get('totals')

        if size < 0 or totals < size:
            size = totals
        if 0 < size <= 1:
            size = int(size * totals)

        yield func(jsd, **kwargs)

        while offset < size:
            jsd = get_json_data(offset, sort_method = self.sort_method)
            offset += len(jsd.get('data', {}))
            yield func(jsd, **kwargs)

    @classmethod
    def parse_data(cls, data):
        """
        解析json数据得到meta和cont
        :param data:
        :return: meta, cont
        """
        meta = Meta()
        cont = data.get('content')
        return meta, cont

    def handle_data(self, data):
        meta, cont = self.parse_data(data, self.sort_method)
        Document.make_document(meta, cont)

    def _run(self, **kwargs):
        def func_init(**kw):
            pass

        kwargs.get('func_init', func_init)(**kwargs)

        for database in self.network_data_packages(kwargs.get('size', 0), kwargs.get('func_net', None)):
            for data in database.get('data', {}):
                kwargs.get('handle_data', self.handle_data)(data)

    custom_run = _run

    def run(self):
        self._run(size=0.02)

class AnswerManage(ItemManage):
    item_name = 'answer'

    def __init__(self, answer_id):
        super(AnswerManage, self).__init__(answer_id)

    @classmethod
    def parse_data(cls, data, sort_method):
        meta = Meta()
        meta.title = data['question']['title']
        meta.author = data['author']['name']
        meta.voteup = data['voteup_count']
        meta.original_url = API.format_url(
            'answer_link', question_id=data['question']['id'], answer_id=data['id'], sort_method = sort_method)

        meta.created_date = timer.timestamp_to_date(data['created_time'])
        meta.author_homepage = API.format_url(
            'author_homepage', user_id=data['author']['url_token'], sort_method = sort_method)

        meta.author_avatar_url = data['author']['avatar_url_template'].format(size='l')

        return meta, data.get('content')

    def run(self):
        resp = self.get_network_data_package(self.item_name, self.item_id)
        self.handle_data(resp.json())


def HasKeywords(answer_detail,keyword):   #判断是否含有所有关键词
    flag=True
    for key in keyword.split():    
        flag2=False
        for sub_key in key.split('+'):
            flag2=flag2 or answer_detail.find(sub_key)>0
            if flag2:
                break
        flag=flag and flag2
        if not flag:
            return False
    return True

class QuestionManage(AnswerManage):
    item_name = 'question'

    def __init__(self, *question_id):
        super(QuestionManage, self).__init__(question_id[0])
        self.filter = question_id[1]
        self.sort_method = question_id[2]
        self.ratio = question_id[3]
        response = self.get_network_data_package('question_meta', self.item_id, sort_method = self.sort_method)

        self.title = re.search(config.get_setting('QuestionManage/title_reg'),
                               response.text).group(1)
        current_dir = self.title
        config.warehouse('~question/%s' % format_path(self.title))
        

    def _run(self, **kwargs):
        def func_init(**kw):
            pass

        kwargs.get('func_init', func_init)(**kwargs)

        for database in self.network_data_packages(kwargs.get('size', 0), kwargs.get('func_net', None)):
            for data in database.get('data', {}):
                if(HasKeywords(data['content'], self.filter)):
                    kwargs.get('handle_data', self.handle_data)(data)

    def run(self):
        self._run(size=self.ratio)


class ArticleManage(ItemManage):
    item_name = 'article'

    def __init__(self, article_id):
        super(ArticleManage, self).__init__(article_id)

    @classmethod
    def parse_data(cls, data, sort_method):
        meta = Meta()

        meta.title = data['title']
        meta.author = data['author']['name']
        meta.voteup = data['voteup_count']
        meta.background = data['image_url']
        meta.original_url = API.format_url('article_link', article_id=data['id'], sort_method=sort_method)
        meta.created_date = timer.timestamp_to_date(data['created'])
        meta.author_homepage = API.format_url(
            'author_homepage', user_id=data['author']['url_token'], sort_method=sort_method)

        meta.author_avatar_url = data['author']['avatar_url_template'].format(size='l')

        return meta, data.get('content')

    def run(self):
        resp = self.get_network_data_package(self.item_name, self.item_id)
        self.handle_data(resp.json())


class ColumnManage(ArticleManage):
    item_name = 'column'

    def __init__(self, column_id):
        super(ColumnManage, self).__init__(column_id)
        resp = self.get_network_data_package('column_meta', self.item_id)
        item_words = re.search(
            config.get_setting('ColumnManage/title_reg'), resp.text).group(1)
        self.item_words = codecs.decode(item_words, 'unicode_escape')
        config.warehouse('~column/%s' % format_path(self.item_words))

    def handle_data(self, data):
        article(data.get('id', None))


    
    
    def run(self):
        self._run(size=-1)


class UserMetaManage(ItemManage):
    item_name = 'user_meta'

    def __init__(self, user_id):
        super(UserMetaManage, self).__init__(user_id)
        resp = self.get_network_data_package(UserMetaManage.item_name, self.item_id)
        self.user_name = resp.json().get('name')
        config.warehouse(config.wh() + '/' + format_path(self.user_name))

    def handle_data(self, data):
        meta, cont = self.parse_data(data)
        return Document.make_document(0, meta, cont)


class UserAnswersManage(UserMetaManage):
    item_name = 'user_answers'

    def __init__(self, user_id):
        super(UserAnswersManage, self).__init__(user_id)
        config.warehouse('~answers')

    @classmethod
    def parse_data(cls, data):
        return AnswerManage.parse_data(data)


class UserArticlesManage(UserMetaManage):
    item_name = 'user_articles'

    def __init__(self, user_id):
        super(UserArticlesManage, self).__init__(user_id)
        config.warehouse('~articles')

    @classmethod
    def parse_data(cls, data):
        return ArticleManage.parse_data(data)


class CollectionManage(ItemManage):
    item_name = 'collection'

    def __init__(self, collection_id):
        super(CollectionManage, self).__init__(collection_id)
        resp = self.get_network_data_package('collection_meta', self.item_id)
        jsd = resp.json()
        self.title = jsd.get('title')
        self.item_totals = jsd.get('item_count')
        config.warehouse('~collection/%s' % format_path(self.title))

    def network_data_packages(self, size, func=None, **kwargs):
        if size > self.item_totals or size < 0:
            size = self.item_totals
        page_totals = size // 10 + 1

        if func is None or type(func).__name__ != 'function':
            def f(x, **kw):
                return x

            func = f

        page = 1
        while page <= page_totals:
            resp = self.get_network_data_package(self.item_name, self.item_id, page=page)
            resp.encoding = 'utf8'
            page += 1
            yield func(resp.text)

    def handle_data(self, data):
        {'answer': answer, 'article': article}.get(data.get('type'))(data.get('id'))

    def run(self):
        def init_data(htm):
            answers = re.findall(
                r'<link itemprop="url" href="/question/\d+/answer/(\d+)">', htm)
            articles = re.findall(
                r'<link itemprop="url" href="https://zhuanlan.zhihu.com/p/(\d+)">', htm)

            resource = list()
            for ans in answers:
                resource.append({'type': 'answer', 'id': ans})

            for art in articles:
                resource.append({'type': 'article', 'id': art})

            return {'data': resource}

        self._run(size=-1, func_net=init_data)


def question(question_id, filter, sort_method, ratio):
    QuestionManage(question_id, filter, sort_method, ratio).run()


def answer(answer_id):
    AnswerManage(answer_id).run()


def column(column_id):
    ColumnManage(column_id).run()


def article(article_id):
    if article_id is not None:
        ArticleManage(article_id).run()


def user_answers(user_id):
    UserAnswersManage(user_id).run()


def user_articles(user_id):
    UserArticlesManage(user_id).run()


@HandleError.catch_error
def collection(collection_id):
    CollectionManage(collection_id).run()
