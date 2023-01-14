from __future__ import annotations
import time
from sqlalchemy import update, and_
from dataclasses import dataclass
from datetime import datetime
from inspect import signature
from asyncio.tasks import Task, ensure_future
from io import BytesIO
import asyncio
from os.path import getsize
from typing import Awaitable, Callable, Union, Optional, Any, List
import httpx
from random import randint
from .utils import err_code, extension, isoformat_translate
from .logger import log
from .error import (
    Parameters,
    InvalidPIN,
    Mail_ID_NOTFOUND
)
from .account import Account, UserUnavailable
from .abstract_models import (
    AttachmentBase,
    StrangerMailBase,
    EmailMessageBase,
    EventBase,
    EmailBase
)
from .models import (
    Attachment as AttachmentTable,
    AttachmentSent,
    Sent,
    User
)


class Event(EventBase):
    def __init__(self, account: Account, workers: int = 30) -> None:
        self.workers = workers
        self.account = account
        self.func: list[
            tuple[
                Callable[[EmailMessage], Any],
                Union[Callable[[EmailMessage], Any], None]
            ]
        ] = []
        self.futures: list[Task] = []

    def message(
        self,
        filter: Optional[Callable[[EmailMessage], Any]] = None
    ) -> Callable[[Union[Callable[[EmailMessage], None],  Any]], Any]:
        def run(f: Union[Callable[[EmailMessage], None],  Any]):
            if callable(filter):
                sig = signature(filter)
                if sig.parameters.keys().__len__() > 1 \
                        or sig.parameters.keys().__len__() < 1:
                    raise Parameters(
                        '1 Parameters Required For filter Parameter')
                log.debug(
                    f'Filter Parameter: {list(sig.parameters.keys())[0]}')
            if not callable(f):
                raise TypeError('Is not function')
            sig = signature(f)
            if sig.parameters.keys().__len__() > 1 or \
                    sig.parameters.keys().__len__() < 1:
                raise Parameters('1 Parameters Required In Callback function')
            log.debug(f'Callback Parameter: {list(sig.parameters.keys())[0]}')
            self.func.append((f, filter))
        return run

    async def on_message(self, data: EmailMessage):
        log.debug('Message Received From %s ' % data.from_mail.email)
        if data.is_new:
            await self.account.push_inbox(data)
            if data.attachments:
                async with self.account.session() as session:
                    async with session.begin():
                        for attachment in data.attachments:
                            session.add(AttachmentTable(
                                mailbox_id=data.mail_id,
                                attachment_id=attachment.attachment_id,
                                size=attachment.size,
                                name=attachment.name
                            ))
                        await session.commit()
        for i in self.func:
            if not i[1] or (i[1] and i[1](data)):
                self.futures.append(asyncio.ensure_future(i[0](data)))
                if self.futures.__len__() > self.workers:
                    for i in self.futures:
                        if i.done():
                            self.futures.remove(i)
                    if self.futures.__len__() > self.workers:
                        await asyncio.gather(*self.futures)


@dataclass
class Attachment(AttachmentBase):
    mail: str
    mail_id: int
    attachment_id: int
    content_id: str
    name: str
    size: int
    myemail: Email

    async def download(self) -> BytesIO:
        log.debug(
            f'Download File, Attachment ID: {self.id} '
            f'FROM: {self.mail.__repr__()} '
            f'NAME: {self.name.__repr__()}')
        bins = await self.myemail.get(
            f'https://tempmail.plus/api/mails/{self.mail_id}'
            f'/attachments/{self.id}'
        )
        return BytesIO(bins.content)

    @property
    def url(self):
        return (
            f'https://tempmail.plus/api/mails/{self.mail_id}'
            f'/attachments/{self.id}')

    async def save_as_file(self, filename: str) -> int:
        return open(filename, 'wb').write((await self.download()).getvalue())

    def __repr__(self):
        return f'<["{self.name}" size:{self.size}]>'


@dataclass
class StrangerMail(StrangerMailBase):
    account: Email
    email: str

    async def send_message(
            self,
            subject: str,
            text: str,
            file: Optional[str] = None,
            filename: Optional[str] = None,
            multiply_file: Optional[list] = []) -> bool:
        """
        :param subject: required
        :param text: required
        :param file: Optional
        :param filename: Optional
        :param multiply_file: Optional
        """
        return await self.account.send_mail(
                        self.email,
                        subject,
                        text,
                        file,
                        filename,
                        multiply_file
                )

    def __repr__(self):
        return self.email


