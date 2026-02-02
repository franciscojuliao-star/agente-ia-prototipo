import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getResumo } from '../../services/api';
import Loading from '../../components/Loading';

export default function Resumo() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const carregar = async () => {
      try {
        const response = await getResumo(id);
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
  if (!data) return <div className="p-6">Resumo não encontrado</div>;

  const resumo = data.conteudo_json?.resumo || {};

  return (
    <div className="max-w-3xl mx-auto p-6">
      <Link to={`/aluno/disciplina/${encodeURIComponent(data.disciplina)}`} className="text-blue-600 hover:underline text-sm">
        ← Voltar
      </Link>

      <div className="mt-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-800">{data.topico}</h1>
        <p className="text-gray-500">{data.disciplina}</p>
        {data.watermark && <p className="text-xs text-gray-400 mt-1">{data.watermark}</p>}
      </div>

      <div className="card space-y-6">
        {resumo.introducao && (
          <div>
            <h2 className="font-bold text-lg text-blue-600 mb-2">📖 Introdução</h2>
            <p className="text-gray-700 leading-relaxed">{resumo.introducao}</p>
          </div>
        )}

        {resumo.desenvolvimento?.length > 0 && (
          <div>
            <h2 className="font-bold text-lg text-blue-600 mb-2">📝 Pontos-Chave</h2>
            <ul className="space-y-2">
              {resumo.desenvolvimento.map((ponto, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-blue-600">•</span>
                  <span className="text-gray-700">{ponto}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {resumo.exemplos?.length > 0 && (
          <div>
            <h2 className="font-bold text-lg text-blue-600 mb-2">💡 Exemplos</h2>
            <ul className="space-y-2">
              {resumo.exemplos.map((exemplo, i) => (
                <li key={i} className="bg-gray-50 p-3 rounded-lg text-gray-700">{exemplo}</li>
              ))}
            </ul>
          </div>
        )}

        {resumo.conclusao && (
          <div>
            <h2 className="font-bold text-lg text-blue-600 mb-2">🎯 Conclusão</h2>
            <p className="text-gray-700 leading-relaxed">{resumo.conclusao}</p>
          </div>
        )}

        {resumo.trechos_fonte?.length > 0 && (
          <div className="border-t pt-4">
            <h3 className="font-medium text-gray-600 mb-2">Fontes do material:</h3>
            <ul className="text-sm text-gray-500 space-y-1">
              {resumo.trechos_fonte.map((fonte, i) => (
                <li key={i} className="italic">"{fonte}"</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
