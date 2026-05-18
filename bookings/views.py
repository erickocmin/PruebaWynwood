from datetime import date, timedelta
from copy import copy
import json
from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView
from django.db.models import Q
from django.contrib.auth.password_validation import get_default_password_validators

from .forms import BookingForm, CheckoutForm, CheckoutProfileForm, LoginForm, RegisterForm, SearchForm
from .models import AdditionalService, Booking, City, Property
from .utils import (
    build_confirmation_url,
    build_ui,
    calculate_booking_total,
    get_footer_sections,
    get_current_language,
    localize_additional_service,
    localize_amenity,
    localize_city,
    localize_footer_section,
    localize_navigation_item,
    localize_property,
    send_booking_confirmation,
    get_navigation_items,
    get_site_configuration,
)

User = get_user_model()


def get_additional_services(language):
    services = list(AdditionalService.objects.filter(is_active=True))
    for service in services:
        localize_additional_service(service, language)
        service.id = service.code
        service.title = service.display_title
        service.description = service.display_description
        service.image_url = service.image.url if service.image else ""
    return services


def get_additional_service_map(language):
    return {service.code: service for service in get_additional_services(language)}


def get_site_rates():
    site_settings = get_site_configuration()
    vat_rate = site_settings.vat_rate if site_settings else Decimal("0.1600")
    city_tax_rate = site_settings.city_tax_rate if site_settings else Decimal("0.0300")
    loyalty_discount = site_settings.loyalty_discount if site_settings else Decimal("18.00")
    points_divisor = site_settings.default_points_divisor if site_settings and site_settings.default_points_divisor else 2
    return site_settings, vat_rate, city_tax_rate, loyalty_discount, points_divisor


def build_selected_services(pending, language):
    selected_service_ids = pending.get("selected_services", [])
    transport_details = pending.get("transport_details", {})
    services_by_code = get_additional_service_map(language)
    services = []
    for service_id in selected_service_ids:
        service = services_by_code.get(service_id)
        if not service:
            continue
        service_copy = {
            "id": service.code,
            "title": service.display_title,
            "description": service.display_description,
            "image": service.image_url,
            "price": service.price,
        }
        if service_copy["id"] == "transport":
            quantity = max(1, int(transport_details.get("quantity", 1) or 1))
            service_copy["quantity"] = quantity
            service_copy["price"] = service_copy["price"] * quantity
            service_copy["trip_type"] = transport_details.get("trip_type", "idavuelta")
            service_copy["vehicle_type"] = transport_details.get("vehicle_type", "suv")
        services.append(service_copy)
    return services


def build_property_gallery(property_obj, minimum=3):
    gallery = []
    slug_media_prefix = f"/media/properties/{property_obj.slug}/"
    for image in property_obj.images.all():
        image_url = image.image.url
        if image_url.startswith(slug_media_prefix):
            continue
        if any(item["url"] == image_url for item in gallery):
            continue
        gallery.append(
            {
                "url": image_url,
                "alt": image.alt_text_es or image.alt_text_en or property_obj.display_title,
            }
        )
    if not gallery and property_obj.primary_image:
        gallery.append(
            {
                "url": property_obj.primary_image.image.url,
                "alt": property_obj.primary_image.alt_text_es or property_obj.primary_image.alt_text_en or property_obj.display_title,
            }
        )
    if not gallery:
        return []
    while len(gallery) < minimum:
        gallery.append(dict(gallery[0]))
    return gallery


def get_city_coordinates(city):
    return (float(city.latitude), float(city.longitude))


def mark_invalid_form_fields(form):
    if not form:
        return form
    for name, field in form.fields.items():
        css_class = field.widget.attrs.get("class", "")
        classes = css_class.split()
        if name in form.errors and "is-invalid" not in classes:
            classes.append("is-invalid")
            field.widget.attrs["class"] = " ".join(filter(None, classes))
    return form


def mark_valid_form_fields(form):
    if not form:
        return form
    for name, field in form.fields.items():
        if name != "password1":
            continue
        css_class = field.widget.attrs.get("class", "")
        classes = css_class.split()
        if name not in form.errors and form.is_bound and form.cleaned_data.get(name) and "is-valid" not in classes:
            classes.append("is-valid")
            field.widget.attrs["class"] = " ".join(filter(None, classes))
    return form


