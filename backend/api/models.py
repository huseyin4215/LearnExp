from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Kullanıcı profil bilgileri"""
    
    PROFESSION_CHOICES = [
        ('student', 'Öğrenci'),
        ('researcher', 'Araştırmacı'),
        ('professor', 'Profesör/Akademisyen'),
        ('engineer', 'Mühendis'),
        ('developer', 'Yazılım Geliştirici'),
        ('data_scientist', 'Veri Bilimci'),
        ('doctor', 'Doktor'),
        ('lawyer', 'Avukat'),
        ('teacher', 'Öğretmen'),
        ('business', 'İş İnsanı'),
        ('freelancer', 'Serbest Çalışan'),
        ('other', 'Diğer'),
    ]
    
    EDUCATION_LEVEL_CHOICES = [
        ('high_school', 'Lise'),
        ('associate', 'Ön Lisans'),
        ('bachelor', 'Lisans'),
        ('master', 'Yüksek Lisans'),
        ('phd', 'Doktora'),
        ('postdoc', 'Post-Doktora'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Meslek bilgileri
    profession = models.CharField(max_length=50, choices=PROFESSION_CHOICES, blank=True)
    profession_detail = models.CharField(max_length=200, blank=True, help_text="Meslek detayı")
    company_or_institution = models.CharField(max_length=200, blank=True, help_text="Şirket veya kurum")
    
    # Eğitim bilgileri
    education_level = models.CharField(max_length=20, choices=EDUCATION_LEVEL_CHOICES, blank=True)
    field_of_study = models.CharField(max_length=200, blank=True, help_text="Mezuniyet/Okuma alanı")
    university = models.CharField(max_length=200, blank=True, help_text="Üniversite")
    graduation_year = models.IntegerField(null=True, blank=True)
    
    # Biyografi
    bio = models.TextField(blank=True, max_length=500, help_text="Kısa biyografi")
    
    # İlgi alanları (JSON listesi olarak)
    interests = models.JSONField(default=list, help_text="İlgi alanları listesi")
    
    # Araştırma alanları
    research_areas = models.JSONField(default=list, help_text="Araştırma alanları")
    
    # Sosyal medya
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    orcid = models.CharField(max_length=50, blank=True, help_text="ORCID ID")
    google_scholar = models.URLField(blank=True)
    
    # Profil durumu
    is_profile_complete = models.BooleanField(default=False)
    
    # Avatar
    avatar_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Kullanıcı Profili"
        verbose_name_plural = "Kullanıcı Profilleri"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} - Profil"
    
    def get_interests_display(self):
        return ", ".join(self.interests) if self.interests else "-"


class SavedArticle(models.Model):
    """Kullanıcının kaydedilen makaleleri"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_articles')
    # Optional FK to a database article
    article = models.ForeignKey(
        'api_collecter.Article', on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='saved_by'
    )
    # Article data (for live-search articles not in DB)
    external_id = models.CharField(max_length=500)
    title = models.CharField(max_length=1000)
    abstract = models.TextField(blank=True, default='')
    authors = models.JSONField(default=list)
    published_date = models.CharField(max_length=50, blank=True, default='')
    journal = models.CharField(max_length=500, blank=True, default='')
    url = models.URLField(max_length=2000, blank=True, default='')
    pdf_url = models.URLField(max_length=2000, blank=True, default='')
    doi = models.CharField(max_length=200, blank=True, default='')
    source_name = models.CharField(max_length=100, blank=True, default='')
    categories = models.JSONField(default=list)
    citation_count = models.IntegerField(default=0)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'external_id']
        ordering = ['-saved_at']
        verbose_name = 'Kaydedilen Makale'
        verbose_name_plural = 'Kaydedilen Makaleler'

    def __str__(self):
        return f"{self.user.username} - {self.title[:50]}"


# Önceden tanımlı ilgi alanları
PREDEFINED_INTERESTS = [
    # Bilgisayar Bilimleri
    "Yapay Zeka", "Makine Öğrenmesi", "Derin Öğrenme", "Doğal Dil İşleme",
    "Bilgisayarlı Görü", "Robotik", "Veri Bilimi", "Büyük Veri",
    "Siber Güvenlik", "Blockchain", "Web Geliştirme", "Mobil Uygulama",
    "Bulut Bilişim", "IoT", "Oyun Geliştirme",
    
    # Mühendislik
    "Elektrik Mühendisliği", "Makine Mühendisliği", "İnşaat Mühendisliği",
    "Kimya Mühendisliği", "Biyomedikal Mühendislik", "Endüstri Mühendisliği",
    
    # Fen Bilimleri
    "Fizik", "Kimya", "Biyoloji", "Matematik", "Astronomi", "Jeoloji",
    "Çevre Bilimleri", "Nanoteknoloji", "Biyoteknoloji", "Genetik",
    
    # Sağlık
    "Tıp", "Eczacılık", "Hemşirelik", "Psikoloji", "Beslenme",
    "Halk Sağlığı", "Nörobilim", "Onkoloji", "Kardiyoloji",
    
    # Sosyal Bilimler
    "Ekonomi", "İşletme", "Finans", "Pazarlama", "Hukuk",
    "Siyaset Bilimi", "Sosyoloji", "Eğitim Bilimleri",
    "İletişim", "Uluslararası İlişkiler", "Kamu Yönetimi",
    
    # Sanat ve Beşeri Bilimler
    "Edebiyat", "Tarih", "Felsefe", "Dilbilim", "Sanat Tarihi",
    "Müzik", "Mimarlık", "Tasarım", "Arkeoloji",
    
    # Diğer
    "Girişimcilik", "Yenilikçilik", "Sürdürülebilirlik", "Enerji",
    "Tarım", "Gıda Teknolojisi", "Uzay Bilimleri"
]
