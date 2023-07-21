# GPT biography generator

## Introduction

Project that uses GPT-3.5-turbo to generate biographies of people based on the e-mails those people have sent to your GMail account.

## Installation

1. Install dependencies:
```bash
python -m pip install -r requirements.txt
```
2. Create an OpenAI acccount [here](chat.openai.com/auth/login)
3. Create an OpenAI api key [here](https://beta.openai.com/account/api-keys)
4. Create an .env file with the following:
```
OPENAI_API_KEY=your_openai_api_key
EMAIL_UN=your_email
EMAIL_PW=gmail_app_password
PERSON=Name of person you want to make a bio of
```

## Usage
```bash
python main.py
```