import argparse
import re
import sys

import zhihu.spider
from zhihu.conf import config
from zhihu.spider import login


def main():
    parser = argparse.ArgumentParser(description='Zhihu Spider', add_help=False)

    parser.add_argument('-u', action='store', help='项目url，多个用"$"分割')
    parser.add_argument('-r', action='store', help='url文本文件，换行分割')
    parser.add_argument('-w', action='store', default=config.wh(), help='文件保存位置')
    parser.add_argument('-f', action='store', default='html', help='文件输出类型(html/markdown)')
    parser.add_argument('-cd', action='store_true', help='缓存原始数据')
    parser.add_argument('-cso', action='store_true', help='输出css文件')
    parser.add_argument('-dg', action='store_true', help='下载图片')
    parser.add_argument('-cv', '--cover', action='store_true', help='覆盖同名文件')
    parser.add_argument('-log', '--login', action='store_true', help='模拟登录知乎，可能解决网络问题(当次有效)')
    parser.add_argument('-log2', '--login-long', action='store_true', help='模拟登录知乎，可能解决网络问题(长期有效)')

    parser.add_argument('-v', '--version', action='store_true', help='版本信息')
    parser.add_argument('-h', '--help', action='store_true', help='帮助')

    args = parser.parse_args()

    if args.help:
        parser.print_help()
        sys.exit(0)
    if args.version:
        print('zhihu %s 本地化收藏知乎优质内容' % zhihu.__version__)
        sys.exit(0)

    if args.login or args.login_long:
        # 仅登录账号或临时登录以退出账号
        pass
    elif args.u is None and args.r is None:
        print('请输入url！')
        sys.exit(0)

    urls = list()

    if args.u is not None:
        urls.extend(re.split(r'[\s$]+', args.u))

    if args.r is not None:
        read_succeed = False
        for enc in ('utf8', 'gbk'):
            try:
                with open(args.r, 'r', encoding=enc) as foo:
                    urls.extend(re.split(r'\s+', foo.read()))
                read_succeed = True
                break
            except(UnicodeError, UnicodeDecodeError):
                pass
            except FileNotFoundError:
                print('url文件不存在（%s），请提供正确路径！' % args.r)
                sys.exit(0)

        if not read_succeed:
            print('无法读取文件，请提供UTF-8或GBK编码的文本文件!')
            sys.exit(0)

    urls = set(urls)
    try:
        urls.remove('')
    except KeyError:
        pass

    file_type = {'html': 0, 'md': 1, 'markdown': 1}

    config.warehouse(args.w)
    config.setting('running/file_type', file_type.get(args.f, 0))
    config.setting('running/cached', args.cd)
    config.setting('running/css_output', args.cso)
    config.setting('running/download_image', args.dg)
    config.setting('running/cover', args.cover)

    acc = None

    if args.login or args.login_long:
        acc = login.ZhihuAccount()
        acc.login_up()

    for url in urls:
        zhihu.spider.start(url)

    if args.login:
        acc.login_out()

    sys.exit(0)


if __name__ == '__main__':
    sys.argv = ['zhihu', '-u', 'https://www.zhihu.com/question/371430700', '-dg']
    main()
