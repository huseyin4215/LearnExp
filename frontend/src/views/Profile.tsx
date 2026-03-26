import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { userStorage, libraryApi } from '../services/api';
import type { LibraryItem } from '../services/api';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Meslek etiketleri
const PROFESSION_LABELS: Record<string, string> = {
    student: 'Öğrenci',
    researcher: 'Araştırmacı',
    professor: 'Profesör/Akademisyen',
    engineer: 'Mühendis',
    developer: 'Yazılım Geliştirici',
    data_scientist: 'Veri Bilimci',
    doctor: 'Doktor',
    lawyer: 'Avukat',
    teacher: 'Öğretmen',
    business: 'İş İnsanı',
    freelancer: 'Serbest Çalışan',
    other: 'Diğer',
};

const EDUCATION_LABELS: Record<string, string> = {
    high_school: 'Lise',
    associate: 'Ön Lisans',
    bachelor: 'Lisans',
    master: 'Yüksek Lisans',
    phd: 'Doktora',
    postdoc: 'Post-Doktora',
};

interface UserProfileData {
    id: number;
    email: string;
    fullName: string;
    profile: {
        profession: string;
        professionDetail: string;
        companyOrInstitution: string;
        educationLevel: string;
        fieldOfStudy: string;
        university: string;
        graduationYear: number | null;
        bio: string;
        interests: string[];
        researchAreas: string[];
        website: string;
        linkedin: string;
        twitter: string;
        orcid: string;
        googleScholar: string;
        isProfileComplete: boolean;
        avatarUrl: string;
    };
}

interface ActivityEntry {
    text: string;
    time: string;
    dotColor: string;
    type: 'save' | 'search' | 'profile';
}

const ActivityItem: React.FC<{ text: string; time: string; dotColor: string }> = ({ text, time, dotColor }) => (
    <div className="flex items-start space-x-3">
        <div className={`w-2 h-2 ${dotColor} rounded-full mt-2`}></div>
        <div className="min-w-0">
            <p className="text-sm text-gray-800 truncate">{text}</p>
            <p className="text-xs text-gray-500">{time}</p>
        </div>
    </div>
);

const formatTimeAgo = (dateStr: string): string => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    const diffHour = Math.floor(diffMs / 3600000);
    const diffDay = Math.floor(diffMs / 86400000);

    if (diffMin < 1) return 'Az önce';
    if (diffMin < 60) return `${diffMin} dakika önce`;
    if (diffHour < 24) return `${diffHour} saat önce`;
    if (diffDay < 7) return `${diffDay} gün önce`;
    return date.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
};

