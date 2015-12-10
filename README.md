subreddit-crawler
=================

generate_graph.py - Builds a database of related subreddits

recommender.py    - Creates a graph of all subreddits related to one that is user defined

### Usage:

To use the graph utilities recommender.py and generate_graph.py one must either run subreddit_crawler.py to populate the MongoDB database, or use mongorestore on the bson in data/dump/reddit.  Once a dataset has been loaded/generated two types of graphs can be constructed; a full network with filters or a region with child node limits.

generate_graph.py can generate a full graph of recommended subreddits.  By default it hides nodes featuring explicit content, but can generate a censored graph (default), full graph, and the difference of the two.  One may also filter out subreddits with subscriber counts below a specified number with the minimum flag.

```
usage: generate_graph.py [-h] [-c] -m MINIMUM [-n] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -c, --censored        Hide over 18 subreddits
  -m MINIMUM, --minimum MINIMUM
                        Min subcribers to be added
  -n, --nsfw            Only over 18 subreddits
  -v, --verbose         Show debugging
```



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

Generate a graph of a set of subreddits related to /r/wikipedia and /r/python.  Render the graph as a pdf with -r (render) flag and limit the number of child nodes to 2 with -b (breadth) flag.  When breadth is restricted the child nodes are chosen at random, breadth also decreases with depth to prevent extremely large graphs.

======

```./recommender.py -s wikipedia -r -b 2```

![Wikipedia Graph](https://github.com/cdated/subreddit-crawler/blob/master/example/wikipedia.png?raw=true)

======

```./recommender.py -s python -r -b 2```

![Python Graph](https://github.com/cdated/subreddit-crawler/blob/master/example/python.png?raw=true)
