import React, { useEffect, useState } from 'react';
import ContentCard from '../components/ContentCard';
import { activityApi, articlesApi, libraryApi, scrapersApi, userStorage } from '../services/api';
import type { Article, APISource } from '../services/api';
import type { ContentType } from '../types';
import { interleaveBySource } from '../utils/content';

const PAGE_SIZE = 12;

const inferContentType = (article: Article): ContentType => {
  const sourceName = (article.api_source?.name || '').toLowerCase();
  const url = (article.url || '').toLowerCase();
  if (sourceName.includes('conference') || url.includes('conference')) return 'conference';
  if (sourceName.includes('event') || url.includes('event')) return 'event';
  return 'article';
};

const SearchDashboard: React.FC = () => {
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [likedIds, setLikedIds] = useState<Set<string>>(new Set());
  const [articles, setArticles] = useState<Article[]>([]);
  const [allResults, setAllResults] = useState<Article[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [dateRange, setDateRange] = useState('');
  const [categories, setCategories] = useState<string[]>([]);
  const [apiSources, setApiSources] = useState<APISource[]>([]);
  const [scraperSources, setScraperSources] = useState<APISource[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [timedOutSources, setTimedOutSources] = useState<string[]>([]);
  const [isPartial, setIsPartial] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [catsData, srcsData, scrapersData] = await Promise.all([
          articlesApi.getCategories(),
          articlesApi.getSources(),
          scrapersApi.list(),
        ]);
        setCategories(catsData.slice(0, 10));
        setApiSources(srcsData);
        setScraperSources(
          scrapersData.map((scraper) => ({
            id: 1000 + scraper.id,
            name: scraper.name,
            description: scraper.source_type,
            response_format: 'scraper',
            is_active: scraper.is_active,
            total_articles_fetched: scraper.total_items_scraped,
          })),
        );
      } catch (error) {
        console.error(error);
      }
    };

    load();
  }, []);

  useEffect(() => {
    const checkSaved = async () => {
      const user = userStorage.getUser();
      if (!user || allResults.length === 0) return;
      try {
        const response = await libraryApi.check(user.id, allResults.map((article) => article.external_id));
        if (response.success) setSavedIds(new Set(response.saved_ids));
      } catch (error) {
        console.error(error);
      }
    };
    checkSaved();
  }, [allResults]);

  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) => (prev.includes(category) ? prev.filter((item) => item !== category) : [...prev, category]));
  };

  const toggleSource = (source: string) => {
    setSelectedSources((prev) => (prev.includes(source) ? prev.filter((item) => item !== source) : [...prev, source]));
  };

  const saveToHistory = (query: string) => {
    if (!query.trim()) return;
    const recent: string[] = JSON.parse(localStorage.getItem('recent_searches') || '[]');
    localStorage.setItem('recent_searches', JSON.stringify([query.trim(), ...recent.filter((item) => item !== query.trim())].slice(0, 10)));
  };

  const applyClientFilters = (results: Article[], page: number) => {
    let filtered = results;

    if (selectedCategories.length > 0) {
      filtered = filtered.filter((article) =>
        article.categories?.some((category) =>
          selectedCategories.some((selected) => category.toLowerCase().includes(selected.toLowerCase())),
        ),
      );
    }

    if (selectedSources.length > 0) {
      filtered = filtered.filter((article) => selectedSources.includes(article.api_source?.name || ''));
    }

    if (dateRange) {
      const cutoff = new Date();
      if (dateRange === 'last_30_days') cutoff.setDate(cutoff.getDate() - 30);
      else if (dateRange === 'last_3_months') cutoff.setMonth(cutoff.getMonth() - 3);
      else if (dateRange === 'last_year') cutoff.setFullYear(cutoff.getFullYear() - 1);

      filtered = filtered.filter((article) => {
        if (!article.published_date) return true;
        const date = new Date(article.published_date);
        return Number.isNaN(date.getTime()) || date >= cutoff;
      });
    }

    filtered = interleaveBySource(filtered);

    const start = (page - 1) * PAGE_SIZE;
    setArticles(filtered.slice(start, start + PAGE_SIZE));
    setTotalCount(filtered.length);
  };

  const fetchArticles = async (forceNewSearch = false, page = currentPage) => {
    setLoading(true);
    setIsPartial(false);
    setTimedOutSources([]);

    try {
      if (searchQuery.trim()) {
        let cached = allResults;

        if (forceNewSearch || cached.length === 0) {
          const selectedApiSources = apiSources.filter((source) => selectedSources.includes(source.name));
          const sourceIds = selectedApiSources.map((source) => source.id);
          const selectedScrapers = scraperSources.filter((source) => selectedSources.includes(source.name));
          const scraperIds = selectedScrapers.map((source) => source.id - 1000);

          const user = userStorage.getUser();
          const response = await articlesApi.searchLive(searchQuery, 60, sourceIds, scraperIds, user?.id);
          if (!response.success) {
            setLoading(false);
            return;
          }

          setIsPartial(response.partial_results || false);
          setTimedOutSources(response.timed_out_sources || []);
          cached = response.articles.map((article, index) => ({
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
          cached = interleaveBySource(cached);
          setAllResults(cached);
        }

        applyClientFilters(cached, page);
      } else {
        const response = await articlesApi.search({
          search: searchQuery,
          categories: selectedCategories.join(','),
          source: selectedSources.join(','),
          date_range: dateRange,
          page,
          page_size: PAGE_SIZE,
        });
        const mixed = interleaveBySource(response.results);
        setArticles(mixed);
        setAllResults(mixed);
        setTotalCount(mixed.length);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (event: React.FormEvent) => {
    event.preventDefault();
    if (selectedSources.length === 0) {
      setSearchError('Arama yapmadan önce en az bir kaynak seçin.');
      return;
    }

    setSearchError('');
    setCurrentPage(1);
    setHasSearched(true);
    setAllResults([]);
    saveToHistory(searchQuery);
    await fetchArticles(true, 1);
  };

  useEffect(() => {
    if (hasSearched && allResults.length > 0) {
      applyClientFilters(allResults, currentPage);
    }
  }, [currentPage]);

  useEffect(() => {
    if (!hasSearched) return;
    if (selectedSources.length === 0) {
      setSearchError('Arama yapmadan önce en az bir kaynak seçin.');
      setArticles([]);
      setAllResults([]);
      setTotalCount(0);
      return;
    }
    setSearchError('');
    setCurrentPage(1);
    fetchArticles(true, 1);
  }, [selectedCategories, selectedSources, dateRange]);

  const toggleSave = async (article: Article) => {
    const user = userStorage.getUser();
    if (!user) return;

    const externalId = article.external_id;
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
          external_id: article.external_id,
          title: article.title,
          abstract: article.abstract,
          authors: article.authors,
          published_date: article.published_date || '',
          journal: article.journal,
          url: article.url,
          pdf_url: article.pdf_url,
          doi: article.doi || '',
          source: article.api_source?.name || 'Bilinmeyen kaynak',
          categories: article.categories,
          citation_count: article.citation_count,
        });
        setSavedIds((prev) => new Set(prev).add(externalId));
      }
    } catch (error) {
      console.error(error);
    }
  };

  const toggleLike = async (article: Article) => {
    const user = userStorage.getUser();
    if (!user) return;
    const externalId = article.external_id;
    const isLiked = likedIds.has(externalId);
    try {
      await activityApi.record(user.id, {
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

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  return (
    <div className="space-y-8">
      <section className="shell page-hero px-6 py-8 md:px-10 md:py-12">
        <div className="relative z-10 max-w-4xl space-y-5 text-white">
          <p className="eyebrow text-white/65">Akademik arama</p>
          <h1 className="font-heading text-5xl leading-tight md:text-6xl">Daha güçlü filtreler, daha net kaynak mantığı ve daha okunabilir akademik sonuçlar.</h1>
          <p className="max-w-3xl text-base leading-8 text-white/70 md:text-lg">
            Akademik veri tabanı mantığını daha modern bir editoryal ürün deneyimiyle birleştir; sonra sonuçları kaynak, kategori ve tarih aralığıyla rafine et.
          </p>

          <form onSubmit={handleSearch} className="section-card-dark p-3">
            <div className="grid gap-3 md:grid-cols-[1fr_auto]">
              <input
                type="text"
                placeholder="Makale, dergi, konferans konusu veya fon çağrısı ara..."
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                className="rounded-[22px] bg-white/5 px-4 py-4 text-sm text-white placeholder:text-white/45 focus:outline-none"
              />
              <button type="submit" className="btn-primary justify-center">
                Ara
              </button>
            </div>
            {searchError && <p className="mt-3 text-sm text-red-300">{searchError}</p>}
          </form>

          <div className="flex flex-wrap gap-2">
            {categories.slice(0, 5).map((tag) => (
              <button key={tag} onClick={() => setSearchQuery(tag)} className="chip border-white/12 bg-white/5 text-white/82">
                {tag}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="shell grid gap-6 xl:grid-cols-[320px_1fr]">
        <aside className="section-card h-fit p-6">
          <p className="eyebrow mb-2">Filtreler</p>
          <h2 className="font-heading text-3xl text-[var(--text-strong)]">Keşfi daralt</h2>

          <div className="mt-6 space-y-6">
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">Tarih aralığı</label>
              <select value={dateRange} onChange={(event) => setDateRange(event.target.value)} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]">
                <option value="">Tüm zamanlar</option>
                <option value="last_30_days">Son 30 gün</option>
                <option value="last_3_months">Son 3 ay</option>
                <option value="last_year">Son 1 yıl</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">Kategoriler</label>
              <div className="flex flex-wrap gap-2">
                {categories.map((category) => (
                  <button key={category} onClick={() => toggleCategory(category)} className={`chip ${selectedCategories.includes(category) ? 'chip-active' : ''}`}>
                    {category}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">API kaynakları</label>
              <div className="flex flex-wrap gap-2">
                {apiSources.map((source) => (
                  <button key={source.id} onClick={() => toggleSource(source.name)} className={`chip ${selectedSources.includes(source.name) ? 'chip-active' : ''}`}>
                    {source.name}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">Tarayıcı kaynaklar</label>
              <div className="flex flex-wrap gap-2">
                {scraperSources.map((source) => (
                  <button key={source.id} onClick={() => toggleSource(source.name)} className={`chip ${selectedSources.includes(source.name) ? 'chip-active' : ''}`}>
                    {source.name}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>

        <div className="space-y-5">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="eyebrow mb-2">Sonuçlar</p>
              <h2 className="font-heading text-4xl text-[var(--text-strong)]">Meta verisi güçlü akademik sonuçlar</h2>
            </div>
            <span className="rounded-full bg-[var(--brand-soft)] px-4 py-2 text-xs font-semibold text-[var(--brand)]">{totalCount} sonuç</span>
          </div>

          {isPartial && (
            <div className="rounded-[24px] border border-[rgba(185,109,23,0.22)] bg-[rgba(185,109,23,0.08)] px-5 py-4 text-sm text-[var(--warning)]">
              Bazı kaynaklar henüz yanıt vermedi: {timedOutSources.length > 0 ? timedOutSources.join(', ') : 'arka planda tarayıcılar çalışıyor.'}
            </div>
          )}

          {!hasSearched ? (
            <div className="section-card px-8 py-16 text-center">
              <p className="font-heading text-3xl text-[var(--text-strong)]">Yüksek niyetli bir araştırma sorgusuyla başla.</p>
              <p className="mt-2 text-sm text-[var(--text-muted)]">Kaynak seçip aramayı çalıştırdığında sonuçlar burada görünecek.</p>
            </div>
          ) : loading ? (
            <div className="section-card px-8 py-16 text-center">
              <p className="font-heading text-3xl text-[var(--text-strong)]">Akademik kaynaklar taranıyor...</p>
            </div>
          ) : articles.length > 0 ? (
            <>
              <div className="space-y-4">
                {articles.map((article) => (
                  <ContentCard
                    key={article.external_id}
                    content={{
                      id: article.external_id,
                      type: inferContentType(article),
                      title: article.title,
                      description: article.abstract || 'Özet bilgisi bulunmuyor.',
                      source: article.api_source?.name || 'Akademik kaynak',
                      authors: article.authors.map((author) => author.name).join(', '),
                      date: article.published_date || article.fetched_at,
                      journal: article.journal,
                      citations: article.citation_count,
                      tags: article.categories.slice(0, 3),
                      keywords: article.keywords.slice(0, 2),
                      url: article.url,
                      pdfUrl: article.pdf_url,
                      imageUrl: article.image_url,
                    }}
                    isSaved={savedIds.has(article.external_id)}
                    onToggleSave={() => toggleSave(article)}
                    isLiked={likedIds.has(article.external_id)}
                    onToggleLike={() => toggleLike(article)}
                  />
                ))}
              </div>

              {totalPages > 1 && (
                <div className="flex justify-center gap-3 pt-4">
                  <button onClick={() => setCurrentPage((page) => Math.max(1, page - 1))} disabled={currentPage === 1} className="btn-secondary disabled:cursor-not-allowed disabled:opacity-40">
                    Önceki
                  </button>
                  <div className="chip">{currentPage} / {totalPages}</div>
                  <button onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))} disabled={currentPage >= totalPages} className="btn-secondary disabled:cursor-not-allowed disabled:opacity-40">
                    Sonraki
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="section-card px-8 py-16 text-center">
              <p className="font-heading text-3xl text-[var(--text-strong)]">Bu kombinasyonda sonuç bulunamadı.</p>
              <p className="mt-2 text-sm text-[var(--text-muted)]">Kategori, tarih aralığı veya sorguyu genişletmeyi dene.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default SearchDashboard;
