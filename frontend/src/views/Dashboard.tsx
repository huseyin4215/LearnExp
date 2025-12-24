import React, { useState } from 'react';
import ContentCard from '../components/ContentCard';
import NewsSlider from '../components/NewsSlider';
import { MOCK_CONTENT } from '../constants';

const StatCard: React.FC<{ icon: string, label: string, value: string, color: string, iconBg: string }> = ({ icon, label, value, color, iconBg }) => (
    <div className={`bg-gradient-to-br ${color} p-6 rounded-xl shadow-sm transition-transform hover:-translate-y-1`}>
        <div className="flex items-center">
            <div className={`w-12 h-12 ${iconBg} rounded-lg flex items-center justify-center text-white`}>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d={icon} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </div>
            <div className="ml-4">
                <p className="text-2xl font-semibold text-gray-800">{value}</p>
                <p className="text-sm text-gray-600">{label}</p>
            </div>
        </div>
    </div>
);

const Dashboard: React.FC = () => {
    const [savedIds, setSavedIds] = useState<Set<string>>(new Set(['c1', 'c2']));

    const toggleSave = (id: string) => {
        setSavedIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    };

    return (
        <div id="dashboardView">
            <section className="gradient-bg text-white py-16 rounded-2xl mb-8">
                <div className="max-w-4xl mx-auto text-center px-6">
                    <h2 className="text-3xl md:text-4xl font-bold mb-4">
                        Welcome back, <span className="text-yellow-300">Ahmet</span>
                    </h2>
                    <p className="text-lg md:text-xl mb-6 text-indigo-100">
                        Your personalized academic content feed is ready
                    </p>
                    <div className="max-w-2xl mx-auto mb-6">
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Quick search in your feed..."
                                className="w-full px-6 py-3 text-gray-800 bg-white rounded-full shadow-lg focus:outline-none pr-14 border border-gray-100"
                            />
                            <button className="absolute right-2 top-2 bg-indigo-600 hover:bg-indigo-700 text-white p-1.5 rounded-full transition-colors">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <StatCard icon="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" label="New Articles" value="24" color="from-blue-50 to-indigo-100" iconBg="bg-indigo-600" />
                <StatCard icon="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z" label="Conferences" value="3" color="from-green-50 to-emerald-100" iconBg="bg-emerald-600" />
                <StatCard icon="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" label="Funding Calls" value="5" color="from-purple-50 to-violet-100" iconBg="bg-violet-600" />
            </div>

            <div className="mb-8">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-800">Haberler</h2>
                    <button className="text-indigo-600 hover:text-indigo-700 font-medium text-sm transition-colors">
                        Tümünü Görüntüleyin →
                    </button>
                </div>
                <NewsSlider />
            </div>

            <div className="space-y-6">
                {MOCK_CONTENT.map(item => (
                    <ContentCard key={item.id} content={item} isSaved={savedIds.has(item.id)} onToggleSave={() => toggleSave(item.id)} />
                ))}
            </div>
        </div>
    );
};

export default Dashboard;
