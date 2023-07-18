from __future__ import annotations
from enum import Enum
from typing import Union
from .error import (
    InvalidPIN
)


def isoformat_translate(format: str):
    split = format.split(' ')[1:]
    index = [
        'jan', 'feb', 'mar', 'apr', 'may', 'jun',
        'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
    ].index(split[1].lower())+1
    month = index.__str__().zfill(2)
    return f'{split[2]}-{month}-{split[0]}T{split[3]}'


def err_code(c: int):
    if c == 1021:
        return InvalidPIN


class EMAIL(Enum):
    MAILTO_PLUS = 'mailto.plus'
    FEXPOST_COM = 'fexpost.com'
    FEXBOX_ORG = 'fexbox.org'
    MAILBOX_IN_UA = 'mailbok.in.ua'
    CHITTHI_IN = 'chitthi.in'
    FEXTEMP_COM = 'fextemp.com'
    ANY_PINK = 'any.pink'
    MEREPOST_COM = 'merepost.com'

    def apply(self, name: str) -> str:
        return name + '@' + self.value

    @classmethod
    def istemp(cls, email: Union[str, Extension]):
        mail = email.ex[1:] if isinstance(
            email, Extension) else (
                email.split('@')[email.split('@').__len__() == 2])
        for e in cls.__members__.values():
            if e.value == mail:
                return True
        return False


class Extension:
    def __init__(self, ex: str):
        self.ex = '@' + ex

    def apply(self, text: str) -> str:
        return f"{text}{self.ex.__str__()}"

    def __repr__(self):
        return self.ex

    def __str__(self):
        return self.ex


extension = [Extension(i.value) for i in EMAIL.__members__.values()]
