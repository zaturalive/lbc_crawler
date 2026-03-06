import { createContext, useContext, useState, useEffect } from 'react';
import { getMe } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('fmc_token'));

  useEffect(() => {
    if (token) {
      getMe(token)
        .then(u => { if (u) setUser(u); })
        .catch(() => {
          setToken(null);
          setUser(null);
          localStorage.removeItem('fmc_token');
        });
    }
  }, [token]);

  const login = (accessToken, userData) => {
    localStorage.setItem('fmc_token', accessToken);
    setToken(accessToken);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('fmc_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
