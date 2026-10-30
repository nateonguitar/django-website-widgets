from ninja import Schema


class MessageErrorResponseDto(Schema):
    """A refusal, worded for the person, which the page shows as it is."""

    message: str


class FieldErrorsResponseDto(Schema):
    """A form's mistakes: a message for each field, which the page shows beside it."""

    errors: dict[str, str]
