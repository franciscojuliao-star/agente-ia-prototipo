import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getMateriaisDisciplina, buscarSemantica } from '../../services/api';
import Loading from '../../components/Loading';

export default function Conteudos() {
  const { disciplina } = useParams();
  const [conteudos, setConteudos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtro, setFiltro] = useState('');
  const [busca, setBusca] = useState('');
  const [resultadosBusca, setResultadosBusca] = useState(null);
  const [buscando, setBuscando] = useState(false);

  useEffect(() => {
    const carregar = async () => {
      try {
        const response = await getMateriaisDisciplina(disciplina, filtro || undefined);
        setConteudos(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    carregar();
  }, [disciplina, filtro]);

  const handleBusca = async (e) => {
    e.preventDefault();
    if (!busca.trim()) return;

    setBuscando(true);
    try {
      const response = await buscarSemantica(disciplina, busca);
      setResultadosBusca(response.data);
    } catch (err) {
      console.error(err);
    } finally {
      setBuscando(false);
    }
  };

  const tipoIcons = { QUIZ: '📝', RESUMO: '📋', FLASHCARD: '🃏' };

  if (loading) return <Loading />;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <Link to="/aluno/disciplinas" className="text-blue-600 hover:underline text-sm">
          ← Voltar às disciplinas
        </Link>
        <h1 className="text-2xl font-bold text-gray-800 mt-2">{decodeURIComponent(disciplina)}</h1>
      </div>

      {/* Busca Semântica */}
      <div className="card mb-6">
        <h2 className="font-semibold text-gray-800 mb-3">🔍 Busca Inteligente</h2>
        <form onSubmit={handleBusca} className="flex gap-2">
          <input
            type="text"
            className="input flex-1"
            placeholder="Faça uma pergunta sobre o conteúdo..."
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
          />
          <button type="submit" className="btn-primary" disabled={buscando}>
            {buscando ? 'Buscando...' : 'Buscar'}
          </button>
        </form>

        {resultadosBusca && (
          <div className="mt-4 space-y-3">
            <h3 className="font-medium text-gray-700">Resultados para: "{resultadosBusca.pergunta}"</h3>
            {resultadosBusca.trechos.map((trecho, i) => (
              <div key={i} className="bg-gray-50 rounded-lg p-3">
                <p className="text-sm text-gray-700">{trecho.texto}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {trecho.titulo} • Relevância: {trecho.relevancia}%
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Filtros */}
      <div className="flex gap-2 mb-4">
        {['', 'QUIZ', 'RESUMO', 'FLASHCARD'].map((tipo) => (
          <button
            key={tipo}
            onClick={() => setFiltro(tipo)}
            className={`px-4 py-2 rounded-lg text-sm ${
              filtro === tipo ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            {tipo || 'Todos'}
          </button>
        ))}
      </div>

      {/* Lista de Conteúdos */}
      {conteudos.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-600">Nenhum conteúdo encontrado</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {conteudos.map((conteudo) => (
            <Link
              key={conteudo.id}
              to={`/aluno/${conteudo.tipo.toLowerCase()}/${conteudo.id}`}
              className="card hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center gap-4">
                <span className="text-3xl">{tipoIcons[conteudo.tipo]}</span>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-800">{conteudo.topico}</h3>
                  <p className="text-sm text-gray-500">
                    {conteudo.tipo} • {new Date(conteudo.aprovado_em).toLocaleDateString()}
                  </p>
                </div>
                <span className="text-blue-600">Acessar →</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
