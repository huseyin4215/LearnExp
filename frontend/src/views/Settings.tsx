import React, { useState } from 'react';
import { MOCK_USER } from '../constants';

type SettingsTab = 'account' | 'interests' | 'security' | 'notifications';

const Settings: React.FC = () => {
    const [activeSettingsTab, setActiveSettingsTab] = useState<SettingsTab>('account');
    const [interests, setInterests] = useState<string[]>(MOCK_USER.interests);
    const [newInterest, setNewInterest] = useState('');

    const addInterest = () => {
        if (newInterest.trim() && !interests.includes(newInterest.trim())) {
            setInterests([...interests, newInterest.trim()]);
            setNewInterest('');
        }
    };

    const removeInterest = (tag: string) => {
        setInterests(interests.filter(i => i !== tag));
    };

    return (
        <div id="settingsView" className="w-full">
            <section className="gradient-bg text-white py-16 rounded-2xl mb-8 text-center">
                <h2 className="text-3xl font-bold mb-4">Account <span className="text-yellow-300">Settings</span></h2>
                <p className="text-lg text-indigo-100">Manage your preferences and platform behavior</p>
            </section>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                {/* Settings Sidebar */}
                <div className="lg:col-span-1">
                    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                        <nav className="flex flex-col">
                            {[
                                { id: 'account', label: 'Hesap Bilgileri', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
                                { id: 'interests', label: 'İlgi Alanları', icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z' },
                                { id: 'security', label: 'Güvenlik', icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z' },
                                { id: 'notifications', label: 'Bildirimler', icon: 'M15 17h5l-5 5v-5zM9 7H4l5-5v5z' }
                            ].map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveSettingsTab(tab.id as SettingsTab)}
                                    className={`flex items-center space-x-3 px-6 py-4 text-sm font-medium border-l-4 transition-all ${activeSettingsTab === tab.id
                                            ? 'bg-indigo-50 border-indigo-600 text-indigo-600'
                                            : 'border-transparent text-gray-600 hover:bg-gray-50'
                                        }`}
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={tab.icon} />
                                    </svg>
                                    <span>{tab.label}</span>
                                </button>
                            ))}
                        </nav>
                    </div>
                </div>

                {/* Settings Content */}
                <div className="lg:col-span-3">
                    <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-sm min-h-[500px]">

                        {activeSettingsTab === 'account' && (
                            <div className="space-y-6 animate-fadeIn">
                                <h3 className="text-xl font-bold text-gray-800 border-b pb-4">Hesap Bilgileri</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <label className="block text-sm font-semibold text-gray-700 mb-2">Tam İsim</label>
                                        <input type="text" defaultValue={MOCK_USER.name} className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm transition-all" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-semibold text-gray-700 mb-2">Meslek / Ünvan</label>
                                        <input type="text" defaultValue={MOCK_USER.role} className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm transition-all" />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-2">Kurum / Üniversite</label>
                                    <input type="text" defaultValue={MOCK_USER.institution} className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm transition-all" />
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-2">Biyografi</label>
                                    <textarea
                                        rows={4}
                                        defaultValue={MOCK_USER.bio}
                                        className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none resize-none shadow-sm transition-all"
                                        placeholder="Kendinizden bahsedin..."
                                    />
                                </div>
                                <div className="flex justify-end pt-4">
                                    <button className="bg-indigo-600 text-white px-8 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-colors shadow-lg">Değişiklikleri Kaydet</button>
                                </div>
                            </div>
                        )}

                        {activeSettingsTab === 'interests' && (
                            <div className="space-y-6 animate-fadeIn">
                                <h3 className="text-xl font-bold text-gray-800 border-b pb-4">Akademik İlgi Alanları</h3>
                                <p className="text-sm text-gray-500">Platformun size daha iyi öneriler sunması için uzmanlık alanlarınızı belirleyin.</p>

                                <div className="flex flex-wrap gap-2 mb-6">
                                    {interests.map(tag => (
                                        <div key={tag} className="flex items-center space-x-1 px-4 py-1.5 bg-indigo-100 text-indigo-700 rounded-full text-sm font-bold">
                                            <span>{tag}</span>
                                            <button onClick={() => removeInterest(tag)} className="hover:text-indigo-900 ml-1">&times;</button>
                                        </div>
                                    ))}
                                </div>

                                <div className="flex space-x-2">
                                    <input
                                        type="text"
                                        value={newInterest}
                                        onChange={(e) => setNewInterest(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && addInterest()}
                                        placeholder="Yeni bir etiket ekle..."
                                        className="flex-1 px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm"
                                    />
                                    <button
                                        onClick={addInterest}
                                        className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-colors"
                                    >
                                        Ekle
                                    </button>
                                </div>
                            </div>
                        )}

                        {activeSettingsTab === 'security' && (
                            <div className="space-y-6 animate-fadeIn">
                                <h3 className="text-xl font-bold text-gray-800 border-b pb-4">Güvenlik ve Şifre Yenileme</h3>
                                <div className="max-w-md space-y-4">
                                    <div>
                                        <label className="block text-sm font-semibold text-gray-700 mb-2">Mevcut Şifre</label>
                                        <input type="password" placeholder="••••••••" className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" />
                                    </div>
                                    <div className="border-t pt-4">
                                        <label className="block text-sm font-semibold text-gray-700 mb-2">Yeni Şifre</label>
                                        <input type="password" placeholder="Yeni şifreniz" className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-semibold text-gray-700 mb-2">Yeni Şifre (Tekrar)</label>
                                        <input type="password" placeholder="Tekrar yazın" className="w-full px-4 py-2 border rounded-lg bg-white border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm" />
                                    </div>
                                    <div className="pt-4 flex justify-end">
                                        <button className="bg-indigo-600 text-white px-8 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-colors shadow-lg">Şifreyi Güncelle</button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeSettingsTab === 'notifications' && (
                            <div className="space-y-6 animate-fadeIn">
                                <h3 className="text-xl font-bold text-gray-800 border-b pb-4">Bildirim Tercihleri</h3>
                                <div className="space-y-4">
                                    {[
                                        { id: 'email-alert', label: 'E-posta Bildirimleri', desc: 'Yeni makale ve konferans duyurularını e-posta ile al.' },
                                        { id: 'weekly-digest', label: 'Haftalık Özet', desc: 'Haftanın en popüler içeriklerini içeren bir özet al.' },
                                        { id: 'funding-alert', label: 'Fon Çağrıları', desc: 'İlgi alanlarınıza uygun yeni fonlar çıktığında uyarıl.' },
                                        { id: 'chat-bot', label: 'AI Asistan Mesajları', desc: 'Asistanın size sunduğu özel hatırlatmalar.' }
                                    ].map(item => (
                                        <div key={item.id} className="flex items-center justify-between p-4 bg-white rounded-xl border border-gray-200 shadow-sm transition-all hover:bg-indigo-50/20">
                                            <div>
                                                <p className="font-bold text-gray-800">{item.label}</p>
                                                <p className="text-xs text-gray-500">{item.desc}</p>
                                            </div>
                                            <label className="relative inline-flex items-center cursor-pointer">
                                                <input type="checkbox" defaultChecked className="sr-only peer" />
                                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                                            </label>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;
