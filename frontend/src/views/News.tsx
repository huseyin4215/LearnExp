import React, { useState, useEffect } from 'react';
import { scrapedContentApi, scrapersApi } from '../services/api';
import type { ScrapedContentItem } from '../services/api';

const NewsPage: React.FC = () => {
  const [items, setItems] = useState<ScrapedContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [scrapers, setScrapers] = useState<{id: number, name: string, is_active: boolean}[]>([]);
  const [selectedScrapers, setSelectedScrapers] = useState<number[]>([]);
  const [isScraping, setIsScraping] = useState(false);
  const itemsPerPage = 12;

  const contentTypes = [
    { value: '', label: 'Tümü' },
    { value: 'article', label: 'Makale' },
    { value: 'conference', label: 'Konferans' },
    { value: 'thesis', label: 'Tez' },
    { value: 'funding', label: 'Fon/Hibe' },
    { value: 'event', label: 'Etkinlik' },
    { value: 'report', label: 'Rapor' },
  ];

  useEffect(() => {
    fetchNews();
    fetchScrapers();
  }, [currentPage, selectedType, searchQuery]);

  const fetchNews = async () => {
    setLoading(true);
    try {
      const response = await scrapedContentApi.fetchLatest(
        currentPage,
        itemsPerPage,
        searchQuery,
        selectedType
      );
      if (response.success) {
        setItems(response.contents);
        setTotalItems(response.total);
      }
    } catch (error) {
      console.error('Failed to fetch news:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchScrapers = async () => {
    try {
      const response = await scrapersApi.list();
      setScrapers(response);
    } catch (error) {
      console.error('Failed to fetch scrapers:', error);
    }
  };

  const handleScrapeNow = async () => {
    if (selectedScrapers.length === 0) {
      alert('Lütfen en az bir kaynak seçin');
      return;
    }
    setIsScraping(true);
    try {
      await Promise.all(
        selectedScrapers.map(id => scrapersApi.run(id, searchQuery || undefined))
      );
      // Refresh after scraping
      setTimeout(() => {
        fetchNews();
        setIsScraping(false);
      }, 2000);
    } catch (error) {
      console.error('Scraping failed:', error);
      setIsScraping(false);
    }
  };

  const toggleScraper = (id: number) => {
    setSelectedScrapers(prev =>
      prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]
    );
  };

  const getContentTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      article: 'Makale',
      thesis: 'Tez',
      conference: 'Konferans',
      book: 'Kitap',
      report: 'Rapor',
      funding: 'Fon/Hibe',
      event: 'Etkinlik',
      other: 'Diğer',
    };
    return labels[type] || type;
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '';
    try {
      return new Date(dateStr).toLocaleDateString('tr-TR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const totalPages = Math.ceil(totalItems / itemsPerPage);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Haberler & Duyurular</h1>
        <p className="text-gray-600">
          Üniversitelerden ve akademik kaynaklardan toplanan güncel haberler, etkinlikler ve duyurular
        </p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ara</label>
            <input
              type="text"
              placeholder="Haberlerde ara..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Content Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">İçerik Türü</label>
            <select
              value={selectedType}
              onChange={(e) => {
                setSelectedType(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              {contentTypes.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>

          {/* Scraper Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Kaynaklar (Gerçek Zamanlı Scrape)
            </label>
            <div className="flex flex-wrap gap-2">
              {scrapers.map(scraper => (
                <button
                  key={scraper.id}
                  onClick={() => toggleScraper(scraper.id)}
                  disabled={!scraper.is_active}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    selectedScrapers.includes(scraper.id)
                      ? 'bg-teal-600 text-white'
                      : scraper.is_active
                      ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      : 'bg-gray-50 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  {scraper.name}
                  {scraper.is_active && (
                    <span className="ml-1 w-1.5 h-1.5 bg-green-400 rounded-full inline-block"></span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Scrape Button */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            {totalItems} haber bulundu
            {selectedScrapers.length > 0 && ` • ${selectedScrapers.length} kaynak seçili`}
          </p>
          <button
            onClick={handleScrapeNow}
            disabled={isScraping || selectedScrapers.length === 0}
            className="bg-teal-600 hover:bg-teal-700 disabled:bg-gray-300 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center"
          >
            {isScraping ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Scraping...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                Şimdi Scrape Et
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results Grid */}
      {loading ? (
        <div className="text-center py-20">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          <p className="mt-4 text-gray-600">Haberler yükleniyor...</p>
        </div>
      ) : items.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {items.map(item => (
              <article
                key={item.id}
                className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
              >
                {/* Image */}
                {item.image_url ? (
                  <div className="h-48 overflow-hidden">
                    <img
                      src={item.image_url}
                      alt={item.title}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  </div>
                ) : (
                  <div className="h-48 bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
                    <svg className="w-16 h-16 text-indigo-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
                    </svg>
                  </div>
                )}

                {/* Content */}
                <div className="p-6">
                  {/* Type Badge */}
                  <span className="inline-block px-3 py-1 bg-indigo-50 text-indigo-700 text-xs font-medium rounded-full mb-3">
                    {getContentTypeLabel(item.content_type)}
                  </span>

                  {/* Title */}
                  <h3 className="text-lg font-semibold text-gray-800 mb-2 line-clamp-2">
                    {item.title}
                  </h3>

                  {/* Abstract */}
                  <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                    {item.abstract || 'Açıklama mevcut değil'}
                  </p>

                  {/* Meta */}
                  <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                    <span>{formatDate(item.published_date)}</span>
                    {item.scraper_name && <span>Kaynak: {item.scraper_name}</span>}
                  </div>

                  {/* Link */}
                  {item.source_url && item.source_url.startsWith('http') ? (
                    <a
                      href={item.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-indigo-600 hover:text-indigo-700 font-medium text-sm"
                    >
                      Devamını Oku
                      <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                      </svg>
                    </a>
                  ) : (
                    <span className="text-gray-400 text-sm">Bağlantı yok</span>
                  )}
                </div>
              </article>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-8 flex justify-center gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50"
              >
                ← Önceki
              </button>
              <span className="px-4 py-2 text-gray-700">
                Sayfa {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50"
              >
                Sonraki →
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-20 bg-white rounded-xl border border-gray-200">
          <svg className="w-20 h-20 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
          </svg>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">Haber bulunamadı</h3>
          <p className="text-gray-500 mb-4">
            {searchQuery
              ? 'Farklı anahtar kelimeler deneyin veya filtreleri temizleyin'
              : 'Henüz scrape edilmiş haber bulunmuyor. Yukarıdan kaynak seçip scrape edebilirsiniz.'}
          </p>
          {searchQuery && (
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedType('');
                setCurrentPage(1);
              }}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Filtreleri Temizle
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default NewsPage;
