"""
Özelleştirilmiş Admin Site
Tüm veri toplama modellerini tek bir grup altında toplar
"""
from django.contrib import admin
from django.contrib.admin.sites import AdminSite


class LearnExpAdminSite(AdminSite):
    site_header = 'LearnExp Yönetim Paneli'
    site_title = 'LearnExp Admin'
    index_title = 'Hoş Geldiniz'


# Varsayılan admin site'ı özelleştir
admin.site.site_header = 'LearnExp Yönetim Paneli'
admin.site.site_title = 'LearnExp Admin'
admin.site.index_title = 'Sistem Yönetimi'

