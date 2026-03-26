import React, { useState, useEffect } from 'react';
import ContentCard from '../components/ContentCard';
import { articlesApi, scrapersApi } from '../services/api';
import type { Article, APISource } from '../services/api';

interface FilterSectionProps {
  title: string;
  options: string[];
  selectedOptions: string[];
  onToggle: (option: string) => void;
}

const FilterSection: React.FC<FilterSectionProps> = ({ title, options, selectedOptions, onToggle }) => (
  <div className="mb-6">
    <h4 className="text-[10px] font-bold text-gray-400 mb-2 uppercase tracking-tighter">{title}</h4>
    <div className="space-y-1">
      {options.map(opt => (
        <label key={opt} className="flex items-center cursor-pointer group">
          <input
            type="checkbox"
            checked={selectedOptions.includes(opt)}
            onChange={() => onToggle(opt)}
            className="w-3 h-3 rounded border-gray-300 text-teal-600 focus:ring-teal-500"
          />
          <span className="ml-2 text-[10px] text-gray-500 group-hover:text-gray-800 transition-colors truncate">{opt}</span>
        </label>
      ))}
    </div>
  </div>
);

const PAGE_SIZE = 12;

const SearchDashboard: React.FC = () => {
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [articles, setArticles] = useState<Article[]>([]);
  const [allResults, setAllResults] = useState<Article[]>([]); // cached full result set
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [dateRange, setDateRange] = useState('');
  const [categories, setCategories] = useState<string[]>([]);
  const [apiSources, setApiSources] = useState<APISource[]>([]); // real APISourceConfig entries
  const [scraperSources, setScraperSources] = useState<APISource[]>([]); // scraper entries
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchError, setSearchError] = useState('');



  const toggleSave = (id: string) => {
    setSavedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleCategory = (category: string) => {
    setSelectedCategories(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const toggleSource = (source: string) => {
    setSelectedSources(prev =>
      prev.includes(source)
        ? prev.filter(s => s !== source)
        : [...prev, source]
    );
  };

  const fetchArticles = async (forceNewSearch = false) => {
    setLoading(true);
    try {
      if (searchQuery && searchQuery.trim().length > 0) {
        // Only pass REAL APISourceConfig IDs (not scraper IDs which are client-only)
        const selectedApiSources = apiSources.filter(s => selectedSources.includes(s.name));
        const sourceIds = selectedApiSources.length > 0
          ? selectedApiSources.map(s => s.id)
          : [];

        // Extract real scraper IDs (remove the +1000 offset applied in loadInitialData)
        const selectedScrapers = scraperSources.filter(s => selectedSources.includes(s.name));
        const scraperIds = selectedScrapers.length > 0
          ? selectedScrapers.map(s => s.id - 1000)
          : [];

        // Use cached results for page changes; only re-fetch on new search or filter change
        let cached = allResults;
        if (forceNewSearch || cached.length === 0) {
          const response = await articlesApi.searchLive(searchQuery, 60, sourceIds, scraperIds);
          if (!response.success) {
            setLoading(false);
            return;
          }
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
            fetched_at: new Date().toISOString()
          }));
          setAllResults(cached);
        }

        // Apply client-side filters
        let filtered = cached;
        if (selectedCategories.length > 0) {
          filtered = filtered.filter(article =>
            article.categories.some(cat =>
              selectedCategories.some(sel => cat.toLowerCase().includes(sel.toLowerCase()))
            )
          );
        }
        if (selectedSources.length > 0) {
          filtered = filtered.filter(article =>
            selectedSources.includes(article.api_source?.name || '')
          );
        }
        if (dateRange) {
          const now = new Date();
          const cutoff = new Date();
          if (dateRange === 'last_30_days') cutoff.setDate(now.getDate() - 30);
          else if (dateRange === 'last_3_months') cutoff.setMonth(now.getMonth() - 3);
          else if (dateRange === 'last_year') cutoff.setFullYear(now.getFullYear() - 1);
          filtered = filtered.filter(a => {
            if (!a.published_date) return true;
            return new Date(a.published_date) >= cutoff;
          });
        }

        // Local pagination
        const start = (currentPage - 1) * PAGE_SIZE;
        setArticles(filtered.slice(start, start + PAGE_SIZE));
        setTotalCount(filtered.length);
      } else {
        const response = await articlesApi.search({
          search: searchQuery,
          categories: selectedCategories.join(','),
          source: selectedSources.join(','),
          date_range: dateRange,
          page: currentPage,
          page_size: PAGE_SIZE,
        });
        setArticles(response.results);
        setTotalCount(response.count);
      }
    } catch (error) {
      console.error('Failed to fetch articles:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedSources.length === 0) {
      setSearchError('Lütfen arama yapmak için en az bir kaynak (API veya Scraper) seçin.');
      return;
    }
    setSearchError('');
    setCurrentPage(1);
    setAllResults([]); // clear cache for fresh search
    setHasSearched(true);
    if (searchQuery.trim()) {
      const recent: string[] = JSON.parse(localStorage.getItem('recent_searches') || '[]');
      const updated = [searchQuery.trim(), ...recent.filter(q => q !== searchQuery.trim())].slice(0, 10);
      localStorage.setItem('recent_searches', JSON.stringify(updated));
    }
    fetchArticles(true);
  };

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [categoriesData, sourcesData, scrapersData] = await Promise.all([
          articlesApi.getCategories(),
          articlesApi.getSources(),
          scrapersApi.list()
        ]);
        setCategories(categoriesData.slice(0, 10));
        setApiSources(sourcesData); // real IDs — safe to pass to searchLive()
        setScraperSources(scrapersData.map(s => ({
          id: 1000 + s.id,
          name: s.name,
          description: s.source_type,
          response_format: 'scraper',
          is_active: s.is_active,
          total_articles_fetched: s.total_items_scraped,
        })));
      } catch (error) {
        console.error('Failed to load initial data:', error);
      }
    };
    loadInitialData();
  }, []);

  // Re-run filter/page on page change (uses cache, no API call)
  useEffect(() => {
    if (hasSearched && allResults.length > 0) {
      fetchArticles(false);
    }
  }, [currentPage]);

  // Reset page and re-fetch on filter/date changes
  useEffect(() => {
    if (hasSearched) {
      if (selectedSources.length === 0) {
        setSearchError('Lütfen arama yapmak için en az bir kaynak (API veya Scraper) seçin.');
        setArticles([]);
        setAllResults([]);
        setTotalCount(0);
        return;
      }
      setSearchError('');
      setCurrentPage(1);
      setAllResults([]); // clear cache so filters re-fetch
      fetchArticles(true);
    }
  }, [selectedCategories, selectedSources, dateRange]);


  return (
    <div id="searchView" className="w-full">
      <section className="gradient-bg text-white py-16 rounded-2xl mb-8">
        <div className="max-w-4xl mx-auto text-center px-6">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Discover <span className="text-yellow-300">Academic Content</span>
          </h2>
          <p className="text-lg md:text-xl mb-6 text-indigo-100">
            Search through millions of research papers, conferences, and funding opportunities
          </p>
          <div className="max-w-3xl mx-auto mb-6">
            <form onSubmit={handleSearch} className="relative">
              {searchError && (
                <div className="absolute -top-12 left-0 right-0 bg-red-100/90 text-red-700 px-4 py-2 rounded-lg text-sm font-medium shadow-sm backdrop-blur-sm border border-red-200">
                  {searchError}
                </div>
              )}
              <input
                type="text"
                placeholder="Search for articles, conferences, funding calls..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-6 py-4 text-lg text-gray-800 dark:text-white bg-white dark:bg-gray-700 rounded-full shadow-lg focus:outline-none pr-16 border border-gray-100 dark:border-gray-600 dark:placeholder-gray-400"
              />
              <button
                type="submit"
                className="absolute right-2 top-2 bg-indigo-600 hover:bg-indigo-700 text-white p-2 rounded-full transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
              </button>
            </form>
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            {categories.slice(0, 4).map(tag => (
              <button
                key={tag}
                onClick={() => {
                  setSearchQuery(tag);
                  setCurrentPage(1);
                  fetchArticles();
                }}
                className="bg-white bg-opacity-20 text-white px-4 py-2 rounded-full text-sm hover:bg-opacity-30 cursor-pointer transition-all"
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-gray-200 p-4 sticky top-24 shadow-sm">
            <h3 className="font-bold text-gray-800 mb-4 text-xs uppercase tracking-widest border-b pb-2">Filters</h3>

            {categories.length > 0 && (
              <FilterSection
                title="Categories"
                options={categories}
                selectedOptions={selectedCategories}
                onToggle={toggleCategory}
              />
            )}

            <div className="mb-6">
              <h4 className="text-[10px] font-bold text-gray-400 mb-2 uppercase tracking-tighter">Date Range</h4>
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="w-full border border-gray-200 rounded px-2 py-1 text-[11px] text-gray-600 bg-white focus:ring-1 focus:ring-indigo-500 outline-none shadow-sm"
              >
                <option value="">All time</option>
                <option value="last_30_days">Last 30 days</option>
                <option value="last_3_months">Last 3 months</option>
                <option value="last_year">Last year</option>
              </select>
            </div>

            {/* API Sources */}
            {apiSources.length > 0 && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-1.5">
                  <h4 className="text-[9px] font-bold text-indigo-400 uppercase tracking-tighter">🔗 API Kaynakları</h4>
                  <button
                    onClick={() => {
                      const apiNames = apiSources.map(s => s.name);
                      const allSelected = apiNames.every(n => selectedSources.includes(n));
                      if (allSelected) setSelectedSources(prev => prev.filter(n => !apiNames.includes(n)));
                      else setSelectedSources(prev => [...new Set([...prev, ...apiNames])]);
                    }}
                    className="text-[8px] text-indigo-500 hover:text-indigo-700 font-semibold uppercase"
                  >
                    {apiSources.every(s => selectedSources.includes(s.name)) ? 'Temizle' : 'Seç'}
                  </button>
                </div>
                <div className="space-y-1">
                  {apiSources.map(s => (
                    <label key={s.id} className="flex items-center cursor-pointer group">
                      <input type="checkbox" checked={selectedSources.includes(s.name)}
                        onChange={() => toggleSource(s.name)}
                        className="w-3 h-3 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
                      <span className="ml-2 text-[10px] text-gray-500 group-hover:text-gray-800 transition-colors truncate">{s.name}</span>
                      <span className="ml-auto w-1.5 h-1.5 bg-indigo-400 rounded-full flex-shrink-0"></span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Scraper Sources */}
            {scraperSources.length > 0 && (
              <div className="mb-2">
                <div className="flex items-center justify-between mb-1.5">
                  <h4 className="text-[9px] font-bold text-teal-400 uppercase tracking-tighter">🕷 Scraper Kaynakları</h4>
                  <button
                    onClick={() => {
                      const scrNames = scraperSources.map(s => s.name);
                      const allSelected = scrNames.every(n => selectedSources.includes(n));
                      if (allSelected) setSelectedSources(prev => prev.filter(n => !scrNames.includes(n)));
                      else setSelectedSources(prev => [...new Set([...prev, ...scrNames])]);
                    }}
                    className="text-[8px] text-teal-500 hover:text-teal-700 font-semibold uppercase"
                  >
                    {scraperSources.every(s => selectedSources.includes(s.name)) ? 'Temizle' : 'Seç'}
                  </button>
                </div>
                <div className="space-y-1">
                  {scraperSources.map(s => (
                    <label key={s.id} className="flex items-center cursor-pointer group">
                      <input type="checkbox" checked={selectedSources.includes(s.name)}
                        onChange={() => toggleSource(s.name)}
                        className="w-3 h-3 rounded border-gray-300 text-teal-600 focus:ring-teal-500" />
                      <span className="ml-2 text-[10px] text-gray-500 group-hover:text-gray-800 transition-colors truncate">{s.name}</span>
                      {s.is_active && <span className="ml-auto w-1.5 h-1.5 bg-green-400 rounded-full flex-shrink-0" title="Aktif"></span>}
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-10">
          <div className="mb-6 flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-800">
              Arama Sonuçları
              {totalCount > 0 && <span className="text-gray-500 font-normal ml-2">({totalCount} makale)</span>}
            </h3>
            {!loading && articles.length > 0 && (
              <span className="text-[10px] bg-green-100 text-green-700 px-2 py-1 rounded font-bold uppercase">Live Data</span>
            )}
          </div>

          {!hasSearched ? (
            <div className="text-center py-20 bg-white rounded-xl border border-gray-200">
              <svg className="w-20 h-20 mx-auto text-indigo-200 mb-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
              <h3 className="text-2xl font-semibold text-gray-700 mb-2">Aramaya başlayın</h3>
              <p className="text-gray-500">Yukarıdaki arama çubuğunu kullanarak makale, konferans veya araştırma arayın</p>
            </div>
          ) : loading ? (
            <div className="text-center py-20">
              <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600"></div>
              <p className="mt-4 text-gray-600">Makaleler aranıyor...</p>
            </div>
          ) : articles.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {articles.map(article => (
                  <ContentCard
                    key={article.id}
                    content={{
                      id: article.id.toString(),
                      type: 'article',
                      title: article.title,
                      description: article.abstract,
                      source: article.api_source?.name || 'Unknown',
                      authors: article.authors.map(a => a.name).join(', '),
                      date: article.published_date || article.fetched_at,
                      journal: article.journal,
                      citations: article.citation_count,
                      tags: article.categories.slice(0, 3),
                      url: article.url,
                      pdfUrl: article.pdf_url,
                      imageUrl: article.image_url,
                    }}
                    isSaved={savedIds.has(article.id.toString())}
                    onToggleSave={() => toggleSave(article.id.toString())}
                  />
                ))}
              </div>

              {/* Pagination */}
              {totalCount > 12 && (
                <div className="mt-8 flex justify-center gap-2">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    ← Önceki
                  </button>
                  <span className="px-4 py-2 text-gray-700">
                    Sayfa {currentPage} / {Math.ceil(totalCount / 12)}
                  </span>
                  <button
                    onClick={() => setCurrentPage(p => p + 1)}
                    disabled={currentPage >= Math.ceil(totalCount / 12)}
                    className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Sonraki →
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-20 bg-white rounded-xl border border-gray-200">
              <svg className="w-20 h-20 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              <h3 className="text-2xl font-semibold text-gray-800 mb-2">Sonuç bulunamadı</h3>
              <p className="text-gray-600 mb-4">Farklı anahtar kelimeler veya filtreler deneyin</p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedCategories([]);
                  setSelectedSources([]);
                  setDateRange('');
                  setCurrentPage(1);
                  setHasSearched(false);
                }}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Filtreleri Temizle
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchDashboard;