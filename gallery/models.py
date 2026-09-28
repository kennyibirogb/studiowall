import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from PIL import Image


class SiteProfile(models.Model):
    """One row only: the artist's name, tagline and contact details."""
    name = models.CharField(max_length=80, default="Artist Name")
    tagline = models.CharField(max_length=140, blank=True, default="Paintings, hung slowly")
    bio = models.TextField(blank=True)
    whatsapp = models.CharField("WhatsApp number", max_length=20, blank=True,
                                help_text="Country code, digits only. Example: 2348012345678")
    email = models.EmailField(blank=True)

    class Meta:
        verbose_name = "site profile"
        verbose_name_plural = "site profile"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]


class Painting(models.Model):
    AVAILABLE, SOLD, NOT_FOR_SALE = "available", "sold", "not_for_sale"
    STATUS = [(AVAILABLE, "Available"), (SOLD, "Sold"), (NOT_FOR_SALE, "Not for sale")]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to="paintings/", width_field="width", height_field="height")
    width = models.PositiveIntegerField(editable=False, null=True)
    height = models.PositiveIntegerField(editable=False, null=True)
    medium = models.CharField(max_length=120, blank=True, help_text="Example: Oil on canvas")
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    size = models.CharField(max_length=60, blank=True, help_text="Example: 60 x 80 cm")
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default=AVAILABLE)
    price = models.CharField(max_length=60, blank=True, help_text="Free text. Example: ₦250,000 or $400")
    price_amount = models.DecimalField("Price in naira (for online checkout)", max_digits=12, decimal_places=2,
                                       null=True, blank=True,
                                       help_text="Number only, e.g. 250000. Leave empty to take enquiries only.")
    payment_link = models.URLField(blank=True, help_text="Optional Paystack, Flutterwave or PayPal link")
    tint = models.CharField(max_length=7, editable=False, default="#1b2320")
    position = models.PositiveIntegerField(default=0, help_text="Lower numbers hang first")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "-created"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("gallery:detail", args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "painting"
            self.slug, n = base, 2
            while Painting.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug, n = f"{base}-{n}", n + 1
        super().save(*args, **kwargs)
        self._set_tint()

    def _set_tint(self):
        """Average colour of the painting; the viewing room takes on this colour."""
        try:
            with Image.open(self.image.path) as im:
                r, g, b = im.convert("RGB").resize((1, 1)).getpixel((0, 0))
        except (OSError, ValueError):
            return
        self.tint = f"#{r:02x}{g:02x}{b:02x}"
        Painting.objects.filter(pk=self.pk).update(tint=self.tint)

    @property
    def can_checkout(self):
        return self.status == self.AVAILABLE and bool(self.price_amount)

    # Layout helpers: give each painting its own slight tilt and drop on the wall.
    @property
    def aspect(self):
        return f"{(self.width or 3) / (self.height or 4):.4f}"

    @property
    def tilt(self):
        return f"{((self.pk or 0) * 37 % 25 - 12) / 10:.1f}"

    @property
    def drop(self):
        return (self.pk or 0) * 13 % 30


def new_reference():
    return uuid.uuid4().hex


class Order(models.Model):
    REQUESTED, PENDING, PAID, CANCELLED = "requested", "pending", "paid", "cancelled"
    STATUS = [(REQUESTED, "Requested (artist will contact buyer)"), (PENDING, "Awaiting payment"),
              (PAID, "Paid"), (CANCELLED, "Cancelled")]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    painting = models.ForeignKey(Painting, on_delete=models.PROTECT, related_name="orders")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default=REQUESTED)
    phone = models.CharField(max_length=30)
    address = models.TextField("Delivery address")
    reference = models.CharField(max_length=40, unique=True, default=new_reference, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.painting.title} for {self.customer}"

    def mark_paid(self):
        self.status, self.paid_at = self.PAID, timezone.now()
        self.save(update_fields=["status", "paid_at"])
        Painting.objects.filter(pk=self.painting_id).update(status=Painting.SOLD)



class CommissionRequest(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("discussing", "In discussion"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("completed", "Completed"),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="commissions"
    )
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    description = models.TextField(help_text="What would you like painted?")
    budget = models.CharField(max_length=60, blank=True, help_text="Optional budget range")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Commission from {self.name} ({self.created:%d %b %Y})"


class CommissionReference(models.Model):
    commission = models.ForeignKey(
        CommissionRequest, on_delete=models.CASCADE, related_name="references"
    )
    image = models.ImageField(upload_to="commissions/%Y/%m/")
    uploaded = models.DateTimeField(auto_now_add=True)