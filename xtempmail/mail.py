from __future__ import annotations
from inspect import signature
import logging
from io import BytesIO
from random import randint
import time
from typing import Any, Callable, Generator, Optional, Union
import requests


author = "krypton-byte"
logging.basicConfig(format='%(asctime)s  %(message)s', level=logging.INFO)
log = logging.getLogger('xtempmail')
log.setLevel(logging.WARNING)
# log=logging.getLogger('xtempmail')
# log.setLevel(logging.INFO)


class Mail_ID_NOTFOUND(Exception):
    pass


class Parameters(Exception):
    pass


class Extension:
    def __init__(self, ex):
        self.ex = '@' + ex

    def apply(self, text: str) -> str:
        return f"{text}{self.ex.__str__()}"

    def __repr__(self):
        return self.ex

    def __str__(self):
        return self.ex


extension = [Extension(i) for i in [
    'mailto.plus', 'fexpost.com', 'fexbox.org',
    'fexbox.ru', 'mailbox.in.ua', 'rover.info',
    'inpwa.com', 'intopwa.com', 'tofeat.com', 'chitthi.in'
]]


class event:
    """
    Event Generator
    """
    def __init__(self) -> None:
        self.messages: list[
            tuple[
                Callable[[EmailMessage], None],
                Callable[[EmailMessage], Any]
            ]
        ] = []

    def message(self, filter: Optional[Callable[[EmailMessage], Any]] = None):
        """
        :param filter: Optional
        """
        def messag(f: Union[Callable[[EmailMessage], None], None]):
            """
            :param f: Required
            """
            if callable(filter):
                sig = signature(filter)
                if sig.parameters.keys().__len__() > 1 \
                        or sig.parameters.keys().__len__() < 1:
                    raise Parameters(
                        '1 Parameters Required For filter Parameter')
                log.info(
                    f'Filter Parameter: {list(sig.parameters.keys())[0]}')
            if not callable(f):
                raise TypeError('Is not function')
            sig = signature(f)
            if sig.parameters.keys().__len__() > 1 or \
                    sig.parameters.keys().__len__() < 1:
                raise Parameters('1 Parameters Required For Callback function')
            log.info(f'Callback Parameter: {list(sig.parameters.keys())[0]}')
            self.messages.append((
                f,
                filter if callable(filter) else (lambda x: x)))
        return messag

    def on_message(self, data: EmailMessage):
        for i in self.messages:
            if i[1](data):
                i[0](data)


def warn_mail(e):
    if '@' + e.split('@')[-1] not in list(
            map(lambda x: x.__str__(), extension)):
        log.warning(f'[!] @{e.split("@")[-1]} unsupported\n')


