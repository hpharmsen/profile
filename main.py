import sys
from imap_tools import MailBox, AND

EMAIL_UN = 'hp@harmsen.nl'
EMAIL_PW = 'tvtogxoflbjtgbjp'
CHUNKSIZE = 5
CHUNKNUM = 50
FROM = 'douwe.osinga@gmail.com'

def get_mails():
    # Get date, subject and body len of all emails from INBOX folder
    with MailBox('imap.gmail.com').login(EMAIL_UN, EMAIL_PW) as mailbox:
        #for f in mailbox.folder.list():
        #    print(f)
        mailbox.folder.set('[Gmail]/All Mail')
        for chunk in range(CHUNKNUM):
            cur_slice = slice(chunk*CHUNKSIZE, (chunk+1)*CHUNKSIZE)
            for msg in mailbox.fetch(AND(from_=FROM), limit=cur_slice):
                text = msg.text or msg.html
                if text.count('> wrote:'):
                    text = text.split('> wrote:')[0].rsplit('\n', 1)[0]
                lines = text.split('\n')
                text = '\n'.join([line for line in lines if not line.startswith('>')])
                print(text)
                yield(msg.date, msg.subject, text)


if __name__ == "__main__":
    for msg in get_mails():
        print(msg)

