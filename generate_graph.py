#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphviz import Digraph
import math
import pymongo
import argparse
import sys

def write_list_to_file(alist, filepath):
    with open(filepath, 'w') as file:
        for item in alist:
            file.write("{}\n".format(item))

def generate_full_graph(related_subs, subscribers, min_subscribers):

    g = Digraph('G', filename='full.gv')

    edges_added = 0
    for key in related_subs:
        for sub in related_subs[key]:
            if not sub:
                continue

            # Filter: only include edge if sub has # subscribers
            if sub in subscribers:
                subscriber_cnt = subscribers[sub]
                if subscriber_cnt >= min_subscribers:
                    log_cnt = math.log2(subscriber_cnt)
                    g.edge(key, sub, weight=str(log_cnt))
                    print("Edge count: " + str(edges_added))
                    edges_added += 1

    g.save()

def generate_censored_graph(related_subs, subscribers, adult, min_subscribers):

    g = Digraph('G', filename='censored.gv')

    edges_added = 0
    for key in related_subs:
        for sub in related_subs[key]:
            if not sub:
                continue

            # Filter: only include edge if sub has # subscribers
            if sub in subscribers and not sub in adult:
                subscriber_cnt = subscribers[sub]
                if subscriber_cnt >= min_subscribers:
                    log_cnt = math.log2(subscriber_cnt)
                    g.edge(key, sub, weight=str(log_cnt))
                    print("Edge count: " + str(edges_added))
                    edges_added += 1

    g.save()


def generate_nsfw_graph(related_subs, subscribers, adult, min_subscribers):

    g = Digraph('G', filename='nsfw.gv')

    edges_added = 0
    for key in related_subs:
        for sub in related_subs[key]:
            if not sub:
                continue

            # Filter: only include edge if sub has # subscribers
            if sub in subscribers and sub in adult:
                subscriber_cnt = subscribers[sub]
                if subscriber_cnt >= min_subscribers:
                    log_cnt = math.log2(subscriber_cnt)
                    g.edge(key, sub, weight=str(log_cnt))
                    print("Edge count: " + str(edges_added))
                    edges_added += 1

    g.save()

def usage(parser):
    """ Let the user know the expected runtime args """

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--censored', action='store_true', help='Hide over 18 subreddits', default=False)
    parser.add_argument('-m', '--minimum', help='Min subcribers to be added', type=int, default=100, required=True)
    parser.add_argument('-n', '--nsfw', action='store_true', help='Only over 18 subreddits', default=False)
    parser.add_argument('-v', '--verbose', action='store_true', help='Show debugging', default=False)

    usage(parser)

    args = parser.parse_args()

    client = pymongo.MongoClient()
    db = client.reddit

    related_subs = {}
    subscribers = {}
    adult = {}
    private = []

    subreddits = db.subreddits.find({'type': 'subreddit'})
    if subreddits:
        for subreddit in subreddits:
            title = subreddit['_id']
            links = subreddit['linked']

            if 'subscribers' in subreddit:
                subscribers[title] = subreddit['subscribers']
                
            if 'adult' in subreddit:
                adult[title] = True

            if 'access' in subreddit:
                if subreddit['access'] == 'private':
                    private.append(title)

            related_subs[title] = links


    write_list_to_file(private, 'private_subs.txt')

    # Censored trumps over args
    if args.censored:
        generate_censored_graph(related_subs, subscribers, adult, args.minimum)
    elif args.nsfw:
        generate_nsfw_graph(related_subs, subscribers, adult, args.minimum)
    else:
        generate_full_graph(related_subs, subscribers, args.minimum)


if __name__ == '__main__':
    main()
