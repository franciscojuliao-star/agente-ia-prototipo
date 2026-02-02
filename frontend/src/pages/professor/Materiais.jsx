import { useState, useEffect } from 'react';
import { getMateriais, deleteMaterial, uploadPDF, uploadVideo, uploadLink, uploadTexto } from '../../services/api';
import Loading from '../../components/Loading';

export default function Materiais() {
  const [materiais, setMateriais] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [tipoUpload, setTipoUpload] = useState('pdf');
  const [formData, setFormData] = useState({ titulo: '', disciplina: '', url: '', texto: '' });
  const [arquivo, setArquivo] = useState(null);
  const [error, setError] = useState('');

  const carregarMateriais = async () => {
    try {
      const response = await getMateriais();
      setMateriais(response.data.materiais);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarMateriais();
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    setUploading(true);
    setError('');

    try {
      if (tipoUpload === 'pdf') {
        const data = new FormData();
        data.append('arquivo', arquivo);
        data.append('titulo', formData.titulo);
        data.append('disciplina', formData.disciplina);
        await uploadPDF(data);
      } else if (tipoUpload === 'video') {
        await uploadVideo({ url: formData.url, titulo: formData.titulo, disciplina: formData.disciplina });
      } else if (tipoUpload === 'link') {
        await uploadLink({ url: formData.url, titulo: formData.titulo, disciplina: formData.disciplina });
      } else {
        await uploadTexto({ texto: formData.texto, titulo: formData.titulo, disciplina: formData.disciplina });
      }

      setShowModal(false);
      setFormData({ titulo: '', disciplina: '', url: '', texto: '' });
      setArquivo(null);
      carregarMateriais();
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao fazer upload');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Tem certeza que deseja excluir este material?')) return;
    try {
      await deleteMaterial(id);
      carregarMateriais();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao excluir');
    }
  };

  const tipoIcons = { PDF: '📄', VIDEO: '🎬', LINK: '🔗', TEXTO: '📝' };

  if (loading) return <Loading />;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Meus Materiais</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">
          + Novo Material
        </button>
      </div>

      {materiais.length === 0 ? (
        <div className="card text-center py-12">
          <span className="text-6xl">📚</span>
          <p className="mt-4 text-gray-600">Nenhum material cadastrado</p>
          <button onClick={() => setShowModal(true)} className="btn-primary mt-4">
            Adicionar primeiro material
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {materiais.map((material) => (
            <div key={material.id} className="card flex justify-between items-center">
              <div className="flex items-center gap-4">
                <span className="text-3xl">{tipoIcons[material.tipo]}</span>
                <div>
                  <h3 className="font-semibold text-gray-800">{material.titulo}</h3>
                  <p className="text-sm text-gray-500">
                    {material.disciplina} • {material.num_chunks} chunks • {new Date(material.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <button onClick={() => handleDelete(material.id)} className="text-red-600 hover:text-red-700">
                Excluir
              </button>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg">
            <h2 className="text-xl font-bold mb-4">Novo Material</h2>

            <div className="flex gap-2 mb-4">
              {['pdf', 'video', 'link', 'texto'].map((tipo) => (
                <button
                  key={tipo}
                  onClick={() => setTipoUpload(tipo)}
                  className={`px-4 py-2 rounded-lg ${tipoUpload === tipo ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}
                >
                  {tipo.toUpperCase()}
                </button>
              ))}
            </div>

            <form onSubmit={handleUpload} className="space-y-4">
              {error && <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">{error}</div>}

              <div>
                <label className="label">Título</label>
                <input
                  type="text"
                  className="input"
                  value={formData.titulo}
                  onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
                  required
                />
              </div>

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

              {tipoUpload === 'pdf' && (
                <div>
                  <label className="label">Arquivo PDF</label>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setArquivo(e.target.files[0])}
                    className="input"
                    required
                  />
                </div>
              )}

              {(tipoUpload === 'video' || tipoUpload === 'link') && (
                <div>
                  <label className="label">{tipoUpload === 'video' ? 'URL do YouTube' : 'URL da página'}</label>
                  <input
                    type="url"
                    className="input"
                    value={formData.url}
                    onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                    required
                    placeholder="https://..."
                  />
                </div>
              )}

              {tipoUpload === 'texto' && (
                <div>
                  <label className="label">Conteúdo</label>
                  <textarea
                    className="input h-32"
                    value={formData.texto}
                    onChange={(e) => setFormData({ ...formData, texto: e.target.value })}
                    required
                    placeholder="Cole o texto aqui..."
                  />
                </div>
              )}

              <div className="flex gap-2 justify-end">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">
                  Cancelar
                </button>
                <button type="submit" className="btn-primary" disabled={uploading}>
                  {uploading ? 'Enviando...' : 'Enviar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
