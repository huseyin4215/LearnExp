
import React, { useState } from 'react';
import { NEWS_ITEMS } from '../constants';
import type { NewsItem } from '../types';

const NewsSlider: React.FC = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const itemsPerView = 3;

  const slide = (dir: 'next' | 'prev') => {
    if (dir === 'next') {
      setCurrentIndex(prev => Math.min(prev + 1, NEWS_ITEMS.length - itemsPerView));
    } else {
      setCurrentIndex(prev => Math.max(prev - 1, 0));
    }
  };

  const getColorClass = (index: number) => {
    const colors = ['indigo', 'emerald', 'violet', 'orange'];
    return colors[index % colors.length];
  };

  return (
    <div className="relative">
      <div className="overflow-hidden">
        <div
          className="flex transition-transform duration-300 ease-in-out"
          style={{ transform: `translateX(-${currentIndex * (100 / itemsPerView)}%)` }}
        >
          {NEWS_ITEMS.map((item: NewsItem, index: number) => (
            <div key={item.id} className="flex-none w-full md:w-1/2 lg:w-1/3 px-3">
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden h-64 hover:-translate-y-1 transition-transform shadow-sm">
                <div className="flex h-full">
                  <div className={`w-32 bg-gradient-to-br ${getColorClass(index) === 'indigo' ? 'from-blue-100 to-indigo-200' : getColorClass(index) === 'emerald' ? 'from-green-100 to-emerald-200' : getColorClass(index) === 'violet' ? 'from-purple-100 to-violet-200' : 'from-orange-100 to-amber-200'} flex items-center justify-center flex-shrink-0`}>
                    <svg className={`w-12 h-12 text-${getColorClass(index)}-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                  </div>
                  <div className="flex-1 p-4 flex flex-col justify-between">
                    <div>
                      <h3 className="serif-font text-base font-semibold text-gray-800 mb-2 leading-tight">{item.title}</h3>
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{item.description}</p>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-2">
                        <span>Tarih: {item.date}</span> • <span>Tür: Haber</span> • <span>Kaynak: {item.source}</span>
                      </div>
                      <button className="text-indigo-600 hover:text-indigo-700 text-sm font-medium">Read More →</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <button onClick={() => slide('prev')} className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 bg-white rounded-full p-2 shadow-lg border border-gray-200 disabled:opacity-50" disabled={currentIndex === 0}>
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M15 19l-7-7 7-7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </button>
      <button onClick={() => slide('next')} className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 bg-white rounded-full p-2 shadow-lg border border-gray-200 disabled:opacity-50" disabled={currentIndex >= NEWS_ITEMS.length - itemsPerView}>
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </button>
    </div>
  );
};

export default NewsSlider;
