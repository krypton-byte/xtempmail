import __future__
from io import BytesIO
from random import randint
import sys
import time
from typing import Generator, Union
import requests

author = "krypton-byte"

class Extension:
    def __init__(self, ex):
        self.ex = '@'+ex
    def __repr__(self):
        return self.ex
    def __str__(self):
        return self.ex

extension = [ Extension(i) for i in ['mailto.plus','fexpost.com','fexbox.org','fexbox.ru','mailbox.in.ua','rover.info','inpwa.com','intopwa.com','tofeat.com','chitthi.in']]

class event:
    def __init__(self) -> None:
        self.messages = []
    def message(self, filter=None):
        def messag(f):
            self.messages.append((f,filter if callable(filter) else (lambda x:x)))
        return messag
    def on_message(self, data):
        for i in self.messages:
            if i[1](data):
                i[0](data)

def warn_mail(e):
    if '@'+e.split('@')[-1] not in list(map(lambda x:x.__str__(), extension)):
        sys.stderr.write(f'[!] @{e.split("@")[-1]} unsupported\n')
        sys.stderr.flush()

class StrangerMail:
    def __init__(self, account, stranger: str) -> None:
        self.email = stranger
        self.account:Email = account
    def send_message(self, subject: str, text: str, file=None, filename='file', multiply_file=[]):
        return self.account.send_mail(self.email, subject, text, file, filename, multiply_file)
    def __repr__(self):
        return self.email

class Attachment:
    def __init__(self, mail, mail_id: int, attachment_id:int, content_id: str, name: str, size:int ) -> None:
        self.mail = mail
        self.mail_id = mail_id
        self.id = attachment_id
        self.content_id = content_id
        self.name = name
        self.size = size
    def download(self, filename=False)->Union[BytesIO, None]:
        """
        :param filename: str->save as file, bool -> BytesIO
        """
        bins=requests.get(f'https://tempmail.plus/api/mails/{self.mail_id}/attachments/{self.id}',params={'email':self.mail, 'epin':''})
        if isinstance(filename, str):
            open(filename,'wb').write(bins.content)
        else:
            return BytesIO(bins.content)
    def __repr__(self):
        return f'<["{self.name}" size:{self.size}]>'

class EmailMessage:
    def __init__(self, **kwargs) -> None:
        self.attachments=[]
        kwargs['from_mail'] = StrangerMail(kwargs['to'], kwargs['from_mail'])
        for i in kwargs.pop('attachments',{}):
            attach = Attachment(**i, mail_id=kwargs['to'].email, mail=kwargs['from_mail'])
            self.attachments.append(attach)
        for key, val in kwargs.items():
            setattr(self, key, val)
    def delete(self)->bool:
        return self.to.delete_message(self.mail_id)
    def __repr__(self) -> str:
        return f'<[from:{self.to} subject:"{self.subject}"" attachment: {self.attachments.__len__()}]>'
        
class Email(requests.Session):
    def __init__(self, name:str, ext:Extension = extension[0], interval = 1) -> None:
        super().__init__()
        self.interval = interval
        self.email = name+ext.__str__()
        self.first_id = randint(10000000, 99999999)
        self.email_id = []
        self.on = event()

    def get_all_message(self)->list:
        data = []
        for mail in self.get(f'https://tempmail.plus/api/mails',params={'email':self.email, 'first_id':self.first_id, 'epin':''}).json()['mail_list']:
            data.append(self.get_mail(mail['mail_id']))
        return data

    def get_new_message(self)->Generator:
        while True:
            try:
                for mail in self.get(f'https://tempmail.plus/api/mails',params={'email':self.email, 'first_id':self.first_id, 'epin':''}).json()['mail_list']:
                    if mail['mail_id'] not in self.email_id:
                        recv=self.get_mail(mail['mail_id'])
                        self.email_id.append(mail['mail_id'])
                        yield recv
            except requests.exceptions.SSLError:
                True
            time.sleep(self.interval)

    def get_mail(self, id: str)->EmailMessage:
        """
        Get Message Content
        :param id:mail_id
        """
        to=self.get(f'https://tempmail.plus/api/mails/{id}', params={'email':self.email, 'first_id':self.first_id, 'epin':''}).json()
        to['to'] = self
        return EmailMessage(**to)

    def delete_message(self, id: int)->bool:
        """
        :param id: mail_id
        """
        id in self.email_id and self.email_id.remove(id)
        return self.delete(f'https://tempmail.plus/api/mails/{id}', data={'email':self.email, 'epin':''}).json()['result']

    def destroy(self)->bool:
        """
        Destroy Inbox
        """
        return self.delete('https://tempmail.plus/api/mails/', data={'email':self.email, 'first_id':self.first_id, 'epin':''}).json().get('result')

    def send_mail(self, to: str, subject: str, text: str, file = None, filename = 'file',multiply_file = [])->bool:
        """
        :param to: Email [str | StrangerMail] -> Not Support external email (gmail, yahoo, etc)
        :param subject: str
        :param text: str
        :param file: filename/file path
        :param filename: str
        :param multiply_file: tuple (BytesIO|path, str)
        """
        warn_mail(to)
        files = []
        to = to.email if isinstance(to, StrangerMail) else to
        if file:
            if isinstance(file, str):
                if filename and isinstance(filename, str):
                    files.append(('file',(filename,open(file,'rb').read())))
                else:
                    files.append(('file',open(file,'rb')))
            elif isinstance(file, BytesIO):
                files.append(('file',(filename,file.getvalue())))
        for i in multiply_file:
            if i.__len__() == 1:
                files.append(('file',open(i[0],'rb')))
            elif i.__len__() > 1:
                x=('file', (i[0],i[1].getvalue()))
                files.append(x)
        return self.post('https://tempmail.plus/api/mails/', data={'email': self.email,'to': to,'subject': subject,'content_type': 'text/html','text': text},files=tuple(files)).json()['result']

    def listen_new_message(self):
        for i in self.get_new_message():
            self.on.on_message(i)

    def __repr__(self) -> str:
        return f'<({self.email})>'

    def __str__(self):
        return self.email