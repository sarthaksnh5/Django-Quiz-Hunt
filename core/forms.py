import random
import string
import uuid
from typing import Tuple

from django import forms
from django.utils.text import slugify

from .models import Contestant, Choice, Question


def _generate_pin() -> str:
    return f"{random.randint(0, 999999):06d}"


type_save_return = Tuple[Contestant, str]


class RegistrationForm(forms.Form):
    name = forms.CharField(max_length=100)
    school_name = forms.CharField(max_length=150)
    phone_number = forms.CharField(max_length=15, required=False)

    def clean(self):
        cleaned = super().clean()
        name = cleaned.get("name", "").strip()
        school = cleaned.get("school_name", "").strip()
        if name and school:
            base_slug = slugify(f"{name}-{school}")[:70]
            slug = base_slug
            idx = 2
            while Contestant.objects.filter(nickname=slug).exists():
                suffix = f"-{idx}"
                slug = (base_slug[: (80 - len(suffix))] + suffix)
                idx += 1
            cleaned["nickname"] = slug
        return cleaned

    def save(self) -> type_save_return:
        cleaned = self.cleaned_data
        contestant = Contestant(
            name=cleaned["name"],
            school_name=cleaned["school_name"],
            phone_number=cleaned.get("phone_number", ""),
            nickname=cleaned["nickname"],
        )
        raw_pin = _generate_pin()
        contestant.set_pin(raw_pin)
        contestant.save()
        return contestant, raw_pin


class NicknameGateForm(forms.Form):
    nickname = forms.SlugField(max_length=80)
    pin_code = forms.CharField(min_length=6, max_length=6)

    def clean(self):
        cleaned = super().clean()
        nickname = cleaned.get("nickname")
        pin_code = cleaned.get("pin_code")
        contestant = None
        if nickname:
            try:
                contestant = Contestant.objects.get(nickname=nickname)
            except Contestant.DoesNotExist:
                raise forms.ValidationError("Invalid nickname or PIN.")
        if contestant and pin_code and not contestant.check_pin(pin_code):
            raise forms.ValidationError("Invalid nickname or PIN.")
        cleaned["contestant_obj"] = contestant
        return cleaned


class AnswerForm(forms.Form):
    choice_id = forms.UUIDField()

    def __init__(self, question: Question, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question

    def get_choice(self) -> Choice:
        choice_id = self.cleaned_data.get("choice_id")
        if not choice_id:
            raise forms.ValidationError("Invalid choice.")
        try:
            return self.question.choices.get(id=choice_id)
        except Choice.DoesNotExist:
            raise forms.ValidationError("Invalid choice.")
