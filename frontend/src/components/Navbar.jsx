import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout, isProfessor } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16 items-center">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">📚</span>
            <span className="font-bold text-xl text-gray-800">AVA RAG</span>
          </Link>

          {user && (
            <div className="flex items-center gap-6">
              <div className="flex gap-4">
                {isProfessor ? (
                  <>
                    <Link to="/professor/materiais" className="text-gray-600 hover:text-blue-600">
                      Materiais
                    </Link>
                    <Link to="/professor/gerar" className="text-gray-600 hover:text-blue-600">
                      Gerar Conteúdo
                    </Link>
                    <Link to="/professor/pendentes" className="text-gray-600 hover:text-blue-600">
                      Pendentes
                    </Link>
                  </>
                ) : (
                  <>
                    <Link to="/aluno/disciplinas" className="text-gray-600 hover:text-blue-600">
                      Disciplinas
                    </Link>
                    <Link to="/aluno/historico" className="text-gray-600 hover:text-blue-600">
                      Histórico
                    </Link>
                  </>
                )}
              </div>

              <div className="flex items-center gap-3 border-l pl-6">
                <span className="text-sm text-gray-600">
                  {user.email}
                  <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${isProfessor ? 'bg-purple-100 text-purple-700' : 'bg-green-100 text-green-700'}`}>
                    {user.role}
                  </span>
                </span>
                <button onClick={handleLogout} className="text-red-600 hover:text-red-700 text-sm">
                  Sair
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
