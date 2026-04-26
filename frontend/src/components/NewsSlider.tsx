import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { activityApi, libraryApi, scrapedContentApi, userStorage } from '../services/api';
import type { ScrapedContentItem } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

const NewsSlider: React.FC = () => {
  const { isEnglish, language } = useLanguage();
  const [items, setItems] = useState<ScrapedContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [likedIds, setLikedIds] = useState<Set<string>>(new Set());
  const [isAutoPaused, setIsAutoPaused] = useState(false);
  const sliderRef = useRef<HTMLDivElement | null>(null);

  const typeLabels: Record<string, string> = {
    article: isEnglish ? 'Article' : 'Makale',
    thesis: isEnglish ? 'Thesis' : 'Tez',
    conference: isEnglish ? 'Conference' : 'Konferans',
    book: isEnglish ? 'Book' : 'Kitap',
    report: isEnglish ? 'Report' : 'Rapor',
    funding: isEnglish ? 'Funding' : 'Fon',
    event: isEnglish ? 'Event' : 'Etkinlik',
    other: isEnglish ? 'Update' : 'Güncelleme',
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return isEnglish ? 'Date unavailable' : 'Tarih yok';
    const date = new Date(dateStr);
    if (Number.isNaN(date.getTime())) return dateStr;
    return date.toLocaleDateString(language === 'en' ? 'en-US' : 'tr-TR', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await scrapedContentApi.fetchLatest(1, 8);
        if (response.success) {
          const nextItems = response.contents.slice(0, 8);
          setItems(nextItems);
          const user = userStorage.getUser();
          if (user && nextItems.length > 0) {
            const extIds = nextItems.map((item) => item.source_url || `scraped-${item.id}`);
            const checkRes = await libraryApi.check(user.id, extIds);
            if (checkRes.success) setSavedIds(new Set(checkRes.saved_ids));
          }
        }
      } catch (error) {
        console.error('Failed to fetch news:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, []);

  const orderedItems = useMemo(() => items.slice(0, 8), [items]);

  const toggleSave = async (item: ScrapedContentItem) => {
    const user = userStorage.getUser();
    if (!user) return;
    const extId = item.source_url || `scraped-${item.id}`;
    const isSaved = savedIds.has(extId);

    try {
      if (isSaved) {
        await libraryApi.remove(user.id, extId);
        setSavedIds((prev) => {
          const next = new Set(prev);
          next.delete(extId);
          return next;
        });
      } else {
        await libraryApi.save(user.id, {
          external_id: extId,
          title: item.title,
          abstract: item.abstract || '',
          authors: (item.authors || []).map((author: string | { name: string }) => (typeof author === 'string' ? { name: author } : author)),
          published_date: item.published_date || '',
          journal: '',
          url: item.source_url || '',
          pdf_url: '',
          doi: '',
          source: item.scraper_name || 'Scraper',
          categories: item.keywords || [],
          citation_count: 0,
        });
        setSavedIds((prev) => new Set(prev).add(extId));
      }
    } catch (error) {
      console.error(error);
    }
  };

  const toggleLike = async (item: ScrapedContentItem) => {
    const user = userStorage.getUser();
    if (!user) return;
    const extId = item.source_url || `scraped-${item.id}`;
    const isLiked = likedIds.has(extId);

    try {
      await activityApi.record(user.id, {
        activity_type: isLiked ? 'remove_like' : 'like',
        content_id: extId,
        content_title: item.title,
      });
      setLikedIds((prev) => {
        const next = new Set(prev);
        if (isLiked) next.delete(extId);
        else next.add(extId);
        return next;
      });
    } catch (error) {
      console.error(error);
    }
  };

  const slide = useCallback((direction: 'prev' | 'next') => {
    if (!sliderRef.current) return;
    const slider = sliderRef.current;
    const amount = slider.clientWidth * 0.82;
    const maxScrollLeft = slider.scrollWidth - slider.clientWidth;

    if (direction === 'next') {
      const nextLeft = slider.scrollLeft + amount;
      if (nextLeft >= maxScrollLeft - 24) {
        slider.scrollTo({ left: 0, behavior: 'smooth' });
        return;
      }

      slider.scrollBy({
        left: amount,
        behavior: 'smooth',
      });
      return;
    }

    const previousLeft = slider.scrollLeft - amount;
    if (previousLeft <= 0) {
      slider.scrollTo({ left: Math.max(maxScrollLeft, 0), behavior: 'smooth' });
      return;
    }

    slider.scrollBy({
      left: -amount,
      behavior: 'smooth',
    });
  }, []);

  useEffect(() => {
    if (orderedItems.length <= 1 || isAutoPaused) return;

    const intervalId = window.setInterval(() => {
      slide('next');
    }, 5000);

    return () => window.clearInterval(intervalId);
  }, [orderedItems.length, isAutoPaused, slide]);

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="h-80 animate-pulse rounded-[24px] border border-[var(--line-soft)] bg-[var(--surface)]" />
        ))}
      </div>
    );
  }

  if (orderedItems.length === 0) {
    return (
      <div className="section-card px-8 py-12 text-center">
        <p className="font-heading text-2xl text-[var(--text-strong)]">{isEnglish ? 'No featured items yet' : 'Henüz öne çıkan içerik yok'}</p>
        <p className="mt-2 text-sm text-[var(--text-muted)]">{isEnglish ? 'New publications and announcements will appear here.' : 'Yeni yayınlar ve duyurular burada görünecek.'}</p>
      </div>
    );
  }

  return (
    <div
      className="relative"
      onMouseEnter={() => setIsAutoPaused(true)}
      onMouseLeave={() => setIsAutoPaused(false)}
      onFocusCapture={() => setIsAutoPaused(true)}
      onBlurCapture={() => setIsAutoPaused(false)}
    >
      {orderedItems.length > 1 && (
        <>
          <button
            onClick={() => slide('prev')}
            className="absolute left-3 top-1/2 z-10 hidden h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full border border-[var(--line-soft)] bg-[color-mix(in_srgb,var(--surface)_88%,white_12%)] text-[var(--text-strong)] shadow-[var(--shadow-md)] transition-transform hover:scale-[1.03] md:flex"
            title={isEnglish ? 'Previous' : 'Önceki'}
            aria-label={isEnglish ? 'Previous' : 'Önceki'}
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <button
            onClick={() => slide('next')}
            className="absolute right-3 top-1/2 z-10 hidden h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full border border-[var(--line-soft)] bg-[color-mix(in_srgb,var(--surface)_88%,white_12%)] text-[var(--text-strong)] shadow-[var(--shadow-md)] transition-transform hover:scale-[1.03] md:flex"
            title={isEnglish ? 'Next' : 'Sonraki'}
            aria-label={isEnglish ? 'Next' : 'Sonraki'}
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </>
      )}

      <div ref={sliderRef} className="flex snap-x snap-mandatory gap-4 overflow-x-auto pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {orderedItems.map((item) => {
          const extId = item.source_url || `scraped-${item.id}`;
          const isSaved = savedIds.has(extId);
          const isLiked = likedIds.has(extId);
          const itemType = typeLabels[item.content_type] || (isEnglish ? 'Update' : 'Güncelleme');
          const sourceName = item.scraper_name || (isEnglish ? 'LearnExp source' : 'LearnExp kaynağı');
          const hasImage = Boolean(item.image_url);

          return (
            <article key={item.id} className="card-base flex w-[88%] min-w-[88%] snap-start flex-col overflow-hidden md:w-[48%] md:min-w-[48%] xl:w-[32%] xl:min-w-[32%]">
              <div className={`relative ${hasImage ? 'h-52' : 'h-28 bg-[linear-gradient(135deg,#10315b,#2854a1)]'}`}>
                {hasImage ? (
                  <img src={item.image_url} alt={item.title} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center text-white/65">
                    <svg className="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                    </svg>
                  </div>
                )}
                <div className="absolute left-4 top-4 flex items-center gap-2">
                  <span className="badge-space">{itemType}</span>
                </div>
              </div>

              <div className="flex flex-1 flex-col p-5">
                <div className="flex items-center justify-between gap-3 text-xs text-[var(--text-muted)]">
                  <span>{sourceName}</span>
                  <span>{formatDate(item.published_date)}</span>
                </div>

                <div className="mt-4 space-y-3">
                  <h3 className="font-heading text-2xl leading-tight text-[var(--text-strong)]">{item.title}</h3>
                  <p className="line-clamp-3 text-sm leading-7 text-[var(--text-primary)]">
                    {item.abstract || (isEnglish ? 'No summary available for this source.' : 'Kaynağa ait özet bulunamadı.')}
                  </p>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {(item.keywords || []).slice(0, 2).map((keyword) => (
                    <span key={keyword} className="chip">
                      {keyword}
                    </span>
                  ))}
                </div>

                <div className="mt-auto flex items-end justify-between gap-3 border-t border-[var(--line-soft)] pt-5">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleLike(item)}
                      className={`flex h-10 w-10 items-center justify-center rounded-full border ${
                        isLiked ? 'border-[rgba(198,69,69,0.18)] bg-[rgba(198,69,69,0.08)] text-[var(--danger)]' : 'border-[var(--line)] text-[var(--text-muted)]'
                      }`}
                      title={isLiked ? (isEnglish ? 'Remove like' : 'Beğeniyi kaldır') : isEnglish ? 'Like' : 'Beğen'}
                      aria-label={isLiked ? (isEnglish ? 'Remove like' : 'Beğeniyi kaldır') : isEnglish ? 'Like' : 'Beğen'}
                    >
                      <svg className="h-4 w-4" fill={isLiked ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => toggleSave(item)}
                      className={`flex h-10 w-10 items-center justify-center rounded-full border ${
                        isSaved ? 'border-[rgba(45,99,226,0.18)] bg-[var(--brand-soft)] text-[var(--brand)]' : 'border-[var(--line)] text-[var(--text-muted)]'
                      }`}
                      title={isSaved ? (isEnglish ? 'Saved' : 'Kaydedildi') : isEnglish ? 'Save' : 'Kaydet'}
                      aria-label={isSaved ? (isEnglish ? 'Saved' : 'Kaydedildi') : isEnglish ? 'Save' : 'Kaydet'}
                    >
                      <svg className="h-4 w-4" fill={isSaved ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                      </svg>
                    </button>
                  </div>
                  {item.source_url?.startsWith('http') && (
                    <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="btn-primary px-4 py-2 text-xs">
                      {isEnglish ? 'Inspect' : 'İncele'}
                    </a>
                  )}
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
};

export default NewsSlider;
