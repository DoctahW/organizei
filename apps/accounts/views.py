import re

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def auth_view(request):
    context = {"active_panel": "login", "errors": {}, "error": None}

    if request.method == "POST":
        form_type = request.POST.get("form_type", "")

        if form_type == "login":
            return _handle_login(request, context)
        elif form_type == "register":
            return _handle_register(request, context)

    context["next"] = request.GET.get("next", "")
    return render(request, "registration/login.html", context)


def _handle_login(request, context):
    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")

    if not username or not password:
        context["error"] = "Preencha todos os campos."
        context["active_panel"] = "login"
        return render(request, "registration/login.html", context)

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        next_url = (
            request.POST.get("next")
            or request.GET.get("next")
            or ""
        )
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            return redirect(next_url)
        return redirect("/dashboard/")

    context["error"] = "Usuário ou senha inválidos."
    context["active_panel"] = "login"
    return render(request, "registration/login.html", context)


def _handle_register(request, context):
    full_name = request.POST.get("full_name", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")
    confirm_password = request.POST.get("confirm_password", "")

    errors = []

    if not full_name:
        errors.append("Nome completo é obrigatório.")

    # Email validation
    if not email:
        errors.append("Email é obrigatório.")
    elif not EMAIL_RE.match(email):
        errors.append("Email inválido.")

    # Password validation
    if len(password) < 8:
        errors.append("Senha deve ter pelo menos 8 caracteres.")
    if password != confirm_password:
        errors.append("As senhas não coincidem.")

    # Use email as username
    username = email

    # Check uniqueness
    if email and User.objects.filter(username=username).exists():
        errors.append("Este email já está cadastrado.")

    if errors:
        context["errors"] = errors
        context["active_panel"] = "register"
        return render(request, "registration/login.html", context)

    first_name = full_name
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
            )
    except IntegrityError:
        context["errors"] = ["Este email já está em uso."]
        context["active_panel"] = "register"
        return render(request, "registration/login.html", context)

    login(request, user)
    return redirect("/dashboard/")


@require_POST
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@login_required
def profile_view(request):
    context = {"saved": False, "errors": []}

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()

        if email and not EMAIL_RE.match(email):
            context["errors"].append("Email inválido.")
        elif not email:
            context["errors"].append("Email é obrigatório.")

        if not context["errors"]:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            request.user.save()
            context["saved"] = True

    context["user_obj"] = request.user
    return render(request, "accounts/profile.html", context)


@login_required
def password_change_view(request):
    context = {"errors": []}

    if request.method == "POST":
        old_password = request.POST.get("old_password", "")
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not request.user.check_password(old_password):
            context["errors"].append("Senha atual incorreta.")

        if len(new_password) < 8:
            context["errors"].append(
                "Nova senha deve ter pelo menos 8 caracteres."
            )

        if new_password != confirm_password:
            context["errors"].append("As senhas não coincidem.")

        if not context["errors"]:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            return redirect("accounts:password_change_done")

    return render(request, "accounts/password_change.html", context)


@login_required
def password_change_done_view(request):
    return render(request, "accounts/password_change_done.html")
