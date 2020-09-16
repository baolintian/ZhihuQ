import os
import platform
import time
from http import cookiejar

import requests
from requests import RequestException

from zhihu.conf import config

"""
扫码登录知乎，并保存cookies
用知乎APP(APP-->我的，右上角)扫描二维码登录知乎。
小提示：知乎扫码特别慢，建议使用微信扫码，按屏幕提示继续操作也可登录。
"""

__all__ = ['cookies_file', 'ZhihuAccount']

c_p = os.path.join(config.default_wh(), 'config', 'cookies')
if not os.path.exists(c_p):
    os.makedirs(c_p)

cookies_file = os.path.join(c_p, 'cookies')


class ZhihuAccount:
    UA = config.get_setting('Crawler/user-agent')

    BASE_HEAD = {
        'Host': 'www.zhihu.com',
        'User-Agent': UA
    }

    LOGIN_UP = 1  # 登录了
    LOGIN_IN = 0  # 请求登录

    def __init__(self):
        self.session = requests.Session()
        self.session.cookies = cookiejar.LWPCookieJar(filename=cookies_file)
        try:
            self.session.cookies.load(ignore_discard=True)
        except FileNotFoundError:
            pass

    def __del__(self):
        try:
            os.remove(os.path.abspath('QR.jpg'))
        except FileNotFoundError:
            pass

    def login_up(self):
        if self.login_status() == ZhihuAccount.LOGIN_UP:
            print('已登录！')
        else:
            print('开始登录...')
            if self.__login():
                if self.login_status() == ZhihuAccount.LOGIN_UP:
                    self.session.cookies.save()
                    print('登录成功！')
                    return
            print('登录失败！')

    def login_out(self):
        self.session.get('https://www.zhihu.com/logout',
                         headers=ZhihuAccount.BASE_HEAD, allow_redirects=False)
        self.session.cookies.save()
        # try:
        #     os.remove('cookies')
        # except FileNotFoundError:
        #     pass
        print('已退出！')

    def login_status(self):
        resp = self.session.get('https://www.zhihu.com/signup',
                                headers=ZhihuAccount.BASE_HEAD, allow_redirects=False)

        if resp.status_code == 302:
            return ZhihuAccount.LOGIN_UP
        else:
            return ZhihuAccount.LOGIN_IN

    def __login(self):
        try:
            self.session.get("https://www.zhihu.com/signup?next=%2F",
                             headers=ZhihuAccount.BASE_HEAD)
            captcha_head = {"Referer": "https://www.zhihu.com/"}
            captcha_head.update(ZhihuAccount.BASE_HEAD)
            self.session.get("https://www.zhihu.com/api/v3/oauth/captcha?lang=en",
                             headers=captcha_head)

            resp = self.session.post("https://www.zhihu.com/udid", headers=ZhihuAccount.BASE_HEAD)
            token_head = {
                'Origin': 'https://www.zhihu.com',
                'Referer': 'https://www.zhihu.com/signup?next=%2F',
                'x-udid': resp.content.decode('utf8')
            }

            token_head.update(ZhihuAccount.BASE_HEAD)
            resp = self.session.post("https://www.zhihu.com/api/v3/account/api/login/qrcode",
                                     headers=token_head)
            token = resp.json().get('token')

            qr = self.session.get(
                f'https://www.zhihu.com/api/v3/account/api/login/qrcode/{token}/image',
                headers=token_head)

            self.__show_qr_code(qr.content)

            print('操作系统已使用关联程序显示二维码，请使用知乎APP扫描。\n'
                  '小提示：知乎APP扫码特别慢，建议使用微信扫描，按屏幕提示继续操作也可登录。\n')

            time.sleep(10)
            start = time.time()
            while True:
                rjs = self.session.get(
                    f'https://www.zhihu.com/api/v3/account/api/login/qrcode/{token}/scan_info',
                    headers=captcha_head).json()
                if rjs.get('user_id', None) or rjs.get('status', None) == 6 or rjs.get('error'):
                    break
                if time.time() - start >= 90:
                    print('登录超时！(<90s)')
                    break
                time.sleep(2)

            return True
        except RequestException as e:
            return False

    @staticmethod
    def __show_qr_code(image):
        """
        调用系统软件显示图片
        """
        image_file = os.path.abspath('QR.jpg')

        with open(image_file, 'wb') as foo:
            foo.write(image)

        if platform.system() == 'Darwin':
            os.subprocess.call(['open', image_file])
        elif platform.system() == 'Linux':
            os.subprocess.call(['xdg-open', image_file])
        else:
            os.startfile(image_file)

    def __enter__(self):
        self.login_up()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.login_out()


if __name__ == '__main__':
    acc = ZhihuAccount()
    acc.login_up()
    # acc.login_out()
