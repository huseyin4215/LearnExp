import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ContentCard from '../components/ContentCard';
import { libraryApi, userStorage } from '../services/api';
import type { LibraryItem } from '../services/api';

const PAGE_SIZE = 10;

const getPageNumbers = (currentPage: number, totalPages: number): (number | '...')[] => {
  const pages: (number | '...')[] = [];

  if (totalPages <= 7) {
    for (let page = 1; page <= totalPages; page += 1) pages.push(page);
    return pages;
  }

  pages.push(1);
  if (currentPage > 3) pages.push('...');
  for (let page = Math.max(2, currentPage - 1); page <= Math.min(totalPages - 1, currentPage + 1); page += 1) pages.push(page);
  if (currentPage < totalPages - 2) pages.push('...');
  pages.push(totalPages);

  return pages;
};

const MyLibrary: React.FC = () => {
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [toast, setToast] = useState<string | null>(null);

  const userId = userStorage.getUser()?.id;

  const fetchLibrary = useCallback(
    async (page = 1, search = '') => {
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
        console.error(error);
      } finally {
        setLoading(false);
      }
    },
    [userId],
  );

  useEffect(() => {
    fetchLibrary();
  }, [fetchLibrary]);

  const handleRemove = async (externalId: string) => {
    if (!userId) return;

    try {
      await libraryApi.remove(userId, externalId);
      setToast('İçerik kütüphaneden kaldırıldı.');
      const nextPage = items.length === 1 && currentPage > 1 ? currentPage - 1 : currentPage;
      await fetchLibrary(nextPage, searchQuery);
      window.setTimeout(() => setToast(null), 2600);
    } catch (error) {
      console.error(error);
    }
  };

  const handleSearch = (event: React.FormEvent) => {
    event.preventDefault();
    fetchLibrary(1, searchQuery);
  };

  const goToPage = (page: number) => {
    if (page < 1 || page > totalPages) return;
    fetchLibrary(page, searchQuery);
    window.scrollTo({ top: 520, behavior: 'smooth' });
  };

  return (
    <div className="space-y-8">
      <section className="shell page-hero px-6 py-8 md:px-10 md:py-12">
        <div className="relative z-10 grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
          <div className="space-y-5 text-white">
            <p className="eyebrow text-white/65">Kişisel araştırma alanı</p>
            <h1 className="font-heading text-5xl leading-tight md:text-6xl">Kaydettiğin yayınları, bağlantıları ve geri dönmek istediğin içerikleri tek yerde tut.</h1>
            <p className="max-w-2xl text-base leading-8 text-white/72 md:text-lg">
              Kütüphane; daha sonra okumak, yeniden incelemek veya araştırma akışını düzenlemek istediğin içerikleri topladığın kişisel alanın.
            </p>

            <form onSubmit={handleSearch} className="section-card-dark p-3">
              <div className="grid gap-3 md:grid-cols-[1fr_auto]">
                <div className="flex items-center gap-3 rounded-[22px] bg-white/5 px-4 py-4">
                  <svg className="h-5 w-5 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Kütüphanede makale, yazar veya konu ara..."
                    className="w-full bg-transparent text-sm text-white placeholder:text-white/42 focus:outline-none"
                  />
                </div>
                <button type="submit" className="btn-primary w-full justify-center md:w-auto">
                  Filtrele
                </button>
              </div>
            </form>
          </div>

          <div className="hero-info-panel p-5">
            <p className="eyebrow text-white/60">Kütüphane özeti</p>
            <div className="mt-4 grid gap-3">
              <div className="hero-info-card">
                <p className="text-3xl font-semibold">{totalItems}</p>
                <p className="mt-1 text-sm text-white/70">Toplam kaydedilen içerik</p>
              </div>
              <div className="hero-info-card">
                <p className="text-3xl font-semibold">{totalPages}</p>
                <p className="mt-1 text-sm text-white/70">Sayfalı düzen ile daha temiz takip</p>
              </div>
              <div className="hero-info-card">
                <p className="text-sm font-semibold">Daha hızlı geri dönüş</p>
                <p className="mt-1 text-sm text-white/70">Kaydettiğin içerikleri tarih, konu ve kaynağa göre yeniden tarayabilirsin.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="shell">
        <div className="section-card p-6 md:p-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="eyebrow mb-2">Kaydedilen içerikler</p>
              <h2 className="font-heading text-4xl text-[var(--text-strong)]">Kütüphane akışı</h2>
            </div>
            <span className="rounded-full bg-[var(--brand-soft)] px-4 py-2 text-xs font-semibold text-[var(--brand)]">
              {totalItems} kayıt
            </span>
          </div>

          {!userId ? (
            <div className="mt-6 rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-alt)] px-8 py-14 text-center">
              <p className="font-heading text-3xl text-[var(--text-strong)]">Kütüphaneyi kullanmak için giriş yap.</p>
              <p className="mt-2 text-sm text-[var(--text-muted)]">Kaydettiğin içeriklere her cihazdan ulaşmak için hesabınla devam et.</p>
              <Link to="/login" className="btn-primary mt-6 inline-flex">
                Giriş yap
              </Link>
            </div>
          ) : loading ? (
            <div className="mt-6 grid gap-4">
              {Array.from({ length: 3 }).map((_, index) => (
                <div key={index} className="h-56 animate-pulse rounded-[24px] border border-[var(--line-soft)] bg-[var(--surface-alt)]" />
              ))}
            </div>
          ) : items.length > 0 ? (
            <div className="mt-6 space-y-4">
              {items.map((item) => (
                <ContentCard
                  key={`lib-${item.external_id}`}
                  content={{
                    id: item.external_id,
                    type: 'article',
                    title: item.title,
                    description: item.abstract || 'Özet bilgisi bulunmuyor.',
                    source: item.source || item.journal || 'Akademik kaynak',
                    authors: item.authors?.map((author: { name: string }) => author.name).filter(Boolean).join(', ') || '',
                    date: item.published_date || item.saved_at,
                    journal: item.journal || '',
                    citations: item.citation_count || 0,
                    tags: item.categories?.slice(0, 4) || [],
                    url: item.url,
                    pdfUrl: item.pdf_url,
                  }}
                  isSaved={true}
                  onToggleSave={() => handleRemove(item.external_id)}
                />
              ))}

              {totalPages > 1 && (
                <div className="flex flex-wrap items-center justify-center gap-2 pt-6">
                  <button
                    onClick={() => goToPage(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="btn-secondary px-4 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Önceki
                  </button>
                  {getPageNumbers(currentPage, totalPages).map((page, index) =>
                    page === '...' ? (
                      <span key={`dots-${index}`} className="px-2 text-sm text-[var(--text-muted)]">
                        ...
                      </span>
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
                  <button
                    onClick={() => goToPage(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="btn-secondary px-4 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Sonraki
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="mt-6 rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-alt)] px-8 py-14 text-center">
              <p className="font-heading text-3xl text-[var(--text-strong)]">Kütüphanen henüz boş.</p>
              <p className="mt-2 text-sm text-[var(--text-muted)]">Makale veya etkinlik kartlarındaki yer imi ikonuyla içerikleri burada biriktirebilirsin.</p>
              <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                <Link to="/" className="btn-primary">
                  Anasayfaya dön
                </Link>
                <Link to="/search" className="btn-secondary">
                  Aramaya git
                </Link>
              </div>
            </div>
          )}
        </div>
      </section>

      {toast && (
        <div className="fixed bottom-24 left-1/2 z-40 -translate-x-1/2 rounded-full bg-[var(--success)] px-5 py-3 text-sm font-semibold text-white shadow-[var(--shadow-lg)]">
          {toast}
        </div>
      )}
    </div>
  );
};

export default MyLibrary;
