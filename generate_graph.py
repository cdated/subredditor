from graphviz import Digraph
import math
import pymongo

def main():
    client = pymongo.MongoClient()
    db = client.reddit

    related_subs = {}
    subscribers = {}
    adult = {}

    subreddits = db.subreddits.find({'type': 'subreddit'})
    if subreddits:
        for subreddit in subreddits:
            title = subreddit['_id']
            links = subreddit['linked']

            if 'subscribers' in subreddit:
                subscribers[title] = subreddit['subscribers']
                
            if 'adult' in subreddit:
                adult[title] = True

            related_subs[title] = links

    generate_full_graph(related_subs, subscribers, adult, min_subscribers=0)
    generate_censored_graph(related_subs, subscribers, adult, min_subscribers=100)
    generate_adult_graph(related_subs, subscribers, adult, min_subscribers=100)

def generate_full_graph(related_subs, subscribers, adult, min_subscribers):

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


def generate_adult_graph(related_subs, subscribers, adult, min_subscribers):

    g = Digraph('G', filename='adult.gv')

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

if __name__ == '__main__':
    main()
