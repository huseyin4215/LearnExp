import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { userStorage } from '../services/api';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

type SettingsTab = 'account' | 'interests' | 'security' | 'notifications';

const PROFESSION_OPTIONS = [
  { value: 'student', label: 'Öğrenci' },
  { value: 'researcher', label: 'Araştırmacı' },
  { value: 'professor', label: 'Profesör / Akademisyen' },
  { value: 'engineer', label: 'Mühendis' },
  { value: 'developer', label: 'Yazılım Geliştirici' },
  { value: 'data_scientist', label: 'Veri Bilimci' },
  { value: 'doctor', label: 'Doktor' },
  { value: 'lawyer', label: 'Avukat' },
  { value: 'teacher', label: 'Öğretmen' },
  { value: 'business', label: 'İş İnsanı' },
  { value: 'freelancer', label: 'Serbest Çalışan' },
  { value: 'other', label: 'Diğer' },
];

const EDUCATION_OPTIONS = [
  { value: 'high_school', label: 'Lise' },
  { value: 'associate', label: 'Ön Lisans' },
  { value: 'bachelor', label: 'Lisans' },
  { value: 'master', label: 'Yüksek Lisans' },
  { value: 'phd', label: 'Doktora' },
  { value: 'postdoc', label: 'Post-Doktora' },
];

