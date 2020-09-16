import re

from zhihu.conf import config
from zhihu.spider.core import HandleError

item_map = {
    'answer': [r'https?://www.zhihu.com/question/\d+/answer/(\d+)$',
               r'https://www.zhihu.com/answer/(\d+)$'],

    'column': [r'https?://zhuanlan.zhihu.com/([^/]+)$'],

    'article': [r'https?://zhuanlan.zhihu.com/p/(\d+)$'],

    'question': [r'https?://www.zhihu.com/question/(\d+)$'],
    'user_answers': [r'https?://www.zhihu.com/people/([^/]+)/answers$'],
    'user_articles': [r'https?://www.zhihu.com/people/([^/]+)/posts$'],
    'collection': [r'https?://www.zhihu.com/collection/(\d+)(?:\?page=\d+)?$']
}


def load_function(name):
    mod = __import__('zhihu.spider.manage', None, None, ['__all__'])
    return getattr(mod, name)


@HandleError.catch_error
def start_with_id(item_id, item_type):
    load_function(item_type)(item_id)
    print('保存目录：%s' % config.wh())


def start(item_link):
    start_with_id(*parse_url(item_link))


def parse_url(item_link):
    for item_type, item_regs in item_map.items():
        for item_reg in item_regs:
            r = re.match(item_reg, item_link)
            if bool(r):
                return r.group(1), item_type
    raise ValueError('can not find the item id. url: %s' % item_link)
