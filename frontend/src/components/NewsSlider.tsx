
import React, { useState, useEffect } from 'react';
import { scrapedContentApi } from '../services/api';
import type { ScrapedContentItem } from '../services/api';

const NewsSlider: React.FC = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [items, setItems] = useState<ScrapedContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const itemsPerView = 3;

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await scrapedContentApi.fetchLatest(1, 10);
        if (response.success && response.contents.length > 0) {
          setItems(response.contents);
        }
      } catch (error) {
        console.error('Failed to fetch news:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchNews();
  }, []);

  const slide = (dir: 'next' | 'prev') => {
    if (dir === 'next') {
      setCurrentIndex(prev => Math.min(prev + 1, Math.max(0, items.length - itemsPerView)));
    } else {
      setCurrentIndex(prev => Math.max(prev - 1, 0));
    }
  };

  const getGradient = (index: number) => {
    const gradients = [
      'from-blue-100 to-indigo-200',
      'from-green-100 to-emerald-200',
      'from-purple-100 to-violet-200',
      'from-orange-100 to-amber-200',
      'from-rose-100 to-pink-200',
      'from-cyan-100 to-teal-200',
    ];
    return gradients[index % gradients.length];
  };

  const getIconColor = (index: number) => {
    const colors = ['text-indigo-600', 'text-emerald-600', 'text-violet-600', 'text-orange-600', 'text-pink-600', 'text-teal-600'];
    return colors[index % colors.length];
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
      return new Date(dateStr).toLocaleDateString('tr-TR', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="flex gap-6">
        {[0, 1, 2].map(i => (
          <div key={i} className="flex-1 bg-white rounded-lg border border-gray-200 h-64 animate-pulse">
            <div className="flex h-full">
              <div className="w-32 bg-gray-200 flex-shrink-0 rounded-l-lg"></div>
              <div className="flex-1 p-4 space-y-3">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-full"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // No content
  if (items.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
        <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
        </svg>
        <p className="text-gray-500 text-sm">Henüz scrape edilmiş içerik bulunmuyor</p>
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="overflow-hidden">
        <div
          className="flex transition-transform duration-300 ease-in-out"
          style={{ transform: `translateX(-${currentIndex * (100 / itemsPerView)}%)` }}
        >
          {items.map((item, index) => (
            <div key={item.id} className="flex-none w-full md:w-1/2 lg:w-1/3 px-3">
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden h-64 hover:-translate-y-1 transition-transform shadow-sm">
                <div className="flex h-full">
                  {item.image_url ? (
                    <div className="w-32 h-full flex-shrink-0 overflow-hidden">
                      <img
                        src={item.image_url}
                        alt={item.title}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).parentElement!.style.display = 'none';
                        }}
                      />
                    </div>
                  ) : (
                    <div className={`w-32 h-full flex-shrink-0 bg-gradient-to-br ${getGradient(index)} flex items-center justify-center`}>
                      <svg className={`w-12 h-12 ${getIconColor(index)}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                      </svg>
                    </div>
                  )}
                  <div className="flex-1 p-4 flex flex-col justify-between min-w-0">
                    <div>
                      <h3 className="serif-font text-base font-semibold text-gray-800 mb-2 leading-tight line-clamp-2">{item.title}</h3>
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{item.abstract || 'Açıklama mevcut değil'}</p>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-2 truncate">
                        {item.published_date && <span>Tarih: {formatDate(item.published_date)}</span>}
                        {item.published_date && item.content_type && ' • '}
                        {item.content_type && <span>Tür: {getContentTypeLabel(item.content_type)}</span>}
                      </div>
                      {item.source_url && item.source_url.startsWith('http') ? (
                        <a
                          href={item.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
                        >
                          Detaylar →
                        </a>
                      ) : (
                        <span className="text-gray-400 text-sm">Bağlantı yok</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      {items.length > itemsPerView && (
        <>
          <button
            onClick={() => slide('prev')}
            className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 bg-white rounded-full p-2 shadow-lg border border-gray-200 disabled:opacity-50"
            disabled={currentIndex === 0}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M15 19l-7-7 7-7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </button>
          <button
            onClick={() => slide('next')}
            className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 bg-white rounded-full p-2 shadow-lg border border-gray-200 disabled:opacity-50"
            disabled={currentIndex >= items.length - itemsPerView}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </button>
        </>
      )}
    </div>
  );
};

export default NewsSlider;
