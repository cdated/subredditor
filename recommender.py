#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphviz import Digraph
import math
import pymongo
import argparse
import random
import sys


class Recommender:
    def __init__(self, breadth=2, depth=2, nsfw=False, verbose=False):
        self.breadth = breadth
        self.depth = depth
        self.verbose = verbose
        self.nsfw = nsfw

        # These only need to be read once per dataset
        self.related_subs_down = {}
        self.subscriber_cnts = {}
        self.adult_table = {}
        self.related_subs_up = {}

        # These vary from graph to graph
        self.edges= {}
        self.censored_cnt = 0

    def msg(self, message):
        if self.verbose:
            print(message)

    def load_dataset(self):
        client = pymongo.MongoClient()
        db = client.reddit

        subreddits = db.subreddits.find({'type': 'subreddit'})
        if subreddits:
            for subreddit in subreddits:
                title = subreddit['_id']
                links = subreddit['linked']
                for link in links:
                    if link in self.related_subs_up:
                        self.related_subs_up[link] += [title]
                    else:
                        self.related_subs_up[link] = [title]

                if 'subscribers' in subreddit:
                    self.subscriber_cnts[title] = subreddit['subscribers']

                if 'adult' in subreddit:
                    self.adult_table[title] = True

                self.related_subs_down[title] = links

    def generate_graph(self, seed, render):
        self.sensored_cnt = 0

        g = Digraph('G', filename=seed+'.gv')

        self.msg("Travsering straight down")
        if seed in self.related_subs_down:
            if self.related_subs_down[seed] != []:
                g = self.add_edges(g, seed, self.breadth, self.depth)

        self.msg("Traversing up, then down")
        if seed in self.related_subs_up:
            for item in self.related_subs_up[seed][:2]:
                g = self.add_edges(g, item, self.breadth, self.depth-1, up=True, reverse=True)

        if not len(self.edges):
            print('Graph is empty, please try another subreddit')
            return

        if self.censored_cnt >= 1:
            print('# of NSFW nodes removed: ' + str(self.censored_cnt))

        g.save()

        # Draw graphviz graph
        if render:
            g.view()

        self.cleanup()

    def add_edges(self, graph, seed, breadth, depth, up=False, reverse=False):
        """ Add subreddits to graph as parent->child nodes through recusive lookup """

        related_dict = self.related_subs_down
        if (depth == 0) or (breadth == 0) or (not seed in related_dict):
            return graph

        if reverse:
            up = not up

        self.msg('depth: ' + str(depth))
        self.msg(seed)
        self.msg(related_dict[seed])

        # Control breadth
        subs = related_dict[seed]
        random.shuffle(subs)
        for sub in subs[:breadth]:
            # Error in database, ignoring now
            if (sub == ':**') or (not sub):
                continue

            # Apply censor
            if sub in self.adult_table and not self.nsfw:
                self.censored_cnt += 1
                continue

            if up:
                a_node, b_node = sub, seed
            else:
                a_node, b_node = seed, sub

            # Keep graph simple by only adding unqiue edges
            cur_edge = a_node + " -> " + b_node
            self.msg(cur_edge)
            if not cur_edge in self.edges:
                graph.edge(a_node, b_node)
                self.edges[cur_edge] = True

            graph = self.add_edges(graph, sub, breadth-1, depth - 1, up)

        return graph

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
    parser.add_argument('-s', '--subreddit', help='Root subreddit', default='programming')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show debugging', default=False)

    usage(parser)

    args = parser.parse_args()

    recommender = Recommender(args.breadth, args.depth, args.nsfw, args.verbose)
    recommender.load_dataset()
    recommender.generate_graph(args.subreddit, args.render)

if __name__ == '__main__':
    main()
