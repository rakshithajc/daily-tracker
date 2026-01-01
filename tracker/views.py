from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Task
from datetime import date, datetime, timedelta
import calendar


def get_week_data(user, week_start):
    days = []
    values = []

    for i in range(7):
        d = week_start + timedelta(days=i)
        total = Task.objects.filter(user=user, date=d).count()
        done = Task.objects.filter(user=user, date=d, is_completed=True).count()
        days.append(d.strftime("%a"))
        values.append(done)

    return days, values

# ---------- calendar builder ----------
def build_month_calendar(user, year, month):
    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(year, month)
    month_data = []

    for week in weeks:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({"day": None})
            else:
                d = date(year, month, day)
                tasks = Task.objects.filter(user=user, date=d)
                total = tasks.count()
                done = tasks.filter(is_completed=True).count()

                if total == 0:
                    status = "none"
                elif done == total:
                    status = "complete"
                else:
                    status = "partial"

                week_data.append({
                    "day": day,
                    "status": status,
                    "date": d.isoformat()
                })
        month_data.append(week_data)

    return month_data


# ---------- streak logic (CORRECT) ----------
def calculate_streak(user):
    streak = 0
    current_day = date.today()

    while True:
        tasks = Task.objects.filter(user=user, date=current_day)

        # Rule 1: if no tasks → streak ends
        if not tasks.exists():
            break

        # Rule 2: if any task incomplete → streak ends
        if tasks.filter(is_completed=False).exists():
            break

        # Otherwise, this day counts
        streak += 1
        current_day -= timedelta(days=1)

    return streak




# ---------- home ----------
@login_required
def home(request):
    # selected date (ONE source of truth)
    selected_date_str = request.GET.get("date")
    week_param = request.GET.get("week")

    if week_param:
        week_start = datetime.strptime(week_param, "%Y-%m-%d").date()
    else:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    selected_date = (
        date.fromisoformat(selected_date_str)
        if selected_date_str
        else date.today()
    )

    # ---------- ADD TASK ----------
    if request.method == "POST":
        title = request.POST.get("title")
        task_date = request.POST.get("task_date")

        if title and task_date:
            Task.objects.create(
                user=request.user,
                title=title,
                date=datetime.strptime(task_date, "%Y-%m-%d").date()
            )

        return redirect(f"/?date={task_date}")

    # ---------- TASKS FOR SELECTED DATE ----------
    tasks = Task.objects.filter(
        user=request.user,
        date=selected_date
    )

    total = tasks.count()
    completed = tasks.filter(is_completed=True).count()
    progress = int((completed / total) * 100) if total > 0 else 0
    week_labels, week_values = get_week_data(request.user, week_start)

    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    # ---------- STREAK ----------
    streak = calculate_streak(request.user)

    # ---------- MONTH LOGIC ----------
    current_month_start = selected_date.replace(day=1)
    next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)
    prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)


    # ---------- WEEKLY DATA ----------
    week_labels = []
    week_values = []

    for i in range(7):
        d = week_start + timedelta(days=i)
        week_labels.append(d.strftime("%a"))
        week_values.append(
            Task.objects.filter(
                user=request.user,
                date=d
            ).count()
        )


    context = {
        # left side
        "tasks": tasks,
        "completed": completed,
        "total": total,
        "progress": progress,
        "streak": streak,
        "selected_date": selected_date,

        # calendars
        "month_name": calendar.month_name[current_month_start.month],
        "year": current_month_start.year,
        "calendar": build_month_calendar(
            request.user,
            current_month_start.year,
            current_month_start.month
        ),

        "next_month_name": calendar.month_name[next_month_start.month],
        "next_year": next_month_start.year,
        "next_calendar": build_month_calendar(
            request.user,
            next_month_start.year,
            next_month_start.month
        ),

        # navigation
        "prev_month": prev_month_start.isoformat(),
        "next_month": next_month_start.isoformat(),
        "week_labels": week_labels,
        "week_values": week_values,
        "prev_week": prev_week.isoformat(),
        "next_week": next_week.isoformat(),
    }

    return render(request, "tracker/home.html", context)


@login_required
def monthly_summary(request):
    today = date.today()
    year = today.year
    month = today.month

    summary = defaultdict(int)

    tasks = Task.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    )

    for t in tasks:
        if t.is_completed:
            summary[t.date] += 1

    labels = [d.strftime("%d") for d in sorted(summary.keys())]
    values = [summary[d] for d in sorted(summary.keys())]

    return render(request, "tracker/monthly.html", {
        "labels": labels,
        "values": values,
        "month": calendar.month_name[month],
        "year": year
    })


# ---------- toggle ----------
@login_required
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_completed = not task.is_completed
    task.save()
    return redirect(request.META.get("HTTP_REFERER", "/"))


# ---------- delete ----------
@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect(request.META.get("HTTP_REFERER", "/"))



def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()

    return render(request, "tracker/signup.html", {"form": form})
