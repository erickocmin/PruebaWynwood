from io import BytesIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from PIL import Image

User = get_user_model()


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class City(TimestampedModel):
    name_es = models.CharField(max_length=120, unique=True)
    name_en = models.CharField(max_length=120, unique=True)
    country_es = models.CharField(max_length=120, default="España")
    country_en = models.CharField(max_length=120, default="Spain")
    hero_copy_es = models.TextField(blank=True)
    hero_copy_en = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=40.416800)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=-3.703800)
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name_es"]
        verbose_name_plural = "cities"

    def __str__(self):
        return self.name_en


class Country(TimestampedModel):
    name_es = models.CharField(max_length=120, unique=True)
    name_en = models.CharField(max_length=120, unique=True)
    iso_code = models.CharField(max_length=2, unique=True)
    phone_code = models.CharField(max_length=8, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name_en"]
        verbose_name_plural = "countries"

    def __str__(self):
        return self.name_en


class SiteConfiguration(TimestampedModel):
    site_name = models.CharField(max_length=120, default="Wynwood House")
    contact_email = models.EmailField(default="hello@wynwoodhouse.com")
    contact_phone = models.CharField(max_length=40, default="+34 555 010 100")
    promo_text_es = models.CharField(max_length=180, blank=True)
    promo_text_en = models.CharField(max_length=180, blank=True)
    promo_timer_label_es = models.CharField(max_length=120, blank=True)
    promo_timer_label_en = models.CharField(max_length=120, blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    app_store_url = models.URLField(blank=True)
    google_play_url = models.URLField(blank=True)
    contact_cta_email = models.EmailField(default="hello@wynwoodhouse.com")
    confirmation_tagline = models.CharField(max_length=180, default="Home Experience, Hotel Quality")
    confirmation_social = models.CharField(max_length=120, default="@wynwood.house")
    confirmation_policy_url = models.URLField(blank=True)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.1600)
    city_tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0300)
    loyalty_discount = models.DecimalField(max_digits=10, decimal_places=2, default=18.00)
    default_points_divisor = models.PositiveIntegerField(default=2)

    def __str__(self):
        return self.site_name


class NavigationItem(TimestampedModel):
    title_es = models.CharField(max_length=120)
    title_en = models.CharField(max_length=120)
    url = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title_en


class FooterSection(TimestampedModel):
    title_es = models.CharField(max_length=120)
    title_en = models.CharField(max_length=120)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title_en


class FooterLink(TimestampedModel):
    section = models.ForeignKey(FooterSection, on_delete=models.CASCADE, related_name="links")
    label_es = models.CharField(max_length=120)
    label_en = models.CharField(max_length=120)
    url = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.label_en


class Property(TimestampedModel):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="properties")
    title_es = models.CharField(max_length=180)
    title_en = models.CharField(max_length=180)
    slug = models.SlugField(unique=True)
    neighborhood_es = models.CharField(max_length=120)
    neighborhood_en = models.CharField(max_length=120)
    summary_es = models.TextField()
    summary_en = models.TextField()
    description_es = models.TextField()
    description_en = models.TextField()
    address = models.CharField(max_length=220)
    guests = models.PositiveIntegerField()
    bedrooms = models.PositiveIntegerField()
    bathrooms = models.PositiveIntegerField()
    nightly_price = models.DecimalField(max_digits=10, decimal_places=2)
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    long_stay_ready = models.BooleanField(default=False)
    amenities = models.ManyToManyField("Amenity", blank=True, related_name="properties")

    class Meta:
        ordering = ["-is_featured", "title_en"]

    def __str__(self):
        return self.title_en

    def get_absolute_url(self):
        return reverse("property-detail", kwargs={"slug": self.slug})

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()


class Amenity(TimestampedModel):
    key = models.SlugField(max_length=50, unique=True)
    label_es = models.CharField(max_length=120)
    label_en = models.CharField(max_length=120)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "label_en"]

    def __str__(self):
        return self.label_en


def property_image_upload_to(instance, filename):
    return f"properties/{instance.property.slug}/{filename}"


class PropertyImage(TimestampedModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=property_image_upload_to)
    alt_text_es = models.CharField(max_length=180, blank=True)
    alt_text_en = models.CharField(max_length=180, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.property.title_en} image"

    def save(self, *args, **kwargs):
        if self.image:
            source = self.image
            image = Image.open(source)
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.thumbnail((1200, 1200))
            output = BytesIO()
            image.save(output, format="WEBP", quality=85, method=6)
            output.seek(0)
            self.image = ContentFile(output.read(), name=f"{Path(source.name).stem}.webp")
        super().save(*args, **kwargs)


def additional_service_upload_to(instance, filename):
    return f"services/{instance.code}/{filename}"


class AdditionalService(TimestampedModel):
    code = models.SlugField(max_length=50, unique=True)
    title_es = models.CharField(max_length=180)
    title_en = models.CharField(max_length=180)
    description_es = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    image = models.ImageField(upload_to=additional_service_upload_to, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    allows_quantity = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "title_en"]

    def __str__(self):
        return self.title_en


class Booking(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="bookings")
    guest = models.ForeignKey(User, on_delete=models.PROTECT, related_name="bookings")
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CONFIRMED)
    payment_reference = models.CharField(max_length=80, blank=True)
    special_request = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "guest", "check_in", "check_out"],
                name="unique_booking_by_guest_and_dates",
            )
        ]

    def __str__(self):
        return f"{self.property.title_en} - {self.guest.email}"

    def clean(self):
        from django.utils import timezone

        today = timezone.localdate()
        if self.check_in and self.check_in < today:
            raise ValidationError({"check_in": "Check-in date cannot be in the past."})
        if self.check_in and self.check_out and self.check_in >= self.check_out:
            raise ValidationError({"check_out": "Check-out must be after check-in."})
        if not self.property_id:
            return
        if self.guests and self.guests > self.property.guests:
            raise ValidationError({"guests": "Guest count exceeds property capacity."})
        overlap_exists = Booking.objects.filter(
            property=self.property,
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
            check_in__lt=self.check_out,
            check_out__gt=self.check_in,
        ).exclude(pk=self.pk).exists()
        if overlap_exists:
            raise ValidationError("This property is already booked for the selected dates.")
