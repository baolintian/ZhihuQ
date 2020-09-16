import random
import time


def random_sleep(begin=None, end=None):
    if begin is None or begin < 0:
        begin = 0
    if end is None:
        end = 20
    if end >= 1000:
        raise ValueError('%d is too big, expect no more than 1000 seconds!')
    r = random.randint(begin, end)
    for i in range(r):
        time.sleep(1)


def sleep_for(second):
    for i in range(second):
        time.sleep(1)


def timestamp_to_date(time_stamp: int = None, ft: str = None):
    if ft is None:
        ft = '%Y-%m-%d'
    if time_stamp is None:
        t = time.gmtime()
    else:
        t_str = time.ctime(time_stamp)
        t = time.strptime(t_str, '%a %b  %d %H:%M:%S %Y')
    return time.strftime(ft, t)


def timestamp():
    return int(time.time())


def timestamp_str():
    return str(timestamp())


if __name__ == '__main__':
    s = timestamp_to_date(ft='%Y-%m-%d')
    print(s)
    print(timestamp_str())
