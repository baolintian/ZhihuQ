#!flask/bin/python
from flask import Flask, jsonify
import run
import zhihu.spider
import test
from zhihu.conf import config
app = Flask(__name__)

@app.route("/question/<path:varargs>")
def api(varargs=None):
    # for mainsite/key1/key2/key3/keyn
    # `varargs` is a string contain the above
    varargs = varargs.split("/")
    print("in")
    zhihu.spider.start(r'https://www.zhihu.com/question/'+varargs[0])
    content = test.merge_file(config.wh())
    return content
    print("out")
    # And now it is a list of strings

if __name__ == '__main__':
    app.run(debug=True)