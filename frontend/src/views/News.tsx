import React, { useEffect, useState } from 'react';
import { activityApi, libraryApi, scrapedContentApi, scrapersApi, userStorage } from '../services/api';
import type { ScrapedContentItem } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

const NewsPage: React.FC = () => {
  const { isEnglish, language } = useLanguage();
  const contentTypes = [
    { value: '', label: isEnglish ? 'All content' : 'Tüm içerikler' },
    { value: 'article', label: isEnglish ? 'Publications' : 'Yayınlar' },
    { value: 'conference', label: isEnglish ? 'Conferences' : 'Konferanslar' },
    { value: 'event', label: isEnglish ? 'Events' : 'Etkinlikler' },
    { value: 'funding', label: isEnglish ? 'Funding' : 'Fonlar' },
    { value: 'report', label: isEnglish ? 'Reports' : 'Raporlar' },
  ];

  const typeTone: Record<string, string> = {
    article: 'badge-space',
    conference: 'badge-ai',
    event: 'badge-business',
    funding: 'badge-biotech',
    report: 'badge-default',
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return isEnglish ? 'Date unavailable' : 'Tarih yok';
    const date = new Date(dateStr);
    if (Number.isNaN(date.getTime())) return dateStr;
    return date.toLocaleDateString(language === 'en' ? 'en-US' : 'tr-TR', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  const [items, setItems] = useState<ScrapedContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [draftQuery, setDraftQuery] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [scrapers, setScrapers] = useState<{ id: number; name: string; is_active: boolean }[]>([]);
  const [selectedScrapers, setSelectedScrapers] = useState<number[]>([]);
  const [isScraping, setIsScraping] = useState(false);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const itemsPerPage = 9;

  useEffect(() => {
    fetchNews();
    fetchScrapers();
  }, [currentPage, selectedType, searchQuery]);

  useEffect(() => {
    const checkSaved = async () => {
      const user = userStorage.getUser();
      if (!user || items.length === 0) return;
      const externalIds = items.map((item) => item.source_url || `scraped-${item.id}`);
      try {
        const response = await libraryApi.check(user.id, externalIds);
        if (response.success) setSavedIds(new Set(response.saved_ids));
      } catch (error) {
        console.error(error);
      }
    };
    checkSaved();
  }, [items]);

  const fetchNews = async () => {
    setLoading(true);
    try {
      const response = await scrapedContentApi.fetchLatest(currentPage, itemsPerPage, searchQuery, selectedType);
      if (response.success) {
        setItems(response.contents);
        setTotalItems(response.total);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchScrapers = async () => {
    try {
      setScrapers(await scrapersApi.list());
    } catch (error) {
      console.error(error);
    }
  };

  const handleSearch = (event: React.FormEvent) => {
    event.preventDefault();
    setCurrentPage(1);
    setSearchQuery(draftQuery.trim());
  };

  const toggleSave = async (item: ScrapedContentItem) => {
    const user = userStorage.getUser();
    if (!user) return;

    const externalId = item.source_url || `scraped-${item.id}`;
    const isSaved = savedIds.has(externalId);

    try {
      if (isSaved) {
        await libraryApi.remove(user.id, externalId);
        setSavedIds((prev) => {
          const next = new Set(prev);
          next.delete(externalId);
          return next;
        });
      } else {
        await libraryApi.save(user.id, {
          external_id: externalId,
          title: item.title,
          abstract: item.abstract || '',
          authors: (item.authors || []).map((author: string | { name: string }) => (typeof author === 'string' ? { name: author } : author)),
          published_date: item.published_date || '',
          journal: '',
          url: item.source_url || '',
          pdf_url: '',
          doi: '',
          source: item.scraper_name || (isEnglish ? 'Source' : 'Kaynak'),
          categories: item.keywords || [],
          citation_count: 0,
        });
        setSavedIds((prev) => new Set(prev).add(externalId));
      }
    } catch (error) {
      console.error(error);
    }
  };

  const handleScrapeNow = async () => {
    if (selectedScrapers.length === 0) return;
    setIsScraping(true);
    try {
      await Promise.all(selectedScrapers.map((id) => scrapersApi.run(id, searchQuery || undefined)));
      setTimeout(() => {
        fetchNews();
        setIsScraping(false);
      }, 1800);
    } catch (error) {
      console.error(error);
      setIsScraping(false);
    }
  };

  const toggleScraper = (id: number) => {
    setSelectedScrapers((prev) => (prev.includes(id) ? prev.filter((value) => value !== id) : [...prev, id]));
  };

  const logView = async (item: ScrapedContentItem) => {
    const user = userStorage.getUser();
    if (!user || !item.source_url) return;
    try {
      await activityApi.record(user.id, {
        activity_type: 'view',
        content_title: item.title,
        content_id: item.source_url,
      });
    } catch (error) {
      console.error(error);
    }
  };

  const totalPages = Math.ceil(totalItems / itemsPerPage);

  return (
    <div className="space-y-8">
      <section className="shell page-hero px-6 py-8 md:px-10 md:py-12">
        <div className="relative z-10 max-w-4xl space-y-5 text-white">
          <p className="eyebrow text-white/65">{isEnglish ? 'Academic news desk' : 'Akademik haber masası'}</p>
          <h1 className="font-heading text-5xl leading-tight md:text-6xl">
            {isEnglish ? 'Announcements, conferences, deadlines, and source-led updates.' : 'Duyurular, konferanslar, son tarihler ve kaynak odaklı güncellemeler.'}
          </h1>
          <p className="max-w-2xl text-base leading-8 text-white/70 md:text-lg">
            {isEnglish
              ? 'Scan academic updates faster, filter by content type, and refresh active sources from a single panel.'
              : 'Güncel akademik içerikleri daha hızlı tarayın, içerik türüne göre filtreleyin ve kaynakları tek panelden yenileyin.'}
          </p>

          <form onSubmit={handleSearch} className="section-card-dark p-3">
            <div className="grid gap-3 md:grid-cols-[1fr_auto]">
              <input
                type="text"
                placeholder={isEnglish ? 'Search announcements, conferences, or updates...' : 'Duyuru, konferans veya güncelleme ara...'}
                value={draftQuery}
                onChange={(event) => setDraftQuery(event.target.value)}
                className="rounded-[22px] bg-white/5 px-4 py-4 text-sm text-white placeholder:text-white/45 focus:outline-none"
              />
              <button type="submit" className="btn-primary justify-center">
                {isEnglish ? 'Search' : 'Ara'}
              </button>
            </div>
          </form>
        </div>
      </section>

      <section className="shell grid gap-6 xl:grid-cols-[320px_1fr]">
        <aside className="section-card h-fit p-6">
          <p className="eyebrow mb-2">{isEnglish ? 'Control panel' : 'Kontrol paneli'}</p>
          <h2 className="font-heading text-3xl text-[var(--text-strong)]">{isEnglish ? 'Refine the feed' : 'Akışı filtrele'}</h2>

          <div className="mt-6 space-y-5">
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">
                {isEnglish ? 'Content type' : 'İçerik türü'}
              </label>
              <select
                value={selectedType}
                onChange={(event) => {
                  setSelectedType(event.target.value);
                  setCurrentPage(1);
                }}
                className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]"
              >
                {contentTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <label className="block text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">
                  {isEnglish ? 'Sources' : 'Kaynaklar'}
                </label>
                <span className="text-xs text-[var(--text-muted)]">
                  {selectedScrapers.length} {isEnglish ? 'selected' : 'seçili'}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {scrapers.map((scraper) => (
                  <button
                    key={scraper.id}
                    onClick={() => toggleScraper(scraper.id)}
                    disabled={!scraper.is_active}
                    className={`chip ${selectedScrapers.includes(scraper.id) ? 'chip-active' : ''} ${!scraper.is_active ? 'opacity-40' : ''}`}
                  >
                    {scraper.name}
                  </button>
                ))}
              </div>
            </div>

            <button onClick={handleScrapeNow} disabled={isScraping || selectedScrapers.length === 0} className="btn-primary w-full justify-center disabled:cursor-not-allowed disabled:opacity-50">
              {isScraping
                ? isEnglish
                  ? 'Refreshing sources...'
                  : 'Kaynaklar yenileniyor...'
                : isEnglish
                  ? 'Refresh selected sources'
                  : 'Seçili kaynakları güncelle'}
            </button>
          </div>
        </aside>

        <div className="space-y-5">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="eyebrow mb-2">{isEnglish ? 'Latest updates' : 'Son güncellemeler'}</p>
              <h2 className="font-heading text-4xl text-[var(--text-strong)]">
                {isEnglish ? 'Source-led academic content feed' : 'Kaynak odaklı akademik içerik akışı'}
              </h2>
            </div>
            <span className="rounded-full bg-[var(--brand-soft)] px-4 py-2 text-xs font-semibold text-[var(--brand)]">
              {totalItems} {isEnglish ? 'items' : 'içerik'}
            </span>
          </div>

          {loading ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, index) => (
                <div key={index} className="h-80 animate-pulse rounded-[24px] border border-[var(--line-soft)] bg-[var(--surface)]" />
              ))}
            </div>
          ) : items.length > 0 ? (
            <>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {items.map((item) => (
                  <article key={item.id} className="card-base flex h-full flex-col overflow-hidden">
                    <div className={`relative ${item.image_url ? 'h-52' : 'h-28 bg-[linear-gradient(135deg,#10315b,#2854a1)]'}`}>
                      {item.image_url ? (
                        <img src={item.image_url} alt={item.title} className="h-full w-full object-cover" />
                      ) : (
                        <div className="flex h-full items-center justify-center text-white/65">
                          <svg className="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                          </svg>
                        </div>
                      )}
                      <div className="absolute left-4 top-4">
                        <span className={typeTone[item.content_type] || 'badge-default'}>{item.content_type || (isEnglish ? 'Update' : 'Güncelleme')}</span>
                      </div>
                    </div>

                    <div className="flex flex-1 flex-col p-5">
                      <div className="flex items-center justify-between gap-3 text-xs text-[var(--text-muted)]">
                        <span>{item.scraper_name || (isEnglish ? 'LearnExp source' : 'LearnExp kaynağı')}</span>
                        <span>{formatDate(item.published_date)}</span>
                      </div>

                      <div className="mt-4 space-y-3">
                        <h3 className="font-heading text-2xl leading-tight text-[var(--text-strong)]">{item.title}</h3>
                        <p className="line-clamp-3 text-sm leading-7 text-[var(--text-primary)]">
                          {item.abstract || (isEnglish ? 'No source summary available.' : 'Kaynağa ait özet bulunmuyor.')}
                        </p>
                      </div>

                      <div className="mt-4 flex flex-wrap gap-2">
                        {(item.keywords || []).slice(0, 2).map((keyword) => (
                          <span key={keyword} className="chip">
                            {keyword}
                          </span>
                        ))}
                      </div>

                      <div className="mt-auto flex items-end justify-between border-t border-[var(--line-soft)] pt-5">
                        <button
                          onClick={() => toggleSave(item)}
                          className={`flex h-10 w-10 items-center justify-center rounded-full border ${
                            savedIds.has(item.source_url || `scraped-${item.id}`)
                              ? 'border-[rgba(45,99,226,0.18)] bg-[var(--brand-soft)] text-[var(--brand)]'
                              : 'border-[var(--line)] text-[var(--text-muted)]'
                          }`}
                          title={savedIds.has(item.source_url || `scraped-${item.id}`) ? (isEnglish ? 'Saved' : 'Kaydedildi') : isEnglish ? 'Save' : 'Kaydet'}
                          aria-label={savedIds.has(item.source_url || `scraped-${item.id}`) ? (isEnglish ? 'Saved' : 'Kaydedildi') : isEnglish ? 'Save' : 'Kaydet'}
                        >
                          <svg className="h-4 w-4" fill={savedIds.has(item.source_url || `scraped-${item.id}`) ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                          </svg>
                        </button>

                        {item.source_url?.startsWith('http') ? (
                          <a href={item.source_url} target="_blank" rel="noopener noreferrer" onClick={() => logView(item)} className="btn-primary px-4 py-2 text-xs">
                            {isEnglish ? 'Inspect' : 'İncele'}
                          </a>
                        ) : (
                          <span className="text-sm text-[var(--text-muted)]">{isEnglish ? 'No link' : 'Bağlantı yok'}</span>
                        )}
                      </div>
                    </div>
                  </article>
                ))}
              </div>

              {totalPages > 1 && (
                <div className="flex justify-center gap-3 pt-4">
                  <button onClick={() => setCurrentPage((page) => Math.max(1, page - 1))} disabled={currentPage === 1} className="btn-secondary disabled:cursor-not-allowed disabled:opacity-40">
                    {isEnglish ? 'Prev' : 'Önceki'}
                  </button>
                  <div className="chip">{currentPage} / {totalPages}</div>
                  <button onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))} disabled={currentPage === totalPages} className="btn-secondary disabled:cursor-not-allowed disabled:opacity-40">
                    {isEnglish ? 'Next' : 'Sonraki'}
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="section-card px-8 py-16 text-center">
              <p className="font-heading text-3xl text-[var(--text-strong)]">
                {isEnglish ? 'No content found for this view.' : 'Bu görünüm için içerik bulunamadı.'}
              </p>
              <p className="mt-2 text-sm text-[var(--text-muted)]">
                {isEnglish ? 'Try broadening the query, changing the content type, or refreshing the selected sources.' : 'Aramayı genişletmeyi, içerik türünü değiştirmeyi veya seçili kaynakları yenilemeyi deneyin.'}
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default NewsPage;