class EmailMessage(EmailMessageBase):
    """
    :param kwargs: required
    """
    def __init__(self, is_new: bool, **kwargs) -> None:
        self.attachments: List[Attachment] = []
        self.from_mail = StrangerMail(kwargs['to'], kwargs['from_mail'])
        for i in kwargs.pop('attachments', {}):
            attach = Attachment(
                **i,
                mail_id=kwargs['mail_id'],
                mail=kwargs['from_mail'],
                myemail=kwargs['to'])
            self.attachments.append(attach)
        self.date: datetime = datetime.fromisoformat(
            isoformat_translate(kwargs["date"]))
        self.from_is_local: bool = kwargs["from_is_local"]
        self.from_name: str = kwargs["from_name"]
        self.is_new = is_new
        self.html: str = kwargs["html"]
        self.is_tls: bool = kwargs["is_tls"]
        self.mail_id: int = kwargs["mail_id"]
        self.message_id: str = kwargs["message_id"]
        self.result: bool = kwargs["result"]
        self.subject: str = kwargs["subject"]
        self.text: str = kwargs["text"]
        self.to: Email = kwargs["to"]

    async def delete(self) -> bool:
        """
        Delete Message
        """
        return await self.to.delete_message(self.mail_id)

    def __repr__(self) -> str:
        return (f'<[from:{self.to} subject:"{self.subject}"" '
                f'attachment: {self.attachments.__len__()}]>')


def warn_mail(e):
    if '@' + e.split('@')[-1] not in list(
            map(lambda x: x.__str__(), extension)):
        log.warning(f'[!] @{e.split("@")[-1]} unsupported\n')


