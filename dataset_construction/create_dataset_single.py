import json
from dataset_construction import gmail_utils
from os.path import join
import os
from constants import DATA_ROOT

def build_query(filter_str, email_addresses, start_date_formatted=None):
    after_clause = " AND after:" + start_date_formatted if start_date_formatted else ''
    query = ' OR '.join([filter_str + x for x in email_addresses]) + after_clause
    return query


def filter_unwanted_threads(threads, threads_container, has_unrecognized_sender):
    # valid = []
    # for t in threads:
    #     if not has_unrecognized_sender(gmail_utils.get_msgs_from_thread(threads_container, t['id'])):
    #         valid.append(t)
    # return valid
    return [x for x in threads if not has_unrecognized_sender(gmail_utils.get_msgs_from_thread(
        threads_container, x['id']))]


def flatten(lst):
    flattened_list = []
    for item in lst:
        if type(item) is list:
            flattened_list.extend(flatten(item))
        else:
            flattened_list.append(item)
    return flattened_list

def make_unrecognized_sender_fn(recognized_senders):
    print(recognized_senders,'\n\n')
    def has_unrecognized_sender(thread_msgs):
        senders = set([gmail_utils.get_sender(msg).email for msg in thread_msgs])
        m = False
        for x in senders:
            if x not in recognized_senders:
                print('\t', x)
                m = True
        return m
    return has_unrecognized_sender


if __name__ == "__main__":
    with open("query_parameters.json", 'r') as fin:
        query_parameters = json.load(fin)
    service = gmail_utils.get_service()
    threads_container = service.users().threads()
    query = build_query(query_parameters['filter_str'],
                        flatten(query_parameters['emails'].values()),
                        query_parameters['start_date'])
    threads = threads_container.list(userId='me', q=query).execute()['threads']
    author_counter = {}
    os.system("rm -rf data")
    os.system("mkdir data")
    neg_filter_fn = make_unrecognized_sender_fn(flatten(query_parameters['emails'].values()) + [query_parameters['me']])
    threads = filter_unwanted_threads(threads, threads_container, neg_filter_fn)
    for thread in threads[::-1]:
        thread_msgs = gmail_utils.get_msgs_from_thread(threads_container, thread['id'])
        for msg in thread_msgs:
            sender = gmail_utils.get_sender(msg).handle
            text_msg = gmail_utils.extract_msg_text_content(msg)
            author_dir = join(DATA_ROOT, sender)
            if not os.path.exists(author_dir):
                os.mkdir(author_dir)
            try:
                count = author_counter[sender]
            except KeyError:
                count = 0
            msg_path = join(author_dir, f"{count:04d}.txt")
            with open(msg_path, 'w') as fout:
                fout.write(text_msg)
            author_counter[sender] = count + 1



