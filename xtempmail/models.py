import asyncio
from sqlalchemy import Column, ForeignKey, func
from sqlalchemy import (Integer, String, DateTime, Boolean)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine
Base = declarative_base()


class User(Base):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    provider = Column(String(15))
    epin = Column(String, default='')
    expired = Column(Integer, default=0)
    secret_inbox = Column(String)
    mailbox = relationship('Mailbox', backref='user')
    sent = relationship('Sent', backref='from_user')


class Mailbox(Base):
    __tablename__ = 'Mailbox'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.id'))
    from_ = Column(String(100))
    from_is_local = Column(Boolean)
    subject = Column(String)
    body = Column(String)
    date = Column(DateTime)
    bs = relationship('Attachment', backref='mailbox')


class Sent(Base):
    __tablename__ = 'Sent'
    id = Column(Integer, primary_key=True)
    to = Column(String)
    from_id = Column(Integer, ForeignKey('User.id'))
    subject = Column(String)
    body = Column(String)
    date = Column(DateTime, server_default=func.now())
    attachment = relationship('AttachmentSent', backref='sent')


class AttachmentSent(Base):
    __tablename__ = 'AttachmentSent'
    id = Column(Integer, primary_key=True)
    path = Column(String)
    size = Column(Integer)
    sent_id = Column(Integer, ForeignKey('Sent.id'))


class Attachment(Base):
    __tablename__ = 'Attachment'
    id = Column(Integer, primary_key=True)
    mailbox_id = Column(Integer, ForeignKey('Mailbox.id'))
    attachment_id = Column(Integer)
    size = Column(Integer)
    name = Column(String)

    @property
    def url(self) -> str:
        return (
            f'https://tempmail.plus/api/mails/{self.mailbox_id}'
            f'/attachments/{self.attachment_id}')


async def main():
    engine = create_async_engine('sqlite+aiosqlite:///test.sqlite3')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class UserUnavailable(Exception):
    pass


if __name__ == '__main__':
    asyncio.run(main())
