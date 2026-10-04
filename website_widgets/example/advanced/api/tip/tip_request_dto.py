from dataclasses import dataclass

from django.http import QueryDict

from website_widgets.example.api.errors import UnprocessableEntityException


@dataclass(kw_only=True)
class TipRequestDto:
    """The tip endpoint's query string: `?number=N`. `number` is `None` when N isn't a whole number."""

    number: int | None

    @classmethod
    def from_query(cls, query: QueryDict) -> 'TipRequestDto':
        raw_number = query.get('number', '')
        number = int(raw_number) if raw_number.isdigit() else None
        return cls(number=number)

    def validate(self):
        if self.number is None:
            raise UnprocessableEntityException(errors={
                'number': ['number must be a whole number, 0 or more.'],
            })
