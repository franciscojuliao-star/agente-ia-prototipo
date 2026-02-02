import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getQuiz, responderQuiz } from '../../services/api';
import Loading from '../../components/Loading';

export default function Quiz() {
  const { id } = useParams();
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(true);
  const [respostas, setRespostas] = useState({});
  const [resultado, setResultado] = useState(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    const carregar = async () => {
      try {
        const response = await getQuiz(id);
        setQuiz(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    carregar();
  }, [id]);

  const handleResposta = (idx, alternativa) => {
    setRespostas({ ...respostas, [idx]: alternativa });
  };

  const handleSubmit = async () => {
    setEnviando(true);
    try {
      const response = await responderQuiz(id, respostas);
      setResultado(response.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao enviar respostas');
    } finally {
      setEnviando(false);
    }
  };

  if (loading) return <Loading />;
  if (!quiz) return <div className="p-6">Quiz não encontrado</div>;

  const questoes = quiz.conteudo_json?.questoes || [];

  return (
    <div className="max-w-3xl mx-auto p-6">
      <Link to={`/aluno/disciplina/${encodeURIComponent(quiz.disciplina)}`} className="text-blue-600 hover:underline text-sm">
        ← Voltar
      </Link>

      <div className="mt-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-800">{quiz.topico}</h1>
        <p className="text-gray-500">{quiz.disciplina} • {questoes.length} questões</p>
        {quiz.watermark && <p className="text-xs text-gray-400 mt-1">{quiz.watermark}</p>}
      </div>

      {!resultado ? (
        <div className="space-y-6">
          {questoes.map((questao, idx) => (
            <div key={idx} className="card">
              <p className="font-medium text-gray-800 mb-4">
                <span className="text-blue-600">{idx + 1}.</span> {questao.pergunta}
              </p>

              <div className="space-y-2">
                {Object.entries(questao.alternativas).map(([letra, texto]) => (
                  <label
                    key={letra}
                    className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                      respostas[idx] === letra
                        ? 'bg-blue-100 border-2 border-blue-500'
                        : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                    }`}
                  >
                    <input
                      type="radio"
                      name={`questao-${idx}`}
                      checked={respostas[idx] === letra}
                      onChange={() => handleResposta(idx, letra)}
                      className="hidden"
                    />
                    <span className="font-bold text-gray-600">{letra.toUpperCase()})</span>
                    <span className="text-gray-700">{texto}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}

          <button
            onClick={handleSubmit}
            disabled={Object.keys(respostas).length < questoes.length || enviando}
            className="btn-primary w-full py-3 text-lg"
          >
            {enviando ? 'Enviando...' : 'Enviar Respostas'}
          </button>
        </div>
      ) : (
        <div className="card">
          <div className="text-center mb-6">
            <span className="text-6xl">{resultado.pontuacao >= 70 ? '🎉' : resultado.pontuacao >= 50 ? '👍' : '📚'}</span>
            <h2 className="text-3xl font-bold mt-4">
              {resultado.pontuacao.toFixed(0)}%
            </h2>
            <p className="text-gray-600">
              Você acertou {resultado.detalhes?.acertos} de {resultado.detalhes?.total} questões
            </p>
          </div>

          <div className="space-y-4">
            {resultado.detalhes?.questoes?.map((q, idx) => (
              <div key={idx} className={`p-4 rounded-lg ${q.acertou ? 'bg-green-50' : 'bg-red-50'}`}>
                <div className="flex items-center gap-2">
                  <span>{q.acertou ? '✅' : '❌'}</span>
                  <span className="font-medium">Questão {q.questao_idx + 1}</span>
                </div>
                <p className="text-sm mt-2">
                  Sua resposta: <strong>{q.resposta_aluno?.toUpperCase() || 'Não respondida'}</strong> |
                  Correta: <strong>{q.resposta_correta?.toUpperCase()}</strong>
                </p>
                {q.explicacao && <p className="text-sm text-gray-600 mt-2 italic">{q.explicacao}</p>}
              </div>
            ))}
          </div>

          <Link
            to={`/aluno/disciplina/${encodeURIComponent(quiz.disciplina)}`}
            className="btn-primary w-full mt-6 block text-center"
          >
            Voltar aos conteúdos
          </Link>
        </div>
      )}
    </div>
  );
}
