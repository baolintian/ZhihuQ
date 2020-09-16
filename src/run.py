import zhihu.spider
from zhihu.conf import config
import test
from zhihu.spider import manage

# ### 程序设置（务必设置存储路径） #### #

# 默认存储路径为用户文档，开发环境下可设置为用户桌面或其他路径，方便查看结果
config.warehouse(r'./download')

config.setting('running/file_type', 0)
config.setting('running/cached', False)
config.setting('running/css_output', False)
config.setting('running/download_image', False)
config.setting('running/cover', False)

# ### 启动爬虫 #### #