interface UserProfileForm {
  fullName: string;
  email: string;
  profession: string;
  professionDetail: string;
  companyOrInstitution: string;
  educationLevel: string;
  fieldOfStudy: string;
  university: string;
  graduationYear: string;
  bio: string;
  interests: string[];
  researchAreas: string[];
  website: string;
  linkedin: string;
  twitter: string;
  orcid: string;
  googleScholar: string;
}

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<SettingsTab>('account');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [newInterest, setNewInterest] = useState('');
  const [newResearchArea, setNewResearchArea] = useState('');

  const [formData, setFormData] = useState<UserProfileForm>({
    fullName: '',
    email: '',
    profession: '',
    professionDetail: '',
    companyOrInstitution: '',
    educationLevel: '',
    fieldOfStudy: '',
    university: '',
    graduationYear: '',
    bio: '',
    interests: [],
    researchAreas: [],
    website: '',
    linkedin: '',
    twitter: '',
    orcid: '',
    googleScholar: '',
  });

  useEffect(() => {
    const fetchUserData = async () => {
      const storedUser = userStorage.getUser();
      if (!storedUser) {
        navigate('/login');
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/user/${storedUser.id}/`);
        const data = await response.json();
        if (data.success && data.user) {
          const user = data.user;
          const profile = user.profile || {};
          setFormData({
            fullName: user.fullName || '',
            email: user.email || '',
            profession: profile.profession || '',
            professionDetail: profile.professionDetail || '',
            companyOrInstitution: profile.companyOrInstitution || '',
            educationLevel: profile.educationLevel || '',
            fieldOfStudy: profile.fieldOfStudy || '',
            university: profile.university || '',
            graduationYear: profile.graduationYear?.toString() || '',
            bio: profile.bio || '',
            interests: profile.interests || [],
            researchAreas: profile.researchAreas || [],
            website: profile.website || '',
            linkedin: profile.linkedin || '',
            twitter: profile.twitter || '',
            orcid: profile.orcid || '',
            googleScholar: profile.googleScholar || '',
          });
        }
      } catch (error) {
        console.error('Failed to fetch user data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserData();
  }, [navigate]);

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const addInterest = () => {
    if (newInterest.trim() && !formData.interests.includes(newInterest.trim())) {
      setFormData((prev) => ({ ...prev, interests: [...prev.interests, newInterest.trim()] }));
      setNewInterest('');
    }
  };

  const removeInterest = (tag: string) => {
    setFormData((prev) => ({ ...prev, interests: prev.interests.filter((item) => item !== tag) }));
  };

  const addResearchArea = () => {
    if (newResearchArea.trim() && !formData.researchAreas.includes(newResearchArea.trim())) {
      setFormData((prev) => ({ ...prev, researchAreas: [...prev.researchAreas, newResearchArea.trim()] }));
      setNewResearchArea('');
    }
  };

  const removeResearchArea = (tag: string) => {
    setFormData((prev) => ({ ...prev, researchAreas: prev.researchAreas.filter((item) => item !== tag) }));
  };

  const handleSaveProfile = async () => {
    const storedUser = userStorage.getUser();
    if (!storedUser) return;

    setIsSaving(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await fetch(`${API_BASE_URL}/user/${storedUser.id}/profile/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fullName: formData.fullName,
          profession: formData.profession,
          professionDetail: formData.professionDetail,
          companyOrInstitution: formData.companyOrInstitution,
          educationLevel: formData.educationLevel,
          fieldOfStudy: formData.fieldOfStudy,
          university: formData.university,
          graduationYear: formData.graduationYear ? parseInt(formData.graduationYear, 10) : null,
          bio: formData.bio,
          interests: formData.interests,
          researchAreas: formData.researchAreas,
          website: formData.website,
          linkedin: formData.linkedin,
          twitter: formData.twitter,
          orcid: formData.orcid,
          googleScholar: formData.googleScholar,
        }),
      });

      const data = await response.json();
      if (data.success) {
        setMessage({ type: 'success', text: 'Değişiklikler başarıyla kaydedildi.' });
        userStorage.setUser({
          ...storedUser,
          fullName: formData.fullName,
          isProfileComplete: data.isProfileComplete,
        });
      } else {
        setMessage({ type: 'error', text: data.message || 'Kaydetme işlemi başarısız oldu.' });
      }
    } catch (error) {
      console.error('Failed to save profile:', error);
      setMessage({ type: 'error', text: 'Sunucuya bağlanılamadı.' });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-[var(--brand)]" />
      </div>
    );
  }

  const tabs: Array<{ id: SettingsTab; label: string }> = [
    { id: 'account', label: 'Hesap' },
    { id: 'interests', label: 'İlgiler' },
    { id: 'security', label: 'Güvenlik' },
    { id: 'notifications', label: 'Bildirimler' },
  ];

  return (
    <div className="space-y-8">
      <section className="shell page-hero px-6 py-8 md:px-10 md:py-12">
        <div className="relative z-10 text-white">
          <p className="eyebrow text-white/65">Hesap ayarları</p>
          <h1 className="mt-3 font-heading text-5xl leading-tight md:text-6xl">Profilini, ilgi alanlarını ve tercihlerını tek merkezden yönet.</h1>
          <p className="mt-4 max-w-3xl text-base leading-8 text-white/70 md:text-lg">
            Bu alan; profil görünürlüğünü, akademik uzmanlık bilgilerini, araştırma konularını ve temel hesap tercihlerini düzenlemek için kullanılır.
          </p>
        </div>
      </section>

      <section className="shell grid gap-6 lg:grid-cols-[260px_1fr]">
        <aside className="section-card h-fit p-4">
          <div className="grid gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`rounded-[20px] px-4 py-3 text-left text-sm font-semibold transition-colors ${
                  activeTab === tab.id ? 'bg-[var(--brand-soft)] text-[var(--brand)]' : 'text-[var(--text-primary)] hover:bg-[var(--surface-alt)]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </aside>

        <div className="section-card p-6 md:p-8">
          {message.text && (
            <div className={`mb-6 rounded-[18px] px-4 py-3 text-sm ${message.type === 'success' ? 'border border-[rgba(31,143,88,0.2)] bg-[rgba(31,143,88,0.08)] text-[var(--success)]' : 'border border-[rgba(198,69,69,0.2)] bg-[rgba(198,69,69,0.08)] text-[var(--danger)]'}`}>
              {message.text}
            </div>
          )}

          {activeTab === 'account' && (
            <div className="space-y-6">
              <div>
                <p className="eyebrow mb-2">Hesap bilgileri</p>
                <h2 className="font-heading text-4xl text-[var(--text-strong)]">Profil ayrıntıları</h2>
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Tam isim</label>
                  <input name="fullName" value={formData.fullName} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">E-posta</label>
                  <input name="email" value={formData.email} disabled className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-soft)]" />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Meslek</label>
                  <select name="profession" value={formData.profession} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]">
                    <option value="">Seçiniz</option>
                    {PROFESSION_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Kurum / şirket</label>
                  <input name="companyOrInstitution" value={formData.companyOrInstitution} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Eğitim seviyesi</label>
                  <select name="educationLevel" value={formData.educationLevel} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]">
                    <option value="">Seçiniz</option>
                    {EDUCATION_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Alan / bölüm</label>
                  <input name="fieldOfStudy" value={formData.fieldOfStudy} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Üniversite</label>
                  <input name="university" value={formData.university} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Mezuniyet yılı</label>
                  <input name="graduationYear" value={formData.graduationYear} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" />
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Biyografi</label>
                <textarea name="bio" rows={5} value={formData.bio} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" />
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Web sitesi</label>
                  <input name="website" value={formData.website} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">LinkedIn</label>
                  <input name="linkedin" value={formData.linkedin} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Twitter / X</label>
                  <input name="twitter" value={formData.twitter} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">ORCID</label>
                  <input name="orcid" value={formData.orcid} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" />
                </div>
                <div className="md:col-span-2">
                  <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Google Scholar</label>
                  <input name="googleScholar" value={formData.googleScholar} onChange={handleInputChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'interests' && (
            <div className="space-y-6">
              <div>
                <p className="eyebrow mb-2">Akademik ilgi alanları</p>
                <h2 className="font-heading text-4xl text-[var(--text-strong)]">Konular ve araştırma başlıkları</h2>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">İlgi alanları</label>
                <div className="mb-4 flex flex-wrap gap-2">
                  {formData.interests.map((tag) => (
                    <span key={tag} className="chip">
                      {tag}
                      <button onClick={() => removeInterest(tag)} className="ml-1 text-[var(--text-muted)]">×</button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input value={newInterest} onChange={(event) => setNewInterest(event.target.value)} className="flex-1 rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" placeholder="Yeni ilgi alanı ekle..." />
                  <button onClick={addInterest} className="btn-secondary">Ekle</button>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Araştırma alanları</label>
                <div className="mb-4 flex flex-wrap gap-2">
                  {formData.researchAreas.map((tag) => (
                    <span key={tag} className="chip chip-active">
                      {tag}
                      <button onClick={() => removeResearchArea(tag)} className="ml-1 text-[var(--text-muted)]">×</button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input value={newResearchArea} onChange={(event) => setNewResearchArea(event.target.value)} className="flex-1 rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" placeholder="Yeni araştırma alanı ekle..." />
                  <button onClick={addResearchArea} className="btn-secondary">Ekle</button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <div>
                <p className="eyebrow mb-2">Güvenlik</p>
                <h2 className="font-heading text-4xl text-[var(--text-strong)]">Şifre ve erişim yönetimi</h2>
              </div>
              <div className="rounded-[24px] border border-[var(--line-soft)] bg-[var(--surface-alt)] p-6">
                <p className="text-sm text-[var(--text-primary)]">
                  Bu bölüm sonraki adımda gerçek şifre güncelleme akışıyla bağlanabilir. Şimdilik şifre sıfırlama ekranı üzerinden devam edebilirsin.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <div>
                <p className="eyebrow mb-2">Bildirimler</p>
                <h2 className="font-heading text-4xl text-[var(--text-strong)]">Takip tercihleri</h2>
              </div>
              <div className="grid gap-4">
                {[
                  { title: 'E-posta bildirimleri', desc: 'Yeni makale ve konferans duyurularını e-posta ile al.' },
                  { title: 'Haftalık özet', desc: 'Haftanın öne çıkan içeriklerini özet halinde gör.' },
                  { title: 'Fon çağrıları', desc: 'İlgi alanına uygun fonlar çıktığında haberdar ol.' },
                ].map((item) => (
                  <div key={item.title} className="flex items-center justify-between rounded-[24px] border border-[var(--line-soft)] bg-[var(--surface-alt)] p-5">
                    <div>
                      <p className="font-semibold text-[var(--text-strong)]">{item.title}</p>
                      <p className="mt-1 text-sm text-[var(--text-muted)]">{item.desc}</p>
                    </div>
                    <div className="h-6 w-11 rounded-full bg-[var(--brand)]/20 p-1">
                      <div className="h-4 w-4 rounded-full bg-[var(--brand)]" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mt-8 border-t border-[var(--line-soft)] pt-6">
            <button onClick={handleSaveProfile} disabled={isSaving} className="btn-primary disabled:cursor-not-allowed disabled:opacity-60">
              {isSaving ? 'Kaydediliyor...' : 'Değişiklikleri kaydet'}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Settings;
