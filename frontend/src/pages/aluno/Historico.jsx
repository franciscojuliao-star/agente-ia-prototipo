import { useState, useEffect } from 'react';
import { getHistorico } from '../../services/api';
import Loading from '../../components/Loading';

export default function Historico() {
  const [tentativas, setTentativas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const carregar = async () => {
      try {
        const response = await getHistorico();
        setTentativas(response.data.tentativas);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    carregar();
  }, []);

  if (loading) return <Loading />;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Meu Histórico</h1>

      {tentativas.length === 0 ? (
        <div className="card text-center py-12">
          <span className="text-6xl">📊</span>
          <p className="mt-4 text-gray-600">Você ainda não respondeu nenhum quiz</p>
        </div>
      ) : (
        <div className="space-y-4">
          {tentativas.map((tentativa) => (
            <div key={tentativa.id} className="card">
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-semibold text-gray-800">Quiz #{tentativa.conteudo_id.slice(0, 8)}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(tentativa.created_at).toLocaleString()}
                  </p>
                </div>
                <div className={`text-2xl font-bold ${
                  tentativa.pontuacao >= 70 ? 'text-green-600' :
                  tentativa.pontuacao >= 50 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {tentativa.pontuacao.toFixed(0)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
