import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ContentCard from '../components/ContentCard';
import NewsSlider from '../components/NewsSlider';
import { activityApi, articlesApi, libraryApi, recommendationApi, scrapedContentApi, userStorage } from '../services/api';
import type { Article, RecommendationItem, ScrapedContentItem } from '../services/api';
import type { ContentType } from '../types';
import { useLanguage } from '../contexts/LanguageContext';
import { formatMatchScore, interleaveBySource } from '../utils/content';

const PAGE_SIZE = 10;

const Toast: React.FC<{ message: string; type: 'success' | 'error'; onClose: () => void }> = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 2500);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`fixed bottom-24 left-1/2 z-40 -translate-x-1/2 rounded-full px-5 py-3 text-sm font-semibold text-white shadow-[var(--shadow-lg)] ${type === 'success' ? 'bg-[var(--success)]' : 'bg-[var(--danger)]'}`}>
      {message}
    </div>
  );
};

const inferContentType = (article: Article): ContentType => {
  const sourceName = (article.api_source?.name || '').toLowerCase();
  const url = (article.url || '').toLowerCase();
  const title = article.title.toLowerCase();

  if (sourceName.includes('conference') || url.includes('conference') || title.includes('conference')) return 'conference';
  if (sourceName.includes('event') || url.includes('event') || title.includes('webinar') || title.includes('workshop')) return 'event';
  return 'article';
};

const getPageNumbers = (currentPage: number, totalPages: number): (number | '...')[] => {
  const pages: (number | '...')[] = [];
  if (totalPages <= 7) {
    for (let index = 1; index <= totalPages; index += 1) pages.push(index);
    return pages;
  }

  pages.push(1);
  if (currentPage > 3) pages.push('...');
  for (let index = Math.max(2, currentPage - 1); index <= Math.min(totalPages - 1, currentPage + 1); index += 1) pages.push(index);
  if (currentPage < totalPages - 2) pages.push('...');
  pages.push(totalPages);
  return pages;
};

const Dashboard: React.FC = () => {
  const { isEnglish, language } = useLanguage();
  const topicRail = isEnglish
    ? ['Artificial Intelligence', 'Robotics', 'Cybersecurity', 'Quantum', 'Bioinformatics']
    : ['Yapay Zeka', 'Robotik', 'Siber Güvenlik', 'Kuantum', 'Biyoinformatik'];

  const user = userStorage.getUser();
  const firstName = user?.fullName?.split(' ')[0] || (isEnglish ? 'Researcher' : 'Araştırmacı');
  const userId = user?.id;

  const [articles, setArticles] = useState<Article[]>([]);
  const [allHomepageResults, setAllHomepageResults] = useState<Article[]>([]);
  const [allLiveResults, setAllLiveResults] = useState<Article[]>([]);
  const [conferences, setConferences] = useState<ScrapedContentItem[]>([]);
  const [announcements, setAnnouncements] = useState<ScrapedContentItem[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [likedIds, setLikedIds] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);

  const formatDate = (dateString: string) => {
    if (!dateString) return isEnglish ? 'Date unavailable' : 'Tarih yok';
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return dateString;
    return date.toLocaleDateString(language === 'en' ? 'en-US' : 'tr-TR', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  const checkSavedStatus = useCallback(
    async (articleList: Array<{ external_id: string }>) => {
      if (!userId || articleList.length === 0) return;
      try {
        const externalIds = articleList.map((article) => article.external_id).filter(Boolean);
        if (externalIds.length === 0) return;
        const result = await libraryApi.check(userId, externalIds);
        if (result.success) setSavedIds((prev) => new Set([...Array.from(prev), ...result.saved_ids]));
      } catch (error) {
        console.error(error);
      }
    },
    [userId],
  );

  const applyResultsPage = useCallback(
    async (sourceResults: Article[], page: number) => {
      const start = (page - 1) * PAGE_SIZE;
      const sliced = sourceResults.slice(start, start + PAGE_SIZE);
      setArticles(sliced);
      setTotalRecords(sourceResults.length);
      setTotalPages(Math.max(1, Math.ceil(sourceResults.length / PAGE_SIZE)));
      setCurrentPage(page);
      await checkSavedStatus(sliced);
    },
    [checkSavedStatus],
  );

  const fetchHomepageArticles = useCallback(async () => {
    setLoading(true);
    try {
      const response = await articlesApi.search({ page_size: 60, page: 1 });
      const mixed = interleaveBySource(response.results);
      setAllHomepageResults(mixed);
      await applyResultsPage(mixed, 1);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [applyResultsPage]);

  useEffect(() => {
    const loadHomepage = async () => {
      try {
        const [conferencesFeed, updatesFeed] = await Promise.all([
          scrapedContentApi.fetchLatest(1, 4, '', 'conference'),
          scrapedContentApi.fetchLatest(1, 4),
        ]);

        if (conferencesFeed.success) setConferences(conferencesFeed.contents.slice(0, 4));
        if (updatesFeed.success) setAnnouncements(updatesFeed.contents.slice(0, 4));
      } catch (error) {
        console.error(error);
      }
    };

    const loadRecommendations = async () => {
      if (!userId) return;
      setRecommendationsLoading(true);
      try {
        const response = await recommendationApi.getRecommendations(userId, 4);
        if (response.success) {
          const mixed = interleaveBySource(response.recommendations).slice(0, 4);
          setRecommendations(mixed);
          await checkSavedStatus(mixed);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setRecommendationsLoading(false);
      }
    };

    fetchHomepageArticles();
    loadHomepage();
    loadRecommendations();
  }, [fetchHomepageArticles, userId, checkSavedStatus]);

  const toggleSave = async (article: Article) => {
    if (!userId) {
      setToast({ message: isEnglish ? 'Sign in to save items.' : 'Kaydetmek için giriş yapın.', type: 'error' });
      return;
    }

    const externalId = article.external_id;
    const isSaved = savedIds.has(externalId);
    try {
      if (isSaved) {
        await libraryApi.remove(userId, externalId);
        setSavedIds((prev) => {
          const next = new Set(prev);
          next.delete(externalId);
          return next;
        });
        setToast({ message: isEnglish ? 'Removed from library.' : 'Kütüphaneden kaldırıldı.', type: 'success' });
      } else {
        await libraryApi.save(userId, {
          external_id: externalId,
          title: article.title,
          abstract: article.abstract || '',
          authors: article.authors || [],
          published_date: article.published_date || '',
          journal: article.journal || '',
          url: article.url || '',
          pdf_url: article.pdf_url || '',
          doi: article.doi || '',
          source: article.api_source?.name || '',
          categories: article.categories || [],
          citation_count: article.citation_count || 0,
        });
        setSavedIds((prev) => new Set(prev).add(externalId));
        setToast({ message: isEnglish ? 'Saved to library.' : 'Kütüphaneye kaydedildi.', type: 'success' });
      }
    } catch (error) {
      console.error(error);
      setToast({ message: isEnglish ? 'Save failed.' : 'Kaydetme işlemi başarısız.', type: 'error' });
    }
  };

  const toggleLike = async (article: Article) => {
    if (!userId) {
      setToast({ message: isEnglish ? 'Sign in to like items.' : 'Beğenmek için giriş yapın.', type: 'error' });
      return;
    }

    const externalId = article.external_id;
    const isLiked = likedIds.has(externalId);
    try {
      await activityApi.record(userId, {
        activity_type: isLiked ? 'remove_like' : 'like',
        content_id: externalId,
        content_title: article.title,
      });
      setLikedIds((prev) => {
        const next = new Set(prev);
        if (isLiked) next.delete(externalId);
        else next.add(externalId);
        return next;
      });
    } catch (error) {
      console.error(error);
    }
  };

  const toggleRecommendationSave = async (item: RecommendationItem) => {
    if (!userId) return;
    const isSaved = savedIds.has(item.external_id);

    try {
      if (isSaved) {
        await libraryApi.remove(userId, item.external_id);
        setSavedIds((prev) => {
          const next = new Set(prev);
          next.delete(item.external_id);
          return next;
        });
      } else {
        await libraryApi.save(userId, {
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

  const toggleRecommendationLike = async (item: RecommendationItem) => {
    if (!userId) return;
    const isLiked = likedIds.has(item.external_id);

    try {
      await activityApi.record(userId, {
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

  const handleSearch = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!searchQuery.trim()) return;

    if (!userStorage.isLoggedIn()) {
      setToast({ message: isEnglish ? 'Sign in for live search.' : 'Canlı arama için giriş yapın.', type: 'error' });
      return;
    }

    setLoading(true);
    setHasSearched(true);
    try {
      const response = await articlesApi.searchLive(searchQuery.trim(), 60, [], [], userId);
      if (response.success) {
        const liveResults: Article[] = response.articles.map((article, index) => ({
          id: Date.now() + index,
          external_id: article.external_id,
          title: article.title,
          abstract: article.abstract,
          authors: article.authors,
          published_date: article.published_date,
          journal: article.journal,
          url: article.url,
          pdf_url: article.pdf_url,
          image_url: article.image_url,
          doi: article.doi,
          categories: article.categories,
          keywords: article.keywords,
          citation_count: article.citation_count,
          api_source: { id: 0, name: article.source },
          fetched_at: new Date().toISOString(),
        }));
        const mixed = interleaveBySource(liveResults);
        setAllLiveResults(mixed);
        await applyResultsPage(mixed, 1);
      }
    } catch (error) {
      console.error(error);
      setToast({ message: isEnglish ? 'Search failed.' : 'Arama sırasında hata oluştu.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const goToPage = async (page: number) => {
    if (page < 1 || page > totalPages) return;
    if (hasSearched) await applyResultsPage(allLiveResults, page);
    else await applyResultsPage(allHomepageResults, page);
    window.scrollTo({ top: 620, behavior: 'smooth' });
  };

  return (
    <div className="space-y-8">
      <section className="shell hero-panel px-6 py-8 md:px-10 md:py-12">
        <div className="relative z-10 grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-3 rounded-full border border-white/65 bg-white px-4 py-2 text-sm font-semibold text-[#10233b] shadow-[0_16px_40px_rgba(8,18,32,0.2)]">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.12)]" />
              <span className="tracking-[0.01em]">
                {isEnglish ? `Welcome back, ${firstName}` : `Hoş geldin, ${firstName}`}
              </span>
            </div>

            <div className="space-y-4">
              <p className="eyebrow text-white/70">{isEnglish ? 'Academic discovery hub' : 'Akademik keşif merkezi'}</p>
              <h1 className="font-heading text-5xl leading-tight text-white md:text-6xl">
                {isEnglish
                  ? 'One interface for publications, conferences, events, and academic announcements.'
                  : 'Yayınlar, konferanslar, etkinlikler ve akademik duyurular için tek arayüz.'}
              </h1>
              <p className="max-w-2xl text-base leading-8 text-white/70 md:text-lg">
                {isEnglish
                  ? 'A calmer academic experience that brings research, deadlines, institutional updates, and personalized recommendations into one place.'
                  : 'Araştırmaları, son tarihleri, kurumsal duyuruları ve kişiselleştirilmiş önerileri tek merkezde toplayan daha modern bir akademik keşif deneyimi.'}
              </p>
            </div>

            <form onSubmit={handleSearch} className="section-card-dark p-3">
              <div className="grid gap-3 md:grid-cols-[1fr_auto]">
                <div className="flex items-center gap-3 rounded-[22px] bg-white/5 px-4 py-4">
                  <svg className="h-5 w-5 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    type="text"
                    placeholder={isEnglish ? 'Search publications, calls, conferences, or topics...' : 'Makale, konferans, çağrı veya konu ara...'}
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    className="w-full bg-transparent text-sm text-white placeholder:text-white/42 focus:outline-none"
                  />
                </div>
                <div className="flex gap-3">
                  <button type="submit" className="btn-primary w-full justify-center md:w-auto">
                    {loading ? (isEnglish ? 'Searching...' : 'Aranıyor...') : isEnglish ? 'Search' : 'Ara'}
                  </button>
                  <Link to="/search" className="btn-secondary w-full justify-center border-white/15 bg-white/5 text-white hover:bg-white/10 md:w-auto">
                    {isEnglish ? 'Advanced' : 'Gelişmiş'}
                  </Link>
                </div>
              </div>
            </form>

            <div className="flex flex-wrap gap-2">
              {topicRail.map((topic) => (
                <button key={topic} className="chip border-white/12 bg-white/5 text-white/84" onClick={() => setSearchQuery(topic)}>
                  {topic}
                </button>
              ))}
            </div>
          </div>

          <div className="hero-info-panel p-5">
            <p className="eyebrow text-white/60">{isEnglish ? 'Why LearnExp' : 'Neden LearnExp'}</p>
            <div className="mt-4 grid gap-3">
              <div className="hero-info-card">
                <p className="text-sm font-semibold">{isEnglish ? 'Search-first academic experience' : 'Arama merkezli akademik deneyim'}</p>
                <p className="mt-1 text-sm text-white/70">
                  {isEnglish ? 'Move from query to source, abstract, event, and deadline faster.' : 'Sorgudan kaynağa, özete, etkinliğe ve son tarihe daha hızlı ilerleyin.'}
                </p>
              </div>
              <div className="hero-info-card">
                <p className="text-sm font-semibold">{isEnglish ? 'Structured content layers' : 'Yapısal içerik katmanları'}</p>
                <p className="mt-1 text-sm text-white/70">
                  {isEnglish ? 'Differentiate publications, conferences, reports, and notices instantly.' : 'Makale, konferans, rapor ve kurumsal duyuruları anında ayırt edin.'}
                </p>
              </div>
              <div className="hero-info-card">
                <p className="text-sm font-semibold">{isEnglish ? 'Library and tracking mindset' : 'Kütüphane ve takip mantığı'}</p>
                <p className="mt-1 text-sm text-white/70">
                  {isEnglish ? 'Save, revisit, and follow the themes most relevant to your work.' : 'Önemli araştırmaları kaydedin, geri dönün ve ilgi alanlarınızı takip edin.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="shell">
        <div className="section-card p-6 md:p-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="eyebrow mb-2">{isEnglish ? 'Content lanes' : 'İçerik akışları'}</p>
              <h2 className="font-heading text-4xl text-[var(--text-strong)]">
                {isEnglish ? 'Publications, conferences, events, and announcements on a single surface.' : 'Tek ekranda yayın, konferans, etkinlik ve duyuru keşfi.'}
              </h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {(isEnglish ? ['Publications', 'Conferences', 'Events', 'Announcements', 'Deadlines'] : ['Yayınlar', 'Konferanslar', 'Etkinlikler', 'Duyurular', 'Son Tarihler']).map((item, index) => (
                <span key={item} className={`chip ${index === 0 ? 'chip-active' : ''}`}>
                  {item}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="shell space-y-4">
        <div className="flex items-end justify-between">
          <div>
            <p className="eyebrow mb-2">{isEnglish ? 'Featured research' : 'Öne çıkan araştırmalar'}</p>
            <h2 className="font-heading text-4xl text-[var(--text-strong)]">
              {isEnglish ? 'Editorially surfaced publications and updates' : 'Editoryal olarak öne çıkarılmış içerikler'}
            </h2>
          </div>
          <Link to="/news" className="text-sm font-semibold text-[var(--brand)]">
            {isEnglish ? 'View all updates' : 'Tümünü gör'}
          </Link>
        </div>
        <NewsSlider />
      </section>

      <section className="shell">
        <div className="section-card p-6 md:p-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="eyebrow mb-2">{isEnglish ? 'For you' : 'Sana özel'}</p>
              <h2 className="font-heading text-4xl text-[var(--text-strong)]">
                {isEnglish ? 'Recommendations matched to your profile' : 'Profiline göre eşleşen öneriler'}
              </h2>
            </div>
            <div className="flex items-center gap-3">
              {userId && (
                <span className="rounded-full bg-[var(--brand-soft)] px-4 py-2 text-xs font-semibold text-[var(--brand)]">
                  {recommendations.length} {isEnglish ? 'matched items' : 'uyumlu içerik'}
                </span>
              )}
              <Link to="/recommendations" className="text-sm font-semibold text-[var(--brand)]">
                {isEnglish ? 'View all recommendations' : 'Tümünü gör'}
              </Link>
            </div>
          </div>

          {!userId ? (
            <div className="mt-6 rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-alt)] px-8 py-12 text-center">
              <p className="font-heading text-2xl text-[var(--text-strong)]">
                {isEnglish ? 'Sign in to unlock tailored recommendations.' : 'Kişiselleştirilmiş önerileri görmek için giriş yap.'}
              </p>
            </div>
          ) : recommendationsLoading ? (
            <div className="mt-6 grid gap-4">
              {Array.from({ length: 3 }).map((_, index) => (
                <div key={index} className="h-56 animate-pulse rounded-[24px] border border-[var(--line-soft)] bg-[var(--surface-alt)]" />
              ))}
            </div>
          ) : recommendations.length > 0 ? (
            <div className="mt-6 space-y-4">
              {recommendations.map((item) => (
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
                  onToggleSave={() => toggleRecommendationSave(item)}
                  isLiked={likedIds.has(item.external_id)}
                  onToggleLike={() => toggleRecommendationLike(item)}
                />
              ))}
            </div>
          ) : (
            <div className="mt-6 rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-alt)] px-8 py-12 text-center">
              <p className="font-heading text-2xl text-[var(--text-strong)]">
                {isEnglish ? 'Recommendations will appear here as your profile grows stronger.' : 'Profilin güçlendikçe öneriler burada görünecek.'}
              </p>
            </div>
          )}
        </div>
      </section>

      <section className="shell grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="section-card p-6 md:p-8">
          <div className="mb-6 flex items-end justify-between">
            <div>
              <p className="eyebrow mb-2">{isEnglish ? 'Curated publications' : 'Seçilmiş yayınlar'}</p>
              <h2 className="font-heading text-4xl text-[var(--text-strong)]">
                {hasSearched ? (isEnglish ? 'Search results' : 'Arama sonuçları') : isEnglish ? 'Latest publications' : 'Son yayınlar'}
              </h2>
            </div>
            <span className="rounded-full bg-[var(--brand-soft)] px-4 py-2 text-xs font-semibold text-[var(--brand)]">
              {totalRecords} {isEnglish ? 'records' : 'kayıt'}
            </span>
          </div>

          <div className="space-y-4">
            {articles.length > 0 ? (
              articles.map((article) => (
                <ContentCard
                  key={article.external_id || article.id}
                  content={{
                    id: article.external_id || article.id.toString(),
                    type: inferContentType(article),
                    title: article.title,
                    description: article.abstract || (isEnglish ? 'No abstract available.' : 'Özet bilgisi bulunmuyor.'),
                    source: article.api_source?.name || (isEnglish ? 'Academic source' : 'Akademik kaynak'),
                    authors: article.authors?.map((author) => author.name).join(', '),
                    date: article.published_date || article.fetched_at,
                    journal: article.journal || '',
                    citations: article.citation_count || 0,
                    tags: article.categories?.slice(0, 3) || [],
                    keywords: article.keywords?.slice(0, 2) || [],
                    url: article.url || '',
                    pdfUrl: article.pdf_url || '',
                    imageUrl: article.image_url,
                  }}
                  isSaved={savedIds.has(article.external_id)}
                  onToggleSave={() => toggleSave(article)}
                  isLiked={likedIds.has(article.external_id)}
                  onToggleLike={() => toggleLike(article)}
                />
              ))
            ) : (
              <div className="rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-alt)] px-8 py-12 text-center">
                <p className="font-heading text-2xl text-[var(--text-strong)]">
                  {isEnglish ? 'Start with a research query.' : 'Bir araştırma sorgusu ile başla.'}
                </p>
                <p className="mt-2 text-sm text-[var(--text-muted)]">
                  {isEnglish ? 'Results will appear here and stay balanced across sources.' : 'Sonuçlar burada görünecek ve kaynak çeşitliliği korunacak.'}
                </p>
              </div>
            )}
          </div>

          {totalPages > 1 && (
            <div className="flex flex-wrap items-center justify-center gap-2 pt-6">
              <button onClick={() => goToPage(currentPage - 1)} disabled={currentPage === 1} className="btn-secondary px-4 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-40">
                {isEnglish ? 'Prev' : 'Önceki'}
              </button>
              {getPageNumbers(currentPage, totalPages).map((page, index) =>
                page === '...' ? (
                  <span key={`dots-${index}`} className="px-2 text-sm text-[var(--text-muted)]">...</span>
                ) : (
                  <button
                    key={page}
                    onClick={() => goToPage(page)}
                    className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-semibold ${
                      currentPage === page ? 'bg-[var(--brand)] text-white' : 'border border-[var(--line)] text-[var(--text-primary)]'
                    }`}
                  >
                    {page}
                  </button>
                ),
              )}
              <button onClick={() => goToPage(currentPage + 1)} disabled={currentPage === totalPages} className="btn-secondary px-4 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-40">
                {isEnglish ? 'Next' : 'Sonraki'}
              </button>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="section-card p-6">
            <p className="eyebrow mb-2">{isEnglish ? 'Upcoming conferences' : 'Yaklaşan konferanslar'}</p>
            <h2 className="font-heading text-3xl text-[var(--text-strong)]">{isEnglish ? 'Date-led events' : 'Tarih odaklı etkinlikler'}</h2>
            <div className="mt-5 space-y-3">
              {conferences.length > 0 ? (
                conferences.map((conference) => (
                  <a
                    key={conference.id}
                    href={conference.source_url?.startsWith('http') ? conference.source_url : '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex gap-4 rounded-[22px] border border-[var(--line-soft)] bg-[var(--surface-alt)] p-4"
                  >
                    {conference.image_url ? (
                      <img src={conference.image_url} alt={conference.title} className="h-24 w-24 rounded-[18px] object-cover" />
                    ) : (
                      <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-[18px] bg-[linear-gradient(135deg,#15325c,#27509a)] text-white">
                        <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                    )}

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-3">
                        <span className="badge-ai">{isEnglish ? 'Conference' : 'Konferans'}</span>
                        <span className="text-xs text-[var(--text-muted)]">{formatDate(conference.published_date || '')}</span>
                      </div>
                      <h3 className="mt-3 text-base font-semibold text-[var(--text-strong)]">{conference.title}</h3>
                      <p className="mt-2 line-clamp-2 text-sm text-[var(--text-muted)]">
                        {conference.abstract || (isEnglish ? 'No event summary yet.' : 'Etkinlik özeti henüz eklenmedi.')}
                      </p>
                    </div>
                  </a>
                ))
              ) : (
                <p className="text-sm text-[var(--text-muted)]">{isEnglish ? 'Conference data will appear here.' : 'Konferans verisi geldiğinde burada görünecek.'}</p>
              )}
            </div>
          </div>

          <div className="section-card p-6">
            <p className="eyebrow mb-2">{isEnglish ? 'Latest announcements' : 'Son duyurular'}</p>
            <h2 className="font-heading text-3xl text-[var(--text-strong)]">{isEnglish ? 'Institutional and editorial updates' : 'Kurumsal ve editoryal güncellemeler'}</h2>
            <div className="mt-5 space-y-4">
              {announcements.slice(0, 4).map((item) => (
                <a
                  key={item.id}
                  href={item.source_url?.startsWith('http') ? item.source_url : '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block border-b border-[var(--line-soft)] pb-4 last:border-b-0"
                >
                  <div className="flex items-center gap-2">
                    <span className="badge-default">{item.content_type || (isEnglish ? 'Update' : 'Güncelleme')}</span>
                    <span className="text-xs text-[var(--text-muted)]">{item.scraper_name || (isEnglish ? 'LearnExp source' : 'LearnExp kaynağı')}</span>
                  </div>
                  <h3 className="mt-3 text-base font-semibold text-[var(--text-strong)]">{item.title}</h3>
                  <p className="mt-2 line-clamp-2 text-sm text-[var(--text-muted)]">
                    {item.abstract || (isEnglish ? 'Summary unavailable.' : 'Güncelleme özeti bulunamadı.')}
                  </p>
                </a>
              ))}
            </div>
          </div>

          <div className="section-card-dark p-6 text-white">
            <p className="eyebrow text-white/60">{isEnglish ? 'Trust layer' : 'Güven katmanı'}</p>
            <h2 className="mt-2 font-heading text-3xl">
              {isEnglish ? 'Built for credible academic discovery.' : 'Akademik güvenilirlik için tasarlandı.'}
            </h2>
            <div className="mt-5 grid gap-3">
              <div className="rounded-[22px] border border-white/10 bg-white/5 p-4">
                <p className="text-sm font-semibold">{isEnglish ? 'Source-first presentation' : 'Kaynak odaklı kurgulama'}</p>
                <p className="mt-1 text-sm text-white/65">
                  {isEnglish ? 'The interface prioritizes source, date, and content type before decoration.' : 'Görsel süsten önce kaynak, tarih ve içerik türünü öne çıkarır.'}
                </p>
              </div>
              <div className="rounded-[22px] border border-white/10 bg-white/5 p-4">
                <p className="text-sm font-semibold">{isEnglish ? 'Search-centered discovery' : 'Arama merkezli keşif'}</p>
                <p className="mt-1 text-sm text-white/65">
                  {isEnglish ? 'Homepage, news, and library flows keep search at the center.' : 'Anasayfa, haberler ve kütüphane akışında aramayı merkezde tutar.'}
                </p>
              </div>
              <div className="rounded-[22px] border border-white/10 bg-white/5 p-4">
                <p className="text-sm font-semibold">{isEnglish ? 'Balanced source mix' : 'Dengeli kaynak karışımı'}</p>
                <p className="mt-1 text-sm text-white/65">
                  {isEnglish ? 'Results are interleaved so one source does not dominate the page.' : 'Sonuçlar kaynaklar arasında karıştırılır; tek bir kaynak sayfayı domine etmez.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
};

export default Dashboard;