class LanguageContextMixin:
    def dispatch(self, request, *args, **kwargs):
        self.language = get_current_language(request)
        self.ui = build_ui(self.language)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ui"] = self.ui
        context["current_language"] = self.language
        context["search_form"] = kwargs.get("search_form") or SearchForm(self.request.GET or None)
        return context


class HomeView(LanguageContextMixin, TemplateView):
    template_name = "bookings/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        featured_properties = list(Property.objects.filter(is_featured=True, is_active=True).select_related("city").prefetch_related("images"))
        for property_obj in featured_properties:
            localize_property(property_obj, self.language)
        featured_cities = list(City.objects.filter(is_featured=True))
        hero_property = featured_properties[0] if featured_properties else None
        for city in featured_cities:
            localize_city(city, self.language)
            city.display_copy = city.hero_copy_es if self.language == "es" else city.hero_copy_en
            city.cover_property = city.properties.filter(is_active=True).prefetch_related("images").first()
            if city.cover_property:
                localize_property(city.cover_property, self.language)
        city_neighborhoods = defaultdict(list)
        active_properties = Property.objects.filter(is_active=True).select_related("city")
        for property_obj in active_properties:
            label = property_obj.neighborhood_es if self.language == "es" else property_obj.neighborhood_en
            if label and label not in city_neighborhoods[str(property_obj.city_id)]:
                city_neighborhoods[str(property_obj.city_id)].append(label)
        for city_id in city_neighborhoods:
            city_neighborhoods[city_id] = sorted(city_neighborhoods[city_id])
        context["featured_properties"] = featured_properties
        context["featured_cities"] = featured_cities
        context["search_form"] = SearchForm(self.request.GET or None)
        context["hero_property"] = hero_property
        context["city_neighborhoods"] = dict(city_neighborhoods)
        return context


class SearchResultsView(LanguageContextMixin, ListView):
    template_name = "bookings/search_results.html"
    context_object_name = "properties"

    def get_queryset(self):
        self.form = SearchForm(self.request.GET or None)
        queryset = Property.objects.filter(is_active=True).select_related("city").prefetch_related("images")
        if self.form.is_valid():
            city = self.form.cleaned_data.get("city")
            check_in = self.form.cleaned_data.get("check_in")
            check_out = self.form.cleaned_data.get("check_out")
            guests = self.form.cleaned_data.get("guests")
            neighborhoods = [
                item.strip()
                for item in (self.request.GET.get("neighborhoods") or "").split(",")
                if item.strip()
            ]
            if city:
                queryset = queryset.filter(city=city)
            if guests:
                queryset = queryset.filter(guests__gte=guests)
            if neighborhoods:
                queryset = queryset.filter(
                    Q(neighborhood_es__in=neighborhoods) | Q(neighborhood_en__in=neighborhoods)
                )
            if check_in and check_out:
                queryset = queryset.exclude(
                    bookings__status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
                    bookings__check_in__lt=check_out,
                    bookings__check_out__gt=check_in,
                )
        base_results = list(queryset.distinct())
        results = []
        if base_results:
            while len(results) < 6:
                results.append(copy(base_results[len(results) % len(base_results)]))
            results = results[:6]
        map_positions = [
            (0.36, 0.27),
            (0.60, 0.39),
            (0.22, 0.54),
            (0.72, 0.62),
            (0.42, 0.71),
            (0.54, 0.22),
            (0.80, 0.30),
            (0.18, 0.78),
        ]
        for index, property_obj in enumerate(results):
            localize_property(property_obj, self.language)
            local_gallery = [item["url"] for item in build_property_gallery(property_obj, minimum=3)[:5]]
            gallery_urls = local_gallery[:]
            property_obj.gallery_urls = gallery_urls
            property_obj.gallery_json = json.dumps(gallery_urls)
            property_obj.map_position = map_positions[index % len(map_positions)]
            base_lat, base_lng = get_city_coordinates(property_obj.city)
            offset_lat = ((index % 3) - 1) * 0.008
            offset_lng = ((index % 4) - 1.5) * 0.008
            property_obj.map_lat = round(base_lat + offset_lat, 6)
            property_obj.map_lng = round(base_lng + offset_lng, 6)
        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = self.form
        context["results_count"] = len(context["properties"])
        context["map_results"] = [
            {
                "title": property_obj.display_title,
                "price": str(property_obj.nightly_price),
                "lat": property_obj.map_lat,
                "lng": property_obj.map_lng,
                "city": property_obj.city.display_name,
                "url": property_obj.get_absolute_url(),
            }
            for property_obj in context["properties"]
        ]
        return context


