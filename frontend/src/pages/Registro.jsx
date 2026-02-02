import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Registro() {
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    senha: '',
    role: 'ALUNO',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { registrar } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await registrar(formData);
      navigate('/login', { state: { message: 'Conta criada com sucesso! Faça login.' } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao registrar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="card w-full max-w-md">
        <div className="text-center mb-8">
          <span className="text-5xl">📚</span>
          <h1 className="text-2xl font-bold text-gray-800 mt-4">Criar Conta</h1>
          <p className="text-gray-600">Registre-se no AVA RAG</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="label">Nome completo</label>
            <input
              type="text"
              className="input"
              value={formData.nome}
              onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
              required
              placeholder="Seu nome"
            />
          </div>

          <div>
            <label className="label">Email</label>
            <input
              type="email"
              className="input"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              placeholder="seu@email.com"
            />
          </div>

          <div>
            <label className="label">Senha</label>
            <input
              type="password"
              className="input"
              value={formData.senha}
              onChange={(e) => setFormData({ ...formData, senha: e.target.value })}
              required
              minLength={6}
              placeholder="Mínimo 6 caracteres"
            />
          </div>

          <div>
            <label className="label">Tipo de conta</label>
            <select
              className="select"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            >
              <option value="ALUNO">Aluno</option>
              <option value="PROFESSOR">Professor</option>
            </select>
          </div>

          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? 'Registrando...' : 'Criar conta'}
          </button>
        </form>

        <p className="mt-6 text-center text-gray-600">
          Já tem conta?{' '}
          <Link to="/login" className="text-blue-600 hover:underline">
            Fazer login
          </Link>
        </p>
      </div>
    </div>
  );
}
