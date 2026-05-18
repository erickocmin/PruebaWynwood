from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from .models import Country, FooterSection, NavigationItem, SiteConfiguration


def get_current_language(request):
    language = request.GET.get("lang") or request.session.get("language") or settings.LANGUAGE_CODE
    if language not in {"en", "es"}:
        language = "en"
    request.session["language"] = language
    return language


def localize_city(city, language):
    city.display_name = city.name_es if language == "es" else city.name_en
    city.display_country = city.country_es if language == "es" else city.country_en
    return city


def localize_country(country, language):
    country.display_name = country.name_es if language == "es" else country.name_en
    return country


def localize_property(property_obj, language):
    property_obj.display_title = property_obj.title_es if language == "es" else property_obj.title_en
    property_obj.display_summary = property_obj.summary_es if language == "es" else property_obj.summary_en
    property_obj.display_description = property_obj.description_es if language == "es" else property_obj.description_en
    property_obj.display_neighborhood = property_obj.neighborhood_es if language == "es" else property_obj.neighborhood_en
    if property_obj.city_id:
        localize_city(property_obj.city, language)
    return property_obj


def localize_amenity(amenity, language):
    amenity.display_label = amenity.label_es if language == "es" else amenity.label_en
    return amenity


def localize_additional_service(service, language):
    service.display_title = service.title_es if language == "es" else service.title_en
    service.display_description = service.description_es if language == "es" else service.description_en
    return service


def get_site_configuration():
    return SiteConfiguration.objects.order_by("id").first()


def localize_navigation_item(item, language):
    item.display_title = item.title_es if language == "es" else item.title_en
    return item


def localize_footer_section(section, language):
    section.display_title = section.title_es if language == "es" else section.title_en
    for link in section.links.all():
        link.display_label = link.label_es if language == "es" else link.label_en
    return section


def get_navigation_items(language):
    items = list(NavigationItem.objects.filter(is_active=True))
    for item in items:
        localize_navigation_item(item, language)
    return items


def get_footer_sections(language):
    sections = list(FooterSection.objects.filter(is_active=True).prefetch_related("links"))
    for section in sections:
        localize_footer_section(section, language)
        section.active_links = [link for link in section.links.all() if link.is_active]
    return sections


