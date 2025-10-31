import uuid
from datetime import datetime

from django.db import models
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q


class BaseUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class QuizConfig(BaseUUIDModel):
    total_allowed_answers_per_user = models.PositiveIntegerField(default=10)
    quiz_started_at = models.DateTimeField(default=now)

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create()
        return obj

    def __str__(self) -> str:
        return f"QuizConfig({self.total_allowed_answers_per_user}, {self.quiz_started_at})"


phone_validator = RegexValidator(regex=r"^\+?\d{7,15}$", message="Enter a valid phone number.")


class Contestant(BaseUUIDModel):
    name = models.CharField(max_length=100)
    school_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15, blank=True, validators=[phone_validator])
    nickname = models.SlugField(max_length=80, unique=True)
    pin_hash = models.CharField(max_length=128, default="", blank=True)

    def __str__(self) -> str:
        return self.nickname

    def set_pin(self, raw_pin: str) -> None:
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin: str) -> bool:
        if not self.pin_hash:
            return False
        return check_password(raw_pin, self.pin_hash)


class Question(BaseUUIDModel):
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title

    def correct_choice(self):
        return self.choices.filter(is_correct=True).first()


class QuestionImage(BaseUUIDModel):
    question = models.ForeignKey(Question, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="question_images/")

    def __str__(self) -> str:
        return f"Image for {self.question.title}"


class Choice(BaseUUIDModel):
    question = models.ForeignKey(Question, related_name="choices", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.text} ({'✓' if self.is_correct else '✗'})"


class Answer(BaseUUIDModel):
    contestant = models.ForeignKey(Contestant, related_name="answers", on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.PROTECT)
    is_correct = models.BooleanField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["contestant", "question"], name="unique_answer_per_contestant_question"),
        ]

    def __str__(self) -> str:
        return f"{self.contestant.nickname} → {self.question.title} ({'✓' if self.is_correct else '✗'})"
