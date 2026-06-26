from urllib import request

from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from django.http import HttpResponse
from django.contrib import messages
from .models import Transactions
@login_required(login_url="/login/")
def mainpage(request):
    return render(request,"expenses/mainpage.html")

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