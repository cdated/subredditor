#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphviz import Digraph
import math
import pymongo
import argparse
import random
import sys
import os


class Recommender:
    def __init__(self, breadth=2, depth=2, nsfw=False, verbose=False):
        self.breadth = breadth
        self.depth = depth
        self.verbose = verbose
        self.nsfw = nsfw

        self.visited = {}

        # These vary from graph to graph
        self.edges= {}
        self.censored_cnt = 0

        # Alternate path other than current dir
        self.output_path = ''

        self.node_count = 0
        self.node_list = []
        self.nodes = {}
        self.links = []

        self.col = None

    def msg(self, message):
        if self.verbose:
            print(message)

    def load_dataset(self):
        uri = os.environ.get('MONGOCLIENT','localhost')
        client = pymongo.MongoClient(uri)
        db = client.redditgraph
        self.col = db.subreddits

    def generate_graph(self, seed, render):
        self.sensored_cnt = 0

        # Ensure the generated file indicates nsfw or not
        filename = seed + '_b' + str(self.breadth) + '_d' + str(self.depth)
        filename = os.path.join(self.output_path, filename)
        if self.nsfw:
            filename += '_nsfw'

        g = Digraph('G', format='png', filename=filename+'.gv')

        sub = self.col.find_one({'name': seed})
        seed_cnt = sub['subscribers']


        self.msg("Traversing up, then down")
        up_links = sub['up_links']
        for item in up_links:
            # Continue if a referrer does not have 50% subscribers
            # This is to prevent very small subs from clustering about a huge one
            subreddit = self.col.find_one({'name': item})
            if subreddit['subscribers'] < (seed_cnt * 0.5):
                continue
            g = self.add_edges(g, item, self.breadth, self.depth, up=True, reverse=False)
        self.msg("Travsering straight down")
        if sub['down_links'] != []:
            g = self.add_edges(g, seed, self.breadth, self.depth)

        if not len(self.edges):
            return ('Failure', 'Graph is empty, please try another subreddit')

        if self.censored_cnt >= 1:
            print('# of NSFW nodes removed: ' + str(self.censored_cnt))

        # Save graphviz file
        g.save()

        # Draw graphviz graph
        if render:
            g.render(view=True)

        # Save json for D3
        filename = filename + '.json'
        with open(filename, "wt") as d3:
            print('{"nodes":[', end="", file=d3)
            print(', '.join(self.node_list), end="", file=d3)
            print('], "links":[', end="", file=d3)
            print(', '.join(self.links) , end="", file=d3)
            print(']}', end="", file=d3)

        self.cleanup()

        return ('Sucess', filename)

    def add_edges(self, graph, seed, breadth, depth, up=False, reverse=False):
        """ Add subreddits to graph as parent->child nodes through recusive lookup """

        if seed in self.visited:
            return graph

        self.visited[seed] = True

        subreddit = self.col.find_one({'name': seed})

        if (depth == 0) or (breadth == 0) or (not subreddit):
            return graph

        # Get current number of subscribers
        sub_cnt = subreddit['subscribers']

        if reverse:
            up = not up

        if up:
            links = subreddit['up_links']
        else:
            links = subreddit['down_links']

        self.msg('depth: ' + str(depth))
        self.msg(seed)
        self.msg(links)

        # Control breadth
        subs = links
        random.shuffle(subs)
        for sub in subs:
            # Error in database, ignoring now
            if (sub == ':**') or (not sub):
                continue

            # If a child has less than 20% of the parent's subscribers filter it out
            # This is to prevent too much clustering
            new_link = self.col.find_one({'name': sub})
            if new_link:
                if new_link['subscribers'] < (sub_cnt * 0.2):
                    continue

            # Apply censor
            if subreddit['nsfw'] and not self.nsfw:
                self.censored_cnt += 1
                continue

            if up:
                a_node, b_node = sub, seed
            else:
                a_node, b_node = seed, sub

            self.update_nodes(a_node)
            self.update_nodes(b_node)

            # Keep graph simple by only adding unqiue edges
            cur_edge = a_node + " -> " + b_node
            self.msg(cur_edge)
            if not cur_edge in self.edges:
                graph.edge(a_node, b_node)
                self.links.append('{"source":' + str(self.nodes[a_node]) +
                                  ',"target":' + str(self.nodes[b_node]) + ', "value":1}')
                self.edges[cur_edge] = True

            graph = self.add_edges(graph, sub, breadth-1, depth - 1, up)

        return graph

    def update_nodes(self, node):
        if not node in self.nodes:
            self.nodes[node] = self.node_count
            self.node_list.append('{"name":"' + node +'"}')
            self.node_count += 1

    def cleanup(self):
        self.edges= {}
        self.censored_cnt = 0

def usage(parser):
    """ Let the user know the expected runtime args """

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-b', '--breadth', help='Tree traversal breadth', type=int, default=100)
    parser.add_argument('-d', '--depth', help='Tree traversal depth', type=int, default=2)
    parser.add_argument('-r', '--render', action='store_true', help='Render graph', default=False)
    parser.add_argument('-n', '--nsfw', action='store_true', help='Allow over 18 subreddits as nodes', default=False)
    parser.add_argument('-s', '--subreddit', help='Root subreddit', required=True)
    parser.add_argument('-v', '--verbose', action='store_true', help='Show debugging', default=False)

    usage(parser)

    args = parser.parse_args()

    recommender = Recommender(args.breadth, args.depth, args.nsfw, args.verbose)
    recommender.load_dataset()
    recommender.generate_graph(args.subreddit, args.render)

if __name__ == '__main__':
    main()
