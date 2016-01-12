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
    seed = request.args.get('seed').lower()
    nsfw = bool(request.args.get('nsfw'))
    depth = int(request.args.get('depth'))

    nsfw_str = ''
    nsfw_html = ''
    if nsfw:
        nsfw_str = '_nsfw'
        nsfw_html = 'checked="true"'

    if depth > 3:
        depth = 3

    rec = recommender.Recommender()
    rec.depth = depth
    rec.nsfw = nsfw
    rec.load_dataset()

    # Graph parameters
    rec.output_path = 'static'

    filename = rec.output_path + '/' + seed + '_d' + str(depth) + nsfw_str + '.json'
    if os.path.exists(filename):
        # graph data exist, skip to render
        html = render_template('graph.html', filename=filename, seed=seed, 
                               depth=depth, nsfw=nsfw_html)
    else:
        # generate graph data
        (result, msg) = rec.generate_graph(seed, False)

        if result == 'Sucess':
            filename = msg
            html = render_template('graph.html', filename=filename, seed=seed, 
                               depth=depth, nsfw=nsfw_html)
        else:
            html = msg

    return html

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.mkdir('static')
    port = int(os.environ.get('PORT',5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)
