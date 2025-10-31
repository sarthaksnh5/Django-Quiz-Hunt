from django.contrib import admin

from .models import QuizConfig, Contestant, Question, Choice, QuestionImage, Answer


@admin.register(QuizConfig)
class QuizConfigAdmin(admin.ModelAdmin):
    list_display = ("total_allowed_answers_per_user", "quiz_started_at")


@admin.register(Contestant)
class ContestantAdmin(admin.ModelAdmin):
    list_display = ("nickname", "name", "school_name", "phone_number")
    search_fields = ("nickname", "name", "school_name")


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


class QuestionImageInline(admin.TabularInline):
    model = QuestionImage
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at")
    list_filter = ("is_active",)
    inlines = [ChoiceInline, QuestionImageInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("contestant", "question", "is_correct", "submitted_at")
    list_filter = ("is_correct", "submitted_at")
    search_fields = ("contestant__nickname", "question__title")
