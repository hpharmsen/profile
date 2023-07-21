import datetime
import os

import openai
from imap_tools import MailBox, AND, OR

EMAIL_UN = 'hp@harmsen.nl'
EMAIL_PW = 'tvtogxoflbjtgbjp'
CHUNKSIZE = 5
CHUNKNUM = 50
FROM = 'mll@lemmens.net'
NAME = "Martijn Lemmens"

# FROM = ("michael.blok@alumni.insead.edu",
#         "mhhblok@gmail.com",
#         "michael@snappet.org",
#         "michael@anderswinst.com")
# NAME = "Michael Blok"

SYSTEM_PROMPT_EXTRACTION = (
    "You are an email processor. Your job is to extract facts from emails as triplets.\n"
    "A triplet is a subject, a predicate and an object. Return them as: subject | predicate | object\n"
    "Output only in English.")

PROMPT_EXTRACTION = (
    f"Below you'll find an email from {NAME}. If that email is not in English, translate it to English\n"
    f"Then extract the facts from the email about {NAME}. Represent each fact as a triple of "
    "subject, predicate and object. For example, if the email contains the fact "
    "'John is a data scientist', the triple would be "
    "(John | is | data scientist)'. List all the facts, one per line.\n"
    "IMPORTANT: Don't return sentences, only triples.\n"
    "Don't return the same fact twice.\n\n")

SYSTEM_PROMPT_PROFILE = ("Your job is to take a list of facts and create a profile of the person. This profile "
                         "should be a detailed and easy to read story about this person.\n")
PROMPT_PROFILE = (f"Below you'll find a list of facts about {NAME}. Create a profile for {NAME}.\n"
                  "The input is a list of attributes. Each attribute is a triplet of \n"
                  "subject, predicate and object. For example, if the person is a data scientist, the triplet would be \n"
                  "(John | is | data scientist)'\n\n"
                  "Stick to the facts, don't make things up.\n")


def call_open_ai(messages, tries=0):
    try:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0.1, )
    except openai.error.OpenAIError:
        if tries > 5:
            raise
        return call_open_ai(messages, tries=tries + 1)
    choices = completion.get("choices")
    if not choices:
        return None
    return choices[0]["message"]["content"]


def get_mails(count=25):
    # Get date, subject and body len of all emails from INBOX folder
    if isinstance(FROM, (list, tuple)):
        pred = OR(*[AND(from_=from_) for from_ in FROM])
        #pred = OR(AND(from_="douwe.osinga@gmail.com"), AND(from_="douwe@neptyne.com"))
    else:
        pred = AND(from_=FROM)
    with MailBox('imap.gmail.com').login(EMAIL_UN, EMAIL_PW) as mailbox:
        mailbox.folder.set('[Gmail]/All Mail')
        # for chunk in range(CHUNKNUM):
        #     cur_slice = slice(chunk * CHUNKSIZE, (chunk + 1) * CHUNKSIZE)
        for msg in mailbox.fetch(pred, reverse=True):
                text = msg.text or msg.html
                if text.count('> wrote:'):
                    text = text.split('> wrote:')[0].rsplit('\n', 1)[0]
                lines = text.split('\n')
                text = '\n'.join([line for line in lines if not line.startswith('>')])
                print(">>", msg.date_str)
                yield msg.date, msg.subject, text
                count -= 1
                if count == 0:
                    return


def get_facts(max_facts=100):
    facts = set()
    for info, subject, body in get_mails():
        if len(body) > 8000:
            body = body[:8000]
        prompt = PROMPT_EXTRACTION + "subject:" + subject + "\n\n" + body
        res = call_open_ai([{"role": "system", "content": SYSTEM_PROMPT_EXTRACTION},
                            {"role": "user", "content": prompt}])
        for line in res.splitlines():
            bits = line.split('|')
            if len(bits) == 3:
                bits = [bit.strip() for bit in bits]
                subject, predicate, obj = bits
                print(subject, "|", predicate, "|", obj)
                facts.add((subject, predicate, obj))
        if len(facts) >= max_facts:
            break
    return facts


def create_profile(facts):
    prompt = PROMPT_PROFILE + "\n".join([f"{fact[0]} | {fact[1]} | {fact[2]}" for fact in facts])
    res = call_open_ai([{"role": "system", "content": SYSTEM_PROMPT_PROFILE},
                        {"role": "user", "content": prompt}])
    return res


if __name__ == "__main__":
    file_name = NAME.replace(" ", "_").lower() + ".txt"

    if os.path.exists(file_name):
        facts = []
        with open(file_name) as f:
            for line in f:
                facts.append(tuple(line.split("|")))
    else:
        facts = get_facts()
        with open(file_name, "w") as f:
            for fact in facts:
                f.write(f"{fact[0]} | {fact[1]} | {fact[2]}\n")
    print(f"using {len(facts)} facts")

    profile = create_profile(facts)
    with open(file_name.replace(".txt", "_profile.txt"), "w") as f:
        f.write(profile)
