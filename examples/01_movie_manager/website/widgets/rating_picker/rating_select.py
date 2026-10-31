from django import forms

from website.widgets.rating_picker.rating_picker import RatingPicker


class RatingSelect(forms.Select):
    """
    RatingPicker as a Django form widget, for a form such as the Movie admin's. Only how it
    renders changes: the field's name is the same, so Select's own value_from_datadict() still
    reads the submitted rating.
    """

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        picker = RatingPicker(name=name, value=value or '', select_id=attrs.get('id'))
        return picker.render()
