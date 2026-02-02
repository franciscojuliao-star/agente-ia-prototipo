import { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, registrar as apiRegistrar } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email, senha) => {
    const response = await apiLogin(email, senha);
    const { access_token, refresh_token } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    // Decodificar token para pegar dados do usuário
    const payload = JSON.parse(atob(access_token.split('.')[1]));
    const userData = {
      id: payload.sub,
      email: payload.email,
      role: payload.role,
    };

    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);

    return userData;
  };

  const registrar = async (data) => {
    const response = await apiRegistrar(data);
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const isProfessor = user?.role === 'PROFESSOR';
  const isAluno = user?.role === 'ALUNO';

  return (
    <AuthContext.Provider value={{ user, login, logout, registrar, loading, isProfessor, isAluno }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
