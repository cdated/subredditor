subreddit-crawler
=================

generate_graph.py - Builds a database of related subreddits

recommender.py    - Creates a graph of all subreddits related to one that is user defined

### Usage:

To use the recommender one must either run generate_graph.py to populate the MongoDB database, or use mongorestore on the bson in data/dump/reddit.

```
usage: recommender.py [-h] [-b BREADTH] [-d DEPTH] [-r] [-n] [-s SUBREDDIT] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -b BREADTH, --breadth BREADTH
                        Tree traversal breadth
  -d DEPTH, --depth DEPTH
                        Tree traversal depth
  -r, --render          Render graph
  -n, --nsfw            Allow over 18 subreddits as nodes
  -s SUBREDDIT, --subreddit SUBREDDIT
                        Root subreddit
  -v, --verbose         Show debugging
```

### Example:

Generate a graph of all subreddits related to /r/programming

```./recommender.py -s programming -r```
