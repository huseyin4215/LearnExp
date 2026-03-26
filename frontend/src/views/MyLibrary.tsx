import React, { useState, useEffect, useCallback } from 'react';
import ContentCard from '../components/ContentCard';
import { libraryApi, userStorage } from '../services/api';
import type { LibraryItem } from '../services/api';

const PAGE_SIZE = 10;

const MyLibrary: React.FC = () => {
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [toast, setToast] = useState<string | null>(null);

  const userId = userStorage.getUser()?.id;

  const fetchLibrary = useCallback(async (page: number = 1, search: string = '') => {
    if (!userId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const response = await libraryApi.list(userId, page, PAGE_SIZE, search);
      if (response.success) {
        setItems(response.items);
        setTotalPages(response.total_pages);
        setTotalItems(response.total);
        setCurrentPage(page);
      }
    } catch (error) {
      console.error('Failed to fetch library:', error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchLibrary();
  }, [fetchLibrary]);

  const handleRemove = async (externalId: string) => {
    if (!userId) return;
    try {
      await libraryApi.remove(userId, externalId);
      setToast('Makale kütüphaneden kaldırıldı');
      // Re-fetch current page
      fetchLibrary(currentPage, searchQuery);
      setTimeout(() => setToast(null), 3000);
    } catch (error) {
      console.error('Failed to remove:', error);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchLibrary(1, searchQuery);
  };

  const goToPage = (page: number) => {
    if (page < 1 || page > totalPages) return;
    fetchLibrary(page, searchQuery);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const getPageNumbers = (): (number | '...')[] => {
    const pages: (number | '...')[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (currentPage > 3) pages.push('...');
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);
      for (let i = start; i <= end; i++) pages.push(i);
      if (currentPage < totalPages - 2) pages.push('...');
      pages.push(totalPages);
    }
    return pages;
  };

  return (
    <div id="myLibraryView">
      <section className="gradient-bg text-white py-16 rounded-2xl mb-8">
        <div className="max-w-4xl mx-auto text-center px-6">
          <div className="w-16 h-16 bg-white bg-opacity-20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
            </svg>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Kütüphanem
          </h2>
          <p className="text-lg md:text-xl mb-6 text-indigo-100">Kaydettiğiniz makaleler ve araştırmalar</p>

          <div className="max-w-2xl mx-auto">
            <form onSubmit={handleSearch} className="relative">
              <input
                type="text"
                placeholder="Kütüphanede ara..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-6 py-3 text-gray-800 bg-white rounded-full shadow-lg focus:outline-none pr-14 border border-gray-100"
              />
              <button type="submit" className="absolute right-2 top-2 bg-indigo-600 hover:bg-indigo-700 text-white p-1.5 rounded-full transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
              </button>
            </form>
          </div>
        </div>
      </section>

      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8 border-b border-gray-200 pb-4">
          <h3 className="text-xl font-bold text-gray-800">Kaydedilen Makaleler</h3>
          <span className="text-xs bg-indigo-50 text-indigo-600 px-3 py-1 rounded-full font-bold">{totalItems} Makale</span>
        </div>

        {!userId ? (
          <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
            <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
            </svg>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">Giriş yapmanız gerekiyor</h3>
            <p className="text-gray-500">Kütüphane özelliğini kullanmak için lütfen giriş yapın</p>
          </div>
        ) : loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            <p className="mt-4 text-gray-600">Kütüphane yükleniyor...</p>
          </div>
        ) : items.length > 0 ? (
          <div className="flex flex-col space-y-8">
            {items.map(item => (
              <ContentCard
                key={`lib-${item.external_id}`}
                content={{
                  id: item.external_id,
                  type: 'article',
                  title: item.title,
                  description: item.abstract,
                  source: item.source || 'Unknown',
                  authors: item.authors
                    ?.map((a: { name: string }) => a.name)
                    .filter((name: string) => name && name.trim() !== '')
                    .join(', ') || '',
                  date: (() => {
                    const d = item.published_date;
                    if (!d || d === 'None' || d === '') return 'Tarih bilgisi yok';
                    const parsed = new Date(d);
                    return isNaN(parsed.getTime())
                      ? 'Tarih bilgisi yok'
                      : parsed.toLocaleDateString('tr-TR', { year: 'numeric', month: 'short', day: 'numeric' });
                  })(),
                  journal: item.journal || '',
                  citations: item.citation_count || 0,
                  tags: item.categories?.slice(0, 3) || [],
                  url: item.url,
                  pdfUrl: item.pdf_url,
                }}
                isSaved={true}
                onToggleSave={() => handleRemove(item.external_id)}
              />
            ))}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center space-x-2 py-6">
                <button
                  onClick={() => goToPage(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  ← Önceki
                </button>
                {getPageNumbers().map((page, idx) => (
                  page === '...' ? (
                    <span key={`dots-${idx}`} className="px-2 py-2 text-gray-400">...</span>
                  ) : (
                    <button
                      key={page}
                      onClick={() => goToPage(page)}
                      className={`w-10 h-10 rounded-lg text-sm font-medium transition-colors ${currentPage === page
                          ? 'bg-indigo-600 text-white shadow-md'
                          : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
                        }`}
                    >
                      {page}
                    </button>
                  )
                ))}
                <button
                  onClick={() => goToPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Sonraki →
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
            <svg className="w-20 h-20 mx-auto text-gray-300 mb-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
            </svg>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">Kütüphaneniz boş</h3>
            <p className="text-gray-500 mb-6">Makaleleri kaydetmek için arama yapın ve bookmark ikonuna tıklayın</p>
            <a href="/" className="inline-flex items-center px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-full transition-colors">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
              Makale Ara
            </a>
          </div>
        )}

        {/* Toast */}
        {toast && (
          <div className="fixed bottom-6 right-6 z-50 px-6 py-3 rounded-lg shadow-lg text-white font-medium bg-emerald-500 animate-bounce">
            ✓ {toast}
          </div>
        )}
      </div>
    </div>
  );
};

export default MyLibrary;