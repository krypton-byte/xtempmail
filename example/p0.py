from xtempmail import Email, extension
import time
import logging
import multiprocessing
from xtempmail.mail import EmailMessage
log = logging.getLogger('xtempmail')
log.setLevel(logging.INFO)
app = Email(name='player0', ext=extension[1])

@app.on.message()
def read(data: EmailMessage):
    if data.from_is_local:
        print(f'P1: {data.text}')
    data.delete()  #delete message

if __name__ == '__main__':
    m=multiprocessing.Process(target=app.listen_new_message, args=(2, ))
    try:
        m.start()
        while True:
            time.sleep(2)
            da = input('message: ')
            app.send_mail(extension[1].apply('player1'), 'test', da)
            print(f'P0: {da}')
    except KeyboardInterrupt:
        m.terminate()
        app.destroy() #destroy inbox
        print('destroyed')