class PropertyDetailView(LanguageContextMixin, DetailView):
    template_name = "bookings/property_detail.html"
    model = Property
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "property"

    def get_queryset(self):
        return Property.objects.filter(is_active=True).select_related("city").prefetch_related("images", "amenities")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        property_obj = context["property"]
        self.request.session["last_viewed_property_slug"] = property_obj.slug
        localize_property(property_obj, self.language)
        gallery = build_property_gallery(property_obj, minimum=3)
        map_lat, map_lng = get_city_coordinates(property_obj.city)
        context["booking_form"] = kwargs.get("booking_form") or self.kwargs.get("booking_form") or BookingForm(property_obj=property_obj, initial={"guests": 1})
        context["property_gallery"] = gallery
        context["property_gallery_json"] = json.dumps([item["url"] for item in gallery])
        context["detail_map_data"] = {
            "title": property_obj.display_title,
            "city": property_obj.city.display_name,
            "country": property_obj.city.display_country,
            "lat": map_lat,
            "lng": map_lng,
        }
        context["nightly_total"] = property_obj.nightly_price + property_obj.cleaning_fee + property_obj.service_fee
        amenities = list(property_obj.amenities.all())
        for amenity in amenities:
            localize_amenity(amenity, self.language)
            amenity.label = amenity.display_label
        context["amenities"] = amenities
        return context


class BeginCheckoutView(LanguageContextMixin, FormView):
    form_class = BookingForm

    def post(self, request, *args, **kwargs):
        property_obj = get_object_or_404(Property, slug=kwargs["slug"], is_active=True)
        form = BookingForm(request.POST, property_obj=property_obj)
        if form.is_valid():
            cleaned = form.cleaned_data
            request.session["pending_booking"] = {
                "property_id": property_obj.pk,
                "check_in": cleaned["check_in"].isoformat(),
                "check_out": cleaned["check_out"].isoformat(),
                "guests": cleaned["guests"],
                "special_request": cleaned.get("special_request", ""),
            }
            return redirect("checkout")
        messages.error(request, "Please fix the reservation details." if self.language == "en" else "Corrige los datos de la reserva.")
        detail_view = PropertyDetailView.as_view()
        return detail_view(request, slug=property_obj.slug, booking_form=form)


class LoginView(LanguageContextMixin, FormView):
    template_name = "bookings/login.html"
    form_class = LoginForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        login(self.request, form.get_user())
        return redirect(self.request.GET.get("next") or reverse("home"))


class RegisterView(LanguageContextMixin, FormView):
    template_name = "bookings/register.html"
    form_class = RegisterForm

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.request.GET.get("next") or reverse("home"))


