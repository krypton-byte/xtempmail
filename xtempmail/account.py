import time
from typing import Optional
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .models import User, Mailbox, Sent, Base
from sqlalchemy.future import select
from sqlalchemy import and_, create_engine
from .abstract_models import EmailMessageBase, AccountBase
from .utils import EMAIL
from .logger import log
from pathlib import Path


class UserUnavailable(Exception):
    pass


class UserAvailable(Exception):
    pass


class SqliteSession:
    def __init__(self, database_path: Path) -> None:
        self.schema = create_async_engine(
            'sqlite+aiosqlite:///' + database_path.__str__())
        self.engine_sync = create_engine(
            'sqlite:///' + database_path.__str__())
        self.session_sync = sessionmaker(
            self.engine_sync,
            expire_on_commit=False
        )
        self.session = sessionmaker(
            self.schema,
            expire_on_commit=False,
            class_=AsyncSession
        )

    async def migrate(self):
        async with self.schema.begin() as session:
            await session.run_sync(Base.metadata.create_all)

    def migrate_sync(self):
        return Base.metadata.create_all(self.engine_sync)

    async def get_user_from_id(self, id_: int) -> User:
        async with self.session() as session:
            async with session.begin():
                data = await session.execute(
                    select(User).where(User.id == id_))
                for i in data.id:
                    return i
                else:
                    raise UserUnavailable(f'id: {id_} not registered')


class Account(SqliteSession, AccountBase):
    def __init__(
        self,
        username: str,
        provider: EMAIL,
        database_path: Path,
        epin: Optional[str] = None,
        duration: int = 3600 * 30
    ):
        super().__init__(database_path)
        self.username = username
        self.provider: str = provider.value
        self.__id = None
        self.full = provider.apply(username)
        if not (epin is None):
            self.set_pin_sync(epin, time.time() + duration)

    @property
    def pin(self) -> str:
        user = self.login_sync()
        if user.expired < time.time():
            with self.session_sync() as session:
                with session.begin():
                    session.execute(
                        update(User).where(User.id == user.id).values(epin=''))
        return self.login_sync().epin

    def set_pin_sync(self, pin: str, duration: int):
        with self.session() as session:
            with session.begin():
                session.execute(update(User).where(
                    User.id == self.get_id_sync()
                ).values(epin=pin, expired=duration))

    async def set_pin(self, pin: str, duration: str):
        async with self.session() as session:
            async with session.begin():
                await session.execute(
                    update(User).where(User.id == await self.get_id()).values(
                        epin=pin,
                        expired=duration
                    )
                )

    async def get_pin(self):
        user = await self.login()
        if user.expired < time.time():
            async with self.session() as session:
                async with session.begin():
                    await session.execute(update(User).where(
                        User.id == user.id
                    ).values(expired=0, epin=''))
        return (await self.login()).epin

    def login_sync(self) -> User:
        with self.session_sync() as session:
            with session.begin():
                for i in session.scalars(select(User).where(and_(
                    User.username == self.username,
                    User.provider == self.provider
                ))).all():
                    return i
                else:
                    raise UserUnavailable(f'{self.full} doesn\'t exist')

    @property
    def secret_inbox(self):
        return self.login_sync().secret_inbox

    @secret_inbox.setter
    def secret_inbox(self):
        with self.session_sync() as session:
            with session.begin():
                for i in session.execute(
                    update(User).where(
                        User.id == self.id
                    )
                ).scalars():
                    return i

    async def set_secret_inbox(self, address: str):
        async with self.session() as session:
            async with session.begin():
                await session.execute(update(User).where(
                    User.id == await self.id
                ).values(secret_inbox=address))

    async def get_secret_inbox(self):
        async with self.session() as session:
            async with session.begin():
                for i in (await session.execute(
                    select(User).where(
                        User.id == await self.get_id()))).scalars():
                    return i

    async def login(self) -> User:
        log.debug(f'login: {self.full}')
        async with self.session() as session:
            async with session.begin():
                scalars = (await session.execute(
                    select(User).where(and_(
                        User.username == self.username,
                        User.provider == self.provider
                    )))).scalars()
                for i in scalars:
                    log.debug(f'user {self.full} is found')
                    return i
                else:
                    log.warn(
                        f'user {self.full} not found',
                        exc_info=UserUnavailable(f'{self.full} doesn\'t exist')
                    )
                    raise UserUnavailable(f'{self.full} doesn\'t exist')

    async def get_id(self) -> int:
        log.debug(f'get id {self.full}')
        if self.__id is None:
            self.__id = (await self.login()).id
        return self.__id

    @property
    def id(self) -> int:
        if self.__id is None:
            self.__id = self.login_sync().id
        return self.__id

    async def create(self) -> None:
        async with self.session() as session:
            async with session.begin():
                try:
                    await self.login()
                    raise UserAvailable(f'{self.full} user is already use')
                except UserUnavailable:
                    session.add(User(
                        username=self.username,
                        provider=self.provider
                    ))
                    await session.commit()
                    log.debug(f'{self.full} user create')

    def create_sync(self) -> None:
        with self.session_sync() as session:
            with session.begin():
                try:
                    self.login_sync()
                    raise UserAvailable(f'{self.full} user is already use')
                except UserUnavailable:
                    session.add(User(
                        username=self.username,
                        provider=self.provider
                    ))
                    session.commit()

    async def search_inbox_by_id(self, id: int) -> Mailbox:
        async with self.session() as session:
            async with session.begin():
                for i in (await self.execute(select(Mailbox).where(and_(
                    Mailbox.id == id,
                    Mailbox.user_id == (await self.login()).id
                )))).scalars():
                    return i

    async def get_all_inbox(self):
        async with self.session() as session:
            async with session.begin():
                return await session.execute(select(Mailbox).where(
                    Mailbox.user_id == (await self.login()).id))

    async def get_all_sent(self):
        async with self.session() as session:
            async with session.begin():
                return await session.execute(select(Sent).where(
                    Sent.from_id == await self.get_id()))

    async def push_inbox(self, inbox: EmailMessageBase):
        mb = Mailbox(
            id=int(inbox.mail_id),
            user_id=(await self.login()).id,
            from_=inbox.from_mail.email,
            from_is_local=inbox.from_is_local,
            subject=inbox.subject,
            body=inbox.text,
            date=inbox.date
        )
        async with self.session() as session:
            async with session.begin():
                session.add(mb)
