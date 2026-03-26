import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { userStorage } from '../services/api';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Meslek seçenekleri
const PROFESSION_OPTIONS = [
  { value: 'student', label: 'Öğrenci' },
  { value: 'researcher', label: 'Araştırmacı' },
  { value: 'professor', label: 'Profesör/Akademisyen' },
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

// Eğitim seviyesi seçenekleri
const EDUCATION_OPTIONS = [
  { value: 'high_school', label: 'Lise' },
  { value: 'associate', label: 'Ön Lisans' },
  { value: 'bachelor', label: 'Lisans' },
  { value: 'master', label: 'Yüksek Lisans' },
  { value: 'phd', label: 'Doktora' },
  { value: 'postdoc', label: 'Post-Doktora' },
];

const CompleteProfile: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [predefinedInterests, setPredefinedInterests] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');

  const [formData, setFormData] = useState({
    profession: '',
    professionDetail: '',
    companyOrInstitution: '',
    educationLevel: '',
    fieldOfStudy: '',
    university: '',
    graduationYear: '',
    bio: '',
    interests: [] as string[],
    customInterest: '',
  });

  // İlgi alanlarını yükle
  useEffect(() => {
    fetch(`${API_BASE_URL}/interests/`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setPredefinedInterests(data.interests);
        }
      })
      .catch(console.error);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const toggleInterest = (interest: string) => {
    setFormData(prev => {
      const interests = prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest];
      return { ...prev, interests };
    });
  };

  const addCustomInterest = () => {
    if (formData.customInterest.trim() && !formData.interests.includes(formData.customInterest.trim())) {
      setFormData(prev => ({
        ...prev,
        interests: [...prev.interests, prev.customInterest.trim()],
        customInterest: ''
      }));
    }
  };

  const removeInterest = (interest: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.filter(i => i !== interest)
    }));
  };

  const filteredInterests = predefinedInterests.filter(interest =>
    interest.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSubmit = async () => {
    setIsLoading(true);
    setError('');

    const user = userStorage.getUser();
    if (!user) {
      navigate('/login');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/user/${user.id}/profile/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          graduationYear: formData.graduationYear ? parseInt(formData.graduationYear) : null,
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Kullanıcı bilgilerini güncelle
        userStorage.setUser({ ...user, isProfileComplete: true });
        navigate('/');
      } else {
        setError(data.message || 'Profil kaydedilemedi.');
      }
    } catch (err) {
      setError('Sunucuya bağlanılamadı.');
    } finally {
      setIsLoading(false);
    }
  };

  const canProceed = () => {
    if (currentStep === 1) {
      return formData.profession && formData.educationLevel;
    }
    if (currentStep === 2) {
      return formData.fieldOfStudy;
    }
    if (currentStep === 3) {
      return formData.interests.length >= 3;
    }
    return true;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-indigo-600">LearnExp</h1>
              <p className="text-sm text-slate-500">Profilinizi tamamlayın</p>
            </div>
            <div className="flex items-center space-x-2">
              {[1, 2, 3, 4].map((step) => (
                <div
                  key={step}
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                    step === currentStep
                      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30'
                      : step < currentStep
                      ? 'bg-green-500 text-white'
                      : 'bg-slate-200 text-slate-500'
                  }`}
                >
                  {step < currentStep ? '✓' : step}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-2xl mx-auto px-4 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm mb-6">
            {error}
          </div>
        )}

        {/* Step 1: Meslek ve Eğitim */}
        {currentStep === 1 && (
          <div className="bg-white rounded-2xl shadow-xl p-8 animate-fadeIn">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-slate-800">Meslek ve Eğitim Bilgileriniz</h2>
              <p className="text-slate-500 mt-2">Size daha iyi öneriler sunabilmemiz için</p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Mesleğiniz *</label>
                <select
                  name="profession"
                  value={formData.profession}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50 focus:bg-white"
                >
                  <option value="">Seçiniz...</option>
                  {PROFESSION_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {formData.profession === 'other' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Meslek Detayı</label>
                  <input
                    type="text"
                    name="professionDetail"
                    value={formData.professionDetail}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50 focus:bg-white"
                    placeholder="Mesleğinizi yazın..."
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Kurum / Şirket</label>
                <input
                  type="text"
                  name="companyOrInstitution"
                  value={formData.companyOrInstitution}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50 focus:bg-white"
                  placeholder="Çalıştığınız veya okuduğunuz kurum..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Eğitim Seviyeniz *</label>
                <select
                  name="educationLevel"
                  value={formData.educationLevel}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50 focus:bg-white"
                >
                  <option value="">Seçiniz...</option>
                  {EDUCATION_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Eğitim Detayları */}
        {currentStep === 2 && (
          <div className="bg-white rounded-2xl shadow-xl p-8 animate-fadeIn">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-slate-800">Eğitim Detayları</h2>
              <p className="text-slate-500 mt-2">Akademik geçmişiniz hakkında</p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Bölüm / Alan *</label>
                <input
                  type="text"
                  name="fieldOfStudy"
                  value={formData.fieldOfStudy}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50 focus:bg-white"
                  placeholder="Örn: Bilgisayar Mühendisliği, Tıp, Hukuk..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Üniversite</label>
                <input
                  type="text"
                  name="university"
                  value={formData.university}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50 focus:bg-white"
                  placeholder="Üniversite adı..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Mezuniyet Yılı</label>
                <input
                  type="number"
                  name="graduationYear"
                  value={formData.graduationYear}
                  onChange={handleChange}
                  min="1950"
                  max="2030"
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50 focus:bg-white"
                  placeholder="2024"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 3: İlgi Alanları */}
        {currentStep === 3 && (
          <div className="bg-white rounded-2xl shadow-xl p-8 animate-fadeIn">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-slate-800">İlgi Alanlarınız</h2>
              <p className="text-slate-500 mt-2">En az 3 alan seçin (Seçili: {formData.interests.length})</p>
            </div>

            {/* Seçilen ilgi alanları */}
            {formData.interests.length > 0 && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-2">Seçilenler</label>
                <div className="flex flex-wrap gap-2">
                  {formData.interests.map(interest => (
                    <span
                      key={interest}
                      className="inline-flex items-center px-3 py-1.5 bg-indigo-100 text-indigo-700 rounded-full text-sm"
                    >
                      {interest}
                      <button
                        onClick={() => removeInterest(interest)}
                        className="ml-2 text-indigo-500 hover:text-indigo-700"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Arama */}
            <div className="mb-4">
              <div className="relative">
                <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50 focus:bg-white"
                  placeholder="İlgi alanı ara..."
                />
              </div>
            </div>

            {/* Özel ilgi alanı ekleme */}
            <div className="mb-6 flex gap-2">
              <input
                type="text"
                value={formData.customInterest}
                onChange={(e) => setFormData({ ...formData, customInterest: e.target.value })}
                className="flex-1 px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50 focus:bg-white text-sm"
                placeholder="Kendi ilgi alanınızı ekleyin..."
                onKeyPress={(e) => e.key === 'Enter' && addCustomInterest()}
              />
              <button
                onClick={addCustomInterest}
                className="px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 text-sm"
              >
                Ekle
              </button>
            </div>

            {/* İlgi alanları listesi */}
            <div className="max-h-64 overflow-y-auto">
              <div className="flex flex-wrap gap-2">
                {filteredInterests.map(interest => (
                  <button
                    key={interest}
                    onClick={() => toggleInterest(interest)}
                    className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                      formData.interests.includes(interest)
                        ? 'bg-indigo-600 text-white'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {interest}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Biyografi */}
        {currentStep === 4 && (
          <div className="bg-white rounded-2xl shadow-xl p-8 animate-fadeIn">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-slate-800">Kendinizi Tanıtın</h2>
              <p className="text-slate-500 mt-2">Kısa bir biyografi yazın (isteğe bağlı)</p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Biyografi
                  <span className="text-slate-400 font-normal ml-2">({formData.bio.length}/500)</span>
                </label>
                <textarea
                  name="bio"
                  value={formData.bio}
                  onChange={handleChange}
                  maxLength={500}
                  rows={5}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50 focus:bg-white resize-none"
                  placeholder="Kendiniz hakkında kısa bir tanıtım yazın. Araştırma alanlarınız, projeleriniz, ilgi duyduğunuz konular..."
                />
              </div>

              {/* Özet */}
              <div className="bg-slate-50 rounded-xl p-6">
                <h3 className="text-sm font-semibold text-slate-700 mb-4">Profil Özeti</h3>
                <div className="space-y-2 text-sm">
                  <p><span className="text-slate-500">Meslek:</span> <span className="text-slate-800">{PROFESSION_OPTIONS.find(p => p.value === formData.profession)?.label || '-'}</span></p>
                  <p><span className="text-slate-500">Eğitim:</span> <span className="text-slate-800">{EDUCATION_OPTIONS.find(e => e.value === formData.educationLevel)?.label || '-'}</span></p>
                  <p><span className="text-slate-500">Alan:</span> <span className="text-slate-800">{formData.fieldOfStudy || '-'}</span></p>
                  <p><span className="text-slate-500">Üniversite:</span> <span className="text-slate-800">{formData.university || '-'}</span></p>
                  <p><span className="text-slate-500">İlgi Alanları:</span> <span className="text-slate-800">{formData.interests.join(', ') || '-'}</span></p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <button
            onClick={() => setCurrentStep(prev => prev - 1)}
            disabled={currentStep === 1}
            className={`px-6 py-3 rounded-xl font-medium transition-all ${
              currentStep === 1
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
            }`}
          >
            ← Geri
          </button>

          {currentStep < 4 ? (
            <button
              onClick={() => setCurrentStep(prev => prev + 1)}
              disabled={!canProceed()}
              className={`px-6 py-3 rounded-xl font-medium transition-all ${
                canProceed()
                  ? 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-500/30'
                  : 'bg-slate-200 text-slate-400 cursor-not-allowed'
              }`}
            >
              Devam →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={isLoading}
              className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-xl hover:from-indigo-700 hover:to-purple-700 shadow-lg shadow-indigo-500/30 disabled:opacity-70"
            >
              {isLoading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Kaydediliyor...
                </span>
              ) : (
                '✓ Profili Tamamla'
              )}
            </button>
          )}
        </div>

        {/* Skip button */}
        <div className="text-center mt-4">
          <button
            onClick={() => navigate('/')}
            className="text-sm text-slate-500 hover:text-slate-700"
          >
            Şimdilik geç, daha sonra tamamla
          </button>
        </div>
      </div>
    </div>
  );
};

export default CompleteProfile;

