import React, { useEffect, useState } from 'react';
import ContentCard from '../components/ContentCard';
import { activityApi, libraryApi, recommendationApi, userStorage } from '../services/api';
import type { RecommendationItem } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';
import { formatMatchScore, interleaveBySource } from '../utils/content';

const Recommendations: React.FC = () => {
  const { isEnglish } = useLanguage();
  const [items, setItems] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [likedIds, setLikedIds] = useState<Set<string>>(new Set());
  const user = userStorage.getUser();

  useEffect(() => {
    const loadRecommendations = async () => {
      if (!user) {
        setLoading(false);
        return;
      }

      try {
        const response = await recommendationApi.getRecommendations(user.id, 18);
        if (response.success) {
          const mixed = interleaveBySource(response.recommendations);
          setItems(mixed);
          if (mixed.length > 0) {
            const check = await libraryApi.check(user.id, mixed.map((item) => item.external_id));
            if (check.success) setSavedIds(new Set(check.saved_ids));
          }
        }
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    loadRecommendations();
  }, [user]);

  const toggleSave = async (item: RecommendationItem) => {
    if (!user) return;
    const isSaved = savedIds.has(item.external_id);

    try {
      if (isSaved) {
        await libraryApi.remove(user.id, item.external_id);
        setSavedIds((prev) => {
          const next = new Set(prev);
          next.delete(item.external_id);
          return next;
        });
      } else {
        await libraryApi.save(user.id, {
          external_id: item.external_id,
          title: item.title,
          abstract: item.abstract || '',
          authors: item.authors || [],
          published_date: item.published_date || '',
          journal: '',
          url: item.url || '',
          pdf_url: item.pdf_url || '',
          doi: item.doi || '',
          source: item.source || 'Recommendation',
          categories: item.categories || [],
          citation_count: 0,
        });
        setSavedIds((prev) => new Set(prev).add(item.external_id));
      }
    } catch (error) {
      console.error(error);
    }
  };

  const toggleLike = async (item: RecommendationItem) => {
    if (!user) return;
    const isLiked = likedIds.has(item.external_id);

    try {
      await activityApi.record(user.id, {
        activity_type: isLiked ? 'remove_like' : 'like',
        content_id: item.external_id,
        content_title: item.title,
      });

      setLikedIds((prev) => {
        const next = new Set(prev);
        if (isLiked) next.delete(item.external_id);
        else next.add(item.external_id);
        return next;
      });
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="space-y-8">
      <section className="shell page-hero px-6 py-8 md:px-10 md:py-12">
        <div className="relative z-10 max-w-4xl space-y-5 text-white">
          <p className="eyebrow text-white/65">{isEnglish ? 'Recommended for you' : 'Sana özel seçimler'}</p>
          <h1 className="font-heading text-5xl leading-tight md:text-6xl">
            {isEnglish ? 'A recommendation feed matched to your interests and activity.' : 'İlgi alanlarına ve etkinliğine göre eşleşen öneri akışı.'}
          </h1>
          <p className="max-w-3xl text-base leading-8 text-white/72 md:text-lg">
            {isEnglish
              ? 'These suggestions combine your saved items, topics, and profile signals. Compatibility is shown on each card.'
              : 'Bu öneriler; kaydettiğin içerikler, ilgi alanların ve profil sinyallerin birleştirilerek hazırlanır. Her kartta uyum oranını görebilirsin.'}
          </p>
        </div>
      </section>

      <section className="shell">
        <div className="section-card p-6 md:p-8">
          <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="eyebrow mb-2">{isEnglish ? 'Recommendation results' : 'Öneri sonuçları'}</p>
              <h2 className="font-heading text-4xl text-[var(--text-strong)]">
                {isEnglish ? 'Content sorted by relevance and source diversity' : 'Uyum ve kaynak çeşitliliğine göre sıralanmış içerikler'}
              </h2>
            </div>
            <span className="rounded-full bg-[var(--brand-soft)] px-4 py-2 text-xs font-semibold text-[var(--brand)]">
              {items.length} {isEnglish ? 'matched results' : 'uyumlu sonuç'}
            </span>
          </div>

          {!user ? (
            <div className="rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-alt)] px-8 py-14 text-center">
              <p className="font-heading text-3xl text-[var(--text-strong)]">
                {isEnglish ? 'Sign in to see tailored recommendations.' : 'Kişiselleştirilmiş öneriler için giriş yap.'}
              </p>
            </div>
          ) : loading ? (
            <div className="grid gap-4">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-56 animate-pulse rounded-[24px] border border-[var(--line-soft)] bg-[var(--surface-alt)]" />
              ))}
            </div>
          ) : items.length > 0 ? (
            <div className="space-y-4">
              {items.map((item) => (
                <ContentCard
                  key={item.external_id}
                  content={{
                    id: item.external_id,
                    type: 'article',
                    title: item.title,
                    description: item.abstract || (isEnglish ? 'No abstract available.' : 'Özet bilgisi bulunmuyor.'),
                    source: item.source || (isEnglish ? 'Recommendation' : 'Öneri'),
                    authors: item.authors?.map((author) => author.name).join(', ') || '',
                    date: item.published_date,
                    tags: item.categories?.slice(0, 3) || [],
                    url: item.url,
                    pdfUrl: item.pdf_url,
                    imageUrl: item.image_url,
                    matchScore: formatMatchScore(item.score) ?? undefined,
                  }}
                  isSaved={savedIds.has(item.external_id)}
                  onToggleSave={() => toggleSave(item)}
                  isLiked={likedIds.has(item.external_id)}
                  onToggleLike={() => toggleLike(item)}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-alt)] px-8 py-14 text-center">
              <p className="font-heading text-3xl text-[var(--text-strong)]">
                {isEnglish ? 'Recommendations will appear here as your profile gets stronger.' : 'Profilin güçlendikçe öneriler burada görünecek.'}
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default Recommendations;