def build_ui(language):
    return {
        "en": {
            "brand_tagline": "Design-forward stays in Spain",
            "nav_search": "Search",
            "nav_featured": "Featured stays",
            "nav_long_stay": "Long stays",
            "nav_login": "Login",
            "nav_register": "Register",
            "nav_logout": "Logout",
            "hero_title": "Find a home that matches the way you travel.",
            "hero_text": "Flexible stays, curated homes, and a seamless booking journey built for city living.",
            "search_cta": "Search stays",
            "featured_title": "Featured properties",
            "featured_text": "Hand-picked apartments with strong conversion copy, fast availability checks, and image-first presentation.",
            "why_spain_title": "Why travel to Spain",
            "why_spain_text": "From Madrid energy to Malaga coastlines, Spain combines lifestyle, architecture, food, and remote-work friendly neighborhoods.",
            "long_stay_title": "Planning a longer stay?",
            "long_stay_text": "Move in with confidence. Flexible monthly options for work trips, relocations, and slow travel.",
            "contact_us": "Contact us",
            "search_results_title": "Search results",
            "search_results_empty": "No properties match the selected filters yet.",
            "property_details": "Property details",
            "reserve_now": "Reserve now",
            "checkout_title": "Checkout",
            "checkout_text": "Complete your reservation and payment securely.",
            "confirmation_title": "Reservation confirmed",
            "confirmation_text": "Your booking is confirmed and a confirmation email has been sent.",
            "login_title": "Login",
            "register_title": "Create account",
            "new_guest_title": "New guest details",
            "footer_copy": "Thoughtful stays across Spain.",
            "footer_contact": "Contact",
            "footer_social": "Social",
            "header_login": "Login",
            "header_menu": "Menu",
            "header_search": "Search",
            "promo_timer_fallback": "Only",
            "results_city": "City",
            "results_neighborhood": "Neighborhood",
            "results_dates": "Check-in - Check-out",
            "results_guests": "Guests",
            "results_price_range": "Price range",
            "results_amenities": "Amenities",
            "property_search_destination": "Destination",
            "property_add_dates": "Add dates",
            "property_up_to_guests": "Up to %(guests)s guests",
            "property_amenities": "Amenities",
            "property_bedrooms": "Bedrooms",
            "property_distribution": "Layout",
            "property_space_for": "Space for %(guests)s guests",
            "property_email": "Email",
            "property_phone": "Phone",
            "property_special_request": "Special request",
            "property_special_request_placeholder": "Tell us anything we should know before your stay.",
            "property_location": "Location",
            "property_check_dates": "Check-in - Check-out",
            "property_guests": "Guests",
            "checkout_register": "Register",
            "checkout_email_help": "We will send your reservation confirmation by email.",
            "checkout_create_password": "Create password",
            "checkout_password_valid": "Valid password.",
            "checkout_login_prompt": "Already have an account?",
            "checkout_login_link": "Log in",
            "checkout_personal_info": "Personal information",
            "checkout_full_name": "Full name",
            "checkout_nationality": "Nationality",
            "checkout_select_country": "Select your country",
            "checkout_phone": "Phone",
            "checkout_birth_date": "Birth date",
            "checkout_special_services": "Special services",
            "checkout_legal": "By selecting continue, you accept the cancellation policy, terms of service, and privacy policy. You also agree to pay the total amount shown.",
            "checkout_continue": "Continue",
            "checkout_newsletter_copy": "Wynwood will send you exclusive member offers, inspiring content, marketing emails, and push notifications. You can opt out at any time.",
            "checkout_newsletter_opt_out": "I do not want to subscribe to the Wynwood House newsletter.",
            "checkout_help": "Need help completing your reservation?",
            "checkout_dates": "Dates",
            "checkout_cleaning_fee": "Cleaning fee",
            "checkout_service_fee": "Service fee",
            "checkout_total": "Total",
            "checkout_points_copy": "With this booking you are earning",
            "checkout_points_link": "Learn more about Wynwood Points",
            "checkout_welcome": "Welcome to Wynwood House %(name)s",
            "checkout_services_intro": "Select your additional services and payment method to continue with the reservation.",
            "checkout_upgrade": "Upgrade your stay with additional services",
            "checkout_payment_title": "Payment method",
            "checkout_payment_intro": "Review your reservation details to continue.",
            "checkout_complete": "Complete reservation",
            "checkout_change": "Change",
            "checkout_back": "Back",
            "checkout_accept_terms": "I accept the cancellation policy, terms of service, and privacy policy. I also agree to pay the total amount shown.",
            "checkout_subscribe_newsletter": "I want to subscribe to the Wynwood House newsletter.",
            "checkout_tax_label": "Taxes",
            "checkout_city_tax": "City tax",
            "checkout_vat": "VAT",
            "checkout_discount": "Wynwood Points discount",
            "confirmation_reserved": "Booking confirmed",
            "confirmation_hello": "Hello",
            "confirmation_thanks": "Thank you for choosing Wynwood House for your next stay.",
            "confirmation_ready": "You are ready to start your Wynwood Experience.",
            "confirmation_email_notice": "Your reservation has been confirmed and we will send all check-in details to your email before arrival.",
            "confirmation_questions": "If you have any questions, feel free to contact us.",
            "confirmation_chat": "Chat with us 24/7",
            "confirmation_points_label": "With this booking you are collecting",
            "confirmation_points_link": "Discover your benefits",
            "confirmation_additional": "To make the most of your Wynwood experience, explore our additional services to personalize your stay:",
            "confirmation_cleaning_fee": "Cleaning fee",
            "guests": "Guests",
            "check_in": "Check-in",
            "check_out": "Check-out",
            "city": "City",
            "night": "night",
            "nights": "nights",
        },
        "es": {
            "brand_tagline": "Estadias con diseno en Espana",
            "nav_search": "Buscar",
            "nav_featured": "Destacadas",
            "nav_long_stay": "Larga estancia",
            "nav_login": "Ingresar",
            "nav_register": "Crear cuenta",
            "nav_logout": "Salir",
            "hero_title": "Encuentra un hogar que se adapte a tu forma de viajar.",
            "hero_text": "Estadias flexibles, propiedades curadas y una reserva fluida pensada para vivir la ciudad.",
            "search_cta": "Buscar estadias",
            "featured_title": "Propiedades destacadas",
            "featured_text": "Apartamentos seleccionados con presentacion visual fuerte y validacion rapida de disponibilidad.",
            "why_spain_title": "Por que viajar a Espana",
            "why_spain_text": "Desde la energia de Madrid hasta la costa de Malaga, Espana combina estilo de vida, arquitectura, gastronomia y barrios ideales para trabajo remoto.",
            "long_stay_title": "Planeas una estadia larga?",
            "long_stay_text": "Instalate con confianza. Opciones mensuales flexibles para viajes de trabajo, reubicaciones y slow travel.",
            "contact_us": "Contactanos",
            "search_results_title": "Resultados de busqueda",
            "search_results_empty": "Aun no hay propiedades que coincidan con los filtros seleccionados.",
            "property_details": "Detalle de la propiedad",
            "reserve_now": "Reservar ahora",
            "checkout_title": "Checkout",
            "checkout_text": "Completa tu reserva y tu pago de forma segura.",
            "confirmation_title": "Reserva confirmada",
            "confirmation_text": "Tu reserva fue confirmada y enviamos un correo de confirmacion.",
            "login_title": "Ingresar",
            "register_title": "Crear cuenta",
            "new_guest_title": "Datos del nuevo huesped",
            "footer_copy": "Estadias pensadas con criterio en toda Espana.",
            "footer_contact": "Contacto",
            "footer_social": "Redes",
            "header_login": "Iniciar sesion",
            "header_menu": "Menu",
            "header_search": "Buscar",
            "promo_timer_fallback": "Quedan solo",
            "results_city": "Ciudad",
            "results_neighborhood": "Distrito",
            "results_dates": "Llegada - Salida",
            "results_guests": "Huespedes",
            "results_price_range": "Rango de precio",
            "results_amenities": "Comodidades",
            "property_search_destination": "Destino",
            "property_add_dates": "Agregar fechas",
            "property_up_to_guests": "Hasta %(guests)s huespedes",
            "property_amenities": "Amenidades",
            "property_bedrooms": "Habitaciones",
            "property_distribution": "Distribucion",
            "property_space_for": "Espacio para %(guests)s huespedes",
            "property_email": "Correo electronico",
            "property_phone": "Telefono",
            "property_special_request": "Solicitud especial",
            "property_special_request_placeholder": "Cuentanos si debemos saber algo antes de tu estadia.",
            "property_location": "Ubicacion",
            "property_check_dates": "Llegada - Salida",
            "property_guests": "Huespedes",
            "checkout_register": "Registro",
            "checkout_email_help": "Te enviaremos la confirmacion de tu reserva por correo electronico.",
            "checkout_create_password": "Crear contrasena",
            "checkout_password_valid": "Contrasena valida.",
            "checkout_login_prompt": "Ya tienes una cuenta?",
            "checkout_login_link": "Iniciar sesion",
            "checkout_personal_info": "Informacion personal",
            "checkout_full_name": "Nombre completo",
            "checkout_nationality": "Nacionalidad",
            "checkout_select_country": "Selecciona tu pais",
            "checkout_phone": "Telefono",
            "checkout_birth_date": "Fecha de nacimiento",
            "checkout_special_services": "Servicios especiales",
            "checkout_legal": "Al seleccionar continuar, aceptas la politica de cancelacion, los terminos de servicio y la politica de privacidad. Tambien estas de acuerdo en pagar la cantidad total mostrada.",
            "checkout_continue": "Continuar",
            "checkout_newsletter_copy": "Wynwood te enviara ofertas exclusivas para miembros, contenido inspirador, correos comerciales y notificaciones push. Puedes dejar de recibirlos en cualquier momento.",
            "checkout_newsletter_opt_out": "No deseo suscribirme al boletin Wynwood House.",
            "checkout_help": "Necesitas ayuda para completar tu reserva?",
            "checkout_dates": "Fechas",
            "checkout_cleaning_fee": "Tarifa de limpieza",
            "checkout_service_fee": "Cargo por servicio",
            "checkout_total": "Total",
            "checkout_points_copy": "Con esta reserva estas generando",
            "checkout_points_link": "Conoce mas sobre Wynwood Points",
            "checkout_welcome": "Bienvenido a Wynwood House %(name)s",
            "checkout_services_intro": "Selecciona tus servicios adicionales y metodo de pago para continuar con la reserva.",
            "checkout_upgrade": "Eleva tu estadia con servicios adicionales",
            "checkout_payment_title": "Metodo de pago",
            "checkout_payment_intro": "Revisa la informacion de tu reserva para continuar.",
            "checkout_complete": "Completar reserva",
            "checkout_change": "Cambiar",
            "checkout_back": "Volver",
            "checkout_accept_terms": "Acepto la politica de cancelacion, los terminos de servicio y la politica de privacidad. Tambien estoy de acuerdo en pagar la cantidad total mostrada.",
            "checkout_subscribe_newsletter": "Deseo suscribirme al boletin Wynwood House.",
            "checkout_tax_label": "Impuestos",
            "checkout_city_tax": "Impuestos de ciudad",
            "checkout_vat": "IVA",
            "checkout_discount": "Descuento Wynwood Points",
            "confirmation_reserved": "Reserva confirmada",
            "confirmation_hello": "Hola",
            "confirmation_thanks": "Gracias por elegir Wynwood House para tu proxima estadia.",
            "confirmation_ready": "Ya estas listo para comenzar tu Wynwood Experience.",
            "confirmation_email_notice": "Tu reserva ha sido confirmada y antes de tu llegada recibirás en tu correo toda la informacion para el ingreso.",
            "confirmation_questions": "Si tienes alguna inquietud no dudes en comunicarte con nosotros.",
            "confirmation_chat": "Conversa con nosotros 24/7",
            "confirmation_points_label": "Con esta reserva estas acumulando",
            "confirmation_points_link": "Descubre tus beneficios",
            "confirmation_additional": "Para aprovechar al maximo tu experiencia en Wynwood, explora nuestros servicios adicionales para personalizar tu estadia:",
            "confirmation_cleaning_fee": "Tarifa de limpieza",
            "guests": "Huespedes",
            "check_in": "Check-in",
            "check_out": "Check-out",
            "city": "Ciudad",
            "night": "noche",
            "nights": "noches",
        },
    }[language]


def calculate_booking_total(property_obj, check_in, check_out):
    nights = (check_out - check_in).days
    subtotal = Decimal(nights) * property_obj.nightly_price
    return subtotal + property_obj.cleaning_fee + property_obj.service_fee


def send_booking_confirmation(booking, language, absolute_url):
    subject = "Reserva confirmada" if language == "es" else "Booking confirmed"
    html_message = render_to_string(
        "bookings/emails/booking_confirmation.html",
        {"booking": booking, "language": language, "absolute_url": absolute_url},
    )
    plain_message = render_to_string(
        "bookings/emails/booking_confirmation.txt",
        {"booking": booking, "language": language, "absolute_url": absolute_url},
    )
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.guest.email],
        html_message=html_message,
    )


def build_confirmation_url(request, booking):
    return request.build_absolute_uri(reverse("booking-confirmation", kwargs={"pk": booking.pk}))
