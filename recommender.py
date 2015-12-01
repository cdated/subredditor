#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphviz import Digraph
import math
import pymongo

EDGES = {}

def main():
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

    depth = 2
    seed = 'python'
    g = Digraph('G', filename=seed+'.gv')

    print("Travsering straight down")
    if seed in related_subs_down:
        if related_subs_down[seed] != []:
            g = add_edges(g, seed, related_subs_down, depth)

    print("Traversing up, then down")
    if seed in related_subs_up:
        for item in related_subs_up[seed]:
            g = add_edges(g, item, related_subs_down, depth-1, up=True, reverse=True)

    g.save()
    g.view()

def add_edges(graph, seed, recommender, depth, up=False, reverse=False):
    #if (depth == 0) or (not seed in recommender) or (seed in visited):
    if (depth == 0) or (not seed in recommender):
        return graph

    if reverse:
        up = not up

    print('depth: ' + str(depth))
    print(seed)
    print(recommender[seed])
    for sub in recommender[seed]:
        if not sub:
            continue

        if up:
            a_node, b_node = sub, seed
        else:
            a_node, b_node = seed, sub

        # Keep graph simple by only adding unqiue edges
        cur_edge = a_node + " -> " + b_node
        print(cur_edge)
        if not cur_edge in EDGES:
            graph.edge(a_node, b_node)
            EDGES[cur_edge] = True

        graph = add_edges(graph, sub, recommender, depth - 1, up)

    return graph

if __name__ == '__main__':
    main()
