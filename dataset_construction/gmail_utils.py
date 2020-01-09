"""
"""
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
import email
from apiclient import errors
import re
import urllib


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
MSG_DELIMITER = "On\s*\w{3},\s*\w{3}\s*\d+,\s*\d+\s*at\s*\d+:\d+\s*(?:A|P)M,\s*.+?>\s*wrote:"


# From Google API examples
def get_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service


def ListMessagesMatchingQuery(service, user_id, query=''):
    """List all Messages of the user's mailbox matching the query.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      query: String used to filter messages returned.
      Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

    Returns:
      List of Messages that match the criteria of the query. Note that the
      returned list contains Message IDs, you must use get with the
      appropriate ID to get the details of a Message.
    """
    try:
        response = service.users().messages().list(userId=user_id,
                                                   q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, q=query,
                                                       pageToken=page_token).execute()
            messages.extend(response['messages'])

        return messages
    except (errors.HttpError, Exception):
        print('An error occurred: %s' % Exception)


def GetMessage(service, user_id, msg_id):
    """Get a Message with given ID.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      msg_id: The ID of the Message required.

    Returns:
      A Message.
    """
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        print('Message snippet: %s' % message['snippet'])

        return message
    except (errors.HttpError, Exception) as e:
        print('An error occurred: %s' % e)


def GetMimeMessage(service, user_id, msg_id):
    """Get a Message and use it to create a MIME Message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      msg_id: The ID of the Message required.

    Returns:
      A MIME Message, consisting of data from Message.
    """
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id,
                                                 format='raw').execute()

        # print('Message snippet: %s' % message['snippet'])

        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

        mime_msg = email.message_from_string(msg_str)

        return mime_msg
    except (errors.HttpError, Exception) as e:
        print('An error occurred: %s' % e)


class GmailMessage(object):
    def __init__(self, author, date, payload):
        self.author = author
        self.date = date
        self.payload = payload

    @property
    def author_handle(self):
        return self.author.split()[1].split("@")[0][1:]

    def __str__(self):
        return f"[{self.author} -- {self.date}\n\n{self.payload}]"

    def __repr__(self):
        return self.__str__()


def decode_raw_msg(raw_msg):
    l = base64.urlsafe_b64decode(raw_msg['raw'])
    m = email.message_from_string(l.decode("utf-8"))
    return m


def extract_msg(msg):
    m = decode_raw_msg(msg)
    msg_author = m['From']
    msg_date = m["Date"]
    msg_payload = m.get_payload()[0].get_payload()
    depth = 0
    while type(msg_payload) is list:
        msg_payload = msg_payload[0].get_payload()
        depth += 1
    if depth > 0:
        print(f"WARNING: Payload had depth of {depth}")
    cutoff_match = re.search(MSG_DELIMITER, msg_payload, flags=re.DOTALL)
    if not cutoff_match:
        print("WARNING: no cutoff match")
        msg_slice = msg_payload
    else:
        cutoff = cutoff_match.span()[0]
        msg_slice = msg_payload[:cutoff]
    return GmailMessage(msg_author, msg_date, urllib.parse.unquote(re.sub("=(\w{2})", "%\g<1>", msg_slice)))


def get_msg_ids_from_thread(threads_container, thread_id):
    return threads_container.get(userId='me', id=thread_id).execute()['messages']
