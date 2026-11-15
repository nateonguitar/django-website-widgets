from django.conf import settings


class TextMessages:
    """
    Texts through the family's SMS provider. A stand-in: it prints each text to runserver's
    console, as the console email backend does, where a real provider's client would make a
    paid request. So the test runner (`movie_manager/test_runner.py`) patches `send()` for every
    test, and a test checking a text patches it again to see the call.
    """

    @staticmethod
    def send(to: str, body: str) -> None:
        print(f'Text to {to}: {body}')

    @staticmethod
    def send_to_shelf_keeper(body: str) -> None:
        TextMessages.send(settings.SHELF_KEEPER_PHONE_NUMBER, body)
