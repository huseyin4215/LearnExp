import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { userStorage } from '../services/api';
import type { User } from '../services/api';

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    login: (user: User) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    isAuthenticated: false,
    login: () => { },
    logout: () => { },
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(() => userStorage.getUser());

    const isAuthenticated = !!user;

    const login = useCallback((userData: User) => {
        userStorage.setUser(userData);
        setUser(userData);
    }, []);

    const logout = useCallback(() => {
        userStorage.removeUser();
        userStorage.removeToken();
        setUser(null);
    }, []);

    // Sync with localStorage on mount
    useEffect(() => {
        const stored = userStorage.getUser();
        if (stored) setUser(stored);
    }, []);

    return (
        <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;
