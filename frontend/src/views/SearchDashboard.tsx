import React, { useState } from 'react';
import ContentCard from '../components/ContentCard';
import { MOCK_CONTENT, NEWS_ITEMS } from '../constants';

const FilterSection: React.FC<{ title: string, options: string[] }> = ({ title, options }) => (
  <div className="mb-6">
    <h4 className="text-[10px] font-bold text-gray-400 mb-2 uppercase tracking-tighter">{title}</h4>
    <div className="space-y-1">
      {options.map(opt => (
        <label key={opt} className="flex items-center cursor-pointer group">
          <input type="checkbox" className="w-3 h-3 rounded border-gray-300 text-teal-600 focus:ring-teal-500" />
          <span className="ml-2 text-[10px] text-gray-500 group-hover:text-gray-800 transition-colors truncate">{opt}</span>
        </label>
      ))}
    </div>
  </div>
);

const SearchDashboard: React.FC = () => {
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());

  const toggleSave = (id: string) => {
    setSavedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

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
            <div className="relative">
              <input
                type="text"
                placeholder="Search for articles, conferences, funding calls..."
                className="w-full px-6 py-4 text-lg text-gray-800 bg-white rounded-full shadow-lg focus:outline-none pr-16 border border-gray-100"
              />
              <button className="absolute right-2 top-2 bg-indigo-600 hover:bg-indigo-700 text-white p-2 rounded-full transition-colors">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
              </button>
            </div>
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            {['Artificial Intelligence', 'Machine Learning', 'Computer Vision', 'NLP'].map(tag => (
              <span key={tag} className="bg-white bg-opacity-20 text-white px-4 py-2 rounded-full text-sm hover:bg-opacity-30 cursor-pointer transition-all">{tag}</span>
            ))}
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-gray-200 p-4 sticky top-24 shadow-sm">
            <h3 className="font-bold text-gray-800 mb-4 text-xs uppercase tracking-widest border-b pb-2">Filters</h3>
            <FilterSection title="Content Type" options={['Articles', 'Conferences', 'Funding', 'Datasets']} />
            <div className="mb-6">
              <h4 className="text-[10px] font-bold text-gray-400 mb-2 uppercase tracking-tighter">Date Range</h4>
              <select className="w-full border border-gray-200 rounded px-2 py-1 text-[11px] text-gray-600 bg-white focus:ring-1 focus:ring-indigo-500 outline-none shadow-sm">
                <option>Last 30 days</option>
                <option>Last 3 months</option>
                <option>Last year</option>
                <option>All time</option>
              </select>
            </div>
            <FilterSection title="Source" options={['arXiv', 'OpenAlex', 'TÜBİTAK']} />
          </div>
        </div>

        <div className="lg:col-span-10">
          <div className="mb-6 flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-800">Latest Academic Discoveries</h3>
            <span className="text-[10px] bg-gray-200 text-gray-600 px-2 py-1 rounded font-bold uppercase">Static Preview</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {MOCK_CONTENT.map(item => (
              <ContentCard
                key={item.id}
                content={item}
                isSaved={savedIds.has(item.id)}
                onToggleSave={() => toggleSave(item.id)}
              />
            ))}
            {NEWS_ITEMS.map((news, idx) => (
              <ContentCard
                key={`search-item-${idx}`}
                content={{
                  ...news,
                  type: idx % 2 === 0 ? 'conference' : 'funding',
                  deadline: idx % 2 === 0 ? 'March 12, 2025' : 'April 01, 2025',
                  location: idx % 2 === 0 ? 'Istanbul, TR' : undefined,
                  amount: idx % 2 !== 0 ? '₺750,000' : undefined,
                }}
                isSaved={savedIds.has(`search-item-${idx}`)}
                onToggleSave={() => toggleSave(`search-item-${idx}`)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchDashboard;