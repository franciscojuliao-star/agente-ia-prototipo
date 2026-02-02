import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getFlashcards } from '../../services/api';
import Loading from '../../components/Loading';

export default function Flashcards() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);

  useEffect(() => {
    const carregar = async () => {
      try {
        const response = await getFlashcards(id);
        setData(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    carregar();
  }, [id]);

  if (loading) return <Loading />;
  if (!data) return <div className="p-6">Flashcards não encontrados</div>;

  const flashcards = data.conteudo_json?.flashcards || [];
  const current = flashcards[currentIndex];

  const next = () => {
    setFlipped(false);
    setCurrentIndex((i) => (i + 1) % flashcards.length);
  };

  const prev = () => {
    setFlipped(false);
    setCurrentIndex((i) => (i - 1 + flashcards.length) % flashcards.length);
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <Link to={`/aluno/disciplina/${encodeURIComponent(data.disciplina)}`} className="text-blue-600 hover:underline text-sm">
        ← Voltar
      </Link>

      <div className="mt-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-800">{data.topico}</h1>
        <p className="text-gray-500">{data.disciplina} • {flashcards.length} flashcards</p>
        {data.watermark && <p className="text-xs text-gray-400 mt-1">{data.watermark}</p>}
      </div>

      <div className="text-center mb-4">
        <span className="text-gray-600">{currentIndex + 1} / {flashcards.length}</span>
      </div>

      <div
        onClick={() => setFlipped(!flipped)}
        className="card min-h-64 flex items-center justify-center cursor-pointer hover:shadow-lg transition-all"
      >
        <div className="text-center p-6">
          {!flipped ? (
            <>
              <span className="text-4xl mb-4 block">❓</span>
              <p className="text-xl text-gray-800">{current?.frente}</p>
              <p className="text-sm text-gray-500 mt-4">Clique para ver a resposta</p>
            </>
          ) : (
            <>
              <span className="text-4xl mb-4 block">💡</span>
              <p className="text-xl text-gray-800">{current?.verso}</p>
              {current?.trecho_fonte && (
                <p className="text-sm text-gray-500 mt-4 italic">"{current.trecho_fonte}"</p>
              )}
            </>
          )}
        </div>
      </div>

      <div className="flex justify-between mt-6">
        <button onClick={prev} className="btn-secondary">
          ← Anterior
        </button>
        <button onClick={() => setFlipped(!flipped)} className="btn-primary">
          {flipped ? 'Ver Pergunta' : 'Ver Resposta'}
        </button>
        <button onClick={next} className="btn-secondary">
          Próximo →
        </button>
      </div>

      <div className="flex justify-center gap-1 mt-6">
        {flashcards.map((_, i) => (
          <button
            key={i}
            onClick={() => { setCurrentIndex(i); setFlipped(false); }}
            className={`w-3 h-3 rounded-full ${i === currentIndex ? 'bg-blue-600' : 'bg-gray-300'}`}
          />
        ))}
      </div>
    </div>
  );
}
