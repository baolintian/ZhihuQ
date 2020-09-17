#!flask/bin/python
# coding=utf-8
from flask import Flask, jsonify, make_response
import zhihu.spider
import test
from zhihu.conf import config
app = Flask(__name__)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route("/question/<path:varargs>")
def api(varargs=None):
    # for mainsite/key1/key2/key3/keyn
    # `varargs` is a string contain the above
    varargs = varargs.split("/")
    print("in")
    # 问题id, 关键词的过滤, 排序方式, 索引的比重
    zhihu.spider.start(r'https://www.zhihu.com/question/'+varargs[0], varargs[1], int(varargs[2]), float(varargs[3]))
    content = test.merge_file(config.wh())
    return content
    print("out")
    # And now it is a list of strings

if __name__ == '__main__':
    app.run(debug=True)