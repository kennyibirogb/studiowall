import json
import os
import urllib.request
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CheckoutForm, SignupForm, CommissionFormWithFiles
from .models import Order, Painting, SiteProfile, CommissionRequest, CommissionReference


def paystack_key():
    return os.environ.get("PAYSTACK_SECRET_KEY", "")


def _paystack(path, payload=None):
    req = urllib.request.Request(
        "https://api.paystack.co" + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Bearer {paystack_key()}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def index(request):
    return render(request, "gallery/index.html", {"paintings": Painting.objects.all()})


def detail(request, slug):
    painting = get_object_or_404(Painting, slug=slug)
    profile = SiteProfile.load()

    text = f'Hello, I\'m interested in "{painting.title}"'
    if painting.price:
        text += f" ({painting.price})"
    text = quote(text + ". Is it still available?")
    whatsapp = f"https://wa.me/{profile.whatsapp}?text={text}" if profile.whatsapp else ""
    mail = (f"mailto:{profile.email}?subject={quote('Enquiry: ' + painting.title)}&body={text}"
            if profile.email else "")

    slugs = list(Painting.objects.values_list("slug", flat=True))
    i = slugs.index(painting.slug)
    return render(request, "gallery/detail.html", {
        "p": painting,
        "whatsapp": whatsapp,
        "mail": mail,
        "gateway": bool(paystack_key()),
        "prev": slugs[i - 1] if i > 0 else None,
        "next": slugs[i + 1] if i < len(slugs) - 1 else None,
    })


@login_required(login_url="login")
def add_to_cart(request, slug):
    painting = get_object_or_404(Painting, slug=slug, status="available")

    # Prevent duplicates
    existing = Order.objects.filter(
        customer=request.user,
        painting=painting,
        status__in=["pending", "requested"]
    ).first()

    if existing:
        messages.info(request, f"“{painting.title}” is already in your orders.")
        return redirect("gallery:orders")

    amount = painting.price_amount
    if amount is None:
        messages.error(request, "This painting has no price set yet.")
        return redirect(painting)

    order = Order(
        customer=request.user,
        painting=painting,
        amount=amount,
        status="requested",
    )
    order.save()

    messages.success(request, f"“{painting.title}” has been added to your orders.")
    return redirect("gallery:orders")


def signup(request):
    form = SignupForm(request.POST or None)
    if form.is_valid():
        login(request, form.save())
        return redirect(request.GET.get("next") or "gallery:index")
    return render(request, "gallery/signup.html", {"form": form})


@login_required(login_url="login")
def checkout(request, slug):
    painting = get_object_or_404(Painting, slug=slug)
    if not painting.can_checkout:
        messages.error(request, "This painting can't be bought online right now.")
        return redirect(painting)

    form = CheckoutForm(request.POST or None)
    if form.is_valid():
        order = form.save(commit=False)
        order.customer, order.painting, order.amount = request.user, painting, painting.price_amount
        order.save()
        if paystack_key():
            try:
                data = _paystack("/transaction/initialize", {
                    "email": request.user.email or f"{request.user.username}@example.com",
                    "amount": int(order.amount * 100),
                    "reference": order.reference,
                    "currency": "NGN",
                    "callback_url": request.build_absolute_uri(reverse("gallery:paystack_callback")),
                })
                order.status = Order.PENDING
                order.save(update_fields=["status"])
                return redirect(data["data"]["authorization_url"])
            except Exception:
                order.delete()
                messages.error(request, "Could not start the payment. Please try again.")
                return redirect(painting)
        messages.success(request, "Request sent. The artist will contact you to arrange payment.")
        return redirect("gallery:orders")
    return render(request, "gallery/checkout.html",
                  {"p": painting, "form": form, "gateway": bool(paystack_key())})


def paystack_callback(request):
    order = get_object_or_404(Order, reference=request.GET.get("reference", ""))
    if order.status != Order.PAID and paystack_key():
        try:
            data = _paystack(f"/transaction/verify/{quote(order.reference)}")["data"]
        except Exception:
            messages.error(request, "We could not confirm the payment yet. Check My orders shortly.")
            return redirect("gallery:orders")
        if data.get("status") == "success" and data.get("amount") == int(order.amount * 100):
            with transaction.atomic():
                order.mark_paid()
            messages.success(request, "Payment received. Thank you!")
        else:
            messages.error(request, "The payment was not completed.")
    return redirect("gallery:orders")


@login_required(login_url="login")
def orders(request):
    return render(request, "gallery/orders.html",
                  {"orders": request.user.orders.select_related("painting")})
    
    
    
    
    
@login_required(login_url="login")
def remove_order(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)

    # Only allow removing unpaid / requested orders
    if order.status in ["requested", "pending"]:
        order.delete()
        messages.success(request, f"“{order.painting.title}” removed from your orders.")
    else:
        messages.error(request, "This order can no longer be removed.")

    return redirect("gallery:orders")

def commission(request):
    form = CommissionFormWithFiles(request.POST or None, request.FILES or None)

    if form.is_valid():
        commission = form.save(commit=False)
        if request.user.is_authenticated:
            commission.customer = request.user
            if not commission.name:
                commission.name = request.user.get_full_name() or request.user.username
            if not commission.email:
                commission.email = request.user.email
        commission.save()

        # Save uploaded reference images
        files = request.FILES.getlist("references")
        for f in files:
            CommissionReference.objects.create(commission=commission, image=f)

        messages.success(request, "Your commission request has been sent. The artist will contact you soon.")
        return redirect("gallery:index")

    return render(request, "gallery/commission.html", {"form": form})