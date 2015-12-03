#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphviz import Digraph
import math
import pymongo
import argparse
import random
import sys

EDGES = {}

def msg(message):
    if VERBOSE:
        print(message)

def load_dataset(seed, render, breadth, depth):
    client = pymongo.MongoClient()
    db = client.reddit

    related_subs_down = {}
    subscribers = {}

    adult = {}

    related_subs_up = {}

    subreddits = db.subreddits.find({'type': 'subreddit'})
    if subreddits:
        for subreddit in subreddits:
            title = subreddit['_id']
            links = subreddit['linked']
            for link in links:
                if link in related_subs_up:
                    related_subs_up[link] += [title]
                else:
                    related_subs_up[link] = [title]

            if 'subscribers' in subreddit:
                subscribers[title] = subreddit['subscribers']

            if 'adult' in subreddit:
                adult[title] = True

            related_subs_down[title] = links

    g = Digraph('G', filename=seed+'.gv')

    msg("Travsering straight down")
    if seed in related_subs_down:
        if related_subs_down[seed] != []:
            g = add_edges(g, seed, related_subs_down, adult, breadth, depth)

    msg("Traversing up, then down")
    if seed in related_subs_up:
        for item in related_subs_up[seed]:
            g = add_edges(g, item, related_subs_down, adult, breadth, depth-1, up=True, reverse=True)

    if not len(EDGES):
        print('Graph is empty, please try another subreddit')
        return

    if CENSORED >= 1:
        print('# of NSFW nodes removed: ' + str(CENSORED))

    g.save()

    # Draw graphviz graph
    if render:
        g.view()

def add_edges(graph, seed, recommender, adult, breadth, depth, up=False, reverse=False):
    #if (depth == 0) or (not seed in recommender) or (seed in visited):
    if (depth == 0) or (breadth == 0) or (not seed in recommender):
        return graph

    if reverse:
        up = not up

    msg('depth: ' + str(depth))
    msg(seed)
    msg(recommender[seed])

    # Control breadth
    subs = recommender[seed]
    random.shuffle(subs)
    for sub in subs[:breadth]:
        # Error in database, ignoring now
        if (sub == ':**') or (not sub):
            continue

        # Apply censor
        if sub in adult and not NSFW:
            global CENSORED
            CENSORED += 1
            continue

        if up:
            a_node, b_node = sub, seed
        else:
            a_node, b_node = seed, sub

        # Keep graph simple by only adding unqiue edges
        cur_edge = a_node + " -> " + b_node
        msg(cur_edge)
        if not cur_edge in EDGES:
            graph.edge(a_node, b_node)
            EDGES[cur_edge] = True

        graph = add_edges(graph, sub, recommender, adult, breadth-1, depth - 1, up)

    return graph

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
    global VERBOSE
    VERBOSE = args.verbose

    global NSFW
    NSFW = args.nsfw

    global CENSORED
    CENSORED = 0

    load_dataset(args.subreddit, args.render, args.breadth, args.depth)

if __name__ == '__main__':
    main()
