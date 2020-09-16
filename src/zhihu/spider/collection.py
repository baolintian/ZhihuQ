# 爬取收藏夹的方案之一，该方案爬取的内容不稳定（时有变动），缺失几个关键数据，但爬取速度应该会快很多
# 对该方案感兴趣的话可以将它们复制到CollectionManage的对应位置运行。

# def handle_data(self, data):
#     if data.get_attrs('data-type') in ('Post', 'Answer'):
#         super(CollectionManage, self).handle_data(data)
#
# @classmethod
# def parse_data(cls, data):
#     meta = Meta(pattern=Meta.simple)
#
#     title = data.find('h2', _class='zm-item-title')
#     try:
#         meta.title = title.string
#     except AttributeError:
#         print(data)
#         raise AttributeError
#     original_url = title.find('a').get_attrs('href')
#
#     if data.get_attrs('data-type') == 'Answer':
#         head = data.find('div', _class='answer-head')
#         original_url = config.get_setting('API/host') + original_url
#     else:
#         head = data.find('div', _class='post-head')
#
#     meta.original_url = original_url
#
#     try:
#         author = head.find('a', _class='author-link')
#         meta.author = author.string
#         meta.author_homepage = config.get_setting('API/host') + author.get_attrs('href')
#     except AttributeError:
#         try:
#             author = head.find('span', _class='name')
#             meta.author = author.string
#             # 这种模式下找不到作者的主页，用知乎主页代替
#             meta.author_homepage = config.get_setting('API/host')
#         except AttributeError:
#             raise
#
#     meta.voteup = int(head.find('div', _class='zm-item-vote-info').get_attrs('data-votecount'))
#
#     # 获得点赞数的API，针对不同对象，提取下列标签的content，并使用相应的API发起请求，返回html标签
#     # <meta itemprop="post-id" content="107121832">
#     # <meta itemprop="answer-id" content="107121832">
#     # https://www.zhihu.com/node/AnswerVoteInfoV2?params={"answer_id":"%s"} % content
#     # https://www.zhihu.com/node/ColumnPostVoteInfoV2?params={"post_id":"%s"} % content
#
#     def stg(r):
#         return {'&quot;': '"', '&lt;': '<', '&gt;': '>'}.get(r.group(0), '')
#
#     return meta, re.sub(
#         '(&quot;)|(&lt;)|(&gt;)', stg, data.find('textarea', _class='content').string)
#
# def run(self):
#     def init_data(htm):
#         htm = Parsing().parse_tag(htm)
#         for t in htm:
#             if t.name == 'html':
#                 return {'data': t.find_all('div', _class="zm-item")}
#
#     self._run(size=-1, func_net=init_data)
