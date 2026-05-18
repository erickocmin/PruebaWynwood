from django.contrib import admin

from .models import (
    AdditionalService,
    Amenity,
    Booking,
    City,
    Country,
    FooterLink,
    FooterSection,
    NavigationItem,
    Property,
    PropertyImage,
    SiteConfiguration,
)


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name_en", "country_en", "is_featured", "sort_order")
    search_fields = ("name_en", "name_es")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title_en", "city", "nightly_price", "guests", "is_featured", "is_active")
    list_filter = ("city", "is_featured", "is_active", "long_stay_ready")
    search_fields = ("title_en", "title_es", "slug", "address")
    prepopulated_fields = {"slug": ("title_en",)}
    inlines = [PropertyImageInline]
    filter_horizontal = ("amenities",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("property", "guest", "check_in", "check_out", "guests", "status", "total_amount")
    list_filter = ("status", "check_in", "check_out")
    search_fields = ("guest__email", "property__title_en", "property__title_es")


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("label_en", "key", "sort_order")
    search_fields = ("label_en", "label_es", "key")
    prepopulated_fields = {"key": ("label_en",)}


@admin.register(AdditionalService)
class AdditionalServiceAdmin(admin.ModelAdmin):
    list_display = ("title_en", "code", "price", "is_active", "sort_order")
    list_filter = ("is_active", "allows_quantity")
    search_fields = ("title_en", "title_es", "code")
    prepopulated_fields = {"code": ("title_en",)}


class FooterLinkInline(admin.TabularInline):
    model = FooterLink
    extra = 1


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name_en", "iso_code", "phone_code", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name_en", "name_es", "iso_code")


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ("site_name", "contact_email", "contact_phone")


@admin.register(NavigationItem)
class NavigationItemAdmin(admin.ModelAdmin):
    list_display = ("title_en", "url", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("title_en", "title_es", "url")


@admin.register(FooterSection)
class FooterSectionAdmin(admin.ModelAdmin):
    list_display = ("title_en", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("title_en", "title_es")
    inlines = [FooterLinkInline]
