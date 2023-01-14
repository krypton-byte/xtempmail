from __future__ import annotations
from abc import ABC, abstractmethod, abstractproperty
from datetime import datetime
from io import BytesIO
from sqlalchemy.orm import sessionmaker
from typing import Union, Callable, Optional, List, Any
from .utils import EMAIL
from .models import User, Mailbox


class EmailBase(ABC):
    email: str
    first_id: int
    epin: str
    params: dict[str, Union[str, int]]
    emails_id: List[int]
    on: EventBase
    account: AccountBase


class AccountBase(ABC):
    username: str
    provider: EMAIL
    session: sessionmaker

    @abstractmethod
    async def login(self) -> User:
        pass

    @abstractmethod
    async def get_id(self) -> int:
        pass

    @abstractproperty
    @abstractmethod
    def secret_inbox(self) -> str:
        pass

    @abstractmethod
    async def get_secret_inbox(self) -> str:
        pass

    @abstractmethod
    async def set_secret_inbox(self, address: str) -> str:
        pass

    @abstractmethod
    async def create(self) -> None:
        pass

    @abstractmethod
    async def search_inbox_by_id(self, id: int) -> Mailbox:
        pass

    @abstractmethod
    async def push_inbox(self, inbox: EmailMessageBase):
        pass

    @abstractmethod
    async def set_pin(self, pin: str, duration: int):
        pass

    @abstractmethod
    def set_pin_sync(self, pin: str, duration: int):
        pass

    @abstractmethod
    async def get_pin(self) -> str:
        pass

    @abstractproperty
    @abstractmethod
    def pin(self) -> str:
        pass

    @abstractproperty
    @abstractmethod
    def id(self):
        pass


class EventBase(ABC):
    workers: int
    account: AccountBase

    @abstractmethod
    def message(
        self,
        filter: Optional[Callable[[EmailMessageBase], Any]] = None
    ) -> Callable[[Union[Callable[[EmailMessageBase], None],  Any]], Any]:
        pass

    @abstractmethod
    async def on_message(self, data: EmailMessageBase) -> None:
        pass


class StrangerMailBase(ABC):
    account: EmailBase
    email: str

    @abstractmethod
    async def send_message(
        self,
        subject: str,
        text: str,
        file: Optional[str] = None,
        filename: Optional[str] = None,
        multiply_file: Optional[list] = []
    ) -> bool:
        pass


class AttachmentBase(ABC):
    mail: str
    mail_id: int
    attachment_id: int
    content_id: str
    name: str
    size: int
    myemail: Any

    @abstractmethod
    async def download(self) -> BytesIO:
        pass

    @abstractproperty
    @abstractmethod
    def url(self) -> str:
        pass

    @abstractmethod
    async def save_as_file(self, filename: str) -> int:
        pass


class EmailMessageBase(ABC):
    attachments: List[AttachmentBase]
    from_mail: StrangerMailBase
    date: datetime
    from_is_local: bool
    subject: str
    from_name: str
    html: str
    mail_id: int
    message_id: str
    result: bool
    text: str
    to: EmailBase

    @abstractmethod
    async def delete(self) -> None:
        pass
