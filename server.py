import recommender
import os
from flask import Flask, render_template, request
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('template.html')

@app.route('/graph')
def my_link():
    # here we want to get the value of user (i.e. ?user=some-value)
    seed = request.args.get('seed')
    nsfw = bool(request.args.get('nsfw'))
    breadth = int(request.args.get('breadth'))
    depth = int(request.args.get('depth'))

    if breadth > 5:
        breadth = 5

    if depth > 5:
        depth = 5

    rec = recommender.Recommender(breadth, depth, nsfw)
    rec.load_dataset()

    # Graph parameters
    rec.output_path = 'static'

    (result, msg) = rec.generate_graph(seed, False)

    if result == 'Sucess':
        filename = msg
        html = render_template('graph.html', filename=filename)
    else:
        html = msg

    return html

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.mkdir('static')
    port = int(os.environ.get('PORT',5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)
