import React from 'react';
import type { AcademicContent } from '../types';
import { useLanguage } from '../contexts/LanguageContext';

interface ContentCardProps {
  content: AcademicContent;
  isSaved: boolean;
  onToggleSave: () => void;
  isLiked?: boolean;
  onToggleLike?: () => void;
  onView?: () => void;
}

const ContentCard: React.FC<ContentCardProps> = ({
  content,
  isSaved,
  onToggleSave,
  isLiked = false,
  onToggleLike,
  onView,
}) => {
  const { isEnglish, language } = useLanguage();

  const badgeMap: Record<string, { label: string; className: string }> = {
    article: { label: isEnglish ? 'Article' : 'Makale', className: 'badge-space' },
    conference: { label: isEnglish ? 'Conference' : 'Konferans', className: 'badge-ai' },
    event: { label: isEnglish ? 'Event' : 'Etkinlik', className: 'badge-business' },
    announcement: { label: isEnglish ? 'Announcement' : 'Duyuru', className: 'badge-default' },
    funding: { label: isEnglish ? 'Funding' : 'Fon', className: 'badge-biotech' },
  };

  const metaToneMap: Record<string, string> = {
    article: 'bg-[rgba(24,106,163,0.08)] text-[#166aa3]',
    conference: 'bg-[rgba(45,99,226,0.1)] text-[#2757cb]',
    event: 'bg-[rgba(185,109,23,0.1)] text-[#9a6119]',
    announcement: 'bg-[rgba(102,120,143,0.12)] text-[#5e7087]',
    funding: 'bg-[rgba(31,143,88,0.1)] text-[#1f8f58]',
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return isEnglish ? 'Date unavailable' : 'Tarih yok';
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return dateString;
    return new Intl.DateTimeFormat(language === 'en' ? 'en-US' : 'tr-TR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    }).format(date);
  };

  const badge = badgeMap[content.type] || { label: isEnglish ? 'Content' : 'İçerik', className: 'badge-default' };
  const metaTone = metaToneMap[content.type] || metaToneMap.announcement;
  const tags = [...(content.tags || []), ...(content.keywords || [])].filter(Boolean).slice(0, 4);
  const hasImage = Boolean(content.imageUrl);

  return (
    <article className="card-base overflow-hidden">
      <div className={`grid gap-0 ${hasImage ? 'lg:grid-cols-[260px_1fr]' : ''}`}>
        {hasImage && (
          <div className="relative h-56 overflow-hidden lg:h-full lg:min-h-[260px]">
            <img src={content.imageUrl} alt={content.title} className="h-full w-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent" />
          </div>
        )}

        <div className="flex min-h-[260px] flex-col p-5 md:p-6">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className={badge.className}>{badge.label}</span>
              {content.source && (
                <span className={`rounded-full px-3 py-1 text-[11px] font-semibold ${metaTone}`}>{content.source}</span>
              )}
              {typeof content.matchScore === 'number' && (
                <span className="rounded-full bg-[rgba(31,143,88,0.12)] px-3 py-1 text-[11px] font-semibold text-[var(--success)]">
                  {isEnglish ? `${content.matchScore}% match` : `%${content.matchScore} uyum`}
                </span>
              )}
              {content.deadline && (
                <span className="rounded-full bg-[rgba(185,109,23,0.14)] px-3 py-1 text-[11px] font-semibold text-[var(--warning)]">
                  {isEnglish ? `Deadline: ${content.deadline}` : `Son tarih: ${content.deadline}`}
                </span>
              )}
            </div>

            <div className="space-y-2">
              <h3 className="font-heading text-2xl font-semibold leading-tight text-[var(--text-strong)]">{content.title}</h3>
              <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-[var(--text-muted)]">
                <span>{formatDate(content.date)}</span>
                {content.authors && <span className="line-clamp-1">{content.authors}</span>}
                {content.journal && <span className="line-clamp-1">{content.journal}</span>}
                {content.location && <span>{content.location}</span>}
                {content.citations != null && content.citations > 0 && <span>{content.citations} {isEnglish ? 'citations' : 'atıf'}</span>}
              </div>
            </div>

            <p className="line-clamp-3 max-w-4xl text-sm leading-7 text-[var(--text-primary)]">{content.description}</p>

            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {tags.map((tag) => (
                  <span key={tag} className="chip">
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="mt-auto flex items-end justify-between gap-4 border-t border-[var(--line-soft)] pt-5">
            <div className="flex items-center gap-2">
              {onToggleLike && (
                <button
                  onClick={onToggleLike}
                  className={`flex h-10 w-10 items-center justify-center rounded-full border transition-colors ${
                    isLiked
                      ? 'border-[rgba(198,69,69,0.18)] bg-[rgba(198,69,69,0.08)] text-[var(--danger)]'
                      : 'border-[var(--line)] bg-[var(--surface)] text-[var(--text-muted)] hover:text-[var(--text-strong)]'
                  }`}
                  title={isLiked ? (isEnglish ? 'Remove like' : 'Beğeniyi kaldır') : isEnglish ? 'Like' : 'Beğen'}
                  aria-label={isLiked ? (isEnglish ? 'Remove like' : 'Beğeniyi kaldır') : isEnglish ? 'Like' : 'Beğen'}
                >
                  <svg className="h-4 w-4" fill={isLiked ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                </button>
              )}

              <button
                onClick={onToggleSave}
                className={`flex h-10 w-10 items-center justify-center rounded-full border transition-colors ${
                  isSaved
                    ? 'border-[rgba(45,99,226,0.18)] bg-[var(--brand-soft)] text-[var(--brand)]'
                    : 'border-[var(--line)] bg-[var(--surface)] text-[var(--text-muted)] hover:text-[var(--text-strong)]'
                }`}
                title={isSaved ? (isEnglish ? 'Saved' : 'Kaydedildi') : isEnglish ? 'Save' : 'Kaydet'}
                aria-label={isSaved ? (isEnglish ? 'Saved' : 'Kaydedildi') : isEnglish ? 'Save' : 'Kaydet'}
              >
                <svg className="h-4 w-4" fill={isSaved ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              </button>
            </div>

            <div className="flex items-center gap-3">
              {content.pdfUrl && content.pdfUrl.startsWith('http') && (
                <a href={content.pdfUrl} target="_blank" rel="noopener noreferrer" onClick={onView} className="btn-secondary px-4 py-2 text-xs">
                  PDF
                </a>
              )}
              {content.url && content.url.startsWith('http') && (
                <a href={content.url} target="_blank" rel="noopener noreferrer" onClick={onView} className="btn-primary px-4 py-2 text-xs">
                  {isEnglish ? 'Details' : 'Detaylar'}
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </article>
  );
};

export default ContentCard;
