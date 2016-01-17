#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphviz import Digraph
import math
import pymongo
import argparse
import sys
import os
import pickle


class Recommender:

    def __init__(self, depth=2, nsfw=False, verbose=False):
        self.depth = depth
        self.verbose = verbose
        self.nsfw = nsfw

        # These vary from graph to graph
        self.edges = {}
        self.censored_cnt = 0

        # Alternate path for generated files
        # Used in webapp to specify 'static' dir
        self.output_path = ''

        # Data structures used to construct d3 output json
        self.d3_node_list = []
        self.node_idx_map = {}
        self.d3_edges = []

        self.col = None
        self.local_dict = {}

        self.up_visited = {}
        self.down_visited = {}

    def msg(self, message):
        """ Conditional print to console """

        # A single point to check verbosity
        if self.verbose:
            print(message)

    def load_dataset(self):
        """ Setup db cursor and load cached data into memory """

        # Load env variable MONGOCLIENT if set, otherwise set to localhost
        uri = os.environ.get('MONGOCLIENT', 'localhost')
        client = pymongo.MongoClient(uri)
        db = client.redditgraph
        self.col = db.subreddits

        # Load a local copy of accessed database records, mitigates Mongolab
        # response times
        pickle_dict = "local_dict.pickle"
        if os.path.exists(pickle_dict):
            self.local_dict = pickle.load(open(pickle_dict, "rb"))

    def query_db(self, sub_name):
        """ Check the local cache, otherwise query remote db """

        # Memoize database queries
        if sub_name in self.local_dict:
            sub = self.local_dict[sub_name]
            # If local lookup fails do db lookup
            if not sub:
                del self.local_dict[sub_name]
                sub = self.query_db(sub_name)
        else:
            sub = self.col.find_one({'name': sub_name})
            self.local_dict[sub_name] = sub

        return sub

    def generate_graph(self, seed, render):
        """ Create graph by connecting adjacent nodes """

        self.sensored_cnt = 0

        # Ensure the generated file indicates nsfw or not
        filename = seed + '_d' + str(self.depth)
        filename = os.path.join(self.output_path, filename)
        if self.nsfw:
            filename += '_nsfw'

        g = Digraph('G', format='png', filename=filename + '.gv')

        sub = self.query_db(seed)
        if not sub:
            return ('Failure', 'Subreddit not in database, please try another subreddit')
        seed_cnt = sub['subscribers']

        if sub['up_links'] != []:
            g = self.add_edges(g, seed, self.depth, up=True, reverse=False)

        self.msg("Traversing up, then down")
        up_links = sub['up_links']
        for item in up_links:
            # Ignore if a referrer does not have 20% subscribers
            # Prevent very small subs from clustering about a huge one
            # subreddit = self.query_db(item)
            # if subreddit['subscribers'] < (seed_cnt * 0.2):
            #     continue
            g = self.add_edges(g, item, self.depth - 1, up=True, reverse=True)

        self.msg("Travsering straight down")
        if sub['down_links'] != []:
            g = self.add_edges(g, seed, self.depth)

        if not len(self.edges):
            return ('Failure', 'Graph is empty, please try another subreddit')

        if self.censored_cnt >= 1:
            self.msg('# of NSFW nodes removed: ' + str(self.censored_cnt))

        # Draw graphviz graph
        if render:
            # Save graphviz file
            g.save()
            g.render(view=True)

        # Save json for D3
        filename = filename + '.json'
        with open(filename, "wt") as d3:
            print('{"nodes":[', end="", file=d3)
            print(', '.join(self.d3_node_list), end="", file=d3)
            print('], "links":[', end="", file=d3)
            print(', '.join(self.d3_edges), end="", file=d3)
            print(']}', end="", file=d3)

        self.cleanup()

        return ('Success', filename)

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
        seed_cnt = subreddit['subscribers']

        # This is used once to get the sibling referers
        # Rather than go straight up or down, go up one level and recurse down
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
        distance = self.depth / depth

        subs = links
        for sub in subs:

            # Error in database, ignoring now
            if (sub == ':**') or (not sub):
                continue

            # If a child has less than 20% of the parent's subscribers filter it out
            # This is to prevent too much clustering
            new_link = self.query_db(sub)
            if new_link:
                new_cnt = new_link['subscribers']
                if (new_cnt < (seed_cnt * 0.2 * distance)) and (self.depth - depth > 0):
                    continue
            else:
                continue

            # If traversing up, change direction of nodes
            if up:
                a_node, b_node = sub, seed
                a_cnt, b_cnt = new_cnt, seed_cnt
            else:
                a_node, b_node = seed, sub
                a_cnt, b_cnt = seed_cnt, new_cnt

            # Add an index for each node:
            # d3 connects edges as idxA->idxB
            # so we need to store their names and numbers (indices)
            self.update_nodes(a_node, a_cnt)
            self.update_nodes(b_node, b_cnt)

            # Keep graph simple by only adding unqiue edges
            cur_edge = a_node + " -> " + b_node
            self.msg(cur_edge)
            if not cur_edge in self.edges:
                # Add edge for graphviz
                graph.edge(a_node, b_node)

                # Add edge for d3.js
                self.d3_edges.append('{"source":' + str(self.node_idx_map[a_node]) +
                                     ',"target":' + str(self.node_idx_map[b_node]) +
                                     ',"value":' + str(depth) + '}')

                # Save edge to ensure it can only be added once
                self.edges[cur_edge] = True

            # Recurse related subs until depth is exhausted
            graph = self.add_edges(graph, sub, depth - 1, up)

        # Save cache to disk
        pickle.dump(self.local_dict, open("local_dict.pickle", "wb"))

        return graph

    def update_nodes(self, node, cnt):
        if not node in self.node_idx_map:
            self.node_idx_map[node] = len(self.node_idx_map)
            try:
                # Scale subscriber counts to emphasis order of magnitude difference
                # without letting large subs dominate the graph
                scale = math.ceil(math.log(cnt, 10))
                size = str(scale * scale)
            except:
                size = '10'
            self.d3_node_list.append(
                '{"name":"' + node + '", "subs":"' + size + '"}')

    def cleanup(self):
        self.edges = {}
        self.censored_cnt = 0


def usage(parser):
    """ Let the user know the expected runtime args """

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()


def main():
    """ Parse cli args and kick off graph generation """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--depth', type=int, default=2,
                        help='Tree traversal depth')
    parser.add_argument('-r', '--render', action='store_true', default=False,
                        help='Render graph')
    parser.add_argument('-n', '--nsfw', action='store_true', default=False,
                        help='Allow over 18 subreddits as nodes')
    parser.add_argument('-s', '--subreddit', required=True,
                        help='Root subreddit')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='Show debugging')
    usage(parser)

    args = parser.parse_args()

    recommender = Recommender(args.depth, args.nsfw, args.verbose)
    recommender.load_dataset()
    recommender.generate_graph(args.subreddit, args.render)

if __name__ == '__main__':
    main()
