from xtempmail.aiomail import Email, EMAIL, EmailMessage
from httpx import AsyncClient
mail = Email(name='ytta', ext=EMAIL.CHITTHI_IN)


@mail.on.message()
async def test(m: EmailMessage):
    if m.text.lower() == 'ping':
        await m.from_mail.send_message('pong', 'pong')
    else:
        client = AsyncClient()
        await m.from_mail.send_message(
            'simi',
            (await client.get(
                'http://simi.krypton-byte.com/id',
                params={'text': m.text}
            )).json()['result'])
        await client.aclose()
    await m.delete()


mail.run_forever(1)
