from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import RegisterForm
from .models import AdditionalService, Amenity, Booking, City, Country, FooterSection, NavigationItem, Property, SiteConfiguration

User = get_user_model()


class BookingModelTests(TestCase):
    def setUp(self):
        SiteConfiguration.objects.create(site_name="Wynwood House")
        NavigationItem.objects.create(title_es="Inicio", title_en="Home", url="/", sort_order=1)
        FooterSection.objects.create(title_es="Contacto", title_en="Contact", sort_order=1)
        self.city = City.objects.create(name_es="Madrid", name_en="Madrid")
        self.property = Property.objects.create(
            city=self.city,
            title_es="Apartamento",
            title_en="Apartment",
            slug="apartment",
            neighborhood_es="Centro",
            neighborhood_en="Center",
            summary_es="Resumen",
            summary_en="Summary",
            description_es="Descripcion",
            description_en="Description",
            address="Street 1",
            guests=2,
            bedrooms=1,
            bathrooms=1,
            nightly_price="100.00",
        )
        self.user = User.objects.create_user(username="guest@example.com", email="guest@example.com", password="Secret123!")

    def test_booking_cannot_overlap(self):
        today = timezone.localdate() + timedelta(days=10)
        Booking.objects.create(
            property=self.property,
            guest=self.user,
            check_in=today,
            check_out=today + timedelta(days=2),
            guests=2,
            total_amount="200.00",
        )
        conflicting = Booking(
            property=self.property,
            guest=self.user,
            check_in=today + timedelta(days=1),
            check_out=today + timedelta(days=3),
            guests=2,
            total_amount="200.00",
        )
        with self.assertRaises(ValidationError):
            conflicting.full_clean()

    def test_booking_requires_future_dates(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        tomorrow = timezone.localdate() + timedelta(days=1)
        booking = Booking(
            property=self.property,
            guest=self.user,
            check_in=yesterday,
            check_out=tomorrow,
            guests=1,
            total_amount="100.00",
        )
        with self.assertRaises(ValidationError):
            booking.full_clean()


class RegisterFormTests(TestCase):
    def test_register_form_rejects_duplicate_email_case_insensitive(self):
        User.objects.create_user(username="guest@example.com", email="guest@example.com", password="Secret123!")
        form = RegisterForm(
            data={"first_name": "Jimmy", "email": "Guest@Example.com", "password1": "AnotherPass123!"},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CheckoutFlowTests(TestCase):
    def setUp(self):
        SiteConfiguration.objects.create(site_name="Wynwood House")
        NavigationItem.objects.create(title_es="Inicio", title_en="Home", url="/", sort_order=1)
        FooterSection.objects.create(title_es="Contacto", title_en="Contact", sort_order=1)
        self.country = Country.objects.create(name_es="Peru", name_en="Peru", iso_code="PE", phone_code="+51")
        self.city = City.objects.create(name_es="Madrid", name_en="Madrid")
        self.amenity = Amenity.objects.create(key="tv", label_es="TV", label_en="TV", sort_order=1)
        self.property = Property.objects.create(
            city=self.city,
            title_es="Apartamento Centro",
            title_en="Downtown Apartment",
            slug="downtown-apartment",
            neighborhood_es="Centro",
            neighborhood_en="Center",
            summary_es="Resumen",
            summary_en="Summary",
            description_es="Descripcion",
            description_en="Description",
            address="Street 123",
            guests=4,
            bedrooms=2,
            bathrooms=2,
            nightly_price="150.00",
            cleaning_fee="25.00",
            service_fee="15.00",
            is_active=True,
        )
        self.property.amenities.add(self.amenity)
        AdditionalService.objects.create(
            code="transport",
            title_es="Servicio de transporte",
            title_en="Transport service",
            description_es="Traslado seguro.",
            description_en="Safe transfer.",
            price="83.00",
            is_active=True,
            allows_quantity=True,
            sort_order=1,
        )

    def test_checkout_payment_creates_booking_user_and_confirmation_email(self):
        session = self.client.session
        check_in = timezone.localdate() + timedelta(days=10)
        check_out = check_in + timedelta(days=3)
        session["pending_booking"] = {
            "property_id": self.property.pk,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "guests": 2,
            "special_request": "Late arrival",
            "selected_services": [],
        }
        session["checkout_details"] = {
            "nationality": self.country.pk,
            "birth_date": "1995-04-20",
            "guest_phone": "+51999999999",
            "newsletter_opt_out": True,
            "register": {
                "first_name": "Jimmy",
                "email": "jimmy@example.com",
                "password1": "SecurePass123!",
            },
        }
        session.save()

        response = self.client.post(
            reverse("checkout-payment"),
            data={
                "payment-payment_method": "card",
                "payment-cardholder_name": "Jimmy",
                "payment-card_number": "4242 4242 4242 4242",
                "payment-expiry_month": 12,
                "payment-expiry_year": timezone.localdate().year + 1,
                "payment-cvv": "123",
                "payment-billing_address": "Street 123",
                "payment-billing_country": self.country.pk,
                "payment-billing_region": "Lima",
                "payment-billing_city": "Lima",
                "payment-billing_postal_code": "15001",
                "payment-accept_terms": "on",
                "payment_method": "card",
                "cardholder_same_person": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.get()
        self.assertEqual(booking.property, self.property)
        self.assertEqual(booking.guest.email, "jimmy@example.com")
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("jimmy@example.com", mail.outbox[0].to)

    def test_checkout_payment_reuses_existing_booking_on_duplicate_google_submit(self):
        check_in = timezone.localdate() + timedelta(days=10)
        check_out = check_in + timedelta(days=3)
        user = User.objects.create_user(username="jimmy@example.com", email="jimmy@example.com", password="SecurePass123!")
        booking = Booking.objects.create(
            property=self.property,
            guest=user,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            total_amount="510.00",
            status=Booking.Status.CONFIRMED,
            payment_reference="WH-GOOGLE-1-1",
        )

        session = self.client.session
        session["pending_booking"] = {
            "property_id": self.property.pk,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "guests": 2,
            "special_request": "",
            "selected_services": [],
        }
        session["checkout_details"] = {
            "nationality": self.country.pk,
            "birth_date": "1995-04-20",
            "guest_phone": "+51999999999",
            "newsletter_opt_out": True,
            "register": {
                "first_name": "Jimmy",
                "email": "jimmy@example.com",
                "password1": "SecurePass123!",
            },
        }
        session.save()

        response = self.client.post(
            reverse("checkout-payment"),
            data={
                "payment_method": "google",
                "accept_terms_google": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(response.url, reverse("booking-confirmation", kwargs={"pk": booking.pk}))

    def test_property_detail_renders_db_backed_amenities(self):
        response = self.client.get(reverse("property-detail", kwargs={"slug": self.property.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TV")
