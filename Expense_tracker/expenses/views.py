from urllib import request
from django.utils import timezone
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import HttpResponse
from django.contrib import messages
from .models import Transactions,Budget
from django.db.models.functions import ExtractMonth
@login_required(login_url="/login/")
@login_required(login_url="/login/")
def mainpage(request):
    today = timezone.now()

    title = request.GET.get("search_text")
    date = request.GET.get("search_date")
    types = request.GET.get("search_types")
    category = request.GET.get("search_category")
    amount = request.GET.get("search_amount")
    see_all = request.GET.get("see_all")
    month = request.GET.get("search_month")

    # Selected month (current month by default)
    selected_month = int(month) if month else today.month

    # Dashboard Cards
    expense = Transactions.objects.filter(
        user=request.user,
        types="Expense",
        date__year=today.year,
        date__month=selected_month
    ).aggregate(total_expense=Sum("amount"))

    income = Transactions.objects.filter(
        user=request.user,
        types="Income",
        date__year=today.year,
        date__month=selected_month
    ).aggregate(total_income=Sum("amount"))

    number_of_transactions = Transactions.objects.filter(
        user=request.user,
        date__year=today.year,
        date__month=selected_month
    ).count()

    Balance = (
        (income["total_income"] or 0)
        - (expense["total_expense"] or 0)
    )

    if Balance < 0:
        Balance = 0

    # Pie Chart
    expenseData = list(
        Transactions.objects.filter(
            user=request.user,
            types="Expense",
            date__year=today.year,
            date__month=selected_month
        )
        .values("category")
        .annotate(total=Sum("amount"))
    )

    # Transaction List
    queryset = Transactions.objects.filter(user=request.user).order_by("-created_at")

    if title:
        queryset = queryset.filter(title__icontains=title)

    if date:
        queryset = queryset.filter(date=date)

    if types:
        queryset = queryset.filter(types=types)

    if category:
        queryset = queryset.filter(category=category)

    if amount:
        queryset = queryset.filter(amount=amount)

    if not see_all:
        queryset = queryset.filter(
            date__year=today.year,
            date__month=selected_month
        )

    queryset = queryset[:10] if see_all else queryset[:5]

    # Budget Tracker
    budgets = Budget.objects.filter(user=request.user)

    budget_data = []

    for budget in budgets:

        spent = (
            Transactions.objects.filter(
                user=request.user,
                category=budget.category,
                types="Expense",
                date__year=today.year,
                date__month=selected_month
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        percentage = (spent / budget.limit) * 100 if budget.limit else 0

        budget_data.append({
            "id": budget.id,
            "category": budget.category,
            "limit": budget.limit,
            "spent": spent,
            "percentage": min(percentage, 100),
            "over_budget": spent > budget.limit,
            "remaining": max(budget.limit - spent, 0),
            "exceeded": max(spent - budget.limit, 0),
        })

    # ==========================
    # Income vs Expense Bar Chart
    # ==========================

    income_queryset = (
        Transactions.objects.filter(
            user=request.user,
            types="Income",
            date__year=today.year
        )
        .annotate(month=ExtractMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    expense_queryset = (
        Transactions.objects.filter(
            user=request.user,
            types="Expense",
            date__year=today.year
        )
        .annotate(month=ExtractMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    income_data = [0] * 12
    expense_data = [0] * 12

    for item in income_queryset:
        income_data[item["month"] - 1] = float(item["total"])

    for item in expense_queryset:
        expense_data[item["month"] - 1] = float(item["total"])

    return render(
        request,
        "expenses/mainpage.html",
        {
            "expense": expense,
            "income": income,
            "Balance": Balance,
            "number_of_transactions": number_of_transactions,
            "queryset": queryset,
            "expenseData": expenseData,
            "budget_data": budget_data,

            # Bar Chart
            "months": months,
            "income_data": income_data,
            "expense_data": expense_data,
        },
    )
def budget_tracker(request):
    if request.method=="POST":
        category=request.POST.get("category")
        limit=request.POST.get("limit")
        if category and limit:
            Budget.objects.update_or_create(
                user=request.user,
                category=category,
                defaults={"limit":limit}
            )
        else:
            messages.info("Please select a category and set a budget limit for it ")
        budget = Budget.objects.filter(user=request.user)
        return redirect("/")
    return render(request,"expenses/budget_tracker.html")

def update_budget(request,id):
    budget = Budget.objects.get(user=request.user,id=id)
    if request.method=="POST":
        
        limit=request.POST.get("limit")
        budget.limit = limit
        budget.save()
        messages.info(request,"Budget updated successfully")
        return redirect("/")
    return render(request,"expenses/update_budget.html",{"budget": budget})

@login_required(login_url="/login/")
def add_transaction(request):
    if request.method=="POST":
        data=request.POST
        title=data.get("title")
        amount=data.get("amount")
        types=data.get("types")
        category=data.get("category")
        date=data.get("date")
        if title and amount and types and category:

            transaction = {
                "user": request.user,
                "title": title,
                "amount": amount,
                "types": types,
                "category": category,
            }

            if date:
                transaction["date"] = date

            Transactions.objects.create(**transaction)
            messages.info(request,"Transaction added successfully")
            return redirect("/add_transaction/")

    return render(request,"expenses/add_transaction.html")

# Create your views here.


@login_required(login_url="/login/")
def transaction(request):
    transactions = Transactions.objects.filter(
        user=request.user
    )

    return render(
        request,
        'expenses/transactions.html',
        {'tasks': transactions}
    )

def delete_transaction(request,id):
    queryset = Transactions.objects.get(
        user=request.user,id=id
    )
    queryset.delete()
    return redirect("/transactions/")

def update_transaction(request,id):
    queryset=Transactions.objects.get(user=request.user,id=id)
    if request.method == "POST":
        data=request.POST
        title=data.get("title")
        amount=data.get("amount")
        types=data.get("types")
        category=data.get("category")
        date=data.get("date")
        queryset.title = title
        queryset.amount = amount
        queryset.types = types
        queryset.category = category
        if date:
            queryset.date = date
        queryset.save()
        messages.info(request,"Transaction updated successfully")
        return redirect("/transactions/")
    return render(request,"expenses/update_transaction.html",{"task": queryset})

def register_user(request):
    if request.method=="POST":
        data=request.POST
        first_name=data.get("first_name")
        last_name=data.get("last_name")
        username=data.get("username")
        email=data.get("email")
        password=data.get("password")

        user=User.objects.filter(username=username)
        if user.exists():
            messages.info(request,"Username already exists")
            return redirect('/register/')


       # ✅ Correct way matching new manager
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        user.set_password(password)
        user.save()

        messages.info(request,"Account created successfully")

        return redirect('/register/')
    return render(request,"expenses/register.html")

def login_user(request):
    if request.method=="POST":
        data=request.POST
        username=data.get("username")
        password=data.get("password")

        if not User.objects.filter(username=username).exists():
            messages.error(request,"Invalid Username")
            return redirect('/login/')
        
        user=authenticate(username=username,password=password)

        if user is None:
            messages.error(request,"Invalid Password")
            return redirect('/login/')
        else:
            login(request,user)
            return redirect("/")

    return render(request,"expenses/login.html")

def logout_user(request):
    logout(request)
    return redirect('/login/')