from typing import Optional
from uuid import UUID

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Max, Q, F, ExpressionWrapper, DurationField
from django.db.models.functions import Coalesce
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import RegistrationForm, NicknameGateForm, AnswerForm
from .models import QuizConfig, Contestant, Question, Answer

SESSION_AUTH_USER_ID = "auth_user_id"


def logout_contestant(request: HttpRequest) -> HttpResponse:
    request.session.pop(SESSION_AUTH_USER_ID, None)
    request.session.modified = True
    return redirect("home")


def _get_contestant_from_session(request: HttpRequest) -> Optional[Contestant]:
    contestant_id = request.session.get(SESSION_AUTH_USER_ID)
    if not contestant_id:
        return None
    try:
        return Contestant.objects.get(id=contestant_id)
    except Contestant.DoesNotExist:
        return None


def home(request: HttpRequest) -> HttpResponse:
    cfg = QuizConfig.get_solo()
    return render(request, "home.html", {"cfg": cfg})


def register(request: HttpRequest) -> HttpResponse:
    cfg = QuizConfig.get_solo()
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            contestant, raw_pin = form.save()
            return render(
                request,
                "registration.html",
                {
                    "cfg": cfg,
                    "form": RegistrationForm(),
                    "success": True,
                    "nickname": contestant.nickname,
                    "pin": raw_pin,
                },
            )
    else:
        form = RegistrationForm()
    return render(request, "registration.html", {"cfg": cfg, "form": form})


def question_entrypoint(request: HttpRequest, question_id: UUID) -> HttpResponse:
    cfg = QuizConfig.get_solo()
    question = get_object_or_404(Question, id=question_id, is_active=True)

    contestant = _get_contestant_from_session(request)
    if contestant:
        return redirect("question_detail", question_id=question.id)

    if request.method == "POST":
        form = NicknameGateForm(request.POST)
        if form.is_valid():
            contestant_obj: Contestant = form.cleaned_data["contestant_obj"]
            request.session[SESSION_AUTH_USER_ID] = str(contestant_obj.id)
            request.session.modified = True
            return redirect("question_detail", question_id=question.id)
    else:
        form = NicknameGateForm()

    return render(
        request,
        "nickname_gate.html",
        {"cfg": cfg, "form": form, "question": question},
    )


def question_detail(request: HttpRequest, question_id: UUID) -> HttpResponse:
    cfg = QuizConfig.get_solo()
    question = get_object_or_404(Question, id=question_id, is_active=True)
    contestant = _get_contestant_from_session(request)
    if not contestant:
        return redirect("question_entrypoint", question_id=question.id)

    # Submission cap
    total_answers = Answer.objects.filter(contestant=contestant).count()
    limit_reached = total_answers >= cfg.total_allowed_answers_per_user

    # Already answered this question?
    existing = Answer.objects.filter(contestant=contestant, question=question).first()

    form = AnswerForm(question)

    return render(
        request,
        "question_detail.html",
        {
            "cfg": cfg,
            "question": question,
            "contestant": contestant,
            "limit_reached": limit_reached,
            "existing": existing,
            "form": form,
            "remaining_after": max(0, cfg.total_allowed_answers_per_user - total_answers - 1),
        },
    )


def submit_answer(request: HttpRequest, question_id: UUID) -> HttpResponse:
    cfg = QuizConfig.get_solo()
    question = get_object_or_404(Question, id=question_id, is_active=True)
    contestant = _get_contestant_from_session(request)
    if not contestant:
        return redirect("question_entrypoint", question_id=question.id)

    if request.method != "POST":
        return redirect("question_detail", question_id=question.id)

    # Enforce cap
    total_answers = Answer.objects.filter(contestant=contestant).count()
    if total_answers >= cfg.total_allowed_answers_per_user:
        return redirect("question_detail", question_id=question.id)

    # Prevent multiple submissions
    if Answer.objects.filter(contestant=contestant, question=question).exists():
        return redirect("question_detail", question_id=question.id)

    form = AnswerForm(question, request.POST)
    if not form.is_valid():
        # Re-render detail with errors
        return render(
            request,
            "question_detail.html",
            {
                "cfg": cfg,
                "question": question,
                "contestant": contestant,
                "limit_reached": False,
                "existing": None,
                "form": form,
                "remaining_after": max(0, cfg.total_allowed_answers_per_user - total_answers - 1),
            },
        )

    choice = form.get_choice()
    is_correct = bool(choice.is_correct)
    Answer.objects.create(
        contestant=contestant,
        question=question,
        selected_choice=choice,
        is_correct=is_correct,
    )

    remaining = max(0, cfg.total_allowed_answers_per_user - total_answers - 1)

    return render(
        request,
        "submission_success.html",
        {
            "cfg": cfg,
            "question": question,
            "contestant": contestant,
            "remaining": remaining,
        },
    )


@staff_member_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    cfg = QuizConfig.get_solo()

    totals = {
        "registered_users": Contestant.objects.count(),
        "total_answers": Answer.objects.count(),
        "total_correct": Answer.objects.filter(is_correct=True).count(),
        "last_answer_time": Answer.objects.aggregate(ts=Max("submitted_at")).get("ts"),
    }

    contestants = (
        Contestant.objects.annotate(
            correct_count=Count("answers", filter=Q(answers__is_correct=True)),
            last_correct=Max("answers__submitted_at", filter=Q(answers__is_correct=True)),
            last_answer=Max("answers__submitted_at"),
        )
        .annotate(ref_time=Coalesce(F("last_correct"), F("last_answer")))
        .annotate(
            elapsed=ExpressionWrapper(
                F("ref_time") - cfg.quiz_started_at,
                output_field=DurationField(),
            )
        )
        .order_by("-correct_count", "elapsed", "nickname")
    )

    return render(
        request,
        "admin_dashboard.html",
        {"cfg": cfg, "totals": totals, "contestants": contestants},
    )


@staff_member_required
def admin_user_detail(request: HttpRequest, nickname: str) -> HttpResponse:
    cfg = QuizConfig.get_solo()
    contestant = get_object_or_404(Contestant, nickname=nickname)
    answers = (
        Answer.objects.filter(contestant=contestant)
        .select_related("question", "selected_choice")
        .order_by("submitted_at")
    )

    mapping = {}
    question_ids = set()
    for a in answers:
        question_ids.add(a.question_id)
    for qid in question_ids:
        try:
            q = Question.objects.get(id=qid)
            cc = q.correct_choice()
            mapping[qid] = cc.text if cc else ""
        except Question.DoesNotExist:
            mapping[qid] = ""
    for a in answers:
        setattr(a, "correct_text", mapping.get(a.question_id, ""))

    return render(
        request,
        "admin_user_detail.html",
        {
            "cfg": cfg,
            "contestant": contestant,
            "answers": answers,
        },
    )
