import React, { useState } from 'react';
import { MOCK_USER } from '../constants';

const ActivityItem: React.FC<{ text: string, time: string, dotColor: string }> = ({ text, time, dotColor }) => (
    <div className="flex items-start space-x-3">
        <div className={`w-2 h-2 ${dotColor} rounded-full mt-2`}></div>
        <div>
            <p className="text-sm text-gray-800">{text}</p>
            <p className="text-xs text-gray-500">{time}</p>
        </div>
    </div>
);

const Profile: React.FC = () => {
    const [interests] = useState<string[]>(MOCK_USER.interests);

    return (
        <div id="profileView">
            <section className="gradient-bg text-white py-16 rounded-2xl mb-8 text-center">
                <div className="w-24 h-24 bg-white bg-opacity-20 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl font-bold">AK</div>
                <h2 className="text-3xl font-bold mb-2">Ahmet <span className="text-yellow-300">Kaya</span></h2>
                <p className="text-lg text-indigo-100">{MOCK_USER.role}</p>
                <p className="text-base text-indigo-200">{MOCK_USER.institution}</p>
            </section>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white rounded-xl border border-gray-200 p-8">
                    <h3 className="text-xl font-semibold mb-6">About</h3>
                    <p className="text-gray-600 mb-4">{MOCK_USER.bio}</p>
                    <div className="flex flex-wrap gap-2">
                        {interests.map(i => <span key={i} className="px-3 py-1 bg-indigo-100 text-indigo-800 text-sm rounded-full">{i}</span>)}
                    </div>
                </div>
                <div className="bg-white rounded-xl border border-gray-200 p-8">
                    <h3 className="text-xl font-semibold mb-6">Recent Activity</h3>
                    <div className="space-y-4">
                        <ActivityItem text="Saved article: 'Transformer-Based Models...'" time="2 hours ago" dotColor="bg-blue-500" />
                        <ActivityItem text="Bookmarked conference: 'ICML 2024'" time="1 day ago" dotColor="bg-purple-500" />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;
