import os

import openai
from imap_tools import MailBox, AND, OR
from dotenv import load_dotenv

from promptreader import PromptReader


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


def get_mails(name):
    # Get date, subject and body len of all emails from INBOX folder
    pred = AND(from_=name)
    with MailBox('imap.gmail.com').login(os.environ['EMAIL_UN'], os.environ['EMAIL_PW']) as mailbox:
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


def get_facts(name: str, max_facts=100):
    file_name = name.replace(" ", "_").lower() + "_facts.txt"

    if os.path.exists(file_name):
        facts = []
        with open(file_name) as f:
            for line in f:
                facts.append(tuple(line.split("|")))
    else:
        facts = find_facts(name, max_facts)
        with open(file_name, "w") as f:
            for fact in facts:
                f.write(f"{fact[0]} | {fact[1]} | {fact[2]}\n")
    return facts


def find_facts(name: str, max_facts=100):
    prompts = PromptReader(locals())
    facts = set()
    for info, subject, body in get_mails(name):
        body = body[:8000]
        prompt = f"{prompts['PROMPT_EXTRACTION'].format(*locals())}\nsubject: {subject}\n\n{body}"
        res = call_open_ai([{"role": "system", "content": prompts['SYSTEM_PROMPT_EXTRACTION']},
                            {"role": "user", "content": prompt}])
        for line in res.splitlines():
            bits = line.split('|')
            if len(bits) == 3:
                bits = [bit.strip() for bit in bits]
                subject, predicate, obj = bits
                print(subject, predicate, obj)
                facts.add((subject, predicate, obj))
        if len(facts) >= max_facts:
            break
    return facts


def create_profile(name, facts):
    prompts = PromptReader(locals())
    l = locals()
    prompt = prompts['PROMPT_PROFILE'] + "\n\n"
    prompt += "".join([f"{fact[0]} | {fact[1]} | {fact[2]}" for fact in facts])
    profile = call_open_ai([{"role": "system", "content": prompts['SYSTEM_PROMPT_PROFILE']},
                        {"role": "user", "content": prompt}])
    file_name = name.replace(" ", "_").lower() + "_profile.txt"
    with open(file_name, "w") as f:
        f.write(profile)
    return profile


if __name__ == "__main__":
    load_dotenv()
    openai.api_key = os.environ["OPENAI_API_KEY"]

    name = os.environ["PERSON"]

    facts = get_facts(name)
    print(f"using {len(facts)} facts")

    profile = create_profile(name, facts)
    print(profile)
