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

def generate_graph(related_subs, subscribers, nsfw_subs, censored, full, min_subscribers, outfile):

    g = Digraph('G', filename=outfile)

    edges_added = 0
    for key in related_subs:
        for sub in related_subs[key]:
            if not sub or not sub in subscribers:
                continue

            # In nsfw_subs and censored is mutually exclusive
            if ((sub in nsfw_subs) != (censored)) or full:
                subscriber_cnt = subscribers[sub]

                # Filter: only include edge if sub has # subscribers
                if subscriber_cnt >= min_subscribers:
                    g.edge(key, sub, weight=calculate_edge_weight(subscriber_cnt))
                    print("Edge count: " + str(edges_added))
                    edges_added += 1

    g.save()


def calculate_edge_weight(subscriber_cnt):
    if subscriber_cnt == 0:
        log_cnt = 0
    else:
        log_cnt = math.log2(subscriber_cnt)

    return str(log_cnt)

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
    nsfw_subs = {}
    private = []

    subreddits = db.subreddits.find({'type': 'subreddit'})
    if subreddits:
        for subreddit in subreddits:
            title = subreddit['_id']
            links = subreddit['linked']

            if 'subscribers' in subreddit:
                subscribers[title] = subreddit['subscribers']

            if 'adult' in subreddit:
                nsfw_subs[title] = True

            if 'access' in subreddit:
                if subreddit['access'] == 'private':
                    private.append(title)

            related_subs[title] = links

    write_list_to_file(private, 'private_subs.txt')

    censored = False
    full = False

    # If censored and nsfw flags, opt for censored
    if args.censored:
        outfile = 'censored.gv'
        censored = True
    elif args.nsfw:
        outfile = 'nsfw.gv'
    else:
        outfile = 'full.gv'
        full = True

    generate_graph(related_subs, subscribers, nsfw_subs, censored, full, args.minimum, outfile)


if __name__ == '__main__':
    main()
