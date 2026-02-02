import { useState, useEffect } from 'react';
import { gerarQuiz, gerarResumo, gerarFlashcards, getMateriais } from '../../services/api';

export default function GerarConteudo() {
  const [tipo, setTipo] = useState('quiz');
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    topico: '',
    disciplina: '',
    num_questoes: 5,
    num_cards: 10,
    dificuldade: 'medio',
    tamanho: 'medio',
  });
  const [materiais, setMateriais] = useState([]);
  const [selectedMateriais, setSelectedMateriais] = useState([]);

  useEffect(() => {
    const fetchMateriais = async () => {
      try {
        const response = await getMateriais();
        setMateriais(response.data.materiais || []);
      } catch (error) {
        console.error('Erro ao buscar materiais:', error);
        setError('Falha ao carregar a lista de materiais.');
      }
    };
    fetchMateriais();
  }, []);

  const handleMaterialChange = (e) => {
    const options = e.target.options;
    const value = [];
    for (let i = 0, l = options.length; i < l; i++) {
      if (options[i].selected) {
        value.push(options[i].value);
      }
    }
    setSelectedMateriais(value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResultado(null);

    try {
      let response;
      const data = {
        topico: formData.topico,
        disciplina: formData.disciplina,
        material_ids: selectedMateriais.length > 0 ? selectedMateriais : undefined,
      };

      if (tipo === 'quiz') {
        response = await gerarQuiz({ ...data, num_questoes: formData.num_questoes, dificuldade: formData.dificuldade });
      } else if (tipo === 'resumo') {
        response = await gerarResumo({ ...data, tamanho: formData.tamanho });
      } else {
        response = await gerarFlashcards({ ...data, num_cards: formData.num_cards });
      }

      setResultado(response.data);
    } catch (err) {
      // Trata erro de validação (422) e outros erros
      if (err.response?.data?.detail) {
        // Se 'detail' for um array (comum em erros 422), formata a mensagem.
        if (Array.isArray(err.response.data.detail)) {
          const errorMsg = err.response.data.detail.map(d => `${d.loc[1]}: ${d.msg}`).join('; ');
          setError(errorMsg);
        } else {
          // Se for uma string
          setError(err.response.data.detail);
        }
      } else {
        setError('Erro ao gerar conteúdo. Verifique a conexão com a API e se o Ollama está rodando.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Gerar Conteúdo com IA</h1>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex gap-2 mb-4">
            {[
              { id: 'quiz', label: '📝 Quiz', icon: '📝' },
              { id: 'resumo', label: '📋 Resumo', icon: '📋' },
              { id: 'flashcard', label: '🃏 Flashcards', icon: '🃏' },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTipo(t.id)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                  tipo === t.id ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">{error}</div>}

            <div>
              <label className="label">Disciplina</label>
              <input
                type="text"
                className="input"
                value={formData.disciplina}
                onChange={(e) => setFormData({ ...formData, disciplina: e.target.value })}
                required
                placeholder="Ex: Algoritmos"
              />
            </div>

            <div>
              <label className="label">Tópico</label>
              <input
                type="text"
                className="input"
                value={formData.topico}
                onChange={(e) => setFormData({ ...formData, topico: e.target.value })}
                required
                placeholder="Ex: Estruturas de repetição"
              />
            </div>

            <div>
              <label className="label">Filtrar por Materiais (opcional)</label>
              <select
                multiple
                className="input h-32"
                value={selectedMateriais}
                onChange={handleMaterialChange}
              >
                {materiais.map((material) => (
                  <option key={material.id} value={material.id}>
                    {material.titulo} ({material.disciplina})
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Segure Ctrl (ou Cmd) para selecionar múltiplos materiais.
              </p>
            </div>


            {tipo === 'quiz' && (
              <>
                <div>
                  <label className="label">Número de questões</label>
                  <input
                    type="number"
                    className="input"
                    min={1}
                    max={20}
                    value={formData.num_questoes}
                    onChange={(e) => setFormData({ ...formData, num_questoes: parseInt(e.target.value) })}
                  />
                </div>
                <div>
                  <label className="label">Dificuldade</label>
                  <select
                    className="select"
                    value={formData.dificuldade}
                    onChange={(e) => setFormData({ ...formData, dificuldade: e.target.value })}
                  >
                    <option value="facil">Fácil</option>
                    <option value="medio">Médio</option>
                    <option value="dificil">Difícil</option>
                  </select>
                </div>
              </>
            )}

            {tipo === 'resumo' && (
              <div>
                <label className="label">Tamanho</label>
                <select
                  className="select"
                  value={formData.tamanho}
                  onChange={(e) => setFormData({ ...formData, tamanho: e.target.value })}
                >
                  <option value="curto">Curto</option>
                  <option value="medio">Médio</option>
                  <option value="longo">Longo</option>
                </select>
              </div>
            )}

            {tipo === 'flashcard' && (
              <div>
                <label className="label">Número de flashcards</label>
                <input
                  type="number"
                  className="input"
                  min={1}
                  max={50}
                  value={formData.num_cards}
                  onChange={(e) => setFormData({ ...formData, num_cards: parseInt(e.target.value) })}
                />
              </div>
            )}

            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin">⏳</span> Gerando com IA...
                </span>
              ) : (
                'Gerar Conteúdo'
              )}
            </button>
          </form>
        </div>

        <div className="card">
          <h2 className="font-semibold text-gray-800 mb-4">Resultado</h2>

          {loading && (
            <div className="flex flex-col items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">A IA está gerando o conteúdo...</p>
              <p className="text-sm text-gray-500">Isso pode levar alguns segundos</p>
            </div>
          )}

          {!loading && !resultado && (
            <div className="text-center py-12 text-gray-500">
              <span className="text-4xl">🤖</span>
              <p className="mt-2">O resultado aparecerá aqui</p>
            </div>
          )}

          {resultado && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className={`px-3 py-1 rounded-full text-sm ${
                  resultado.status === 'AGUARDANDO_APROVACAO' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'
                }`}>
                  {resultado.status}
                </span>
                <span className="text-sm text-gray-500">{resultado.tipo}</span>
              </div>

              <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                <pre className="text-sm whitespace-pre-wrap">
                  {JSON.stringify(resultado.conteudo_json, null, 2)}
                </pre>
              </div>

              <p className="text-sm text-gray-600">
                Vá para <strong>Pendentes</strong> para aprovar este conteúdo.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
