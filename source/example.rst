Example
=======


Get New Message
----------------

.. code-block:: python

    from xtempmail import extension, Email
    mail = Email('kryptonn', extension[1])
    @mail.on.message()
    def get(data):
        print(data)
    
    mail.listen_new_message(interval=2)



Download File Attachment
------------------------

.. code-block:: python

    from xtempmail import extension, Email
    mail = Email('kryptonn', extension[1])
    @mail.on.message(filter=(lambda msg: msg.attament))
    def get(data: EmailMessage):
        for i in data.attachments:
            i.save_as_file(i.name) #save as file
            i.download().getvalue() # save as BytesIO Object
    mail.listen_new_message(interval=2)

Send Message
-------------

.. code-block:: python

    from xtempmail import extension, Email
    mail = Email('kryptonn', extension[1])
    mail.send_message('example@mailto.plus', 'subject', 'text')

Send Message With File
-----------------------


.. code-block:: python

    from xtempmail import extension, Email
    from io import BytesIO
    mail = Email('kryptonn', extension[1])    
    mail.send_message('example@mailto.plus', 'subject', 'text', file='image.jpg') # using path
    mail.send_message('example@mailto.plus', 'subject', 'text', multiply_file=(('doc.txt',BytesIO(b'....')),)) #using BytesIO



Reply Message
--------------

.. code-block:: python

    from xtempmail import extension, Email
    app = Email('kryptonn', extension[1])
    @app.on.message()
    def get(data: EmailMessage):
        print(f"\tfrom: {data.from_mail}\n\tsubject: {data.subject}\n\tpesan: {data.text}\n\tReply -> Hapus")
        ok = []
        for i in data.attachments: # -> Forward attachment
            ok.append(( i.name, i.download()))
        if data.from_is_local:
            data.from_mail.send_message(data.subject,data.text, multiply_file=ok) # -> Forward message
    app.listen_new_message(interval=2) 


Delete Message
--------------
.. code-block:: python

    from xtempmail import extension, Email
    mail = Email('kryptonn', extension[1])
    @mail.on.message()
    def get(data):
        data.delete()
    mail.listen_new_message(interval=2)

Filter Message
--------------
.. code-block:: python

    from xtempmail import extension, Email
    mail = Email('kryptonn', extension[1])
    @mail.on.message(filter=(lambda msg: msg.from_mail.__str__().endswith('@gmail.com')))
    def get(data):
        print(data)
    
    mail.listen_new_message(interval=2)