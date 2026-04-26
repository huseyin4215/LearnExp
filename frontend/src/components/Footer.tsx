import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';

const Footer: React.FC = () => {
  const { isEnglish } = useLanguage();

  const footerGroups = [
    {
      title: isEnglish ? 'Discover' : 'Keşfet',
      links: [
        { label: isEnglish ? 'Publications' : 'Yayınlar', to: '/search' },
        { label: isEnglish ? 'Announcements' : 'Duyurular', to: '/news' },
        { label: isEnglish ? 'Recommendations' : 'Öneriler', to: '/recommendations' },
        { label: isEnglish ? 'Library' : 'Kütüphanem', to: '/library' },
      ],
    },
    {
      title: isEnglish ? 'Platform' : 'Platform',
      links: [
        { label: isEnglish ? 'Advanced Search' : 'Gelişmiş Arama', to: '/search' },
        { label: isEnglish ? 'Profile' : 'Profil', to: '/profile' },
        { label: isEnglish ? 'Settings' : 'Ayarlar', to: '/settings' },
        { label: isEnglish ? 'Accessibility' : 'Erişilebilirlik', to: '/accessibility' },
      ],
    },
    {
      title: isEnglish ? 'Support' : 'Destek',
      links: [
        { label: isEnglish ? 'Privacy' : 'Gizlilik', to: '/privacy' },
        { label: isEnglish ? 'Help Center' : 'Yardım', to: '/help' },
        { label: isEnglish ? 'Contact' : 'İletişim', to: '/contact' },
      ],
    },
  ];

  const stats = [
    { label: isEnglish ? 'Tracked sources' : 'Takip edilen kaynak', value: '20+' },
    { label: isEnglish ? 'Content lanes' : 'İçerik akışı', value: '6' },
    { label: isEnglish ? 'Discovery modes' : 'Keşif modu', value: isEnglish ? 'Search, alerts, library' : 'Arama, uyarı, kütüphane' },
  ];

  return (
    <footer className="site-footer mt-16">
      <div className="shell">
        <div className="footer-grid">
          <div className="space-y-5">
            <div>
              <p className="eyebrow mb-3">LearnExp</p>
              <h2 className="font-heading text-3xl font-semibold text-[var(--text-strong)]">
                {isEnglish ? 'Academic discovery with editorial clarity.' : 'Editoryal netlikle akademik keşif.'}
              </h2>
            </div>
            <p className="max-w-xl text-sm text-[var(--text-muted)]">
              {isEnglish
                ? 'LearnExp brings publications, conferences, events, announcements, and institutional updates into one research workspace.'
                : 'LearnExp; yayınları, konferansları, etkinlikleri, duyuruları ve kurumsal güncellemeleri tek bir araştırma çalışma alanında bir araya getirir.'}
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              {stats.map((stat) => (
                <div key={stat.label} className="footer-stat">
                  <p className="text-lg font-semibold text-[var(--text-strong)]">{stat.value}</p>
                  <p className="text-xs text-[var(--text-muted)]">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-8 sm:grid-cols-3">
            {footerGroups.map((group) => (
              <div key={group.title}>
                <h3 className="mb-3 text-sm font-semibold text-[var(--text-strong)]">{group.title}</h3>
                <ul className="space-y-2">
                  {group.links.map((link) => (
                    <li key={link.label}>
                      <Link className="footer-link" to={link.to}>
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-10 flex flex-col gap-3 border-t border-[var(--line-soft)] pt-6 text-xs text-[var(--text-muted)] sm:flex-row sm:items-center sm:justify-between">
          <p>
            {isEnglish
              ? 'LearnExp is designed for publications, conferences, events, deadlines, and research tracking.'
              : 'LearnExp; yayınlar, konferanslar, etkinlikler, son tarihler ve araştırma takibi için tasarlandı.'}
          </p>
          <div className="flex gap-4">
            <span>{isEnglish ? 'Privacy-aware' : 'Gizlilik odaklı'}</span>
            <span>{isEnglish ? 'Accessible defaults' : 'Erişilebilir varsayılanlar'}</span>
            <span>{isEnglish ? 'Institution-ready' : 'Kurum dostu yapı'}</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
