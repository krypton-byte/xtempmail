import asyncio
import logging
from xtempmail.aiomail import EMAIL, EmailMessage, Email
log = logging.getLogger('xtempmail')
log.setLevel(logging.INFO)
app = Email(name='krypton', ext=EMAIL.MAILTO_PLUS)

@app.on.message()
async def baca(data: EmailMessage):
    print(f"\tfrom: {data.from_mail}\n\tsubject: {data.subject}\n\tpesan: {data.text}\n\tReply -> Hapus")
    ok = []
    for i in data.attachments: # -> Forward attachment
        ok.append(( i.name, i.download()))
    if data.from_is_local:
        await data.from_mail.send_message(data.subject, data.text, multiply_file=ok) # -> Forward message
    await data.delete()  #delete message

@app.on.message(lambda msg:msg.attachments)
async def get_message_media(data: EmailMessage):
    print(f'attachment: {[i.name for i in data.attachments]}')

@app.on.message(lambda x:x.from_mail.__str__().endswith('@gmail.com'))
async def getGmailMessage(data: EmailMessage):
    print(f'Gmail: {data.from_mail}')

if __name__ == '__main__':
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(app.listen())
    except Exception:
        asyncio.run(app.destroy())
