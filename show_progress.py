#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import pymongo

def main():
    client = pymongo.MongoClient()
    db = client.reddit

    while 1:
        db_backlog = db.subreddits.find_one({'name': 'backlog'})
        if db_backlog:
            backlog = db_backlog['items']
            print('Checking ' + backlog[-1])
            print('Checked: ' + str(db.command('collstats', 'subreddits')['count']))
            print('Remaining: ' + str(len(backlog)))
            print()
        else:
            sys.exit(0)
        time.sleep(2)

if __name__ == '__main__':
    main()
