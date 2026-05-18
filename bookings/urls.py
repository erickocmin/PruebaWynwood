from django.urls import path

from .views import (
    BeginCheckoutView,
    BookingConfirmationView,
    CheckoutServicesView,
    CheckoutView,
    CheckoutPaymentView,
    CheckoutFlexServiceView,
    CheckoutTransportServiceView,
    HomeView,
    LoginView,
    LogoutView,
    PropertyDetailView,
    RegisterView,
    SearchResultsView,
    SetLanguageView,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("search/", SearchResultsView.as_view(), name="search-results"),
    path("properties/<slug:slug>/", PropertyDetailView.as_view(), name="property-detail"),
    path("properties/<slug:slug>/reserve/", BeginCheckoutView.as_view(), name="begin-checkout"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("checkout/services/", CheckoutServicesView.as_view(), name="checkout-services"),
    path("checkout/payment/", CheckoutPaymentView.as_view(), name="checkout-payment"),
    path("checkout/services/flexible/", CheckoutFlexServiceView.as_view(), name="checkout-flex"),
    path("checkout/services/transport/", CheckoutTransportServiceView.as_view(), name="checkout-transport"),
    path("booking/<int:pk>/confirmation/", BookingConfirmationView.as_view(), name="booking-confirmation"),
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("language/<str:language>/", SetLanguageView.as_view(), name="set-language"),
]
