import React, { useState, useEffect, useCallback } from 'react';
import ContentCard from '../components/ContentCard';
import NewsSlider from '../components/NewsSlider';
import { articlesApi, libraryApi, userStorage } from '../services/api';
import type { Article } from '../services/api';

const StatCard: React.FC<{ icon: string, label: string, value: string, color: string, iconBg: string }> = ({ icon, label, value, color, iconBg }) => (
    <div className={`bg-gradient-to-br ${color} p-6 rounded-xl shadow-sm transition-transform hover:-translate-y-1`}>
        <div className="flex items-center">
            <div className={`w-12 h-12 ${iconBg} rounded-lg flex items-center justify-center text-white`}>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d={icon} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </div>
            <div className="ml-4">
                <p className="text-2xl font-semibold text-gray-800">{value}</p>
                <p className="text-sm text-gray-600">{label}</p>
            </div>
        </div>
    </div>
);

// Toast notification component
const Toast: React.FC<{ message: string; type: 'success' | 'error'; onClose: () => void }> = ({ message, type, onClose }) => {
    useEffect(() => {
        const timer = setTimeout(onClose, 3000);
        return () => clearTimeout(timer);
    }, [onClose]);

    return (
        <div className={`fixed bottom-6 right-6 z-50 px-6 py-3 rounded-lg shadow-lg text-white font-medium transition-all animate-bounce-in ${type === 'success' ? 'bg-emerald-500' : 'bg-red-500'
            }`}>
            {type === 'success' ? '✓' : '✗'} {message}
        </div>
    );
};

const PAGE_SIZE = 10;

