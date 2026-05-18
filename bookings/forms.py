from datetime import date

from django import forms
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import Booking, City, Country

User = get_user_model()


class DateInput(forms.DateInput):
    input_type = "date"


class SearchForm(forms.Form):
    city = forms.ModelChoiceField(queryset=City.objects.none(), required=False, empty_label="Any city")
    check_in = forms.DateField(required=False, widget=DateInput())
    check_out = forms.DateField(required=False, widget=DateInput())
    guests = forms.IntegerField(required=False, min_value=1, max_value=20)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["city"].queryset = City.objects.all()
        self.fields["city"].empty_label = "Ciudad o destino"
        self.fields["city"].widget.attrs.update({"class": "hero-select"})
        self.fields["check_in"].widget.attrs.update({"class": "hero-date", "aria-label": "Check in"})
        self.fields["check_out"].widget.attrs.update({"class": "hero-date", "aria-label": "Check out"})
        self.fields["guests"].widget.attrs.update({"class": "hero-guests", "placeholder": "Numero de huespedes"})

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get("check_in")
        check_out = cleaned_data.get("check_out")
        if check_in and check_in < date.today():
            self.add_error("check_in", "Check-in date cannot be in the past.")
        if check_in and check_out and check_in >= check_out:
            self.add_error("check_out", "Check-out must be after check-in.")
        return cleaned_data


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["check_in", "check_out", "guests", "special_request"]
        widgets = {
            "check_in": DateInput(),
            "check_out": DateInput(),
            "special_request": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, property_obj=None, **kwargs):
        self.property_obj = property_obj
        super().__init__(*args, **kwargs)
        self.fields["check_in"].widget.attrs.update({"class": "booking-field__input", "min": date.today().isoformat()})
        self.fields["check_out"].widget.attrs.update({"class": "booking-field__input", "min": date.today().isoformat()})
        self.fields["guests"].widget.attrs.update({"class": "booking-field__input", "min": 1})
        self.fields["special_request"].widget.attrs.update(
            {"class": "booking-field__textarea", "placeholder": "Tell us anything we should know before your stay."}
        )
        if property_obj:
            self.fields["guests"].max_value = property_obj.guests

    def clean(self):
        cleaned_data = super().clean()
        if not self.property_obj:
            raise ValidationError("Property context is required.")
        booking = Booking(
            property=self.property_obj,
            guest=self.initial.get("guest"),
            check_in=cleaned_data.get("check_in"),
            check_out=cleaned_data.get("check_out"),
            guests=cleaned_data.get("guests") or 1,
            total_amount=0,
        )
        if booking.check_in and booking.check_out:
            booking.full_clean(exclude=["guest", "total_amount", "payment_reference", "status"])
        return cleaned_data


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                raise ValidationError("Invalid email or password.")
        return cleaned_data

    def get_user(self):
        return self.user_cache


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ["first_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget = forms.PasswordInput(render_value=True)
        placeholders = {
            "first_name": "Ingresa tu nombre",
            "email": "correo@ejemplo.com",
            "password1": "Ingresa una nueva contrasena",
        }
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "checkout-input"})
            if name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[name]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        if password1:
            candidate = User(
                username=cleaned_data.get("email", ""),
                email=cleaned_data.get("email", ""),
                first_name=cleaned_data.get("first_name", ""),
            )
            try:
                password_validation.validate_password(password1, candidate)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.username = user.email
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class CheckoutProfileForm(forms.Form):
    nationality = forms.ModelChoiceField(queryset=Country.objects.none(), empty_label="Select your country")
    birth_date = forms.DateField(widget=DateInput())
    guest_phone = forms.CharField(
        max_length=30,
        validators=[
            RegexValidator(
                regex=r"^\+?[0-9 ()-]{7,30}$",
                message="Enter a valid phone number.",
            )
        ],
    )

    def __init__(self, *args, language="en", **kwargs):
        self.language = language
        super().__init__(*args, **kwargs)
        self.fields["nationality"].queryset = Country.objects.filter(is_active=True)
        self.fields["nationality"].empty_label = "Selecciona tu pais" if language == "es" else "Select your country"
        self.fields["nationality"].widget.attrs.update({"class": "checkout-input"})
        self.fields["birth_date"].widget.attrs.update({"class": "checkout-input", "max": date.today().isoformat()})
        self.fields["guest_phone"].widget.attrs.update(
            {"class": "checkout-input", "placeholder": "Ingresa numero de telefono" if language == "es" else "Enter phone number"}
        )

    def clean_birth_date(self):
        birth_date = self.cleaned_data["birth_date"]
        today = date.today()
        if birth_date >= today:
            raise ValidationError("Ingresa una fecha valida." if self.language == "es" else "Enter a valid birth date.")
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 18:
            raise ValidationError(
                "Debes ser mayor de edad para reservar." if self.language == "es" else "You must be an adult to book."
            )
        return birth_date


class CheckoutForm(forms.Form):
    cardholder_name = forms.CharField(max_length=120)
    card_number = forms.CharField(max_length=19, min_length=12)
    expiry_month = forms.IntegerField(min_value=1, max_value=12)
    expiry_year = forms.IntegerField(min_value=date.today().year, max_value=date.today().year + 20)
    cvv = forms.CharField(max_length=4, min_length=3)
    billing_address = forms.CharField(max_length=180)
    billing_country = forms.ModelChoiceField(queryset=Country.objects.none())
    billing_region = forms.CharField(max_length=120)
    billing_city = forms.CharField(max_length=120)
    billing_postal_code = forms.CharField(max_length=20)
    accept_terms = forms.BooleanField()

    def __init__(self, *args, language="en", **kwargs):
        self.language = language
        super().__init__(*args, **kwargs)
        self.fields["billing_country"].queryset = Country.objects.filter(is_active=True)
        for name in ("cardholder_name", "card_number", "cvv", "billing_address", "billing_region", "billing_city", "billing_postal_code"):
            self.fields[name].widget.attrs.update({"class": "checkout-payment-input"})
        self.fields["billing_country"].widget.attrs.update({"class": "checkout-payment-select"})

    def clean_card_number(self):
        digits = "".join(char for char in self.cleaned_data["card_number"] if char.isdigit())
        if len(digits) < 12:
            raise ValidationError("Card number is invalid.")
        return digits

    def clean_cvv(self):
        cvv = "".join(char for char in self.cleaned_data["cvv"] if char.isdigit())
        if len(cvv) not in {3, 4}:
            raise ValidationError("CVV is invalid.")
        return cvv