class StrangerMail:
    """
        :param account: Email
        :param stranger: str
    """
    def __init__(self, account: Email, stranger: str) -> None:
        self.email = stranger
        self.account = account

    def send_message(
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
        return self.account.send_mail(
                        self.email,
                        subject,
                        text,
                        file,
                        filename,
                        multiply_file
                )

    def __repr__(self):
        return self.email


class Attachment:
    """
    :param mail: mail
    :param mail_id: Mail Identity
    :param attachment_id: Attachment Identity
    :param contnet_id: str
    :param name: filename
    :param size: Filesize
    """
    def __init__(
            self,
            mail,
            mail_id: int,
            attachment_id: int,
            content_id: str,
            name: str,
            size: int,
            myemail: str
    ) -> None:
        self.mail = mail
        self.mail_id = mail_id
        self.id = attachment_id
        self.content_id = content_id
        self.name = name
        self.size = size
        self.myemail = myemail

    def download(self) -> BytesIO:
        """
        :param filename: str->save as file, bool -> BytesIO
        """
        log.info(
            f'Download File, Attachment ID: {self.id} '
            f'FROM: {self.mail.__repr__()} '
            f'NAME: {self.name.__repr__()}')
        bins = requests.get(
            f'https://tempmail.plus/api/mails/{self.mail_id}'
            f'/attachments/{self.id}',
            params={
                'email': self.myemail,
                'epin': ''}
        )
        return BytesIO(bins.content)

    def save_as_file(self, filename: str) -> int:
        return open(filename, 'wb').write(self.download().getvalue())

    def __repr__(self):
        return f'<["{self.name}" size:{self.size}]>'


class EmailMessage:
    """
    :param kwargs: required
    """
    def __init__(self, **kwargs) -> None:
        self.attachments: list[Attachment] = []
        self.from_mail = StrangerMail(kwargs['to'], kwargs['from_mail'])
        for i in kwargs.pop('attachments', {}):
            attach = Attachment(
                **i,
                mail_id=kwargs['mail_id'],
                mail=kwargs['from_mail'],
                myemail=kwargs['to'])
            self.attachments.append(attach)
        self.date: str = kwargs["date"]
        self.from_is_local: bool = kwargs["from_is_local"]
        self.from_name: str = kwargs["from_name"]
        self.html: str = kwargs["html"]
        self.is_tls: bool = kwargs["is_tls"]
        self.mail_id: int = kwargs["mail_id"]
        self.message_id: str = kwargs["message_id"]
        self.result: bool = kwargs["result"]
        self.subject: str = kwargs["subject"]
        self.text: str = kwargs["text"]
        self.to: Email = kwargs["to"]

    def delete(self) -> bool:
        """
        Delete Message
        """
        return self.to.delete_message(self.mail_id)

    def __repr__(self) -> str:
        return (f'<[from:{self.to} subject:"{self.subject}"" '
                f'attachment: {self.attachments.__len__()}]>')


class Email(requests.Session):
    """
    :param name: Email username
    :param ext: Extension
    """
    def __init__(self, name: str, ext: Extension = extension[0]) -> None:
        super().__init__()
        self.email = ext.apply(name)
        self.first_id = randint(10000000, 99999999)
        self.email_id: list[int] = []
        log.info(f'Email: {self.email}')
        self.on = event()

    def get_all_message(self) -> list:
        data = []
        log.info('Get All Message')
        params: dict[str, Union[str, int]] = {
                'email': self.email,
                'first_id': self.first_id,
                'epin': ''}
        for mail in self.get(
                'https://tempmail.plus/api/mails',
                params=params).json()['mail_list']:
            data.append(self.get_mail(mail['mail_id']))
        return data

    def get_new_message(
        self,
        interval: int
    ) -> Generator[
        EmailMessage,
        EmailMessage,
        EmailMessage
    ]:
        while True:
            try:
                params: dict[str, Union[str, int]] = {
                        'email': self.email,
                        'first_id': self.first_id,
                        'epin': ''}
                for mail in self.get(
                        'https://tempmail.plus/api/mails',
                        params=params).json()['mail_list']:
                    if mail['mail_id'] not in self.email_id:
                        recv = self.get_mail(mail['mail_id'])
                        log.info(
                            f'New message from {mail["from_mail"]} '
                            f'subject: {mail["subject"].__repr__()}'
                            f' ID: {mail["mail_id"]}')
                        self.email_id.append(mail['mail_id'])
                        yield recv
            except requests.exceptions.SSLError:
                True
            time.sleep(interval)

    def get_mail(self, id: str) -> EmailMessage:
        """
        Get Message Content

        :param id: mail_id
        """
        params: dict[str, Union[str, int]] = {
                'email': self.email,
                'first_id': self.first_id,
                'epin': ''}
        to = self.get(
            f'https://tempmail.plus/api/mails/{id}',
            params=params).json()
        to['to'] = self
        log.info(f'Get Message From ID: {id.__repr__()}')
        return EmailMessage(**to)

    def delete_message(self, id: int) -> bool:
        """
        :param id: mail_id
        """
        if id in self.email_id:
            self.email_id.remove(id)
        status = self.delete(
            f'https://tempmail.plus/api/mails/{id}',
            data={
                'email': self.email,
                'epin': ''
            }).json()['result']
        if status:
            log.info('Email Message Successfully deleted')
        else:
            log.warn('Email Message not found')
            raise Mail_ID_NOTFOUND()
        return status

    def destroy(self) -> bool:
        """
        Destroy Inbox
        """
        stat = self.delete(
            'https://tempmail.plus/api/mails/',
            data={
                'email': self.email,
                'first_id': self.first_id,
                'epin': ''
            }).json().get('result')
        log.info('Inbox Destroyed')
        return stat

    def send_mail(
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
        log.info(
                f'Send Message From: {self.email.__repr__()} To: '
                f'{to.__repr__()} Subject: {subject.__repr__()} '
                f'Attachment: {bool(file or multiply_file)}')
        files: list[tuple[str, Union[tuple[str, bytes], Any]]] = []
        to = to.email if isinstance(to, StrangerMail) else to
        if file:
            if isinstance(file, str):
                if filename and isinstance(filename, str):
                    files.append((
                        'file',
                        (filename or file, open(file, 'rb').read())))
                else:
                    files.append(('file', open(file, 'rb')))
            elif isinstance(file, BytesIO):
                files.append(('file', (filename, file.getvalue())))
        for i in (multiply_file or []):
            if i.__len__() == 1:
                files.append(('file', open(i[0], 'rb')))
            elif i.__len__() > 1:
                files.append(('file', (i[0], i[1].getvalue())))
        return self.post(
                'https://tempmail.plus/api/mails/',
                data={
                    'email': self.email,
                    'to': to,
                    'subject': subject,
                    'content_type': 'text/html',
                    'text': text
                }, files=tuple(files)).json()['result']

    def listen_new_message(self, interval: int):
        """
        :param interval: required
        """
        log.info('Listen New Message')
        log.info(f'Interval: {interval}')
        for i in self.get_new_message(interval=interval):
            self.on.on_message(i)

    def __repr__(self) -> str:
        return f'<({self.email})>'

    def __str__(self):
        return self.email