const Dashboard: React.FC = () => {
    // Restore state from sessionStorage on mount
    const cached = sessionStorage.getItem('dashboard_state');
    const initial = cached ? JSON.parse(cached) : null;

    const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
    const [articles, setArticles] = useState<Article[]>(initial?.articles || []);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState(initial?.searchQuery || '');
    const [totalArticles, setTotalArticles] = useState(initial?.totalArticles || 0);
    const [currentPage, setCurrentPage] = useState(initial?.currentPage || 1);
    const [totalPages, setTotalPages] = useState(initial?.totalPages || 1);
    const [isLiveSearch, setIsLiveSearch] = useState(initial?.isLiveSearch || false);
    const [allLiveResults, setAllLiveResults] = useState<Article[]>(initial?.allLiveResults || []);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
    const [hasSearched, setHasSearched] = useState(initial?.hasSearched || false);

    // Save state to sessionStorage whenever it changes
    useEffect(() => {
        if (hasSearched) {
            sessionStorage.setItem('dashboard_state', JSON.stringify({
                articles, searchQuery, totalArticles, currentPage, totalPages,
                isLiveSearch, allLiveResults, hasSearched
            }));
        }
    }, [articles, searchQuery, totalArticles, currentPage, totalPages, isLiveSearch, allLiveResults, hasSearched]);

    const userId = userStorage.getUser()?.id;

    // Check which articles are saved (for bookmark state)
    const checkSavedStatus = useCallback(async (articleList: Article[]) => {
        if (!userId || articleList.length === 0) return;
        try {
            const externalIds = articleList.map(a => a.external_id).filter(Boolean);
            if (externalIds.length === 0) return;
            const result = await libraryApi.check(userId, externalIds);
            if (result.success) {
                setSavedIds(new Set(result.saved_ids));
            }
        } catch (e) {
            console.error('Failed to check saved status:', e);
        }
    }, [userId]);

    // On mount: re-trigger interrupted search or check saved status for cached results
    useEffect(() => {
        if (initial?.searchQuery && initial?.articles?.length === 0 && initial?.hasSearched) {
            // Search was interrupted — re-trigger
            fetchLive(initial.searchQuery);
        } else if (initial?.articles?.length > 0) {
            // Cached results exist — check bookmark status
            checkSavedStatus(initial.articles);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Toggle save/unsave
    const toggleSave = async (article: Article) => {
        if (!userId) {
            setToast({ message: 'Kaydetmek için giriş yapın', type: 'error' });
            return;
        }

        const externalId = article.external_id;
        const isSaved = savedIds.has(externalId);

        try {
            if (isSaved) {
                await libraryApi.remove(userId, externalId);
                setSavedIds(prev => {
                    const next = new Set(prev);
                    next.delete(externalId);
                    return next;
                });
                setToast({ message: 'Kütüphaneden kaldırıldı', type: 'success' });
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
                setSavedIds(prev => new Set(prev).add(externalId));
                setToast({ message: 'Kütüphaneye kaydedildi!', type: 'success' });
            }
        } catch (error) {
            console.error('Save/unsave failed:', error);
            setToast({ message: 'İşlem başarısız oldu', type: 'error' });
        }
    };

    // Fetch articles from database (paginated)
    const fetchFromDB = async (search: string, page: number) => {
        setLoading(true);
        try {
            const response = await articlesApi.search({
                search,
                page_size: PAGE_SIZE,
                page,
            });
            setArticles(response.results);
            setTotalArticles(response.count);
            setCurrentPage(page);
            setTotalPages(Math.ceil(response.count / PAGE_SIZE));
            setIsLiveSearch(false);
            checkSavedStatus(response.results);
        } catch (error) {
            console.error('Failed to fetch articles:', error);
        } finally {
            setLoading(false);
        }
    };

    // Live search from APIs
    const fetchLive = async (search: string) => {
        setLoading(true);
        try {
            const response = await articlesApi.searchLive(search, 50); // Get up to 50 results

            if (response.success) {
                const convertedArticles: Article[] = response.articles.map((article, index) => ({
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

                setAllLiveResults(convertedArticles);
                setTotalArticles(response.total_found);
                setIsLiveSearch(true);
                setCurrentPage(1);
                setTotalPages(Math.ceil(convertedArticles.length / PAGE_SIZE));

                // Show first page
                setArticles(convertedArticles.slice(0, PAGE_SIZE));
                checkSavedStatus(convertedArticles);
            }
        } catch (error) {
            console.error('Failed to live search:', error);
        } finally {
            setLoading(false);
        }
    };

    // Handle page change
    const goToPage = (page: number) => {
        if (page < 1 || page > totalPages) return;

        if (isLiveSearch) {
            // Client-side pagination for live results
            const start = (page - 1) * PAGE_SIZE;
            const end = start + PAGE_SIZE;
            setArticles(allLiveResults.slice(start, end));
            setCurrentPage(page);
            window.scrollTo({ top: 400, behavior: 'smooth' });
        } else {
            // Server-side pagination for DB results
            fetchFromDB(searchQuery, page);
            window.scrollTo({ top: 400, behavior: 'smooth' });
        }
    };

    // Handle search
    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();

        // Check auth before searching
        if (!userStorage.isLoggedIn()) {
            setToast({ message: 'Arama yapmak için lütfen giriş yapın', type: 'error' });
            setTimeout(() => {
                window.location.href = '/login';
            }, 1000);
            return;
        }

        setHasSearched(true);
        setCurrentPage(1);
        if (searchQuery.trim()) {
            // Save search to recent_searches in localStorage
            const recent: string[] = JSON.parse(localStorage.getItem('recent_searches') || '[]');
            const updated = [searchQuery.trim(), ...recent.filter(q => q !== searchQuery.trim())].slice(0, 10);
            localStorage.setItem('recent_searches', JSON.stringify(updated));

            fetchLive(searchQuery.trim());
        } else {
            fetchFromDB('', 1);
        }
    };

    // Generate page numbers for pagination
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
        <div id="dashboardView">
            <section className="gradient-bg text-white py-16 rounded-2xl mb-8">
                <div className="max-w-4xl mx-auto text-center px-6">
                    <h2 className="text-3xl md:text-4xl font-bold mb-4">
                        Hoş geldiniz, <span className="text-yellow-300">{userStorage.getUser()?.fullName?.split(' ')[0] || 'Kullanıcı'}</span>
                    </h2>
                    <p className="text-lg md:text-xl mb-6 text-indigo-100">
                        Akademik içerik arama motorunuz hazır
                    </p>
                    <div className="max-w-2xl mx-auto mb-6">
                        <form onSubmit={handleSearch} className="relative">
                            <input
                                type="text"
                                placeholder="Makale, konferans veya araştırma arayın..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full px-6 py-3 text-gray-800 dark:text-white bg-white dark:bg-gray-700 rounded-full shadow-lg focus:outline-none pr-14 border border-gray-100 dark:border-gray-600 dark:placeholder-gray-400"
                            />
                            <button
                                type="submit"
                                className="absolute right-2 top-2 bg-indigo-600 hover:bg-indigo-700 text-white p-1.5 rounded-full transition-colors"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                                </svg>
                            </button>
                        </form>
                    </div>
                </div>
            </section>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <StatCard icon="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" label="Bulunan Sonuç" value={hasSearched ? totalArticles.toString() : '—'} color="from-blue-50 to-indigo-100" iconBg="bg-indigo-600" />
                <StatCard icon="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" label="Kaydedilen" value={savedIds.size.toString()} color="from-green-50 to-emerald-100" iconBg="bg-emerald-600" />
                <StatCard icon="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" label="Kaynak Sayısı" value={isLiveSearch ? 'Canlı API' : 'Veritabanı'} color="from-purple-50 to-violet-100" iconBg="bg-violet-600" />
            </div>

            <div className="mb-8">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-800">Haberler</h2>
                    <a 
                        href="/news"
                        className="text-indigo-600 hover:text-indigo-700 font-medium text-sm transition-colors"
                    >
                        Tümünü Görüntüleyin →
                    </a>
                </div>
                <NewsSlider />
            </div>

            <div className="space-y-6">
                {!hasSearched ? (
                    <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
                        <svg className="w-20 h-20 mx-auto text-indigo-200 mb-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                        <h3 className="text-xl font-semibold text-gray-700 mb-2">Aramaya başlayın</h3>
                        <p className="text-gray-500">Yukarıdaki arama çubuğunu kullanarak makale, konferans veya araştırma arayın</p>
                    </div>
                ) : loading ? (
                    <div className="text-center py-12">
                        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                        <p className="mt-4 text-gray-600">Makaleler yükleniyor...</p>
                    </div>
                ) : articles.length > 0 ? (
                    <>
                        {/* Results info */}
                        <div className="flex items-center justify-between">
                            <p className="text-sm text-gray-500">
                                Toplam {totalArticles} sonuç • Sayfa {currentPage} / {totalPages}
                            </p>
                            {isLiveSearch && (
                                <span className="text-xs bg-green-50 text-green-700 px-3 py-1 rounded-full font-medium">
                                    🔴 Canlı API Sonuçları
                                </span>
                            )}
                        </div>

                        {articles.map(article => (
                            <ContentCard
                                key={article.external_id || article.id}
                                content={{
                                    id: article.external_id || article.id.toString(),
                                    type: 'article',
                                    title: article.title,
                                    description: article.abstract,
                                    source: article.api_source?.name || 'Unknown',
                                    authors: article.authors
                                        ?.map(a => a.name)
                                        .filter(name => name && name.trim() !== '')
                                        .join(', ') || '',
                                    date: (() => {
                                        const d = article.published_date;
                                        if (!d || d === 'None' || d === '') return 'Tarih bilgisi yok';
                                        const parsed = new Date(d);
                                        return isNaN(parsed.getTime())
                                            ? 'Tarih bilgisi yok'
                                            : parsed.toLocaleDateString('tr-TR', { year: 'numeric', month: 'short', day: 'numeric' });
                                    })(),
                                    journal: article.journal || '',
                                    citations: article.citation_count || 0,
                                    tags: [...new Set([
                                        ...(article.categories?.slice(0, 3) || []),
                                        ...(article.keywords?.slice(0, 3) || [])
                                    ])].slice(0, 5),
                                    url: article.url || (article.doi ? `https://doi.org/${article.doi.replace(/^https?:\/\/doi\.org\//, '')}` : ''),
                                    pdfUrl: article.pdf_url,
                                }}
                                isSaved={savedIds.has(article.external_id)}
                                onToggleSave={() => toggleSave(article)}
                            />
                        ))}

                        {/* Pagination Controls */}
                        {totalPages > 1 && (
                            <div className="flex items-center justify-center space-x-2 py-6">
                                {/* Previous button */}
                                <button
                                    onClick={() => goToPage(currentPage - 1)}
                                    disabled={currentPage === 1}
                                    className="px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                                >
                                    ← Önceki
                                </button>

                                {/* Page numbers */}
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

                                {/* Next button */}
                                <button
                                    onClick={() => goToPage(currentPage + 1)}
                                    disabled={currentPage === totalPages}
                                    className="px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                                >
                                    Sonraki →
                                </button>
                            </div>
                        )}

                        {/* Total info */}
                        <div className="text-center py-2">
                            <p className="text-sm text-gray-400">Toplam {totalArticles} makale arasından {articles.length} makale gösteriliyor</p>
                        </div>
                    </>
                ) : (
                    <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
                        <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                        <h3 className="text-xl font-semibold text-gray-800 mb-2">Sonuç bulunamadı</h3>
                        <p className="text-gray-600">Farklı anahtar kelimeler deneyin</p>
                    </div>
                )}
            </div>

            {/* Toast notification */}
            {toast && (
                <Toast
                    message={toast.message}
                    type={toast.type}
                    onClose={() => setToast(null)}
                />
            )}
        </div>
    );
};

export default Dashboard;
