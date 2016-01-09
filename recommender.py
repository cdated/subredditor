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
    def __init__(self, depth=2, nsfw=False, verbose=False):
        self.depth = depth
        self.verbose = verbose
        self.nsfw = nsfw

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
        self.local_dict = {}

        self.up_visited = {}
        self.down_visited = {}

    def msg(self, message):
        if self.verbose:
            print(message)

    def load_dataset(self):
        uri = os.environ.get('MONGOCLIENT','localhost')
        client = pymongo.MongoClient(uri)
        db = client.redditgraph
        self.col = db.subreddits

    def query_db(self, sub_name):
        # Memoize database queries
        if sub_name in self.local_dict:
            sub = self.local_dict[sub_name]
        else:
            sub = self.col.find_one({'name': sub_name})
            self.local_dict[sub_name] = sub

        return sub

    def generate_graph(self, seed, render):
        self.sensored_cnt = 0

        # Ensure the generated file indicates nsfw or not
        filename = seed + '_d' + str(self.depth)
        filename = os.path.join(self.output_path, filename)
        if self.nsfw:
            filename += '_nsfw'

        g = Digraph('G', format='png', filename=filename+'.gv')

        sub = self.query_db(seed)
        if not sub:
            return ('Failure', 'Subreddit not in database, please try another subreddit')
        seed_cnt = sub['subscribers']

        if sub['up_links'] != []:
            g = self.add_edges(g, seed, self.depth-1, up=True, reverse=False)

        self.msg("Traversing up, then down")
        up_links = sub['up_links']
        for item in up_links:
            # Continue if a referrer does not have 50% subscribers
            # This is to prevent very small subs from clustering about a huge one
            subreddit = self.query_db(item)
            if subreddit['subscribers'] < (seed_cnt * 0.5):
                continue
            g = self.add_edges(g, item, self.depth-1, up=True, reverse=True)

        self.msg("Travsering straight down")
        if sub['down_links'] != []:
            g = self.add_edges(g, seed, self.depth)

        if not len(self.edges):
            return ('Failure', 'Graph is empty, please try another subreddit')

        if self.censored_cnt >= 1:
            print('# of NSFW nodes removed: ' + str(self.censored_cnt))


        # Draw graphviz graph
        if render:
            # Save graphviz file
            g.save()
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

    def add_edges(self, graph, seed, depth, up=False, reverse=False):
        """ Add subreddits to graph as parent->child nodes through recusive lookup """

        subreddit = self.query_db(seed)

        if (depth == 0) or (not subreddit):
            return graph

        # Apply censor before wasting time
        if subreddit['nsfw'] and not self.nsfw:
            self.censored_cnt += 1
            return graph

        # Get current number of subscribers
        sub_cnt = subreddit['subscribers']

        if reverse:
            up = not up

        if up:
            if seed in self.up_visited:
                return graph
            else:
                self.up_visited[seed] = True
            links = subreddit['up_links']
        else:
            if seed in self.down_visited:
                return graph
            else:
                self.down_visited[seed] = True
            links = subreddit['down_links']

        self.msg('depth: ' + str(depth))
        self.msg(seed)
        self.msg(links)

        # As we get further from the seed we need to be more careful
        # about adding child nodes
        distance = self.depth/depth

        subs = links
        for sub in subs:

            # Error in database, ignoring now
            if (sub == ':**') or (not sub):
                continue

            # If a child has less than 20% of the parent's subscribers filter it out
            # This is to prevent too much clustering
            new_link= self.query_db(sub)
            if new_link:
                if new_link['subscribers'] < (sub_cnt * 0.1 * distance):
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

            graph = self.add_edges(graph, sub, depth - 1, up)

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

    parser.add_argument('-d', '--depth', help='Tree traversal depth', type=int, default=2)
    parser.add_argument('-r', '--render', action='store_true', help='Render graph', default=False)
    parser.add_argument('-n', '--nsfw', action='store_true', help='Allow over 18 subreddits as nodes', default=False)
    parser.add_argument('-s', '--subreddit', help='Root subreddit', required=True)
    parser.add_argument('-v', '--verbose', action='store_true', help='Show debugging', default=False)

    usage(parser)

    args = parser.parse_args()

    recommender = Recommender(args.depth, args.nsfw, args.verbose)
    recommender.load_dataset()
    recommender.generate_graph(args.subreddit, args.render)

if __name__ == '__main__':
    main()
