import { useState, useEffect } from 'react';
import { getConteudosPendentes, aprovarConteudo, rejeitarConteudo, deleteConteudo } from '../../services/api';
import Loading from '../../components/Loading';

export default function Pendentes() {
  const [conteudos, setConteudos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedConteudo, setSelectedConteudo] = useState(null);
  const [motivoRejeicao, setMotivoRejeicao] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const carregarConteudos = async () => {
    try {
      const response = await getConteudosPendentes();
      setConteudos(response.data.conteudos);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarConteudos();
  }, []);

  const handleAprovar = async (id) => {
    setActionLoading(true);
    try {
      await aprovarConteudo(id);
      carregarConteudos();
      setSelectedConteudo(null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao aprovar');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejeitar = async (id) => {
    if (!motivoRejeicao || motivoRejeicao.length < 10) {
      alert('Informe um motivo com pelo menos 10 caracteres');
      return;
    }
    setActionLoading(true);
    try {
      await rejeitarConteudo(id, motivoRejeicao);
      carregarConteudos();
      setSelectedConteudo(null);
      setMotivoRejeicao('');
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao rejeitar');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Excluir este conteúdo?')) return;
    try {
      await deleteConteudo(id);
      carregarConteudos();
      setSelectedConteudo(null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao excluir');
    }
  };

  const tipoIcons = { QUIZ: '📝', RESUMO: '📋', FLASHCARD: '🃏' };

  if (loading) return <Loading />;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Conteúdos Pendentes</h1>

      {conteudos.length === 0 ? (
        <div className="card text-center py-12">
          <span className="text-6xl">✅</span>
          <p className="mt-4 text-gray-600">Nenhum conteúdo pendente de aprovação</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-4">
            {conteudos.map((conteudo) => (
              <div
                key={conteudo.id}
                onClick={() => setSelectedConteudo(conteudo)}
                className={`card cursor-pointer transition-all hover:shadow-lg ${
                  selectedConteudo?.id === conteudo.id ? 'ring-2 ring-blue-500' : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{tipoIcons[conteudo.tipo]}</span>
                  <div>
                    <h3 className="font-semibold text-gray-800">{conteudo.topico}</h3>
                    <p className="text-sm text-gray-500">
                      {conteudo.disciplina} • {conteudo.tipo} • {new Date(conteudo.criado_em).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {selectedConteudo && (
            <div className="card sticky top-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="font-bold text-lg">{selectedConteudo.topico}</h2>
                  <p className="text-sm text-gray-500">{selectedConteudo.disciplina}</p>
                </div>
                <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm">
                  {selectedConteudo.status}
                </span>
              </div>

              <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto mb-4">
                <pre className="text-sm whitespace-pre-wrap">
                  {JSON.stringify(selectedConteudo.conteudo_json, null, 2)}
                </pre>
              </div>

              <div className="space-y-3">
                <button
                  onClick={() => handleAprovar(selectedConteudo.id)}
                  disabled={actionLoading}
                  className="btn-success w-full"
                >
                  {actionLoading ? 'Processando...' : '✓ Aprovar'}
                </button>

                <div>
                  <textarea
                    className="input mb-2"
                    placeholder="Motivo da rejeição (min. 10 caracteres)"
                    value={motivoRejeicao}
                    onChange={(e) => setMotivoRejeicao(e.target.value)}
                  />
                  <button
                    onClick={() => handleRejeitar(selectedConteudo.id)}
                    disabled={actionLoading}
                    className="btn-danger w-full"
                  >
                    ✗ Rejeitar
                  </button>
                </div>

                <button
                  onClick={() => handleDelete(selectedConteudo.id)}
                  className="w-full text-gray-500 hover:text-red-600 text-sm"
                >
                  Excluir permanentemente
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
