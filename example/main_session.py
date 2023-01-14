import asyncio
from xtempmail.aiomail_session import Email, Account, EmailMessage
from xtempmail.utils import EMAIL
import logging
from xtempmail.account import SqliteSession
from pathlib import Path
log = logging.getLogger('xtempmail')
log.setLevel(logging.INFO)
db_path = Path(__file__).parent / 'data.sqlite3'
if not db_path.exists():
    print(db_path)
    SqliteSession(db_path).migrate_sync()
session = Account('anjaymabarx', EMAIL.MAILTO_PLUS, database_path=db_path)
app = Email(session)
secret = app.account.secret_inbox
print('secret ', secret)


@app.on.message()
async def anu(data: EmailMessage):
    print(data)
    # await data.from_mail.send_message(
    #     'reply',
    #     'test body',
    #     multiply_file=[[
    #         'anu.py',
    #         BytesIO(b'a'*10)
    #     ]]
    # )
    await app.send_mail(secret, 'Overload', 'Overload')


async def main():
    await app.listen(2)
    await app.aclose()


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.run_forever()
