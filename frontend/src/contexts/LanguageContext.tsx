import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

export type SiteLanguage = 'tr' | 'en';

interface LanguageContextType {
  language: SiteLanguage;
  setLanguage: (language: SiteLanguage) => void;
  isEnglish: boolean;
}

const LanguageContext = createContext<LanguageContextType>({
  language: 'tr',
  setLanguage: () => {},
  isEnglish: false,
});

export const useLanguage = () => useContext(LanguageContext);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<SiteLanguage>(() => {
    const stored = localStorage.getItem('site-language');
    return stored === 'en' ? 'en' : 'tr';
  });

  useEffect(() => {
    document.documentElement.lang = language;
    localStorage.setItem('site-language', language);
  }, [language]);

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      isEnglish: language === 'en',
    }),
    [language],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
};

export default LanguageContext;
