#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import praw
import time
import sys
import re
import pymongo
from urllib.request import urlopen

RELATED_SUBS = {}

def connection_valid():
    try:
        urlopen('http://www.reddit.com')
        return True
    except:
        return False

def check_connection():
    retries = 0
    while connection_valid() == False:
        if retries > 5:
            print("Connection to Reddit failed, exiting")
            sys.exit(1)
        time.sleep(4)
        retries += 1

def extract_references(line):
    references = []
    while len(line):
        start_index = line.find('/r/')

        # If line does not seem to contain a subreddit
        if start_index == -1:
            break 

        # Trim the '/r/' out of the string
        start_index += 3

        # Grab subreddit name substring
        rel_sub = line[start_index:].strip()
        rel_sub_strs = re.sub('[^0-9a-zA-Z_]+', ' ', rel_sub).split()
        if rel_sub_strs:
            rel_sub = rel_sub_strs[0]

        # Trim out the subreddit chars for next iteration
        line = line[start_index+len(rel_sub):]

        # Combined subreddits won't be counted
        if '+' in rel_sub:
            continue

        references.append(rel_sub)

    return references

def get_related(reddit, sub_title, db, backlog):
    new_subreddits = []

    # Initialize references to empty list to mark as tried
    RELATED_SUBS[sub_title] = []

    try:
        subreddit = reddit.get_subreddit(sub_title)
    except praw.errors.NotFound:
        # Invalid subreddit
        return []

    # Get description of sub and lowercase for matching
    try:
        desc = subreddit.description.lower()
    except praw.errors.Forbidden: 
        record = {'_id' : sub_title,
                  'linked' : [],
                  'access' : 'private',
                  'type' : 'subreddit'}
        add_record(db, record)
        return []
    except praw.errors.NotFound:
        record = {'_id' : sub_title,
                  'linked' : [],
                  'access' : 'banned',
                  'type' : 'subreddit'}
        add_record(db, record)
        return []
    except praw.errors.InvalidSubreddit:
        return []
    except AttributeError:
        return []

    # Split description by line
    lines = desc.split('\n')
    if not len(lines):
        lines = desc.split('>')

    for line in lines:
        if '/r/' in line:
            references = extract_references(line)

            for rel_sub in references:
                # Ignore self references
                if rel_sub == sub_title:
                    continue

                # Add unique references to dict
                if not rel_sub in RELATED_SUBS[sub_title]:
                    RELATED_SUBS[sub_title].append(rel_sub)

                # If found subreddit not explored, put it in the backlog
                if (not rel_sub in backlog) and \
                   (not rel_sub in RELATED_SUBS) and \
                   (not rel_sub in new_subreddits):
                    new_subreddits.append(rel_sub)

    record = {'_id' : sub_title,
              'type' : 'subreddit',
              'language' : subreddit.lang,
              'created' : subreddit.created_utc,
              'subscribers' : subreddit.subscribers,
              'linked' : RELATED_SUBS[sub_title]}

    if subreddit.over18:
        record['adult'] = True

    # Add related sub list by subreddit to database
    add_record(db, record)

    return new_subreddits

def add_record(db, record):
    try:
        db.subreddits.insert_one(record)
    except pymongo.errors.DuplicateKeyError:
        # Ignore collision
        pass

def crawl(subreddit_seed):
    client = pymongo.MongoClient()
    db = client.reddit

    db_backlog = db.subreddits.find_one({'name': 'backlog'})
    if db_backlog:
        backlog = db_backlog['items']

    # If the backlog object is invalid or empty, use the seed
    if not db_backlog or not backlog:
        backlog = [subreddit_seed]

    subreddits = db.subreddits.find({'type': 'subreddit'})
    if subreddits:
        for subreddit in subreddits:
            title = subreddit['_id']
            links = subreddit['linked']
            RELATED_SUBS[title] = links

    reddit = praw.Reddit(user_agent='related_subs')

    # Work through the backlog
    while len(backlog):
        # Check connection before continuing
        check_connection()

        # Remove and investigate last item from backlog
        subreddit = backlog.pop()

        if not subreddit in RELATED_SUBS:
            if not subreddit:
                continue

            try:
                backlog += get_related(reddit, subreddit, db, backlog)
            except:
                try:
                    print("Failed to access reddit.com, retrying")
                    time.sleep(5)
                    backlog += get_related(reddit, subreddit, db, backlog)
                except:
                    print("Failed again, exiting")
                    sys.exit(1)

        # Update the backlog in the DB
        db.subreddits.update_one({'name': 'backlog'}, {"$set": {"items": backlog}}, upsert=True)

def usage(parser):
    """ Let the user know the expected runtime args """

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--subreddit', help='Subreddit seed', required=True)

    usage(parser)

    args = parser.parse_args()
    crawl(args.subreddit)

if __name__ == '__main__':
    main()
