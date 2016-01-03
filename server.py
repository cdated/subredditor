import recommender
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
    
    rec = recommender.Recommender(breadth, depth, nsfw)
    rec.load_dataset()

    # Graph parameters
    rec.output_path = 'static'

    (result, msg) = rec.generate_graph(seed, True)

    if result == 'Sucess':
        filename = msg
        html = "<img src='" + filename + "'></img>"
    else:
        html = msg

    return html

if __name__ == '__main__':
  app.run(debug=True)
