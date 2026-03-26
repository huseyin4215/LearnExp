import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { userStorage } from '../services/api';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

type SettingsTab = 'account' | 'interests' | 'security' | 'notifications';

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
    const [activeSettingsTab, setActiveSettingsTab] = useState<SettingsTab>('account');
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });
    
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
    
    const [newInterest, setNewInterest] = useState('');
    const [newResearchArea, setNewResearchArea] = useState('');

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

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const addInterest = () => {
        if (newInterest.trim() && !formData.interests.includes(newInterest.trim())) {
            setFormData(prev => ({
                ...prev,
                interests: [...prev.interests, newInterest.trim()]
            }));
            setNewInterest('');
        }
    };

    const removeInterest = (tag: string) => {
        setFormData(prev => ({
            ...prev,
            interests: prev.interests.filter(i => i !== tag)
        }));
    };

    const addResearchArea = () => {
        if (newResearchArea.trim() && !formData.researchAreas.includes(newResearchArea.trim())) {
            setFormData(prev => ({
                ...prev,
                researchAreas: [...prev.researchAreas, newResearchArea.trim()]
            }));
            setNewResearchArea('');
        }
    };

    const removeResearchArea = (tag: string) => {
        setFormData(prev => ({
            ...prev,
            researchAreas: prev.researchAreas.filter(i => i !== tag)
        }));
    };

    const handleSaveProfile = async () => {
        const storedUser = userStorage.getUser();
        if (!storedUser) return;

        setIsSaving(true);
        setMessage({ type: '', text: '' });

        try {
            const response = await fetch(`${API_BASE_URL}/user/${storedUser.id}/profile/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    fullName: formData.fullName,
                    profession: formData.profession,
                    professionDetail: formData.professionDetail,
                    companyOrInstitution: formData.companyOrInstitution,
                    educationLevel: formData.educationLevel,
                    fieldOfStudy: formData.fieldOfStudy,
                    university: formData.university,
                    graduationYear: formData.graduationYear ? parseInt(formData.graduationYear) : null,
                    bio: formData.bio,
                    interests: formData.interests,
                    researchAreas: formData.researchAreas,
                    website: formData.website,
                    linkedin: formData.linkedin,
                    twitter: formData.twitter,
                    orcid: formData.orcid,
                    googleScholar: formData.googleScholar,
                })
            });
            
            const data = await response.json();
            if (data.success) {
                setMessage({ type: 'success', text: 'Değişiklikler başarıyla kaydedildi!' });
                // Update stored user data
                userStorage.setUser({ 
                    ...storedUser, 
                    fullName: formData.fullName,
                    isProfileComplete: data.isProfileComplete 
                });
            } else {
                setMessage({ type: 'error', text: data.message || 'Kaydetme başarısız oldu.' });
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
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    return (
        <div id="settingsView" className="w-full">
            <section className="gradient-bg text-white py-16 rounded-2xl mb-8 text-center">
                <h2 className="text-3xl font-bold mb-4">Hesap <span className="text-yellow-300">Ayarları</span></h2>
                <p className="text-lg text-indigo-100">Profil bilgilerinizi ve tercihlerinizi yönetin</p>
            </section>

            {/* Success/Error Message */}
            {message.text && (
                <div className={`mb-6 px-4 py-3 rounded-lg ${
                    message.type === 'success' 
                        ? 'bg-green-100 border border-green-400 text-green-700' 
                        : 'bg-red-100 border border-red-400 text-red-700'
                }`}>
                    {message.text}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                {/* Settings Sidebar */}
                <div className="lg:col-span-1">
                    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                        <nav className="flex flex-col">
                            {[
                                { id: 'account', label: 'Hesap Bilgileri', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
                                { id: 'interests', label: 'İlgi Alanları', icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z' },
                                { id: 'security', label: 'Güvenlik', icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z' },
                                { id: 'notifications', label: 'Bildirimler', icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9' }
                            ].map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveSettingsTab(tab.id as SettingsTab)}
                                    className={`flex items-center space-x-3 px-6 py-4 text-sm font-medium border-l-4 transition-all ${activeSettingsTab === tab.id
                                        ? 'bg-indigo-50 border-indigo-600 text-indigo-600'
                                        : 'border-transparent text-gray-600 hover:bg-gray-50'
                                    }`}
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={tab.icon} />
                                    </svg>
                                    <span>{tab.label}</span>
                                </button>
                            ))}
                        </nav>
                    </div>
                </div>

                {/* Settings Content */}
                <div className="lg:col-span-3">
                    <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-sm min-h-[500px]">

                        {activeSettingsTab === 'account' && (
                            <div className="space-y-6 animate-fadeIn">
                                <h3 className="text-xl font-bold text-gray-800 border-b pb-4">Hesap Bilgileri</h3>
                                
                                {/* Kişisel Bilgiler */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <label className="block text-sm font-semibold text-gray-700 mb-2">Tam İsim</label>
                                        <input 
                                            type="text" 
                                            name="fullName"
                                            value={formData.fullName}
                                            onChange={handleInputChange}
                                            className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm transition-all" 
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-semibold text-gray-700 mb-2">E-posta</label>
                                        <input 
                                            type="email" 
                                            name="email"
                                            value={formData.email}
                                            disabled
                                            className="w-full px-4 py-2 border rounded-lg bg-gray-100 border-gray-200 text-gray-500 cursor-not-allowed" 
                                        />
                                    </div>
                                </div>

                                {/* Meslek Bilgileri */}
                                <div className="border-t pt-6">
                                    <h4 className="text-lg font-semibold text-gray-700 mb-4">Meslek Bilgileri</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">Meslek</label>
                                            <select 
                                                name="profession"
                                                value={formData.profession}
                                                onChange={handleInputChange}
                                                className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm"
                                            >
                                                <option value="">Seçiniz</option>
                                                {PROFESSION_OPTIONS.map(opt => (
                                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                        {formData.profession === 'other' && (
                                            <div>
                                                <label className="block text-sm font-semibold text-gray-700 mb-2">Meslek Detayı</label>
                                                <input 
                                                    type="text" 
                                                    name="professionDetail"
                                                    value={formData.professionDetail}
                                                    onChange={handleInputChange}
                                                    placeholder="Mesleğinizi yazın"
                                                    className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" 
                                                />
                                            </div>
                                        )}
                                        <div className={formData.profession !== 'other' ? '' : 'md:col-span-2'}>
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">Kurum / Şirket</label>
                                            <input 
                                                type="text" 
                                                name="companyOrInstitution"
                                                value={formData.companyOrInstitution}
                                                onChange={handleInputChange}
                                                placeholder="Çalıştığınız kurum"
                                                className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" 
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Eğitim Bilgileri */}
                                <div className="border-t pt-6">
                                    <h4 className="text-lg font-semibold text-gray-700 mb-4">Eğitim Bilgileri</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">Eğitim Seviyesi</label>
                                            <select 
                                                name="educationLevel"
                                                value={formData.educationLevel}
                                                onChange={handleInputChange}
                                                className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm"
                                            >
                                                <option value="">Seçiniz</option>
                                                {EDUCATION_OPTIONS.map(opt => (
                                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">Alan / Bölüm</label>
                                            <input 
                                                type="text" 
                                                name="fieldOfStudy"
                                                value={formData.fieldOfStudy}
                                                onChange={handleInputChange}
                                                placeholder="Örn: Bilgisayar Mühendisliği"
                                                className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" 
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">Üniversite</label>
                                            <input 
                                                type="text" 
                                                name="university"
                                                value={formData.university}
                                                onChange={handleInputChange}
                                                placeholder="Örn: İstanbul Teknik Üniversitesi"
                                                className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" 
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">Mezuniyet Yılı</label>
                                            <input 
                                                type="number" 
                                                name="graduationYear"
                                                value={formData.graduationYear}
                                                onChange={handleInputChange}
                                                placeholder="Örn: 2024"
                                                min="1950"
                                                max="2030"
                                                className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" 
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Biyografi */}
                                <div className="border-t pt-6">
                                    <label className="block text-sm font-semibold text-gray-700 mb-2">Biyografi</label>
                                    <textarea
                                        name="bio"
                                        rows={4}
                                        value={formData.bio}
                                        onChange={handleInputChange}
                                        className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none resize-none shadow-sm transition-all"
                                        placeholder="Kendinizden kısaca bahsedin..."
                                    />
                                </div>

                                {/* Sosyal Medya */}
                                <div className="border-t pt-6">
                                    <h4 className="text-lg font-semibold text-gray-700 mb-4">Sosyal Bağlantılar</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">Web Sitesi</label>
                                            <input 
                                                type="url" 
                                                name="website"
                                                value={formData.website}
                                                onChange={handleInputChange}
                                                placeholder="https://example.com"
                                                className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" 
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">LinkedIn</label>
                                            <input 
                                                type="url" 
                                                name="linkedin"
                                                value={formData.linkedin}
                                                onChange={handleInputChange}
                                                placeholder="https://linkedin.com/in/username"
                                                className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" 
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">Twitter/X</label>
                                            <input 
                                                type="text" 
                                                name="twitter"
                                                value={formData.twitter}
                                                onChange={handleInputChange}
                                                placeholder="@username"
                                                className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" 
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">ORCID</label>
                                            <input 
                                                type="text" 
                                                name="orcid"
                                                value={formData.orcid}
                                                onChange={handleInputChange}
                                                placeholder="0000-0000-0000-0000"
                                                className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" 
                                            />
                                        </div>
                                        <div className="md:col-span-2">
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">Google Scholar</label>
                                            <input 
                                                type="url" 
                                                name="googleScholar"
                                                value={formData.googleScholar}
                                                onChange={handleInputChange}
                                                placeholder="https://scholar.google.com/citations?user=..."
                                                className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" 
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="flex justify-end pt-4">
                                    <button 
                                        onClick={handleSaveProfile}
                                        disabled={isSaving}
                                        className="bg-indigo-600 text-white px-8 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                    >
                                        {isSaving && (
                                            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                            </svg>
                                        )}
                                        {isSaving ? 'Kaydediliyor...' : 'Değişiklikleri Kaydet'}
                                    </button>
                                </div>
                            </div>
                        )}

                        {activeSettingsTab === 'interests' && (
                            <div className="space-y-6 animate-fadeIn">
                                <h3 className="text-xl font-bold text-gray-800 border-b pb-4">Akademik İlgi Alanları</h3>
                                <p className="text-sm text-gray-500">Platformun size daha iyi öneriler sunması için uzmanlık alanlarınızı belirleyin.</p>

                                {/* İlgi Alanları */}
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-3">İlgi Alanları</label>
                                    <div className="flex flex-wrap gap-2 mb-4">
                                        {formData.interests.map(tag => (
                                            <div key={tag} className="flex items-center space-x-1 px-4 py-1.5 bg-indigo-100 text-indigo-700 rounded-full text-sm font-bold">
                                                <span>{tag}</span>
                                                <button onClick={() => removeInterest(tag)} className="hover:text-indigo-900 ml-1">&times;</button>
                                            </div>
                                        ))}
                                        {formData.interests.length === 0 && (
                                            <p className="text-gray-400 text-sm italic">Henüz ilgi alanı eklenmedi.</p>
                                        )}
                                    </div>

                                    <div className="flex space-x-2">
                                        <input
                                            type="text"
                                            value={newInterest}
                                            onChange={(e) => setNewInterest(e.target.value)}
                                            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addInterest())}
                                            placeholder="Yeni bir ilgi alanı ekle..."
                                            className="flex-1 px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm"
                                        />
                                        <button
                                            onClick={addInterest}
                                            className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-colors"
                                        >
                                            Ekle
                                        </button>
                                    </div>
                                </div>

                                {/* Araştırma Alanları */}
                                <div className="border-t pt-6">
                                    <label className="block text-sm font-semibold text-gray-700 mb-3">Araştırma Alanları</label>
                                    <div className="flex flex-wrap gap-2 mb-4">
                                        {formData.researchAreas.map(tag => (
                                            <div key={tag} className="flex items-center space-x-1 px-4 py-1.5 bg-purple-100 text-purple-700 rounded-full text-sm font-bold">
                                                <span>{tag}</span>
                                                <button onClick={() => removeResearchArea(tag)} className="hover:text-purple-900 ml-1">&times;</button>
                                            </div>
                                        ))}
                                        {formData.researchAreas.length === 0 && (
                                            <p className="text-gray-400 text-sm italic">Henüz araştırma alanı eklenmedi.</p>
                                        )}
                                    </div>

                                    <div className="flex space-x-2">
                                        <input
                                            type="text"
                                            value={newResearchArea}
                                            onChange={(e) => setNewResearchArea(e.target.value)}
                                            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addResearchArea())}
                                            placeholder="Yeni bir araştırma alanı ekle..."
                                            className="flex-1 px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-purple-500 outline-none shadow-sm"
                                        />
                                        <button
                                            onClick={addResearchArea}
                                            className="bg-purple-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-purple-700 transition-colors"
                                        >
                                            Ekle
                                        </button>
                                    </div>
                                </div>

                                <div className="flex justify-end pt-4 border-t">
                                    <button 
                                        onClick={handleSaveProfile}
                                        disabled={isSaving}
                                        className="bg-indigo-600 text-white px-8 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                    >
                                        {isSaving && (
                                            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                            </svg>
                                        )}
                                        {isSaving ? 'Kaydediliyor...' : 'Değişiklikleri Kaydet'}
                                    </button>
                                </div>
                            </div>
                        )}

                        {activeSettingsTab === 'security' && (
                            <div className="space-y-6 animate-fadeIn">
                                <h3 className="text-xl font-bold text-gray-800 border-b pb-4">Güvenlik ve Şifre Yenileme</h3>
                                <div className="max-w-md space-y-4">
                                    <div>
                                        <label className="block text-sm font-semibold text-gray-700 mb-2">Mevcut Şifre</label>
                                        <input type="password" placeholder="••••••••" className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" />
                                    </div>
                                    <div className="border-t pt-4">
                                        <label className="block text-sm font-semibold text-gray-700 mb-2">Yeni Şifre</label>
                                        <input type="password" placeholder="Yeni şifreniz" className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-semibold text-gray-700 mb-2">Yeni Şifre (Tekrar)</label>
                                        <input type="password" placeholder="Tekrar yazın" className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" />
                                    </div>
                                    <div className="pt-4 flex justify-end">
                                        <button className="bg-indigo-600 text-white px-8 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-colors shadow-lg">Şifreyi Güncelle</button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeSettingsTab === 'notifications' && (
                            <div className="space-y-6 animate-fadeIn">
                                <h3 className="text-xl font-bold text-gray-800 border-b pb-4">Bildirim Tercihleri</h3>
                                <div className="space-y-4">
                                    {[
                                        { id: 'email-alert', label: 'E-posta Bildirimleri', desc: 'Yeni makale ve konferans duyurularını e-posta ile al.' },
                                        { id: 'weekly-digest', label: 'Haftalık Özet', desc: 'Haftanın en popüler içeriklerini içeren bir özet al.' },
                                        { id: 'funding-alert', label: 'Fon Çağrıları', desc: 'İlgi alanlarınıza uygun yeni fonlar çıktığında uyarıl.' },
                                        { id: 'chat-bot', label: 'AI Asistan Mesajları', desc: 'Asistanın size sunduğu özel hatırlatmalar.' }
                                    ].map(item => (
                                        <div key={item.id} className="flex items-center justify-between p-4 bg-white rounded-xl border border-gray-200 shadow-sm transition-all hover:bg-indigo-50/20">
                                            <div>
                                                <p className="font-bold text-gray-800">{item.label}</p>
                                                <p className="text-xs text-gray-500">{item.desc}</p>
                                            </div>
                                            <label className="relative inline-flex items-center cursor-pointer">
                                                <input type="checkbox" defaultChecked className="sr-only peer" />
                                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                                            </label>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;
