[![Unittest](https://github.com/krypton-byte/xtempmail/actions/workflows/typing.yml/badge.svg)](https://github.com/krypton-byte/xtempmail/actions/workflows/typing.yml)
[![Upload to PyPi](https://github.com/krypton-byte/xtempmail/actions/workflows/release.yml/badge.svg)](https://github.com/krypton-byte/xtempmail/actions/workflows/release.yml)
# Temporary Mail
Tempmail client for <a href='https://tempmail.plus'>tempmail.plus</a>

## Installation
```python
$ pip install git+https://github.com/krypton-byte/xtempmail
```

## Feature
<ul>
    <li> Custom Name/Mail</li>
    <li> Reply/send Message(support attachment file)</li>
    <li> Read Message (support Download attachment file)</li>
    <li> Delete message</li>
    <li> Destroy Inbox</li>
    <li> Lock Inbox</li>
    <li> Unlock Inbox</li>
    <li> Generate Secret Inbox</li>
    <li> Asynchronous</li>
    <li> Synchronous</li>
</ul>

## Example
```
example/main.py
```

## Usage Sync
```python
from xtempmail import Email, extension
import logging
from xtempmail.mail import EmailMessage, EMAIL
log = logging.getLogger('xtempmail')
log.setLevel(logging.INFO)
app = Email(name='krypton', ext=ext=EMAIL.MAILTO_PLUS))

@app.on.message()
def baca(data: EmailMessage):
    print(f"\tFrom: {data.from_mail}\n\tSubject: {data.subject}\n\tBody: {data.text}\n\tReply -> Delete")
    ok = []
    for i in data.attachments: # -> Forward attachment
        ok.append(( i.name, i.download()))
    if data.from_is_local:
        data.from_mail.send_message(data.subject, data.text, multiply_file=ok) # -> Forward message
    data.delete()  #delete message

@app.on.message(lambda msg:msg.attachments)
def get_message_media(data: EmailMessage):
    print(f'Attachment: {[i.name for i in data.attachments]}')

@app.on.message(lambda x:x.from_mail.__str__().endswith('@gmail.com'))
def getGmailMessage(data: EmailMessage):
    print(f'Gmail: {data.from_mail}')


if __name__ == '__main__':
    try:
        app.listen_new_message(1)
    except KeyboardInterrupt:
        app.destroy() #destroy inbox
```

## Usage Async
```python

import asyncio
import logging
from xtempmail.aiomail import EMAIL, EmailMessage, Email
log = logging.getLogger('xtempmail')
log.setLevel(logging.INFO)
app = Email(name='krypton', ext=EMAIL.MAILTO_PLUS)
@app.on.message()
async def baca(data: EmailMessage):
    print(f"\tFrom: {data.from_mail}\n\tSubject: {data.subject}\n\tBody: {data.text}\n\tReply -> Delete")
    ok = []
    for i in data.attachments: # -> Forward attachmen
        ok.append(( i.name, await i.download()))
    if data.from_is_local:
        await data.from_mail.send_message(data.subject, data.text, multiply_file=ok) # -> Forward message
    await data.delete()  #delete message

@app.on.message(lambda msg:msg.attachments)
async def get_message_media(data: EmailMessage):
    print(f'Attachment: {[i.name for i in data.attachments]}')

@app.on.message(lambda x:x.from_mail.__str__().endswith('@gmail.com'))
async def getGmailMessage(data: EmailMessage):
    print(f'Gmail: {data.from_mail}')

if __name__ == '__main__':
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(app.listen())
    except Exception:
        asyncio.run(app.destroy())


```

## Demo
<img src="assets/res.webp">