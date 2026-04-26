import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ContentCard from '../components/ContentCard';
import { activityApi, libraryApi, recommendationApi, userStorage } from '../services/api';
import type { ActivityItem, RecommendationItem } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';
import { formatMatchScore, interleaveBySource } from '../utils/content';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

const PROFESSION_LABELS: Record<string, string> = {
  student: 'Öğrenci',
  researcher: 'Araştırmacı',
  professor: 'Profesör / Akademisyen',
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
  tone: string;
}

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
  const { isEnglish } = useLanguage();
  const [userData, setUserData] = useState<UserProfileData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activities, setActivities] = useState<ActivityEntry[]>([]);
  const [savedCount, setSavedCount] = useState(0);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [recsLoading, setRecsLoading] = useState(false);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [likedIds, setLikedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    const fetchUserData = async () => {
      const storedUser = userStorage.getUser();
      if (!storedUser) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/user/${storedUser.id}/`);
        const data = await response.json();
        if (data.success) setUserData(data.user);

        const [libraryData, activityData] = await Promise.all([
          libraryApi.list(storedUser.id, 1, 1),
          activityApi.getRecent(storedUser.id, 8),
        ]);

        if (libraryData.success) setSavedCount(libraryData.total);

        if (activityData.success) {
          const mapped = activityData.activities.map((activity: ActivityItem) => ({
            text: activity.content_title,
            time: formatTimeAgo(activity.created_at),
            tone:
              activity.type === 'save'
                ? 'bg-[var(--brand)]'
                : activity.type === 'search'
                  ? 'bg-emerald-500'
                  : activity.type === 'profile_update'
                    ? 'bg-amber-500'
                    : 'bg-slate-400',
          }));
          setActivities(mapped);
        }
      } catch (error) {
        console.error('Failed to fetch user data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserData();
  }, []);

  useEffect(() => {
    const fetchRecommendations = async () => {
      const storedUser = userStorage.getUser();
      if (!storedUser) return;
      setRecsLoading(true);
      try {
        const data = await recommendationApi.getRecommendations(storedUser.id, 4);
        if (data.success && data.recommendations) {
          const mixed = interleaveBySource(data.recommendations);
          setRecommendations(mixed);
          const extIds = mixed.map((item) => item.external_id);
          if (extIds.length > 0) {
            const checkRes = await libraryApi.check(storedUser.id, extIds);
            if (checkRes.success) setSavedIds(new Set(checkRes.saved_ids));
          }
        }
      } catch (error) {
        console.error('Failed to fetch recommendations:', error);
      } finally {
        setRecsLoading(false);
      }
    };

    fetchRecommendations();
  }, []);

  const toggleSave = async (rec: RecommendationItem) => {
    const user = userStorage.getUser();
    if (!user) return;

    const isSaved = savedIds.has(rec.external_id);
    try {
      if (isSaved) {
        await libraryApi.remove(user.id, rec.external_id);
        setSavedIds((prev) => {
          const next = new Set(prev);
          next.delete(rec.external_id);
          return next;
        });
      } else {
        await libraryApi.save(user.id, {
          external_id: rec.external_id,
          title: rec.title,
          abstract: rec.abstract || '',
          authors: rec.authors || [],
          published_date: rec.published_date || '',
          journal: '',
          url: rec.url || '',
          pdf_url: rec.pdf_url || '',
          doi: rec.doi || '',
          source: rec.source || 'Öneri',
          categories: rec.categories || [],
          citation_count: 0,
        });
        setSavedIds((prev) => new Set(prev).add(rec.external_id));
      }
    } catch (error) {
      console.error('Failed to toggle save:', error);
    }
  };

  const toggleLike = async (rec: RecommendationItem) => {
    const user = userStorage.getUser();
    if (!user) return;

    const isLiked = likedIds.has(rec.external_id);
    try {
      await activityApi.record(user.id, {
        activity_type: isLiked ? 'remove_like' : 'like',
        content_id: rec.external_id,
        content_title: rec.title,
      });

      setLikedIds((prev) => {
        const next = new Set(prev);
        if (isLiked) next.delete(rec.external_id);
        else next.add(rec.external_id);
        return next;
      });
    } catch (error) {
      console.error('Failed to toggle like:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-[var(--brand)]" />
      </div>
    );
  }

  if (!userData) {
    return (
      <div className="shell section-card px-8 py-16 text-center">
        <p className="font-heading text-3xl text-[var(--text-strong)]">Profil görüntülemek için giriş yapın.</p>
        <Link to="/login" className="mt-4 inline-flex text-sm font-semibold text-[var(--brand)]">
          Giriş yap
        </Link>
      </div>
    );
  }

  const profile = userData.profile || {};
  const nameParts = userData.fullName?.split(' ') || ['', ''];
  const firstName = nameParts[0];
  const lastName = nameParts.slice(1).join(' ');
  const initials = `${firstName[0] || ''}${lastName[0] || ''}`.toUpperCase();
  const professionLabel = profile.profession ? PROFESSION_LABELS[profile.profession] || profile.professionDetail || profile.profession : '';
  const educationLabel = profile.educationLevel ? EDUCATION_LABELS[profile.educationLevel] : '';
  const roleText = [professionLabel, profile.fieldOfStudy].filter(Boolean).join(' • ');
  const institutionText = profile.university || profile.companyOrInstitution || '';

  return (
    <div className="space-y-8">
      <section className="shell page-hero px-6 py-8 md:px-10 md:py-12">
        <div className="relative z-10 flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex items-center gap-6 text-white">
            {profile.avatarUrl ? (
              <img src={profile.avatarUrl} alt={userData.fullName} className="h-24 w-24 rounded-full border-4 border-white/20 object-cover" />
            ) : (
              <div className="flex h-24 w-24 items-center justify-center rounded-full border border-white/10 bg-white/10 text-3xl font-bold">
                {initials}
              </div>
            )}

            <div>
              <p className="eyebrow text-white/65">Araştırma profili</p>
              <h1 className="mt-2 font-heading text-5xl text-white">{firstName} {lastName}</h1>
              {roleText && <p className="mt-3 text-base text-white/75">{roleText}</p>}
              {institutionText && <p className="mt-1 text-sm text-white/60">{institutionText}</p>}
              {educationLabel && <p className="mt-1 text-sm text-white/60">{educationLabel}</p>}
            </div>
          </div>

          <Link to="/settings" className="btn-secondary border-white/15 bg-white/5 text-white hover:bg-white/10">
            Profili düzenle
          </Link>
        </div>
      </section>

      <section className="shell grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <div className="section-card p-6 md:p-8">
            <p className="eyebrow mb-2">Hakkımda</p>
            <h2 className="font-heading text-3xl text-[var(--text-strong)]">Profil özeti</h2>
            <p className="mt-4 text-sm leading-8 text-[var(--text-primary)]">
              {profile.bio || 'Henüz biyografi eklenmemiş. Profil ayarlarından akademik geçmişinizi ve ilgi alanlarınızı tamamlayabilirsiniz.'}
            </p>

            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <div className="stat-card">
                <p className="text-2xl font-semibold text-[var(--text-strong)]">{savedCount}</p>
                <p className="text-xs text-[var(--text-muted)]">Kaydedilen içerik</p>
              </div>
              <div className="stat-card">
                <p className="text-2xl font-semibold text-[var(--text-strong)]">{profile.interests?.length || 0}</p>
                <p className="text-xs text-[var(--text-muted)]">İlgi alanı</p>
              </div>
              <div className="stat-card">
                <p className="text-2xl font-semibold text-[var(--text-strong)]">{profile.researchAreas?.length || 0}</p>
                <p className="text-xs text-[var(--text-muted)]">Araştırma alanı</p>
              </div>
            </div>

            {profile.interests?.length > 0 && (
              <div className="mt-6">
                <h3 className="mb-3 text-sm font-semibold text-[var(--text-strong)]">İlgi alanları</h3>
                <div className="flex flex-wrap gap-2">
                  {profile.interests.map((interest, index) => (
                    <span key={`${interest}-${index}`} className="chip">
                      {interest}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {profile.researchAreas?.length > 0 && (
              <div className="mt-6">
                <h3 className="mb-3 text-sm font-semibold text-[var(--text-strong)]">Araştırma alanları</h3>
                <div className="flex flex-wrap gap-2">
                  {profile.researchAreas.map((area, index) => (
                    <span key={`${area}-${index}`} className="chip chip-active">
                      {area}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="section-card p-6 md:p-8">
            <div className="flex items-end justify-between">
              <div>
                <p className="eyebrow mb-2">Sana özel</p>
                <h2 className="font-heading text-3xl text-[var(--text-strong)]">Önerilen içerikler</h2>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-full bg-[var(--brand-soft)] px-4 py-2 text-xs font-semibold text-[var(--brand)]">
                  {recommendations.length} {isEnglish ? 'matched' : 'uyumlu'}
                </span>
                <Link to="/recommendations" className="text-sm font-semibold text-[var(--brand)]">
                  {isEnglish ? 'View all' : 'Tümünü gör'}
                </Link>
              </div>
            </div>

            {recsLoading ? (
              <div className="py-10 text-center text-sm text-[var(--text-muted)]">Öneriler yükleniyor...</div>
            ) : recommendations.length > 0 ? (
              <div className="mt-5 space-y-4">
                {recommendations.map((rec) => (
                  <ContentCard
                    key={rec.external_id}
                    content={{
                      id: rec.external_id,
                      type: 'article',
                      title: rec.title,
                      description: rec.abstract || 'Özet bilgisi bulunmuyor.',
                      source: rec.source || 'Öneri',
                      authors: rec.authors?.map((author) => author.name).join(', ') || '',
                      date: rec.published_date,
                      tags: rec.categories?.slice(0, 3) || [],
                      url: rec.url,
                      pdfUrl: rec.pdf_url,
                      imageUrl: rec.image_url,
                      matchScore: formatMatchScore(rec.score) ?? undefined,
                    }}
                    isSaved={savedIds.has(rec.external_id)}
                    onToggleSave={() => toggleSave(rec)}
                    isLiked={likedIds.has(rec.external_id)}
                    onToggleLike={() => toggleLike(rec)}
                  />
                ))}
              </div>
            ) : (
              <p className="mt-5 text-sm text-[var(--text-muted)]">Daha fazla içerik keşfettikçe sana özel öneriler burada görünecek.</p>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="section-card p-6">
            <p className="eyebrow mb-2">Hesap bilgileri</p>
            <h2 className="font-heading text-3xl text-[var(--text-strong)]">Kimlik ve bağlantılar</h2>

            <div className="mt-5 space-y-4 text-sm text-[var(--text-primary)]">
              <div>
                <p className="text-[var(--text-muted)]">E-posta</p>
                <p className="font-semibold text-[var(--text-strong)]">{userData.email}</p>
              </div>
              {profile.website && (
                <div>
                  <p className="text-[var(--text-muted)]">Web sitesi</p>
                  <a href={profile.website} target="_blank" rel="noopener noreferrer" className="font-semibold text-[var(--brand)]">
                    {profile.website}
                  </a>
                </div>
              )}
              {profile.linkedin && (
                <div>
                  <p className="text-[var(--text-muted)]">LinkedIn</p>
                  <a href={profile.linkedin} target="_blank" rel="noopener noreferrer" className="font-semibold text-[var(--brand)]">
                    Profili aç
                  </a>
                </div>
              )}
              {profile.googleScholar && (
                <div>
                  <p className="text-[var(--text-muted)]">Google Scholar</p>
                  <a href={profile.googleScholar} target="_blank" rel="noopener noreferrer" className="font-semibold text-[var(--brand)]">
                    Profili aç
                  </a>
                </div>
              )}
            </div>
          </div>

          <div className="section-card p-6">
            <p className="eyebrow mb-2">Son aktiviteler</p>
            <h2 className="font-heading text-3xl text-[var(--text-strong)]">Araştırma akışı</h2>
            <div className="mt-5 space-y-4">
              {activities.length > 0 ? (
                activities.map((activity, index) => (
                  <div key={`${activity.text}-${index}`} className="flex items-start gap-3">
                    <div className={`mt-2 h-2.5 w-2.5 rounded-full ${activity.tone}`} />
                    <div>
                      <p className="text-sm font-medium text-[var(--text-strong)]">{activity.text}</p>
                      <p className="text-xs text-[var(--text-muted)]">{activity.time}</p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-[var(--text-muted)]">Henüz aktivite bulunmuyor.</p>
              )}
            </div>
          </div>

          {!profile.isProfileComplete && (
            <div className="rounded-[28px] border border-[rgba(185,109,23,0.18)] bg-[rgba(185,109,23,0.08)] p-6">
              <h3 className="text-lg font-semibold text-[var(--warning)]">Profilini tamamla</h3>
              <p className="mt-2 text-sm text-[var(--text-primary)]">Daha iyi öneriler ve daha kişisel bir keşif deneyimi için profil bilgilerini tamamla.</p>
              <Link to="/complete-profile" className="mt-4 inline-flex btn-primary">
                Tamamla
              </Link>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default Profile;
