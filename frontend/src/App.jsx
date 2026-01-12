import { useState, useEffect, useCallback } from 'react';
import { getDocuments, searchDocuments, uploadDocument } from './api';
import Constellation from './components/Constellation';

const API_BASE = 'http://localhost:8000';

function App() {
  const [documents, setDocuments] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'constellation'

  const fetchDocuments = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getDocuments();
      setDocuments(data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSearch = useCallback(async (q) => {
    if (!q.trim()) {
      fetchDocuments();
      return;
    }
    try {
      setLoading(true);
      const data = await searchDocuments(q);
      setDocuments(data);
    } catch (error) {
      console.error('Error searching documents:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchDocuments]);

  useEffect(() => {
    const timer = setTimeout(() => {
      handleSearch(searchQuery);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchQuery, handleSearch]);

  // Polling for processing items
  useEffect(() => {
    const hasProcessingItems = documents.some(doc => !doc.tags || doc.tags.length === 0 || !doc.caption);

    if (hasProcessingItems) {
      const pollTimer = setInterval(() => {
        if (!searchQuery) {
          fetchDocuments();
        } else {
          handleSearch(searchQuery);
        }
      }, 3000);

      return () => clearInterval(pollTimer);
    }
  }, [documents, searchQuery, fetchDocuments, handleSearch]);

  const onFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      setIsUploading(true);
      await uploadDocument(file);
      fetchDocuments();
    } catch (error) {
      alert('Upload failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsUploading(false);
    }
  };

  const getImageUrl = (relPath) => `${API_BASE}/data/${relPath}`;

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-200 font-sans selection:bg-indigo-500/30">
      {/* Header */}
      <header className="sticky top-0 z-40 w-full backdrop-blur-md bg-slate-900/70 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">EYE</h1>
          </div>

          <div className="flex-1 max-w-md mx-8">
            <div className="relative group">
              <input
                type="text"
                placeholder="Search images, tags, captions..."
                className="w-full bg-slate-800/50 border border-slate-700/50 rounded-2xl py-2.5 pl-11 pr-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all group-hover:border-slate-600"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <svg className="absolute left-4 top-3 w-5 h-5 text-slate-500 group-focus-within:text-indigo-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* View Mode Toggle */}
            <div className="flex items-center gap-2 bg-slate-800/50 rounded-xl p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-4 py-2 rounded-lg transition-all ${
                  viewMode === 'grid'
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Grid
              </button>
              <button
                onClick={() => setViewMode('constellation')}
                className={`px-4 py-2 rounded-lg transition-all ${
                  viewMode === 'constellation'
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Graph
              </button>
            </div>

            <label className="cursor-pointer group">
              <input type="file" className="hidden" onChange={onFileChange} accept="image/*" />
              <div className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg shadow-indigo-600/20 active:scale-95">
                {isUploading ? (
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                )}
                <span>{isUploading ? 'Uploading...' : 'Upload'}</span>
              </div>
            </label>
          </div>
        </div>
      </header>

      {viewMode === 'constellation' ? (
        <Constellation />
      ) : (
        <main className="max-w-7xl mx-auto px-6 py-10">
          {loading && documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-32 opacity-50">
              <div className="w-12 h-12 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
              <p>Loading your visual memory...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-32 bg-slate-900/40 rounded-3xl border border-dashed border-slate-800">
              <p className="text-slate-500 text-lg">No images found. Try uploading one!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="group relative bg-slate-900/50 rounded-2xl overflow-hidden border border-slate-800 hover:border-indigo-500/50 transition-all hover:-translate-y-1 cursor-pointer"
                  onClick={() => setSelectedDoc(doc)}
                >
                  <div className="aspect-square overflow-hidden bg-slate-950">
                    <img
                      src={getImageUrl(doc.relative_path)}
                      alt={doc.filename}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      loading="lazy"
                    />
                  </div>
                  <div className="p-4 bg-gradient-to-t from-slate-950/80 to-transparent">
                    <p className="text-sm font-medium truncate text-slate-300">{doc.filename}</p>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {doc.tags.slice(0, 3).map((tag, i) => (
                        <span key={i} className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                          {tag}
                        </span>
                      ))}
                      {doc.tags.length > 3 && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-500">
                          +{doc.tags.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      )}

      {/* Detail Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 sm:p-10">
          <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => setSelectedDoc(null)} />
          <div className="relative w-full max-w-5xl bg-slate-900 rounded-3xl overflow-hidden shadow-2xl border border-slate-800 flex flex-col md:flex-row max-h-[90vh]">
            <button
              className="absolute top-4 right-4 z-10 p-2 bg-slate-950/50 hover:bg-slate-950 rounded-full text-slate-400 hover:text-white transition-colors"
              onClick={() => setSelectedDoc(null)}
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <div className="md:w-2/3 bg-black flex items-center justify-center overflow-hidden">
              <img
                src={getImageUrl(selectedDoc.relative_path)}
                alt={selectedDoc.filename}
                className="max-w-full max-h-full object-contain"
              />
            </div>

            <div className="md:w-1/3 p-8 overflow-y-auto">
              <div className="mb-6">
                <h2 className="text-xl font-bold text-white mb-1 truncate">{selectedDoc.filename}</h2>
              </div>

              <div className="mb-8">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">AI Analysis</h3>
                <p className="text-slate-300 italic leading-relaxed text-sm bg-slate-800/50 p-4 rounded-xl border border-slate-700/30">
                  {selectedDoc.caption || 'AI is still processing this image...'}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Detected Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedDoc.tags.map((tag, i) => (
                    <span key={i} className="px-3 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-medium">
                      {tag}
                    </span>
                  ))}
                  {selectedDoc.tags.length === 0 && (
                    <span className="text-slate-600 text-sm italic">Processing tags...</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;