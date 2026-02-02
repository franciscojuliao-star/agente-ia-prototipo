import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getDisciplinas } from '../../services/api';
import Loading from '../../components/Loading';

export default function Disciplinas() {
  const [disciplinas, setDisciplinas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const carregar = async () => {
      try {
        const response = await getDisciplinas();
        setDisciplinas(response.data.disciplinas);
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
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Disciplinas Disponíveis</h1>

      {disciplinas.length === 0 ? (
        <div className="card text-center py-12">
          <span className="text-6xl">📚</span>
          <p className="mt-4 text-gray-600">Nenhuma disciplina com conteúdo disponível</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {disciplinas.map((disciplina) => (
            <Link
              key={disciplina.nome}
              to={`/aluno/disciplina/${encodeURIComponent(disciplina.nome)}`}
              className="card hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center gap-4">
                <span className="text-4xl">📖</span>
                <div>
                  <h3 className="font-semibold text-gray-800 text-lg">{disciplina.nome}</h3>
                  <p className="text-sm text-gray-500">{disciplina.num_conteudos} conteúdos disponíveis</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
