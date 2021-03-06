subredditor
=================

[![forthebadge](http://forthebadge.com/images/badges/built-with-love.svg)](http://forthebadge.com) [![forthebadge](http://forthebadge.com/images/badges/powered-by-electricity.svg)](http://forthebadge.com)

### Description:

Subredditor creates visualizations of how subreddits relate to one another

<p align="center">
  <img src="https://github.com/cdated/subredditor/blob/master/static/example/webapp.png?raw=true" alt="Webapp" width="600px" height="whatever">
</p>

### Standalone Usage:

To use `recommender.py` one must either populate the MongoDB database with https://github.com/cdated/reddit-crawler, or use mongorestore on the bson in data/dump/reddit.

`recommender.py` generates a sub-region of the full graph with limits on the breadth and depth of child nodes.  The user must specify a subreddit as the root to which parent and child nodes are connected.  Output is a graphviz file and optionally a png.

```
usage: recommender.py [-h] [-b BREADTH] [-d DEPTH] [-r] [-n] [-s SUBREDDIT] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -d DEPTH, --depth DEPTH
                        Tree traversal depth
  -r, --render          Render graph
  -n, --nsfw            Allow over 18 subreddits as nodes
  -s SUBREDDIT, --subreddit SUBREDDIT
                        Root subreddit
  -v, --verbose         Show debugging
```

#### Loading Database

There's already a database (approx 8Mb) in the repo for those who don't want to run the crawler to see the connections.  To load it just run the `restore_db.sh` script.

### Example:

Generating a graph of subreddits related to /r/wikipedia and /r/python.  Render the graph as a pdf with -r (render) flag and limit the number of child nodes to 2 with -b (breadth) flag.  When breadth is restricted the child nodes are chosen at random, breadth also decreases with depth to prevent extremely large graphs.

======

```./recommender.py -s wikipedia -r```

![Wikipedia Graph](https://github.com/cdated/subredditor/blob/master/static/example/wikipedia.png?raw=true)

======

```./recommender.py -s python -r```

![Python Graph](https://github.com/cdated/subredditor/blob/master/static/example/python.png?raw=true)
