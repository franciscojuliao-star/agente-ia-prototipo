import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Loading from './components/Loading';

// Pages
import Login from './pages/Login';
import Registro from './pages/Registro';
import Materiais from './pages/professor/Materiais';
import GerarConteudo from './pages/professor/GerarConteudo';
import Pendentes from './pages/professor/Pendentes';
import Disciplinas from './pages/aluno/Disciplinas';
import Conteudos from './pages/aluno/Conteudos';
import Quiz from './pages/aluno/Quiz';
import Flashcards from './pages/aluno/Flashcards';
import Resumo from './pages/aluno/Resumo';
import Historico from './pages/aluno/Historico';

function PrivateRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();

  if (loading) return <Loading />;

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={user.role === 'PROFESSOR' ? '/professor/materiais' : '/aluno/disciplinas'} />;
  }

  return (
    <>
      <Navbar />
      <main>{children}</main>
    </>
  );
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) return <Loading />;

  if (user) {
    return <Navigate to={user.role === 'PROFESSOR' ? '/professor/materiais' : '/aluno/disciplinas'} />;
  }

  return children;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/registro" element={<PublicRoute><Registro /></PublicRoute>} />

      {/* Professor Routes */}
      <Route path="/professor/materiais" element={<PrivateRoute allowedRoles={['PROFESSOR']}><Materiais /></PrivateRoute>} />
      <Route path="/professor/gerar" element={<PrivateRoute allowedRoles={['PROFESSOR']}><GerarConteudo /></PrivateRoute>} />
      <Route path="/professor/pendentes" element={<PrivateRoute allowedRoles={['PROFESSOR']}><Pendentes /></PrivateRoute>} />

      {/* Aluno Routes */}
      <Route path="/aluno/disciplinas" element={<PrivateRoute allowedRoles={['ALUNO']}><Disciplinas /></PrivateRoute>} />
      <Route path="/aluno/disciplina/:disciplina" element={<PrivateRoute allowedRoles={['ALUNO']}><Conteudos /></PrivateRoute>} />
      <Route path="/aluno/quiz/:id" element={<PrivateRoute allowedRoles={['ALUNO']}><Quiz /></PrivateRoute>} />
      <Route path="/aluno/flashcard/:id" element={<PrivateRoute allowedRoles={['ALUNO']}><Flashcards /></PrivateRoute>} />
      <Route path="/aluno/resumo/:id" element={<PrivateRoute allowedRoles={['ALUNO']}><Resumo /></PrivateRoute>} />
      <Route path="/aluno/historico" element={<PrivateRoute allowedRoles={['ALUNO']}><Historico /></PrivateRoute>} />

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/login" />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-gray-100">
          <AppRoutes />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}
