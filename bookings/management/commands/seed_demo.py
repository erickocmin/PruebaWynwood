from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

from bookings.models import (
    AdditionalService,
    Amenity,
    City,
    Country,
    FooterLink,
    FooterSection,
    NavigationItem,
    Property,
    PropertyImage,
    SiteConfiguration,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Insert demo data for the booking flow."

    def handle(self, *args, **options):
        self.create_admin()
        self.create_site_configuration()
        self.create_navigation()
        self.create_footer()
        self.create_countries()
        amenities = self.create_amenities()
        madrid, barcelona, malaga = self.create_cities()
        properties = [
            self.create_property(madrid, "Madrid Gran Via Residence", "Residencia Gran Via Madrid", "madrid-gran-via-residence", "Centro", "Center", Decimal("165.00"), True),
            self.create_property(barcelona, "Barcelona Gothic Loft", "Loft Gotico Barcelona", "barcelona-gothic-loft", "Ciutat Vella", "Ciutat Vella", Decimal("185.00"), True),
            self.create_property(malaga, "Malaga Marina Escape", "Escapada Marina Malaga", "malaga-marina-escape", "Soho", "Soho", Decimal("145.00"), False),
        ]
        for property_obj in properties:
            property_obj.amenities.set(amenities)
            if not property_obj.images.exists():
                self.attach_image(property_obj, property_obj.title_en)
        self.create_additional_services()
        self.stdout.write(self.style.SUCCESS("Demo data inserted successfully."))

    @property
    def media_source_dir(self):
        return Path("media/properties")

    def create_admin(self):
        if not User.objects.filter(email="admin@example.com").exists():
            User.objects.create_superuser(
                username="admin@example.com",
                email="admin@example.com",
                password="AdminPass123!",
                first_name="Admin",
                last_name="WH",
            )

    def create_cities(self):
        madrid, _ = City.objects.get_or_create(
            name_en="Madrid",
            defaults={
                "name_es": "Madrid",
                "country_en": "Spain",
                "country_es": "Espana",
                "hero_copy_en": "Fast-paced living, museums, and walkable neighborhoods.",
                "hero_copy_es": "Vida urbana, museos y barrios caminables.",
                "is_featured": True,
                "latitude": Decimal("40.416800"),
                "longitude": Decimal("-3.703800"),
                "sort_order": 1,
            },
        )
        self.sync_model_fields(
            madrid,
            name_es="Madrid",
            country_en="Spain",
            country_es="Espana",
            hero_copy_en="Fast-paced living, museums, and walkable neighborhoods.",
            hero_copy_es="Vida urbana, museos y barrios caminables.",
            is_featured=True,
            latitude=Decimal("40.416800"),
            longitude=Decimal("-3.703800"),
            sort_order=1,
        )
        barcelona, _ = City.objects.get_or_create(
            name_en="Barcelona",
            defaults={
                "name_es": "Barcelona",
                "country_en": "Spain",
                "country_es": "Espana",
                "hero_copy_en": "Sea views, architecture, and creative energy.",
                "hero_copy_es": "Vistas al mar, arquitectura y energia creativa.",
                "is_featured": True,
                "latitude": Decimal("41.385100"),
                "longitude": Decimal("2.173400"),
                "sort_order": 2,
            },
        )
        self.sync_model_fields(
            barcelona,
            name_es="Barcelona",
            country_en="Spain",
            country_es="Espana",
            hero_copy_en="Sea views, architecture, and creative energy.",
            hero_copy_es="Vistas al mar, arquitectura y energia creativa.",
            is_featured=True,
            latitude=Decimal("41.385100"),
            longitude=Decimal("2.173400"),
            sort_order=2,
        )
        malaga, _ = City.objects.get_or_create(
            name_en="Malaga",
            defaults={
                "name_es": "Malaga",
                "country_en": "Spain",
                "country_es": "Espana",
                "hero_copy_en": "Sun, coastlines, and relaxed long stays.",
                "hero_copy_es": "Sol, costa y estadias largas relajadas.",
                "is_featured": True,
                "latitude": Decimal("36.721300"),
                "longitude": Decimal("-4.421400"),
                "sort_order": 3,
            },
        )
        self.sync_model_fields(
            malaga,
            name_es="Malaga",
            country_en="Spain",
            country_es="Espana",
            hero_copy_en="Sun, coastlines, and relaxed long stays.",
            hero_copy_es="Sol, costa y estadias largas relajadas.",
            is_featured=True,
            latitude=Decimal("36.721300"),
            longitude=Decimal("-4.421400"),
            sort_order=3,
        )
        return madrid, barcelona, malaga

    def create_site_configuration(self):
        site_configuration, _ = SiteConfiguration.objects.get_or_create(
            id=1,
            defaults={
                "site_name": "Wynwood House",
                "contact_email": "hello@wynwoodhouse.com",
                "contact_phone": "+34 555 010 100",
                "promo_text_es": "Corre! 20% de descuento en todos los viajes",
                "promo_text_en": "Hurry! 20% off on every trip",
                "promo_timer_label_es": "Quedan solo",
                "promo_timer_label_en": "Only",
                "instagram_url": "https://www.instagram.com/wynwood.house/",
                "linkedin_url": "https://www.linkedin.com/company/wynwood-house/",
                "facebook_url": "https://www.facebook.com/Wynwoodhouseofficial/",
                "app_store_url": "https://apps.apple.com/",
                "google_play_url": "https://play.google.com/",
                "contact_cta_email": "hello@wynwoodhouse.com",
                "confirmation_tagline": "Home Experience, Hotel Quality",
                "confirmation_social": "@wynwood.house",
                "confirmation_policy_url": "#",
            },
        )
        self.sync_model_fields(
            site_configuration,
            site_name="Wynwood House",
            contact_email="hello@wynwoodhouse.com",
            contact_phone="+34 555 010 100",
            promo_text_es="Corre! 20% de descuento en todos los viajes",
            promo_text_en="Hurry! 20% off on every trip",
            promo_timer_label_es="Quedan solo",
            promo_timer_label_en="Only",
            instagram_url="https://www.instagram.com/wynwood.house/",
            linkedin_url="https://www.linkedin.com/company/wynwood-house/",
            facebook_url="https://www.facebook.com/Wynwoodhouseofficial/",
            app_store_url="https://apps.apple.com/",
            google_play_url="https://play.google.com/",
            contact_cta_email="hello@wynwoodhouse.com",
            confirmation_tagline="Home Experience, Hotel Quality",
            confirmation_social="@wynwood.house",
            confirmation_policy_url="#",
            vat_rate=Decimal("0.1600"),
            city_tax_rate=Decimal("0.0300"),
            loyalty_discount=Decimal("18.00"),
            default_points_divisor=2,
        )

    def create_navigation(self):
        items = [
            ("Casa Wynwood", "Wynwood House", "/", 1),
            ("The Collection*", "The Collection*", "/#featured", 2),
            ("Publica tu propiedad", "List your property", "/#long-stay", 3),
            ("Invierte en Bienes Raices", "Invest in Real Estate", "/search/", 4),
        ]
        for title_es, title_en, url, sort_order in items:
            item, _ = NavigationItem.objects.get_or_create(
                title_en=title_en,
                defaults={"title_es": title_es, "url": url, "sort_order": sort_order, "is_active": True},
            )
            self.sync_model_fields(item, title_es=title_es, url=url, sort_order=sort_order, is_active=True)

    def create_footer(self):
        sections = [
            (
                "Destinos",
                "Destinations",
                1,
                [("Madrid", "Madrid", "/search/"), ("Barcelona", "Barcelona", "/search/"), ("Malaga", "Malaga", "/search/")],
            ),
            (
                "Servicios",
                "Services",
                2,
                [("Grupos y largas estadias", "Groups and long stays", "#"), ("Eventos y producciones", "Events and productions", "#")],
            ),
            (
                "Nosotros",
                "About us",
                3,
                [("Quienes somos", "Who we are", "#"), ("Blog y noticias", "Blog and news", "#"), ("Contactanos", "Contact us", "mailto:hello@wynwoodhouse.com")],
            ),
        ]
        for title_es, title_en, sort_order, links in sections:
            section, _ = FooterSection.objects.get_or_create(
                title_en=title_en,
                defaults={"title_es": title_es, "sort_order": sort_order, "is_active": True},
            )
            self.sync_model_fields(section, title_es=title_es, sort_order=sort_order, is_active=True)
            for link_index, (label_es, label_en, url) in enumerate(links, start=1):
                footer_link, _ = FooterLink.objects.get_or_create(
                    section=section,
                    label_en=label_en,
                    defaults={"label_es": label_es, "url": url, "sort_order": link_index, "is_active": True},
                )
                self.sync_model_fields(
                    footer_link,
                    label_es=label_es,
                    url=url,
                    sort_order=link_index,
                    is_active=True,
                )

    def create_countries(self):
        countries = [
            ("España", "Spain", "ES", "+34"),
            ("Peru", "Peru", "PE", "+51"),
            ("Colombia", "Colombia", "CO", "+57"),
            ("Mexico", "Mexico", "MX", "+52"),
            ("Panama", "Panama", "PA", "+507"),
            ("Estados Unidos", "United States", "US", "+1"),
        ]
        for sort_order, (name_es, name_en, iso_code, phone_code) in enumerate(countries, start=1):
            country, _ = Country.objects.get_or_create(
                iso_code=iso_code,
                defaults={
                    "name_es": name_es,
                    "name_en": name_en,
                    "phone_code": phone_code,
                    "is_active": True,
                    "sort_order": sort_order,
                },
            )
            self.sync_model_fields(
                country,
                name_es=name_es,
                name_en=name_en,
                phone_code=phone_code,
                is_active=True,
                sort_order=sort_order,
            )

    def create_amenities(self):
        amenities = [
            ("elevator", "Ascensor", "Elevator"),
            ("parking", "Estacionamiento", "Indoor Parking"),
            ("tv", "TV", "TV"),
            ("doorman", "Porteria", "Doorman"),
            ("balcony", "Patio o balcon", "Patio or Balcony"),
            ("grill", "Parrilla", "BBQ grill"),
        ]
        created = []
        for index, (key, label_es, label_en) in enumerate(amenities, start=1):
            amenity, _ = Amenity.objects.get_or_create(
                key=key,
                defaults={"label_es": label_es, "label_en": label_en, "sort_order": index},
            )
            self.sync_model_fields(amenity, label_es=label_es, label_en=label_en, sort_order=index)
            created.append(amenity)
        return created

    def create_property(self, city, title_en, title_es, slug, neighborhood_es, neighborhood_en, nightly_price, featured):
        property_obj, _ = Property.objects.get_or_create(
            slug=slug,
            defaults={
                "city": city,
                "title_en": title_en,
                "title_es": title_es,
                "neighborhood_es": neighborhood_es,
                "neighborhood_en": neighborhood_en,
                "summary_en": "A polished apartment built for short and mid-term stays.",
                "summary_es": "Un apartamento cuidado para estadias cortas y medianas.",
                "description_en": "Spacious interiors, strong daylight, fast Wi-Fi, and a smooth booking flow for guests who value design and convenience.",
                "description_es": "Interiores amplios, buena luz natural, Wi-Fi rapido y una experiencia de reserva fluida para huespedes que valoran diseno y conveniencia.",
                "address": f"{slug.replace('-', ' ').title()} 12, Spain",
                "guests": 4,
                "bedrooms": 2,
                "bathrooms": 2,
                "nightly_price": nightly_price,
                "cleaning_fee": Decimal("35.00"),
                "service_fee": Decimal("25.00"),
                "is_featured": featured,
                "is_active": True,
                "long_stay_ready": True,
            },
        )
        self.sync_model_fields(
            property_obj,
            city=city,
            title_en=title_en,
            title_es=title_es,
            neighborhood_es=neighborhood_es,
            neighborhood_en=neighborhood_en,
            summary_en="A polished apartment built for short and mid-term stays.",
            summary_es="Un apartamento cuidado para estadias cortas y medianas.",
            description_en="Spacious interiors, strong daylight, fast Wi-Fi, and a smooth booking flow for guests who value design and convenience.",
            description_es="Interiores amplios, buena luz natural, Wi-Fi rapido y una experiencia de reserva fluida para huespedes que valoran diseno y conveniencia.",
            address=f"{slug.replace('-', ' ').title()} 12, Spain",
            guests=4,
            bedrooms=2,
            bathrooms=2,
            nightly_price=nightly_price,
            cleaning_fee=Decimal("35.00"),
            service_fee=Decimal("25.00"),
            is_featured=featured,
            is_active=True,
            long_stay_ready=True,
        )
        return property_obj

    def attach_image(self, property_obj, label):
        image = Image.new("RGB", (1600, 1000), color=(238, 224, 204))
        draw = ImageDraw.Draw(image)
        draw.rectangle((80, 80, 1520, 920), outline=(35, 32, 28), width=6)
        draw.text((140, 140), label, fill=(35, 32, 28))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        property_image = PropertyImage(property=property_obj, is_primary=True, sort_order=0)
        property_image.image.save(f"{property_obj.slug}.png", ContentFile(buffer.read()), save=True)

    def create_additional_services(self):
        services = [
            {
                "code": "flex",
                "title_en": "Flexible check-in and check-out",
                "title_es": "Check-in y check-out flexible",
                "description_en": "Add schedule flexibility to your arrival or departure without changing your booking dates.",
                "description_es": "Agrega flexibilidad a tu llegada o salida sin cambiar las fechas de tu reserva.",
                "price": Decimal("24.00"),
                "sort_order": 1,
                "image_name": "are-you-ready.webp",
            },
            {
                "code": "transport",
                "title_en": "Transport service",
                "title_es": "Servicio de transporte",
                "description_en": "Schedule secure airport transfers for arrival, departure, or both legs of your stay.",
                "description_es": "Programa traslados seguros al aeropuerto para la llegada, la salida o ambos trayectos.",
                "price": Decimal("83.00"),
                "sort_order": 2,
                "allows_quantity": True,
                "image_name": "hero.jpg",
            },
            {
                "code": "fridge",
                "title_en": "Stock the fridge",
                "title_es": "Llena tu nevera",
                "description_en": "Prepare your stay with pre-arrival grocery packs tailored to your trip.",
                "description_es": "Prepara tu estadia con packs de compras previas a tu llegada segun tu viaje.",
                "price": Decimal("35.00"),
                "sort_order": 3,
                "image_name": "panes.png",
            },
            {
                "code": "crib",
                "title_en": "Baby crib",
                "title_es": "Cuna para bebe",
                "description_en": "Request a crib before arrival to make family stays easier.",
                "description_es": "Solicita una cuna antes de tu llegada para facilitar las estadias en familia.",
                "price": Decimal("18.00"),
                "sort_order": 4,
                "image_name": "vino.png",
            },
        ]
        for service_data in services:
            image_name = service_data.pop("image_name")
            service, _ = AdditionalService.objects.get_or_create(code=service_data["code"], defaults=service_data)
            needs_save = False
            for field, value in service_data.items():
                if getattr(service, field) != value:
                    setattr(service, field, value)
                    needs_save = True
            if needs_save:
                service.save()
            if not service.image:
                self.attach_service_image(service, image_name)

    def attach_service_image(self, service, image_name):
        source_path = self.media_source_dir / image_name
        if not source_path.exists():
            return
        with source_path.open("rb") as image_file:
            service.image.save(image_name, File(image_file), save=True)

    def sync_model_fields(self, instance, **values):
        changed = False
        for field, value in values.items():
            if getattr(instance, field) != value:
                setattr(instance, field, value)
                changed = True
        if changed:
            instance.save()
