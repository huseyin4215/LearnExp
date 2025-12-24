

import React from 'react';
import type { AcademicContent } from '../types';

interface ContentCardProps {
  content: AcademicContent;
  isSaved: boolean;
  onToggleSave: () => void;
}

const ContentCard: React.FC<ContentCardProps> = ({ content, isSaved, onToggleSave }) => {
  const isConference = content.type === 'conference';


  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-all">
      <div className="flex items-start justify-between mb-3">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${isConference ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'}`}>
          {isConference ? 'Conference' : 'Funding Call'}
        </span>
        <div className="flex items-center space-x-2">
          <button onClick={onToggleSave} className={`p-1 transition-colors ${isSaved ? 'text-teal-600' : 'text-gray-400 hover:text-teal-600'}`}>
            <svg className="w-4 h-4" fill={isSaved ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
            </svg>
          </button>
          <button className="p-1 text-gray-400 hover:text-red-500"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path></svg></button>
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
            {content.date}
          </span>
        </div>
      ) : (
        <p className="text-sm text-gray-600 mb-3">
          <span className="font-medium">{content.source}</span> • Funding Amount: {content.amount}
        </p>
      )}
      <p className="text-gray-700 text-sm leading-relaxed mb-4">{content.description}</p>
      <div className={`${isConference ? 'bg-orange-50 border-orange-200' : 'bg-red-50 border-red-200'} border rounded-lg p-3 mb-4`}>
        <p className={`text-sm ${isConference ? 'text-orange-800' : 'text-red-800'}`}>
          <span className="font-medium">Deadline:</span> {content.deadline}
        </p>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex flex-wrap gap-2">
          {content.tags.map(tag => <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">{tag}</span>)}
        </div>
        <button className="text-teal-600 hover:text-teal-700 text-sm font-medium transition-colors">View Details →</button>
      </div>
    </div>
  );
};

export default ContentCard;
