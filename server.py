#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import recommender
import os
from flask import Flask, render_template, request
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('template.html')


@app.route('/graph')
def generate_graph():
    # Get the values (i.e. ?seed=some-subreddit&depth=2&nsfw=on)
    seed = request.args.get('seed').lower()
    depth = int(request.args.get('depth'))
    nsfw = bool(request.args.get('nsfw'))

    # Check checkbox and add '_nsfw' suffix to generated files if nsfw
    nsfw_str, nsfw_html = '', ''
    if nsfw:
        nsfw_str = '_nsfw'
        nsfw_html = 'checked="true"'

    # Max out depth users can input
    if depth > 3:
        depth = 3

    # Create class instance of the graph generator
    rec = recommender.Recommender()
    rec.depth = depth
    rec.nsfw = nsfw
    rec.load_dataset()

    # Build filename new output file
    rec.output_path = 'static'
    filename = rec.output_path + '/' + seed + \
        '_d' + str(depth) + nsfw_str + '.json'

    # If graph exists, load from cache, else generate it
    if os.path.exists(filename):
        (result, msg) = 'Success', ''
    else:
        (result, msg) = rec.generate_graph(seed, False)

    # Render output html with graph data
    if result == 'Success':
        html = render_template('graph.html', filename=filename, seed=seed,
                               depth=depth, nsfw=nsfw_html)
    # Print error message to user
    else:
        html = msg

    return html

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.mkdir('static')
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)
