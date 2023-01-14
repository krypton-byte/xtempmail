#!/usr/bin/env python3
import argparse
import asyncio
from sqlalchemy import select, and_
from .aiomail_session import Email, UserUnavailable
from .models import User, Mailbox, Base
from .utils import EMAIL
from .account import Account, SqliteSession
from prettytable import PrettyTable
from .logger import log
import logging
arg = argparse.ArgumentParser()
subparser = arg.add_subparsers(help='Actions', dest='command')
send = subparser.add_parser('send')
create = subparser.add_parser('create')
dump = subparser.add_parser('dump')
migrate = subparser.add_parser('migrate')
table = dump.add_subparsers(help='Table', dest='table')
user = table.add_parser('user')
user.add_argument('--provider', choices=[i.value for i in EMAIL])
inbox = table.add_parser('inbox')
inbox.add_argument('--from', type=str, dest='from_mail')
inbox.add_argument('--to', type=str)
inbox.add_argument('--count', action='store_true')
sent = table.add_parser('sent')
sent.add_argument('--from', type=str, dest='from_mail')
sent.add_argument('--to', type=str)
arg.add_argument(
    '--log-level',
    default='notset',
    choices=[
        'debug',
        'critical',
        'error',
        'fatal',
        'warning',
        'info',
        'notset'
    ]
)
arg.add_argument(
    '--database',
    help='path of database (sqlite)',
    default='test.sqlite3',
    type=str
)
create.add_argument(
    '--provider',
    choices=[i.value for i in EMAIL],
    required=True
)
create.add_argument(
    '--username',
    type=str,
    required=True
)
send.add_argument(
    '--from',
    type=str,
    dest='from_mail',
    required=True
)
send.add_argument('--to', type=str, required=True)
send.add_argument('--subject', type=str, required=True)
send.add_argument('--body', type=str, required=True)
send.add_argument('attachments', type=str, nargs='*')
parse = arg.parse_args()
log.setLevel(getattr(logging, parse.log_level.upper()))


async def main():
    db = SqliteSession(parse.database)
    if parse.command == 'create':
        account = Account(
            username=parse.username,
            provider=EMAIL(parse.provider),
            database_path=parse.database
        )
        await account.create()
        print(f'{account.full} created')
    elif parse.command == 'send':
        username, provider = parse.from_mail.split('@')
        account = Account(
            username=username,
            provider=EMAIL(provider),
            database_path=parse.database
        )
        email = Email(account)
        resp = await email.send_mail(
            parse.to,
            parse.subject,
            parse.body,
            multiply_file=[(i,) for i in parse.attachments]
        )
        if not resp:
            print('[x] Not valid email destination')
        await email.aclose()
    elif parse.command == 'dump':
        if parse.table == 'user':
            async with db.session() as session:
                async with session.begin():
                    pt = PrettyTable()
                    pt.field_names = ['username', 'provider', 'pin', 'expired']
                    cnt = 0
                    op = select(User)
                    if parse.provider:
                        op = op.where(User.provider == parse.provider)
                    for i in (await session.execute(op)).scalars():
                        pt.add_row([i.username, i.provider, i.epin, i.expired])
                        cnt += 1
                    pt.add_row(['Total', '', '', cnt])
                    pt.align = "l"
                    print(pt.get_string())

        elif parse.table == 'inbox':
            pt = PrettyTable()
            pt.field_names = ['id', 'user_id', 'from', 'subject', 'body']
            if parse.to:
                username, provider = parse.to.split('@')
            async with db.session() as session:
                async with session.begin():
                    try:
                        op = select(Mailbox)
                        if parse.from_mail and parse.to:
                            op = op.where(and_(
                                Mailbox.from_ == parse.from_mail,
                                Mailbox.user_id == await Account(
                                    username,
                                    EMAIL(provider),
                                    parse.database
                                ).get_id()))
                        elif parse.to:
                            op = op.where(Mailbox.user_id == await Account(
                                username,
                                EMAIL(provider),
                                parse.database
                            ).get_id())
                        elif parse.from_mail:
                            op = op.where(Mailbox.from_ == parse.from_mail)
                        data = await session.execute(op)
                        for i in data.scalars():
                            pt.add_row([
                                i.id,
                                i.user_id,
                                i.from_,
                                i.subject,
                                i.body
                            ])
                    except UserUnavailable:
                        pass
                    print(pt.get_string())

    elif parse.command == 'migrate':
        async with db.schema.begin() as session:
            await session.run_sync(Base.metadata.create_all)

asyncio.run(main())
