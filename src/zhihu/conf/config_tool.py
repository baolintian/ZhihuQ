import json
import os
import re

from zhihu.conf.config import config
from zhihu.document.html import Parsing


def str_dict(config_dict, file, indent=0, variable=None):
    comma = ','
    if indent == 0:
        comma = ''
    if variable is not None:
        indent += len(variable) + 3
        file.write('%s = ' % variable)
    padding = ' ' * indent
    file.write('{\n')
    for key, value in config_dict.items():
        if isinstance(value, dict):
            file.write("%s'%s': " % (padding, key))
            str_dict(value, file, indent + 4)
        else:
            file.write("%s'%s': %s,\n" % (padding, key, repr(value)))

    file.write('%s}%s\n' % (padding, comma))


def print_dict(config_dict, indent=0):
    comma = ','
    if indent == 0:
        comma = ''
    padding = ' ' * indent
    print('{\n', end='')
    for key, value in config_dict.items():
        if isinstance(value, dict):
            print("%s'%s': " % (padding, key), end='')
            print_dict(value, indent+4)
        else:
            print("%s'%s': %s,\n" % (padding, key, repr(value)), end='')

    print('%s}%s\n' % (padding, comma), end='')


def make_python_code(config_dict, resource_file):
    with open(resource_file, 'w', encoding='utf8') as foo:
        str_dict(config_dict, foo, variable='config')


def to_file(func):
    def decorate():
        func()
        config['running']['default_wh'] = ''
        make_python_code(config_dict=config, resource_file='config.py')

    return decorate


def format_css(input_file, output_file=None):
    style = open(input_file, 'r', encoding='utf8').read()

    style = re.sub(r'/\*[^/*]+\*/', '', style)
    style = re.sub(r'\n', '', style)
    style = re.sub(r'\s{2,}', '', style)

    style = re.sub(r'\s*{\n*', '{', style)
    style = re.sub(r'\s+}', '}', style)
    style = re.sub(r',\n', ',', style)

    if output_file is not None:
        open(output_file, 'w', encoding='utf8').write(style)
    return style


@to_file
def init_style():
    css_files_dir = r'../document/attachment'
    css_files = os.listdir(css_files_dir)
    for css in css_files:
        if css.endswith('css'):
            try:
                config['head']['style'][css[:-4]]['code'] = open(
                    os.path.join(css_files_dir, css), 'r', encoding='utf8').read()
                config['head']['style'][css[:-4]]['format_code'] = format_css(
                    os.path.join(css_files_dir, css))
            except TypeError:
                print(type(css), type(config))


@to_file
def init_tag():
    f = open(r'../document/attachment/element.html', 'r',
             encoding='utf8')
    contents_list = Parsing().parse_tag(f.read())
    config['tag'] = dict()
    config['tag']['bgg'] = str(contents_list[0])
    config['tag']['header'] = str(contents_list[1])
    config['tag']['video'] = str(contents_list[2])
    config['tag']['lc_img'] = str(contents_list[3])
    config['tag']['lc_svg'] = str(contents_list[4])
    config['tag']['ref_ind'] = str(contents_list[5])
    config['tag']['quo'] = str(contents_list[6])
    config['tag']['header_simple'] = str(contents_list[7])


if __name__ == '__main__':
    init_tag()