class LogoutView(View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("home")


class CheckoutView(LanguageContextMixin, TemplateView):
    template_name = "bookings/checkout.html"

    def build_pending_from_property(self, property_obj, request):
        raw_check_in = request.POST.get("check_in") or request.GET.get("check_in")
        raw_check_out = request.POST.get("check_out") or request.GET.get("check_out")
        raw_guests = request.POST.get("guests") or request.GET.get("guests") or 1
        try:
            check_in = date.fromisoformat(raw_check_in) if raw_check_in else date.today() + timedelta(days=1)
        except (TypeError, ValueError):
            check_in = date.today() + timedelta(days=1)
        try:
            check_out = date.fromisoformat(raw_check_out) if raw_check_out else check_in + timedelta(days=2)
        except (TypeError, ValueError):
            check_out = check_in + timedelta(days=2)
        if check_out <= check_in:
            check_out = check_in + timedelta(days=2)
        try:
            guests = max(1, int(raw_guests))
        except (TypeError, ValueError):
            guests = 1
        return {
            "property_id": property_obj.pk,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "guests": guests,
            "special_request": request.POST.get("special_request", "") or request.GET.get("special_request", ""),
        }

    def bootstrap_pending_booking(self, request):
        property_slug = request.GET.get("property_slug") or request.GET.get("property") or request.session.get("last_viewed_property_slug")
        if not property_slug:
            return None
        property_obj = get_object_or_404(Property, slug=property_slug, is_active=True)
        pending = self.build_pending_from_property(property_obj, request)
        request.session["pending_booking"] = pending
        return pending

    def get(self, request, *args, **kwargs):
        if not request.session.get("pending_booking") and not self.bootstrap_pending_booking(request):
            return redirect("home")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        property_slug = request.POST.get("property_slug")
        if property_slug:
            property_obj = get_object_or_404(Property, slug=property_slug, is_active=True)
            booking_form = BookingForm(request.POST, property_obj=property_obj)
            if booking_form.is_valid():
                cleaned = booking_form.cleaned_data
                pending = {
                    "property_id": property_obj.pk,
                    "check_in": cleaned["check_in"].isoformat(),
                    "check_out": cleaned["check_out"].isoformat(),
                    "guests": cleaned["guests"],
                    "special_request": cleaned.get("special_request", ""),
                }
            else:
                pending = self.build_pending_from_property(property_obj, request)
            request.session["pending_booking"] = pending
            return redirect("checkout")

        pending = request.session.get("pending_booking")
        if not pending:
            return redirect("home")
        property_obj = get_object_or_404(Property, pk=pending["property_id"], is_active=True)
        register_form = RegisterForm(request.POST, prefix="register") if not request.user.is_authenticated else None
        profile_form = CheckoutProfileForm(request.POST, language=self.language)
        register_valid = True
        if register_form is not None:
            register_valid = register_form.is_valid()
            register_form = mark_invalid_form_fields(register_form)
            register_form = mark_valid_form_fields(register_form)
        profile_valid = profile_form.is_valid()
        profile_form = mark_invalid_form_fields(profile_form)
        selected_services = request.POST.getlist("selected_services")
        if register_valid and profile_valid:
            request.session["checkout_details"] = {
                "nationality": profile_form.cleaned_data["nationality"].pk,
                "nationality_label": profile_form.cleaned_data["nationality"].name_es if self.language == "es" else profile_form.cleaned_data["nationality"].name_en,
                "birth_date": profile_form.cleaned_data["birth_date"].isoformat(),
                "guest_phone": profile_form.cleaned_data["guest_phone"],
                "newsletter_opt_out": bool(request.POST.get("newsletter_opt_out")),
                "register": register_form.cleaned_data if register_form is not None else {},
            }
            pending["selected_services"] = selected_services
            request.session["pending_booking"] = pending
            return redirect("checkout-services")
        pending["selected_services"] = selected_services
        request.session["pending_booking"] = pending
        localize_property(property_obj, self.language)
        return self.render_to_response(
            self.get_context_data(
                property=property_obj,
                booking_summary=self.build_booking_summary(pending, property_obj),
                register_form=register_form or mark_invalid_form_fields(RegisterForm(prefix="register")),
                profile_form=profile_form,
                checkout_submitted=True,
            )
        )

    def build_booking_summary(self, pending, property_obj):
        check_in = date.fromisoformat(pending["check_in"])
        check_out = date.fromisoformat(pending["check_out"])
        selected_services = build_selected_services(pending, self.language)
        service_total = sum((service["price"] for service in selected_services), Decimal("0"))
        return {
            "check_in": check_in,
            "check_out": check_out,
            "guests": pending["guests"],
            "nights": (check_out - check_in).days,
            "nightly_subtotal": Decimal((check_out - check_in).days) * property_obj.nightly_price,
            "selected_services": selected_services,
            "service_total": service_total,
            "subtotal": calculate_booking_total(property_obj, check_in, check_out),
            "total": calculate_booking_total(property_obj, check_in, check_out) + service_total,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pending = self.request.session.get("pending_booking")
        if pending:
            property_obj = kwargs.get("property") or get_object_or_404(Property, pk=pending["property_id"], is_active=True)
            localize_property(property_obj, self.language)
            context["property"] = property_obj
            context["booking_summary"] = kwargs.get("booking_summary") or self.build_booking_summary(pending, property_obj)
            gallery = build_property_gallery(property_obj, minimum=1)
            context["checkout_image"] = gallery[0]["url"] if gallery else ""
            _, _, _, _, points_divisor = get_site_rates()
            context["checkout_points"] = int((context["booking_summary"]["total"] or 0) // points_divisor)
        selected_service_ids = self.request.session.get("pending_booking", {}).get("selected_services", [])
        context["register_form"] = kwargs.get("register_form") or RegisterForm(prefix="register")
        initial_profile = self.request.session.get("checkout_details", {})
        if initial_profile.get("nationality"):
            initial_profile = {
                **initial_profile,
                "nationality": initial_profile.get("nationality"),
            }
        context["profile_form"] = kwargs.get("profile_form") or CheckoutProfileForm(
            initial={
                "nationality": initial_profile.get("nationality"),
                "birth_date": initial_profile.get("birth_date"),
                "guest_phone": initial_profile.get("guest_phone"),
            },
            language=self.language,
        )
        context["password_validation_items"] = [
            validator.get_help_text() for validator in get_default_password_validators()
        ]
        context["additional_services"] = [
            {
                "id": service.code,
                "title": service.display_title,
                "description": service.display_description,
                "image": service.image_url,
                "price": service.price,
                "selected": service.code in selected_service_ids,
            }
            for service in get_additional_services(self.language)
        ]
        context["checkout_submitted"] = kwargs.get("checkout_submitted", False)
        return context


class CheckoutServicesView(LanguageContextMixin, TemplateView):
    template_name = "bookings/checkout_services.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("pending_booking"):
            return redirect("home")
        if not request.session.get("checkout_details"):
            return redirect("checkout")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        pending = request.session.get("pending_booking")
        if not pending:
            return redirect("home")
        pending["selected_services"] = request.POST.getlist("selected_services")
        request.session["pending_booking"] = pending
        return redirect("checkout-payment")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pending = self.request.session.get("pending_booking")
        property_obj = get_object_or_404(Property, pk=pending["property_id"], is_active=True)
        localize_property(property_obj, self.language)
        booking_summary = CheckoutView().build_booking_summary(pending, property_obj)
        gallery = build_property_gallery(property_obj, minimum=1)
        checkout_details = self.request.session.get("checkout_details", {})
        context["property"] = property_obj
        context["booking_summary"] = booking_summary
        context["checkout_image"] = gallery[0]["url"] if gallery else ""
        context["checkout_points"] = int((booking_summary["total"] or 0) // 2)
        context["additional_services"] = [
            {
                "id": service.code,
                "title": service.display_title,
                "description": service.display_description,
                "image": service.image_url,
                "price": service.price,
                "selected": service.code in self.request.session.get("pending_booking", {}).get("selected_services", []),
            }
            for service in get_additional_services(self.language)
        ]
        context["guest_name"] = (self.request.user.first_name if self.request.user.is_authenticated else checkout_details.get("register", {}).get("first_name", "")).strip() or "Guest"
        return context


class CheckoutPaymentView(LanguageContextMixin, TemplateView):
    template_name = "bookings/checkout_payment.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("pending_booking"):
            return redirect("home")
        if not request.session.get("checkout_details"):
            return redirect("checkout")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        pending = request.session.get("pending_booking")
        checkout_details = request.session.get("checkout_details", {})
        property_obj = get_object_or_404(Property, pk=pending["property_id"], is_active=True)
        payment_method = request.POST.get("payment_method", "card")
        checkout_form = CheckoutForm(request.POST, prefix="payment", language=self.language)
        confirmation_error = None
        requires_card_fields = payment_method == "card"
        if payment_method == "card" and not request.POST.get("cardholder_same_person"):
            confirmation_error = "Debes confirmar que el titular de la tarjeta es la misma persona que realiza la reserva." if self.language == "es" else "You must confirm that the cardholder is the same person making the reservation."
        elif payment_method == "apple":
            if not request.POST.get("accept_terms_apple"):
                confirmation_error = "Debes aceptar los terminos para continuar con Apple Pay." if self.language == "es" else "You must accept the terms to continue with Apple Pay."
        elif payment_method == "google":
            if not request.POST.get("accept_terms_google"):
                confirmation_error = "Debes aceptar los terminos para continuar con Google Pay." if self.language == "es" else "You must accept the terms to continue with Google Pay."
        if (not requires_card_fields or checkout_form.is_valid()) and confirmation_error is None:
            user = request.user if request.user.is_authenticated else None
            if not request.user.is_authenticated:
                register_data = checkout_details.get("register", {})
                email = (register_data.get("email") or "").strip().lower()
                user = User.objects.filter(email__iexact=email).first() if email else None
                if user is None:
                    register_form = RegisterForm(register_data)
                    if not register_form.is_valid():
                        return redirect("checkout")
                    user = register_form.save()
                login(request, user)
            check_in = date.fromisoformat(pending["check_in"])
            check_out = date.fromisoformat(pending["check_out"])
            booking_summary = self.build_booking_summary(pending, property_obj)
            existing_booking = Booking.objects.filter(
                property=property_obj,
                guest=user,
                check_in=check_in,
                check_out=check_out,
            ).first()
            if existing_booking:
                request.session.pop("pending_booking", None)
                request.session.pop("checkout_details", None)
                return redirect("booking-confirmation", pk=existing_booking.pk)
            booking = Booking(
                property=property_obj,
                guest=user,
                check_in=check_in,
                check_out=check_out,
                guests=pending["guests"],
                special_request=pending.get("special_request", ""),
                total_amount=booking_summary["total"],
                status=Booking.Status.CONFIRMED,
                payment_reference=f"WH-{payment_method.upper()}-{property_obj.pk}-{user.pk}",
            )
            try:
                booking.full_clean()
                booking.save()
            except ValidationError as error:
                existing_booking = Booking.objects.filter(
                    property=property_obj,
                    guest=user,
                    check_in=check_in,
                    check_out=check_out,
                ).first()
                if existing_booking:
                    request.session.pop("pending_booking", None)
                    request.session.pop("checkout_details", None)
                    return redirect("booking-confirmation", pk=existing_booking.pk)
                error_messages = []
                if hasattr(error, "message_dict"):
                    for messages_list in error.message_dict.values():
                        error_messages.extend(messages_list)
                elif hasattr(error, "messages"):
                    error_messages.extend(error.messages)
                confirmation_error = " ".join(error_messages) if error_messages else (
                    "No fue posible completar la reserva. Verifica la disponibilidad e intenta nuevamente."
                    if self.language == "es"
                    else "We could not complete the booking. Please check availability and try again."
                )
            else:
                send_booking_confirmation(booking, self.language, build_confirmation_url(request, booking))
                request.session.pop("pending_booking", None)
                request.session.pop("checkout_details", None)
                return redirect("booking-confirmation", pk=booking.pk)
        localize_property(property_obj, self.language)
        return self.render_to_response(
            self.get_context_data(
                property=property_obj,
                booking_summary=self.build_booking_summary(pending, property_obj),
                checkout_form=checkout_form,
                confirmation_error=confirmation_error,
            )
        )

    def build_booking_summary(self, pending, property_obj):
        check_in = date.fromisoformat(pending["check_in"])
        check_out = date.fromisoformat(pending["check_out"])
        selected_services = build_selected_services(pending, self.language)
        nightly_subtotal = Decimal((check_out - check_in).days) * property_obj.nightly_price
        service_total = sum((service["price"] for service in selected_services), Decimal("0"))
        subtotal = calculate_booking_total(property_obj, check_in, check_out)
        _, vat_rate, city_tax_rate, loyalty_discount, _ = get_site_rates()
        vat = (nightly_subtotal * vat_rate).quantize(Decimal("0.01"))
        city_tax = (nightly_subtotal * city_tax_rate).quantize(Decimal("0.01"))
        discount = loyalty_discount
        total = subtotal + service_total + vat + city_tax - discount
        return {
            "check_in": check_in,
            "check_out": check_out,
            "guests": pending["guests"],
            "nights": (check_out - check_in).days,
            "nightly_subtotal": nightly_subtotal,
            "selected_services": selected_services,
            "service_total": service_total,
            "subtotal": subtotal,
            "vat": vat,
            "city_tax": city_tax,
            "vat_rate": vat_rate,
            "city_tax_rate": city_tax_rate,
            "discount": discount,
            "total": total,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pending = self.request.session.get("pending_booking")
        property_obj = kwargs.get("property") or get_object_or_404(Property, pk=pending["property_id"], is_active=True)
        localize_property(property_obj, self.language)
        booking_summary = kwargs.get("booking_summary") or self.build_booking_summary(pending, property_obj)
        gallery = build_property_gallery(property_obj, minimum=1)
        checkout_details = self.request.session.get("checkout_details", {})
        context["property"] = property_obj
        context["booking_summary"] = booking_summary
        context["checkout_image"] = gallery[0]["url"] if gallery else ""
        _, _, _, _, points_divisor = get_site_rates()
        context["checkout_points"] = int((booking_summary["total"] or 0) // points_divisor)
        context["checkout_form"] = kwargs.get("checkout_form") or CheckoutForm(prefix="payment", language=self.language)
        context["additional_services"] = [
            {
                "id": service.code,
                "title": service.display_title,
                "description": service.display_description,
                "image": service.image_url,
                "price": service.price,
                "selected": service.code in self.request.session.get("pending_booking", {}).get("selected_services", []),
            }
            for service in get_additional_services(self.language)
        ]
        context["guest_name"] = (self.request.user.first_name if self.request.user.is_authenticated else checkout_details.get("register", {}).get("first_name", "")).strip() or "Guest"
        context["confirmation_error"] = kwargs.get("confirmation_error")
        return context


class CheckoutFlexServiceView(LanguageContextMixin, TemplateView):
    template_name = "bookings/checkout_flex.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("pending_booking"):
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        pending = request.session.get("pending_booking")
        if not pending:
            return redirect("home")
        if request.POST.get("action") == "back":
            selected_services = set(pending.get("selected_services", []))
            selected_services.discard("flex")
            pending["selected_services"] = list(selected_services)
            pending.pop("flex_details", None)
            request.session["pending_booking"] = pending
            return redirect("checkout-services")
        selected_services = set(pending.get("selected_services", []))
        selected_services.add("flex")
        pending["selected_services"] = list(selected_services)
        pending["flex_details"] = {
            "request_type": request.POST.get("request_type", "both"),
            "check_in_slot": request.POST.get("check_in_slot", "11:00AM - 1:00PM"),
            "check_out_slot": request.POST.get("check_out_slot", "1:00PM - 3:00PM"),
        }
        request.session["pending_booking"] = pending
        return redirect("checkout-services")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pending = self.request.session.get("pending_booking")
        property_obj = get_object_or_404(Property, pk=pending["property_id"], is_active=True)
        localize_property(property_obj, self.language)
        booking_summary = CheckoutPaymentView().build_booking_summary(pending, property_obj)
        gallery = build_property_gallery(property_obj, minimum=1)
        flex_details = pending.get("flex_details", {})
        context["property"] = property_obj
        context["booking_summary"] = booking_summary
        context["checkout_image"] = gallery[0]["url"] if gallery else ""
        _, _, _, _, points_divisor = get_site_rates()
        context["checkout_points"] = int((booking_summary["total"] or 0) // points_divisor)
        flex_service = get_object_or_404(AdditionalService, code="flex", is_active=True)
        localize_additional_service(flex_service, self.language)
        context["flex_service"] = {
            "id": flex_service.code,
            "title": flex_service.display_title,
            "description": flex_service.display_description,
            "image": flex_service.image.url if flex_service.image else "",
            "price": flex_service.price,
        }
        context["flex_details"] = {
            "request_type": flex_details.get("request_type", "both"),
            "check_in_slot": flex_details.get("check_in_slot", "11:00AM - 1:00PM"),
            "check_out_slot": flex_details.get("check_out_slot", "1:00PM - 3:00PM"),
        }
        return context


class CheckoutTransportServiceView(LanguageContextMixin, TemplateView):
    template_name = "bookings/checkout_transport.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("pending_booking"):
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        pending = request.session.get("pending_booking")
        if not pending:
            return redirect("home")
        if request.POST.get("action") == "back":
            selected_services = set(pending.get("selected_services", []))
            selected_services.discard("transport")
            pending["selected_services"] = list(selected_services)
            pending.pop("transport_details", None)
            request.session["pending_booking"] = pending
            return redirect("checkout-services")
        selected_services = set(pending.get("selected_services", []))
        selected_services.add("transport")
        pending["selected_services"] = list(selected_services)
        pending["transport_details"] = {
            "trip_type": request.POST.get("trip_type", "idavuelta"),
            "vehicle_type": request.POST.get("vehicle_type", "suv"),
            "quantity": max(1, int(request.POST.get("quantity", 1) or 1)),
        }
        request.session["pending_booking"] = pending
        return redirect("checkout-services")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pending = self.request.session.get("pending_booking")
        property_obj = get_object_or_404(Property, pk=pending["property_id"], is_active=True)
        localize_property(property_obj, self.language)
        booking_summary = CheckoutPaymentView().build_booking_summary(pending, property_obj)
        gallery = build_property_gallery(property_obj, minimum=1)
        transport_details = pending.get("transport_details", {})
        context["property"] = property_obj
        context["booking_summary"] = booking_summary
        context["checkout_image"] = gallery[0]["url"] if gallery else ""
        _, _, _, _, points_divisor = get_site_rates()
        context["checkout_points"] = int((booking_summary["total"] or 0) // points_divisor)
        transport_service = get_object_or_404(AdditionalService, code="transport", is_active=True)
        localize_additional_service(transport_service, self.language)
        context["transport_service"] = {
            "id": transport_service.code,
            "title": transport_service.display_title,
            "description": transport_service.display_description,
            "image": transport_service.image.url if transport_service.image else "",
            "price": transport_service.price,
        }
        context["transport_details"] = {
            "trip_type": transport_details.get("trip_type", "idavuelta"),
            "vehicle_type": transport_details.get("vehicle_type", "suv"),
            "quantity": max(1, int(transport_details.get("quantity", 1) or 1)),
        }
        context["transport_total"] = context["transport_service"]["price"] * context["transport_details"]["quantity"]
        return context


class BookingConfirmationView(LanguageContextMixin, LoginRequiredMixin, DetailView):
    template_name = "bookings/confirmation.html"
    model = Booking
    context_object_name = "booking"

    def get_queryset(self):
        return Booking.objects.select_related("property", "guest", "property__city").filter(guest=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = context["booking"]
        property_obj = booking.property
        localize_property(property_obj, self.language)
        gallery = build_property_gallery(property_obj, minimum=1)
        booking_nights = max(1, (booking.check_out - booking.check_in).days)
        nightly_subtotal = property_obj.nightly_price * booking_nights
        context["confirmation_image"] = gallery[0]["url"] if gallery else ""
        context["guest_first_name"] = booking.guest.first_name.strip() if booking.guest else ""
        context["booking_nights"] = booking_nights
        context["nightly_subtotal"] = nightly_subtotal
        _, _, _, loyalty_discount, points_divisor = get_site_rates()
        context["confirmation_discount"] = loyalty_discount
        context["confirmation_points"] = int((booking.total_amount or 0) // points_divisor)
        upsells = get_additional_services(self.language)[:4]
        context["confirmation_upsells"] = [
            {"label": service.display_title, "image": service.image_url}
            for service in upsells
        ]
        return context


class SetLanguageView(View):
    def get(self, request, *args, **kwargs):
        language = kwargs.get("language")
        if language in {"en", "es"}:
            request.session["language"] = language
        return HttpResponseRedirect(request.GET.get("next") or reverse("home"))