class Email(httpx.AsyncClient, EmailBase):
    def __init__(
        self,
        account: Account,
        workers: int = 40
    ):
        super().__init__(timeout=60)
        try:
            account.login_sync()
        except UserUnavailable:
            account.create_sync()
        self.email = account.full
        self.account = account
        self.on = Event(account, workers)
        self.first_id = randint(10000000, 99999999)
        self.emails_id: list[int] = []
        self.params: dict[str, Union[str, int]] = {
            'email': self.email,
            'first_id': self.first_id,
            'epin': account.pin
        }
        log.debug(f'Email: {self.email}')

    async def get_all_message(self) -> tuple[EmailMessage]:
        data: list[Awaitable] = []
        mail_ = (await self.get('https://tempmail.plus/api/mails')).json()
        if mail_.get('err'):
            ob = err_code(mail_['err']['code'])
            if ob:
                raise ob(mail_['err']['msg'])
        for mail in mail_['mail_list']:
            data.append(self.get_mail(mail['mail_id'], is_new=mail_['is_new']))
        return await asyncio.gather(*data)

    async def get_new_message(self) -> tuple[EmailMessage]:
        mes: list[Task] = []
        for mail in (await self.get(
                'https://tempmail.plus/api/mails',
                )).json()['mail_list']:
            if mail['mail_id'] not in self.emails_id:
                mes.append(ensure_future(
                    self.get_mail(mail['mail_id'], is_new=mail['is_new'])))
                self.emails_id.append(mail['mail_id'])
        return await asyncio.gather(*mes)

    async def listen(
        self,
        interval: int = 1
    ):
        futures: list[Task] = []
        while True:
            futures.append(ensure_future(
                asyncio.gather(*[
                        self.on.on_message(i) for i in (
                            await self.get_new_message())])))
            await asyncio.sleep(interval)
            for i in futures:
                if i.done():
                    futures.remove(i)

    def run_forever(self, interval: int):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.listen(interval))

    async def get_mail(self, id: str, is_new: bool) -> EmailMessage:
        """
        Get Message Content
        :param id: mail_id
        """
        to = (await self.get(
            f'https://tempmail.plus/api/mails/{id}',
            )).json()
        to['to'] = self
        return EmailMessage(**to, is_new=is_new)

    async def delete_message(self, id: int) -> bool:
        """
        :param id: mail_id
        """
        if id in self.emails_id:
            self.emails_id.remove(id)
        status = (await self.delete(
            f'https://tempmail.plus/api/mails/{id}')).json()['result']
        if status:
            log.debug('Email Message Successfully deleted')
        else:
            log.warn('Email Message not found')
            raise Mail_ID_NOTFOUND()
        return status

    async def destroy(self) -> bool:
        """
        Destroy Inbox
        """
        stat = (await self.delete(
            'https://tempmail.plus/api/mails/')).json().get('result')
        log.debug('Inbox Destroyed')
        return stat

    async def send_mail(
            self,
            to: str,
            subject: str,
            text: str,
            file: Optional[str] = None,
            filename: Optional[str] = None,
            multiply_file: Optional[list] = []
    ) -> bool:
        """
        :param to: Email [str | StrangerMail] -> Not Support external email\
        (Gmail, Yahoo, etc.)
        :param subject: str
        :param text: str
        :param file: filename/file path
        :param filename: str
        :param multiply_file: tuple (BytesIO|path, str)
        """
        warn_mail(to)
        log.debug(
                f'Send Message From: {self.email.__repr__()} To: '
                f'{to.__repr__()} Subject: {subject.__repr__()} '
                f'Attachment: {bool(file or multiply_file)}')
        files: list[tuple[str, Union[tuple[str, bytes], Any]]] = []
        to: str = to.email if isinstance(to, StrangerMail) else to
        async with self.account.session() as session:
            async with session.begin():
                sent = Sent(
                    to=to,
                    from_id=await self.account.get_id(),
                    subject=subject,
                    body=text
                )
                session.add(sent)
                await session.commit()
                await session.flush()
                async with self.account.session() as session2:
                    async with session2.begin():
                        if file:
                            if isinstance(file, str):
                                if filename and isinstance(filename, str):
                                    files.append((
                                        'file',
                                        (
                                            filename or file,
                                            open(file, 'rb').read()
                                        )))
                                    session2.add(AttachmentSent(
                                        path=file,
                                        size=getsize(file),
                                        sent_id=sent.id
                                    ))
                                else:
                                    files.append(('file', open(file, 'rb')))
                            elif isinstance(file, BytesIO):
                                files.append((
                                    'file',
                                    (filename, file.getvalue())
                                ))
                                session2.add(AttachmentSent(
                                        path=filename,
                                        size=getsize(file),
                                        sent_id=sent.id
                                ))
                        for i in (multiply_file or []):
                            if i.__len__() == 1:
                                files.append(('file', open(i[0], 'rb')))
                                session2.add(AttachmentSent(
                                        path=i[0],
                                        size=getsize(i[0]),
                                        sent_id=sent.id
                                    ))
                            elif i.__len__() > 1:
                                files.append(('file', (i[0], i[1].getvalue())))
                                session2.add(AttachmentSent(
                                        path=i[0],
                                        size=i[1].getbuffer().nbytes,
                                        sent_id=sent.id
                                    ))
                        await session2.commit()
                return (await self.post(
                        'https://tempmail.plus/api/mails/',
                        data={
                            'email': self.email,
                            'to': to,
                            'subject': subject,
                            'content_type': 'text/html',
                            'text': text
                        }, files=tuple(files))).json()['result']

    async def secret_address(self) -> str:
        if await self.protected():
            raise InvalidPIN()
        em = (await self.get(
            'https://tempmail.plus/api/box/hidden'
            )).json()['email']
        await self.account.set_secret_inbox(em)
        return em

    async def protected(self) -> bool:
        x = (await self.get('https://tempmail.plus/api/mails')).json()
        if x.get('err'):
            f = err_code(x['err']['code'])
            if f == InvalidPIN:
                return True
        return False

    async def Lock_Inbox(self, pin: str, duration_minutes: int = 60) -> bool:
        if self.protected:
            raise InvalidPIN()
        cp_params = self.params.copy()
        cp_params.update({
            'ttl_minutes': duration_minutes,
            'pin': pin
        })
        if (await self.post(
            'https://tempmail.plus/api/box',
            data=cp_params
        )).json()['result']:
            self.params['epin'] = pin
            async with self.account.session() as session:
                async with session.begin():
                    await session.execute(
                        update(User).where(and_(
                            User.username == self.account.username,
                            User.provider == self.account.provider.value
                        )).values(
                            epin=pin,
                            expired=int(time.time() + duration_minutes)
                        )
                    )
                    await self.account.set_pin(pin)
            return True
        return False

    async def Delete_Lock(self) -> bool:
        if self.protected:
            raise InvalidPIN()
        return await self.Lock_Inbox('', 0)

    def __repr__(self) -> str:
        return f'<({self.email})>'

    def __str__(self):
        return self.email
