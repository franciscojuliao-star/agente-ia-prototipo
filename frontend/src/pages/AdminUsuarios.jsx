import { useState, useEffect } from 'react';
import {
  getUsuarios,
  getUsuariosPendentes,
  aprovarUsuario,
  atualizarStatusUsuario,
  excluirUsuario,
  getEstatisticas,
} from '../services/api';

export default function AdminUsuarios() {
  const [usuarios, setUsuarios] = useState([]);
  const [pendentes, setPendentes] = useState([]);
  const [estatisticas, setEstatisticas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filtro, setFiltro] = useState('todos'); // todos, ativos, pendentes
  const [filtroRole, setFiltroRole] = useState(''); // '', PROFESSOR, ALUNO

  useEffect(() => {
    carregarDados();
  }, []);

  const carregarDados = async () => {
    setLoading(true);
    try {
      const [usuariosRes, pendentesRes, estatisticasRes] = await Promise.all([
        getUsuarios(),
        getUsuariosPendentes(),
        getEstatisticas(),
      ]);
      setUsuarios(usuariosRes.data);
      setPendentes(pendentesRes.data);
      setEstatisticas(estatisticasRes.data);
      setError('');
    } catch (err) {
      setError('Erro ao carregar dados');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAprovar = async (id) => {
    try {
      await aprovarUsuario(id);
      await carregarDados();
    } catch (err) {
      setError('Erro ao aprovar usuário');
      console.error(err);
    }
  };

  const handleDesativar = async (id) => {
    if (!window.confirm('Deseja desativar este usuário?')) return;
    try {
      await atualizarStatusUsuario(id, false);
      await carregarDados();
    } catch (err) {
      setError('Erro ao desativar usuário');
      console.error(err);
    }
  };

  const handleAtivar = async (id) => {
    try {
      await atualizarStatusUsuario(id, true);
      await carregarDados();
    } catch (err) {
      setError('Erro ao ativar usuário');
      console.error(err);
    }
  };

  const handleExcluir = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este usuário? Esta ação é irreversível.')) return;
    try {
      await excluirUsuario(id);
      await carregarDados();
    } catch (err) {
      setError('Erro ao excluir usuário');
      console.error(err);
    }
  };

  const usuariosFiltrados = usuarios.filter((u) => {
    if (filtro === 'ativos' && !u.ativo) return false;
    if (filtro === 'pendentes' && u.ativo) return false;
    if (filtroRole && u.role !== filtroRole) return false;
    return true;
  });

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Administração de Usuários</h1>

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Cards de estatísticas */}
      {estatisticas && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-500 text-sm">Total de Usuários</p>
            <p className="text-2xl font-bold text-gray-900">{estatisticas.total_usuarios}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-500 text-sm">Usuários Ativos</p>
            <p className="text-2xl font-bold text-green-600">{estatisticas.usuarios_ativos}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-500 text-sm">Pendentes</p>
            <p className="text-2xl font-bold text-yellow-600">{estatisticas.usuarios_pendentes}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-500 text-sm">Professores</p>
            <p className="text-2xl font-bold text-blue-600">{estatisticas.total_professores}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-500 text-sm">Alunos</p>
            <p className="text-2xl font-bold text-purple-600">{estatisticas.total_alunos}</p>
          </div>
        </div>
      )}

      {/* Usuários pendentes */}
      {pendentes.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-yellow-800 mb-4">
            Usuários Aguardando Aprovação ({pendentes.length})
          </h2>
          <div className="space-y-3">
            {pendentes.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between bg-white p-4 rounded-lg shadow-sm"
              >
                <div>
                  <p className="font-medium text-gray-900">{user.nome}</p>
                  <p className="text-sm text-gray-500">{user.email}</p>
                  <span
                    className={`inline-block px-2 py-1 text-xs rounded-full mt-1 ${
                      user.role === 'PROFESSOR'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-purple-100 text-purple-800'
                    }`}
                  >
                    {user.role}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleAprovar(user.id)}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition"
                  >
                    Aprovar
                  </button>
                  <button
                    onClick={() => handleExcluir(user.id)}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
                  >
                    Recusar
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="flex gap-4 mb-6">
        <select
          value={filtro}
          onChange={(e) => setFiltro(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="todos">Todos</option>
          <option value="ativos">Ativos</option>
          <option value="pendentes">Pendentes</option>
        </select>
        <select
          value={filtroRole}
          onChange={(e) => setFiltroRole(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Todos os tipos</option>
          <option value="PROFESSOR">Professores</option>
          <option value="ALUNO">Alunos</option>
        </select>
        <button
          onClick={carregarDados}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
        >
          Atualizar
        </button>
      </div>

      {/* Tabela de usuários */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Usuário
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tipo
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Criado em
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ações
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {usuariosFiltrados.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <p className="font-medium text-gray-900">{user.nome}</p>
                    <p className="text-sm text-gray-500">{user.email}</p>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-block px-2 py-1 text-xs rounded-full ${
                      user.role === 'PROFESSOR'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-purple-100 text-purple-800'
                    }`}
                  >
                    {user.role}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-block px-2 py-1 text-xs rounded-full ${
                      user.ativo
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {user.ativo ? 'Ativo' : 'Pendente'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(user.created_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex justify-end gap-2">
                    {user.ativo ? (
                      <button
                        onClick={() => handleDesativar(user.id)}
                        className="text-yellow-600 hover:text-yellow-900"
                      >
                        Desativar
                      </button>
                    ) : (
                      <button
                        onClick={() => handleAtivar(user.id)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Ativar
                      </button>
                    )}
                    <button
                      onClick={() => handleExcluir(user.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Excluir
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {usuariosFiltrados.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            Nenhum usuário encontrado com os filtros selecionados.
          </div>
        )}
      </div>
    </div>
  );
}
