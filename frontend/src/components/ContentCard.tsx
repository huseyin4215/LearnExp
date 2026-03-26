
import React from 'react';
import type { AcademicContent } from '../types';

interface ContentCardProps {
  content: AcademicContent;
  isSaved: boolean;
  onToggleSave: () => void;
}

const ContentCard: React.FC<ContentCardProps> = ({ content, isSaved, onToggleSave }) => {
  const isConference = content.type === 'conference';
  const isFunding = content.type === 'funding';
  const isArticle = content.type === 'article'; // or default

  let badgeText = 'Resource';
  let badgeColor = 'bg-gray-100 text-gray-800';
  if (isConference) {
    badgeText = 'Conference';
    badgeColor = 'bg-purple-100 text-purple-800';
  } else if (isFunding) {
    badgeText = 'Funding Call';
    badgeColor = 'bg-green-100 text-green-800';
  } else if (isArticle) {
    badgeText = 'Article / Paper';
    badgeColor = 'bg-blue-100 text-blue-800';
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return dateString;
      return new Intl.DateTimeFormat('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' }).format(date);
    } catch {
      return dateString;
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-all">
      <div className="flex items-start justify-between mb-3">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeColor}`}>
          {badgeText}
        </span>
        <div className="flex items-center space-x-2">
          <button onClick={onToggleSave} className={`p-1 transition-colors ${isSaved ? 'text-teal-600' : 'text-gray-400 hover:text-teal-600'}`}>
            <svg className="w-4 h-4" fill={isSaved ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
            </svg>
          </button>
          <button className="p-1 text-gray-400 hover:text-red-500 transition-colors"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path></svg></button>
        </div>
      </div>

      <h3 className="serif-font text-lg font-semibold text-gray-800 mb-2 leading-tight">{content.title}</h3>

      {isConference ? (
        <div className="flex items-center text-sm text-gray-600 mb-3 space-x-4">
          <span className="flex items-center">
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path></svg>
            {content.location}
          </span>
          <span className="flex items-center">
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 0h6m-6 0l-2 2m8-2l2 2"></path></svg>
            {formatDate(content.date)}
          </span>
        </div>
      ) : isFunding ? (
        <p className="text-sm text-gray-600 mb-3">
          <span className="font-medium text-gray-800">Source:</span> {content.source} • <span className="font-medium text-gray-800">Funding Amount:</span> {content.amount}
        </p>
      ) : (
        <div className="text-sm text-gray-600 mb-3 space-y-1">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span className="flex items-center">
              <svg className="w-3.5 h-3.5 mr-1 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
              <span className="font-medium text-gray-800">Source:</span>&nbsp;{content.source || 'Unknown'}
            </span>
            <span className="flex items-center">
              <svg className="w-3.5 h-3.5 mr-1 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
              <span className="font-medium text-gray-800">Published:</span>&nbsp;{formatDate(content.date)}
            </span>
          </div>
          {content.authors && content.authors.trim() !== '' && (
            <div className="flex items-start">
              <svg className="w-3.5 h-3.5 mr-1 mt-0.5 text-orange-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
              <span><span className="font-medium text-gray-800">Authors:</span> {content.authors}</span>
            </div>
          )}
          {content.journal && (
            <div className="flex items-center">
              <svg className="w-3.5 h-3.5 mr-1 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
              <span><span className="font-medium text-gray-800">Journal:</span> {content.journal}</span>
            </div>
          )}
          {content.citations != null && content.citations > 0 && (
            <div className="flex items-center">
              <svg className="w-3.5 h-3.5 mr-1 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
              <span><span className="font-medium text-gray-800">Citations:</span> {content.citations}</span>
            </div>
          )}
        </div>
      )}

      {content.imageUrl && (
        <img
          src={content.imageUrl}
          alt={content.title}
          className="w-full h-48 object-cover rounded-lg mb-4 border border-gray-100"
        />
      )}

      {/* Article Summary / Description */}
      <p className="text-gray-700 text-sm leading-relaxed mb-4">{content.description}</p>

      {/* Optional Deadline */}
      {content.deadline && (
        <div className={`${isConference ? 'bg-orange-50 border-orange-200' : 'bg-red-50 border-red-200'} border rounded-lg p-3 mb-4`}>
          <p className={`text-sm ${isConference ? 'text-orange-800' : 'text-red-800'}`}>
            <span className="font-medium">Deadline:</span> {content.deadline}
          </p>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex flex-wrap gap-2">
          {content.tags && content.tags.map(tag => <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">{tag}</span>)}
          {content.keywords && content.keywords.map((kw: string) => <span key={`kw-${kw}`} className="px-2 py-1 bg-indigo-50 text-indigo-700 text-xs rounded font-medium border border-indigo-100">{kw}</span>)}
        </div>

        <div className="flex items-center gap-3">
          {content.pdfUrl && content.pdfUrl.startsWith('http') && (
            <a href={content.pdfUrl} target="_blank" rel="noopener noreferrer" className="text-red-500 hover:text-red-600 text-sm font-medium transition-colors flex items-center">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
              PDF
            </a>
          )}
          {content.url && content.url.startsWith('http') && (
            <a href={content.url} target="_blank" rel="noopener noreferrer" className="text-teal-600 hover:text-teal-700 text-sm font-medium transition-colors">
              Detaylar →
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default ContentCard;
