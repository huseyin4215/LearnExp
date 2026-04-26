import React, { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { userStorage } from '../services/api';
import { useTheme } from '../contexts/ThemeContext';
import { useLanguage } from '../contexts/LanguageContext';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

interface UserData {
  id: number;
  email: string;
  fullName: string;
  isProfileComplete?: boolean;
}

const Navbar: React.FC = () => {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [userData, setUserData] = useState<UserData | null>(null);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { isDark, toggleTheme } = useTheme();
  const { language, setLanguage, isEnglish } = useLanguage();

  const mainLinks = useMemo(
    () => [
      { path: '/', label: isEnglish ? 'Home' : 'Anasayfa' },
      { path: '/search', label: isEnglish ? 'Publications' : 'Yayınlar' },
      { path: '/news', label: isEnglish ? 'Announcements' : 'Duyurular' },
      { path: '/library', label: isEnglish ? 'Library' : 'Kütüphane' },
    ],
    [isEnglish],
  );

  useEffect(() => {
    const storedUser = userStorage.getUser();
    if (!storedUser) {
      setUserData(null);
      return;
    }

    setUserData(storedUser);
    fetch(`${API_BASE_URL}/user/${storedUser.id}/`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.user) {
          setUserData({
            id: data.user.id,
            email: data.user.email,
            fullName: data.user.fullName,
            isProfileComplete: data.user.profile?.isProfileComplete || false,
          });
        }
      })
      .catch(console.error);
  }, [location.pathname]);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isProfileOpen && !(event.target as HTMLElement).closest('.profile-dropdown')) {
        setIsProfileOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isProfileOpen]);

  const handleLogout = () => {
    setIsProfileOpen(false);
    userStorage.removeToken();
    userStorage.removeUser();
    setUserData(null);
    navigate('/login');
  };

  const isActive = (path: string) => location.pathname === path;

  const initials = (name?: string) => {
    if (!name) return '?';
    const parts = name.split(' ');
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
  };

  return (
    <header
      className={`sticky top-0 z-40 border-b transition-all duration-300 ${
        scrolled ? 'border-[var(--line-soft)] bg-[var(--surface-glass)] backdrop-blur-xl' : 'border-transparent bg-transparent'
      }`}
    >
      <div className="shell">
        <nav className="flex items-center justify-between py-4">
          <Link to="/" className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#355fd4,#2147a8)] shadow-[0_16px_32px_rgba(45,99,226,0.25)]">
              <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
            </div>
            <div>
              <p className="text-lg font-semibold tracking-tight text-[var(--text-strong)]">LearnExp</p>
              <p className="text-[11px] uppercase tracking-[0.22em] text-[var(--text-muted)]">
                {isEnglish ? 'Smart Academic Discovery' : 'Akıllı Akademik Keşif'}
              </p>
            </div>
          </Link>

          <div className="hidden items-center gap-1 lg:flex">
            {mainLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`relative rounded-full px-4 py-2 text-sm font-semibold transition-all ${
                  isActive(link.path)
                    ? 'nav-link-active bg-[var(--brand-soft)] text-[var(--brand)]'
                    : 'text-[var(--text-muted)] hover:bg-[var(--surface)] hover:text-[var(--text-strong)]'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className="flex h-10 w-10 items-center justify-center rounded-full border border-[var(--line)] bg-[var(--surface)] text-[var(--text-muted)] transition-colors hover:text-[var(--text-strong)]"
              title={isDark ? (isEnglish ? 'Light theme' : 'Açık tema') : isEnglish ? 'Dark theme' : 'Koyu tema'}
            >
              {isDark ? (
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>

            <div className="hidden items-center gap-2 rounded-full border border-[var(--line)] bg-[var(--surface)] px-2 py-1 sm:flex">
              <span className="px-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">
                {isEnglish ? 'Lang' : 'Dil'}
              </span>
              <button
                onClick={() => setLanguage('tr')}
                className={`rounded-full px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                  language === 'tr' ? 'bg-[var(--brand-soft)] text-[var(--brand)]' : 'text-[var(--text-muted)]'
                }`}
                title="Türkçe"
              >
                TR
              </button>
              <button
                onClick={() => setLanguage('en')}
                className={`rounded-full px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                  language === 'en' ? 'bg-[var(--brand-soft)] text-[var(--brand)]' : 'text-[var(--text-muted)]'
                }`}
                title="English"
              >
                EN
              </button>
            </div>

            <button
              onClick={() => setIsMobileMenuOpen((value) => !value)}
              className="flex h-10 w-10 items-center justify-center rounded-full border border-[var(--line)] bg-[var(--surface)] text-[var(--text-muted)] lg:hidden"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={isMobileMenuOpen ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'} />
              </svg>
            </button>

            {userData ? (
              <div className="relative profile-dropdown">
                <button
                  className="flex items-center gap-3 rounded-full border border-[var(--line)] bg-[var(--surface)] px-2 py-2 shadow-[var(--shadow-sm)]"
                  onClick={() => setIsProfileOpen((value) => !value)}
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[linear-gradient(135deg,#355fd4,#2147a8)] text-xs font-bold text-white">
                    {initials(userData.fullName)}
                  </div>
                  <div className="hidden text-left md:block">
                    <p className="text-sm font-semibold text-[var(--text-strong)]">{userData.fullName}</p>
                    <p className="text-xs text-[var(--text-muted)]">{isEnglish ? 'Research profile' : 'Araştırma profili'}</p>
                  </div>
                </button>

                {isProfileOpen && (
                  <div className="absolute right-0 mt-3 w-64 rounded-3xl border border-[var(--line-soft)] bg-[var(--surface)] p-2 shadow-[var(--shadow-lg)]">
                    <div className="rounded-2xl bg-[var(--surface-alt)] p-4">
                      <p className="text-sm font-semibold text-[var(--text-strong)]">{userData.fullName}</p>
                      <p className="mt-1 text-xs text-[var(--text-muted)]">{userData.email}</p>
                      {!userData.isProfileComplete && (
                        <Link to="/complete-profile" onClick={() => setIsProfileOpen(false)} className="mt-3 inline-flex text-xs font-semibold text-[var(--brand)]">
                          {isEnglish ? 'Complete profile' : 'Profili tamamla'}
                        </Link>
                      )}
                    </div>
                    <div className="mt-2 grid gap-1">
                      <Link to="/profile" onClick={() => setIsProfileOpen(false)} className="rounded-2xl px-4 py-3 text-sm text-[var(--text-primary)] hover:bg-[var(--surface-alt)]">
                        {isEnglish ? 'Profile' : 'Profil'}
                      </Link>
                      <Link to="/recommendations" onClick={() => setIsProfileOpen(false)} className="rounded-2xl px-4 py-3 text-sm text-[var(--text-primary)] hover:bg-[var(--surface-alt)]">
                        {isEnglish ? 'Recommendations' : 'Öneriler'}
                      </Link>
                      <Link to="/settings" onClick={() => setIsProfileOpen(false)} className="rounded-2xl px-4 py-3 text-sm text-[var(--text-primary)] hover:bg-[var(--surface-alt)]">
                        {isEnglish ? 'Settings' : 'Ayarlar'}
                      </Link>
                      <button onClick={handleLogout} className="rounded-2xl px-4 py-3 text-left text-sm font-semibold text-[var(--danger)] hover:bg-[var(--surface-alt)]">
                        {isEnglish ? 'Sign out' : 'Çıkış yap'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="hidden items-center gap-2 sm:flex">
                <Link to="/login" className="btn-secondary">
                  {isEnglish ? 'Sign in' : 'Giriş yap'}
                </Link>
                <Link to="/register" className="btn-primary">
                  {isEnglish ? 'Create account' : 'Kayıt ol'}
                </Link>
              </div>
            )}
          </div>
        </nav>

        {isMobileMenuOpen && (
          <div className="mb-4 rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface)] p-3 shadow-[var(--shadow-md)] lg:hidden">
            <div className="grid gap-1">
              {mainLinks.map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`rounded-2xl px-4 py-3 text-sm font-semibold ${
                    isActive(link.path) ? 'bg-[var(--brand-soft)] text-[var(--brand)]' : 'text-[var(--text-primary)]'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Navbar;
