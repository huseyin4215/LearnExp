import React, { useState } from 'react';
import ContentCard from '../components/ContentCard';
import { MOCK_CONTENT } from '../constants';

const MyLibrary: React.FC = () => {
  const [savedIds] = useState<Set<string>>(new Set(['c1', 'c2', 'extra-1', 'extra-2', 'extra-3']));

  return (
    <div id="myLibraryView">
      <section className="gradient-bg text-white py-16 rounded-2xl mb-8">
        <div className="max-w-4xl mx-auto text-center px-6">
          <div className="w-16 h-16 bg-white bg-opacity-20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
            </svg>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            My <span className="text-yellow-300">Library</span>
          </h2>
          <p className="text-lg md:text-xl mb-6 text-indigo-100">Your saved articles, conferences, and funding opportunities</p>

          <div className="max-w-2xl mx-auto">
            <div className="relative">
              <input
                type="text"
                placeholder="Search in your library..."
                className="w-full px-6 py-3 text-gray-800 bg-white rounded-full shadow-lg focus:outline-none pr-14 border border-gray-100"
              />
              <button className="absolute right-2 top-2 bg-indigo-600 hover:bg-indigo-700 text-white p-1.5 rounded-full transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
              </button>
            </div>
          </div>
        </div>
      </section>

      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8 border-b border-gray-200 pb-4">
          <h3 className="text-xl font-bold text-gray-800">Saved Items</h3>
          <div className="flex space-x-2">
            <span className="text-xs bg-indigo-50 text-indigo-600 px-3 py-1 rounded-full font-bold">{savedIds.size} Items</span>
          </div>
        </div>

        {/* Single Column List */}
        <div className="flex flex-col space-y-8">
          {MOCK_CONTENT.map(item => (
            <ContentCard
              key={`lib-${item.id}`}
              content={item}
              isSaved={true}
              onToggleSave={() => { }}
            />
          ))}

          {/* Extra Static Professional Content for Library Display */}
          <ContentCard
            key="lib-extra-1"
            content={{
              id: 'extra-1',
              type: 'conference',
              title: 'Neural Information Processing Systems (NeurIPS) 2024',
              description: 'NeurIPS is the premier world-class conference on machine learning and computational neuroscience. Featuring breakthrough research in Generative AI and LLMs.',
              source: 'NeurIPS Foundation',
              date: 'Dec 10-15, 2024',
              location: 'Vancouver, Canada',
              deadline: 'Registration Open',
              tags: ['Deep Learning', 'Neural Networks', 'AI Ethics']
            }}
            isSaved={true}
            onToggleSave={() => { }}
          />

          <ContentCard
            key="lib-extra-2"
            content={{
              id: 'extra-2',
              type: 'funding',
              title: 'Horizon Europe: AI for Healthcare Excellence Grant',
              description: 'European Commission funding for large-scale research projects focusing on AI applications in diagnostic imaging and personalized medicine.',
              source: 'EU Horizon Europe',
              date: '2025 Cycle',
              amount: 'Up to €2,500,000',
              deadline: 'August 15, 2025',
              tags: ['Healthcare', 'AI', 'Public Funding']
            }}
            isSaved={true}
            onToggleSave={() => { }}
          />

          <ContentCard
            key="lib-extra-3"
            content={{
              id: 'extra-3',
              type: 'conference',
              title: 'CVPR 2025 - Computer Vision and Pattern Recognition',
              description: 'The world\'s leading conference on computer vision. Exploring the latest in 3D reconstruction, object detection, and video analysis.',
              source: 'IEEE / CVF',
              date: 'June 2025',
              location: 'Nashville, TN',
              deadline: 'Review Stage',
              tags: ['Computer Vision', 'Robotics']
            }}
            isSaved={true}
            onToggleSave={() => { }}
          />
        </div>

        <div className="mt-12 text-center pb-12">
          <button className="text-gray-400 text-sm font-medium hover:text-indigo-600 transition-colors">
            Show Archived Content
          </button>
        </div>
      </div>
    </div>
  );
};

export default MyLibrary;