import json
from dataset_construction import gmail_utils
from os.path import join
import os
from constants import DATA_ROOT


def build_query(filter_str, email_addresses, start_date_formatted=None):
    after_clause = " AND after:" + start_date_formatted if start_date_formatted else ''
    query = ' OR '.join([filter_str + x for x in email_addresses]) + after_clause
    return query


if __name__ == "__main__":
    with open("query_parameters.json", 'r') as fin:
        query_parameters = json.load(fin)
    service = gmail_utils.get_service()
    threads_container = service.users().threads()
    query = build_query(query_parameters['filter_str'],
                        query_parameters['emails'].values(),
                        query_parameters['start_date'])
    threads = threads_container.list(userId='me', q=query).execute()['threads']
    author_counter = {}
    for thread in threads[:1]:
        thread_msgs = gmail_utils.get_msg_ids_from_thread(threads_container, thread['id'])
        for msg in thread_msgs:
            print(gmail_utils.extract_msg_text_content(msg))
            # author_dir = join(DATA_ROOT, author_handle)
            # if not os.path.exists(author_dir):
            #     os.mkdir(author_dir)
            # try:
            #     count = author_counter[author_handle]
            # except KeyError:
            #     count = 0
            # msg_path = join(author_dir, f"{count:04d}.txt")
            # with open(msg_path, 'w') as fout:
            #     fout.write(msg_parsed.payload)



