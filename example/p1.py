from xtempmail import Email, extension
import logging
from xtempmail.mail import EmailMessage
log = logging.getLogger('xtempmail')
log.setLevel(logging.INFO)
app = Email(name='player1', ext=extension[1])


@app.on.message()
def read(data: EmailMessage):
    if data.from_is_local:
        resp = {
            'hi': 'hello',
            'hello': 'hi',
        }.get(data.text, '??')
        data.from_mail.send_message(f'Reply: {data.subject}', resp)
        # -> Forward message
        print(f'p0: {data.text}\np1: {resp}')
    data.delete()  # delete message


if __name__ == '__main__':
    try:
        app.listen_new_message(interval=2)
    except KeyboardInterrupt:
        app.destroy()  # destroy inbox
        print('destroyed')
