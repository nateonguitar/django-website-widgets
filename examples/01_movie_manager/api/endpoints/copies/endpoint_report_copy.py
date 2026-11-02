from asgiref.sync import sync_to_async
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.http import HttpRequest
from django.utils import timezone
from ninja import Schema, Status
from ninja.security import django_auth

from api.endpoints.copies import copies_router
from api.endpoints.error_responses import FieldErrorsResponseDto, MessageErrorResponseDto
from api.models import Copy, CopyReport, CopyReportKind, Rental, User


# Loose types, checked in the endpoint, as create_movie's are: a person fills this form in, so
# each mistake gets a message for them, keyed by field for the dialog.
class ReportCopyRequestDto(Schema):
    kind: str = ''
    notes: str = ''
    unrecoverable: bool = False


class ReportCopyResponseDto(Schema):
    report_id: int
    label: str
    # Whether the report took the copy out of rotation, which the row on My movies says.
    retired: bool


@copies_router.post(
    path='/{slug:label}/reports',
    auth=django_auth,
    url_name='report_copy',
    response={
        201: ReportCopyResponseDto,
        400: FieldErrorsResponseDto,
        404: MessageErrorResponseDto,
    })
async def report_copy(
    request: HttpRequest,
    label: str,
    dto: ReportCopyRequestDto,
) -> Status[ReportCopyResponseDto | FieldErrorsResponseDto | MessageErrorResponseDto]:
    # The person who has it out reports on it, and staff on any copy in rotation. Anyone else's
    # copy is a 404, not a 403 that would confirm the label exists.
    copies = Copy.objects.filter(label=label, retired_at__isnull=True)
    if not request.auth.is_staff:
        out_with_you = Rental.objects.filter(copy=OuterRef('pk'), user=request.auth, returned_at__isnull=True)
        copies = copies.filter(Exists(out_with_you))
    copy = await copies.afirst()
    if copy is None:
        not_found = MessageErrorResponseDto(message="That copy isn't out with you.")
        return Status(status_code=404, value=not_found)

    notes = dto.notes.strip()
    errors = {}
    if dto.kind not in CopyReportKind.values:
        errors['kind'] = "Pick what's wrong with it."
    if not notes:
        errors['notes'] = 'Say a little about it.'
    elif len(notes) > CopyReport.NOTES_MAX_LENGTH:
        errors['notes'] = f'At most {CopyReport.NOTES_MAX_LENGTH} characters.'
    if errors:
        invalid = FieldErrorsResponseDto(errors=errors)
        return Status(status_code=400, value=invalid)

    report = await _record_report(copy, request.auth, dto.kind, notes, dto.unrecoverable)
    reported = ReportCopyResponseDto(report_id=report.id, label=copy.label, retired=dto.unrecoverable)
    return Status(status_code=201, value=reported)


# The report, the retiring and the closed rental land together or not at all.
# transaction.atomic() has no async form, so this runs in Django's sync thread.
@sync_to_async
def _record_report(copy: Copy, user: User, kind: str, notes: str, unrecoverable: bool) -> CopyReport:
    with transaction.atomic():
        report = CopyReport.objects.create(copy=copy, user=user, kind=kind, notes=notes, unrecoverable=unrecoverable)
        if unrecoverable:
            now = timezone.now()
            copy.retired_at = now
            copy.save(update_fields=['retired_at'])
            # A lost disc can't come back, so its rental ends here, with no return receipt.
            Rental.objects.filter(copy=copy, returned_at__isnull=True).update(returned_at=now)
    return report
