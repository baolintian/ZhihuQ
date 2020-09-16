#!flask/bin/python
from flask import Flask, jsonify
import spider
app = Flask(__name__)

tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol',
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web',
        'done': False
    }
]

@app.route("/question/<path:varargs>")
def api(varargs=None):
    # for mainsite/key1/key2/key3/keyn
    # `varargs` is a string contain the above
    varargs = varargs.split("/")
    print("in")
    spider.GetAnswer(varargs[1])
    print("out")
    # And now it is a list of strings

if __name__ == '__main__':
    app.run(debug=True)