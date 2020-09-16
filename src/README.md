# zhihuSpider

程序提供一种简单快捷的方式**本地化收藏**知乎上的内容，如：**答案**、**文章**等，并尽可能保持内容格式与知乎上的一致。由用户提供知乎上相应项目的url，通过知乎API爬取数据数据，数据经解析后最终输出为**markdown**或**html**文件存储到本地，同时可下载内容附带的图片。

第三方依赖库

```python
requests
pygments
```

## 更新

1. 支持 **问题、答案、专栏、文章、收藏夹、用户答案及文章** 的爬取。

2. 重构部分代码，增强爬虫的扩展性。

3. 安装后**支持命令行运行**。

4. 支持登录知乎账号，出现网络错误后可尝试登录。

## 使用

在命令行输入`zhihu -h`获得帮助信息：

```
zhihu -h
usage: zhihu [-u U] [-r R] [-w W] [-f F] [-cd] [-cso] [-dg] [-cv] [-log]
             [-log2] [-v] [-h]

Zhihu Spider

optional arguments:
  -u U                 项目url，多个用"$"分割
  -r R                 url文本文件，换行分割
  -w W                 文件保存位置
  -f F                 文件输出类型(html/markdown)
  -cd                  缓存原始数据
  -cso                 输出css文件
  -dg                  下载图片
  -cv, --cover         覆盖同名文件
  -log, --login        模拟登录知乎，可能解决网络问题(当次有效)
  -log2, --login-long  模拟登录知乎，可能解决网络问题(长期有效)
  -v, --version        版本信息
  -h, --help           帮助
```

获取“如何看待2020年非洲蝗虫灾害？”（20200215热榜问题） **前2%** 个答案并下载答案中的图片：

```
zhihu -u https://www.zhihu.com/question/371430700 -dg
```
有两种方式支持批量获内容，第一种：将问题（答案、文章、专栏等）链接放置在文本文件(如batch.txt)中，每行一个链接。如：

文本文件(batch.txt)内容：
```
https://www.zhihu.com/question/371430700
https://www.zhihu.com/question/371430701
https://www.zhihu.com/question/371430702
https://www.zhihu.com/question/371430703
```
爬虫命令：
```
zhihu -r batch.txt
```

第二种：使用`""`将多个链接引起，使它们成为一个字符串，用`空格`或`#`分隔链接，如：

```
zhihu -u "https://www.zhihu.com/question/371430702#https://www.zhihu.com/question/371430702 https://www.zhihu.com/question/371430703"
```