const Profile: React.FC = () => {
    const [userData, setUserData] = useState<UserProfileData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activities, setActivities] = useState<ActivityEntry[]>([]);
    const [savedCount, setSavedCount] = useState(0);

    useEffect(() => {
        const fetchUserData = async () => {
            const storedUser = userStorage.getUser();
            if (!storedUser) {
                setIsLoading(false);
                return;
            }

            try {
                // Fetch user profile
                const response = await fetch(`${API_BASE_URL}/user/${storedUser.id}/`);
                const data = await response.json();
                if (data.success) {
                    setUserData(data.user);
                }

                // Fetch saved articles (library) for activity feed
                try {
                    const libraryData = await libraryApi.list(storedUser.id, 1, 5);
                    if (libraryData.success) {
                        setSavedCount(libraryData.total);

                        const savedActivities: ActivityEntry[] = libraryData.items.map((item: LibraryItem) => ({
                            text: `"${item.title.length > 50 ? item.title.substring(0, 50) + '...' : item.title}" kaydedildi`,
                            time: formatTimeAgo(item.saved_at),
                            dotColor: 'bg-indigo-500',
                            type: 'save' as const,
                        }));

                        // Get recent searches from localStorage
                        const recentSearches: string[] = JSON.parse(localStorage.getItem('recent_searches') || '[]');
                        const searchActivities: ActivityEntry[] = recentSearches.slice(0, 3).map((query, i) => ({
                            text: `"${query}" araması yapıldı`,
                            time: i === 0 ? 'Son arama' : `${i + 1}. son arama`,
                            dotColor: 'bg-blue-500',
                            type: 'search' as const,
                        }));

                        // Combine and add profile creation
                        const allActivities: ActivityEntry[] = [
                            ...savedActivities,
                            ...searchActivities,
                            {
                                text: 'Profil oluşturuldu',
                                time: 'Başlangıç',
                                dotColor: 'bg-green-500',
                                type: 'profile' as const,
                            },
                        ];

                        setActivities(allActivities);
                    }
                } catch {
                    // Library fetch failed — show just profile activity
                    setActivities([{
                        text: 'Profil oluşturuldu',
                        time: 'Başlangıç',
                        dotColor: 'bg-green-500',
                        type: 'profile',
                    }]);
                }
            } catch (error) {
                console.error('Failed to fetch user data:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchUserData();
    }, []);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    if (!userData) {
        return (
            <div className="text-center py-16">
                <p className="text-gray-500 mb-4">Profil bilgilerinizi görüntülemek için giriş yapın.</p>
                <Link to="/login" className="text-indigo-600 hover:text-indigo-700 font-medium">
                    Giriş Yap
                </Link>
            </div>
        );
    }

    const profile = userData.profile || {};
    const nameParts = userData.fullName?.split(' ') || ['', ''];
    const firstName = nameParts[0];
    const lastName = nameParts.slice(1).join(' ');
    const initials = `${firstName[0] || ''}${lastName[0] || ''}`.toUpperCase();

    const professionLabel = profile.profession
        ? PROFESSION_LABELS[profile.profession] || profile.professionDetail || profile.profession
        : '';

    const educationLabel = profile.educationLevel
        ? EDUCATION_LABELS[profile.educationLevel]
        : '';

    const roleText = [professionLabel, profile.fieldOfStudy].filter(Boolean).join(' • ');
    const institutionText = profile.university || profile.companyOrInstitution || '';

    return (
        <div id="profileView">
            {/* Hero Section */}
            <section className="gradient-bg text-white py-16 rounded-2xl mb-8 text-center relative overflow-hidden">
                <div className="absolute inset-0 opacity-10">
                    <div className="absolute top-10 left-10 w-32 h-32 bg-white rounded-full blur-3xl"></div>
                    <div className="absolute bottom-10 right-10 w-48 h-48 bg-white rounded-full blur-3xl"></div>
                </div>

                <div className="relative z-10">
                    {profile.avatarUrl ? (
                        <img
                            src={profile.avatarUrl}
                            alt={userData.fullName}
                            className="w-24 h-24 rounded-full mx-auto mb-4 border-4 border-white/30"
                        />
                    ) : (
                        <div className="w-24 h-24 bg-white bg-opacity-20 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl font-bold">
                            {initials}
                        </div>
                    )}

                    <h2 className="text-3xl font-bold mb-2">
                        {firstName} <span className="text-yellow-300">{lastName}</span>
                    </h2>

                    {roleText && (
                        <p className="text-lg text-indigo-100">{roleText}</p>
                    )}

                    {institutionText && (
                        <p className="text-base text-indigo-200">{institutionText}</p>
                    )}

                    {educationLabel && (
                        <p className="text-sm text-indigo-300 mt-1">{educationLabel}</p>
                    )}

                    {/* Social Links */}
                    <div className="flex justify-center gap-4 mt-4">
                        {profile.linkedin && (
                            <a href={profile.linkedin} target="_blank" rel="noopener noreferrer" className="text-white/70 hover:text-white">
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
                                </svg>
                            </a>
                        )}
                        {profile.twitter && (
                            <a href={`https://twitter.com/${profile.twitter}`} target="_blank" rel="noopener noreferrer" className="text-white/70 hover:text-white">
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
                                </svg>
                            </a>
                        )}
                        {profile.googleScholar && (
                            <a href={profile.googleScholar} target="_blank" rel="noopener noreferrer" className="text-white/70 hover:text-white">
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M12 24a7 7 0 110-14 7 7 0 010 14zm0-24L0 9.5l4.838 3.94A8 8 0 0112 8a8 8 0 017.162 5.44L24 9.5 12 0z" />
                                </svg>
                            </a>
                        )}
                        {profile.orcid && (
                            <a href={`https://orcid.org/${profile.orcid}`} target="_blank" rel="noopener noreferrer" className="text-white/70 hover:text-white text-sm font-medium">
                                ORCID
                            </a>
                        )}
                    </div>
                </div>

                {/* Edit Button */}
                <Link
                    to="/settings"
                    className="absolute top-4 right-4 bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition-colors"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Düzenle
                </Link>
            </section>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* About Section */}
                <div className="bg-white rounded-xl border border-gray-200 p-8">
                    <h3 className="text-xl font-semibold mb-6">Hakkımda</h3>

                    {profile.bio ? (
                        <p className="text-gray-600 mb-6">{profile.bio}</p>
                    ) : (
                        <p className="text-gray-400 italic mb-6">Henüz biyografi eklenmemiş.</p>
                    )}

                    {/* İlgi Alanları */}
                    {profile.interests && profile.interests.length > 0 && (
                        <div>
                            <h4 className="text-sm font-semibold text-gray-700 mb-3">İlgi Alanları</h4>
                            <div className="flex flex-wrap gap-2">
                                {profile.interests.map((interest, index) => (
                                    <span
                                        key={index}
                                        className="px-3 py-1 bg-indigo-100 text-indigo-800 text-sm rounded-full"
                                    >
                                        {interest}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Araştırma Alanları */}
                    {profile.researchAreas && profile.researchAreas.length > 0 && (
                        <div className="mt-6">
                            <h4 className="text-sm font-semibold text-gray-700 mb-3">Araştırma Alanları</h4>
                            <div className="flex flex-wrap gap-2">
                                {profile.researchAreas.map((area, index) => (
                                    <span
                                        key={index}
                                        className="px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full"
                                    >
                                        {area}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Stats & Activity */}
                <div className="space-y-8">
                    {/* Quick Stats */}
                    <div className="bg-white rounded-xl border border-gray-200 p-8">
                        <h3 className="text-xl font-semibold mb-6">İstatistikler</h3>
                        <div className="grid grid-cols-3 gap-4 text-center">
                            <div className="p-4 bg-indigo-50 rounded-xl">
                                <div className="text-2xl font-bold text-indigo-600">{savedCount}</div>
                                <div className="text-xs text-gray-500">Kaydedilen</div>
                            </div>
                            <div className="p-4 bg-purple-50 rounded-xl">
                                <div className="text-2xl font-bold text-purple-600">
                                    {JSON.parse(localStorage.getItem('recent_searches') || '[]').length}
                                </div>
                                <div className="text-xs text-gray-500">Arama</div>
                            </div>
                            <div className="p-4 bg-emerald-50 rounded-xl">
                                <div className="text-2xl font-bold text-emerald-600">{profile.interests?.length || 0}</div>
                                <div className="text-xs text-gray-500">İlgi Alanı</div>
                            </div>
                        </div>
                    </div>

                    {/* Recent Activity */}
                    <div className="bg-white rounded-xl border border-gray-200 p-8">
                        <h3 className="text-xl font-semibold mb-6">Son Aktiviteler</h3>
                        <div className="space-y-4">
                            {activities.length > 0 ? (
                                activities.map((activity, index) => (
                                    <ActivityItem
                                        key={index}
                                        text={activity.text}
                                        time={activity.time}
                                        dotColor={activity.dotColor}
                                    />
                                ))
                            ) : (
                                <p className="text-sm text-gray-400 text-center py-4">
                                    Daha fazla aktivite için platformu kullanmaya başlayın.
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Profile Completion Warning */}
            {!profile.isProfileComplete && (
                <div className="mt-8 bg-amber-50 border border-amber-200 rounded-xl p-6 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center">
                            <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        </div>
                        <div>
                            <h4 className="font-semibold text-amber-800">Profilinizi tamamlayın</h4>
                            <p className="text-sm text-amber-600">Daha iyi öneriler almak için profilinizi tamamlayın.</p>
                        </div>
                    </div>
                    <Link
                        to="/complete-profile"
                        className="bg-amber-600 hover:bg-amber-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                    >
                        Tamamla
                    </Link>
                </div>
            )}
        </div>
    );
};

export default Profile;
