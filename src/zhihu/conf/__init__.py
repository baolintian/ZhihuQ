import os
import pickle

import zhihu.conf.config as zcc

__all__ = ['config']


class Config:
    """程序配置信息"""

    def __init__(self):
        self.config = zcc.config
        self.root_warehouse = self.default_wh()

    def save(self, file):
        with open(file, 'wb') as foo:
            pickle.dump(self.config, foo)

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value

    def __delitem__(self, key):
        del self.config[key]

    def __iter__(self):
        return iter(self.config)

    @classmethod
    def _setting(cls, region, key):
        try:
            return region[key]
        except KeyError:
            region[key] = dict()
            return cls._get_setting(region, key)
        except TypeError:
            raise ValueError('%s is a setting value, not region.' % region)

    def setting(self, key, value):
        keys = key.split('/')
        region = self.config
        for key in keys[:-1]:
            region = self._setting(region, key)
        region[keys[-1]] = value

    def default_wh(self):
        try:
            # 配置文件中不包含默认路径能保证其正确性，其必然是"Documents\zhihuSpider"
            dw = self.get_setting('running/default_wh')
            assert dw != ''
            return dw
        except (KeyError, AssertionError):
            dfp = os.path.join(os.path.expanduser('~'), r'Documents\zhihuSpider')
            self.setting('running/default_wh', dfp)
            try:
                os.makedirs(dfp)
            except FileExistsError:
                pass
            return self.default_wh()

    def _warehouse(self, path):
        if path.startswith('~'):
            path = os.path.normpath(os.path.join(self.root_warehouse, path.strip('~')))
        else:
            self.root_warehouse = path
        try:
            os.makedirs(path)
        except FileExistsError:
            pass
        except OSError:
            # 输入了不合法的路径，不作处理，切回默认路径
            self._warehouse(self.default_wh())
            return
        self.setting('running/warehouse', path)

    def cached_warehouse(self):
        path = os.path.join(self.default_wh(), 'cached')
        try:
            assert os.path.exists(path)
        except AssertionError:
            os.makedirs(path)
        return path

    def warehouse(self, path=None):
        if path is None:
            try:
                return self.get_setting('running/warehouse')
            except KeyError:
                return self.default_wh()
        self._warehouse(path)
        # 设置完了返回给调用的地方
        return self.warehouse()

    wh = warehouse

    @classmethod
    def _get_setting(cls, region, key):
        return region[key]

    def get_setting(self, key: str):
        region = self.config
        keys = key.split('/')
        try:
            for key in keys:
                region = self._get_setting(region, key)
            return region
        except KeyError:
            raise KeyError('There is no setting option named %s.' % key)


config: Config = Config()


if __name__ == '__main__':
    a = config.warehouse()
    print(a)
    config.warehouse(r'C:\Users\Milloy\Desktop')
    config.warehouse('~collection/菜汤')
    a = config.warehouse()
    print(a)
