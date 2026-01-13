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
  const [viewMode, setViewMode] = useState('grid');

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

  useEffect(() => {
    const hasProcessingItems = documents.some(doc => !doc.tags || doc.tags.length === 0 || !doc.caption);
    if (hasProcessingItems) {
      const pollTimer = setInterval(() => {
        if (!searchQuery) fetchDocuments();
        else handleSearch(searchQuery);
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
      alert('Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const getImageUrl = (relPath) => `${API_BASE}/data/${relPath}`;

  return (
    <div className="min-h-screen bg-black text-white font-sans selection:bg-white/20">
      <header className="sticky top-0 z-40 w-full backdrop-blur-md bg-black/80 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-2xl">
              <svg className="w-6 h-6 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <h1 className="text-2xl font-black tracking-tighter">EYE</h1>
          </div>

          <div className="flex-1 max-w-md mx-8">
            <div className="relative group">
              <input
                type="text"
                placeholder="SEARCH..."
                className="w-full bg-white/5 border border-white/10 rounded-none py-2.5 pl-11 pr-4 focus:outline-none focus:border-white transition-all placeholder:text-white/20"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <svg className="absolute left-4 top-3 w-5 h-5 text-white/20 group-focus-within:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1 bg-white/5 p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-4 py-2 text-xs font-bold uppercase transition-all ${viewMode === 'grid' ? 'bg-white text-black' : 'text-white/40 hover:text-white'}`}
              >
                Grid
              </button>
              <button
                onClick={() => setViewMode('constellation')}
                className={`px-4 py-2 text-xs font-bold uppercase transition-all ${viewMode === 'constellation' ? 'bg-white text-black' : 'text-white/40 hover:text-white'}`}
              >
                Graph
              </button>
            </div>

            <label className="cursor-pointer group">
              <input type="file" className="hidden" onChange={onFileChange} accept="image/*" />
              <div className="flex items-center gap-2 bg-white text-black px-5 py-2.5 font-bold uppercase text-xs transition-all active:scale-95 hover:invert">
                {isUploading ? '...' : 'Upload'}
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
            <div className="flex flex-col items-center justify-center py-32 opacity-20">
              <div className="w-12 h-12 border-2 border-white border-t-transparent rounded-full animate-spin mb-4" />
              <p className="font-bold tracking-widest uppercase text-xs">Loading...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-32 border border-white/10">
              <p className="text-white/20 font-bold uppercase tracking-widest text-xs">No entries found</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="group relative bg-white/5 overflow-hidden border border-white/10 hover:border-white transition-all cursor-pointer grayscale hover:grayscale-0"
                  onClick={() => setSelectedDoc(doc)}
                >
                  <div className="aspect-square overflow-hidden">
                    <img
                      src={getImageUrl(doc.relative_path)}
                      alt={doc.filename}
                      className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                      loading="lazy"
                    />
                  </div>
                  <div className="p-4 bg-black/80 backdrop-blur-sm border-t border-white/5">
                    <p className="text-[10px] font-bold uppercase tracking-widest truncate">{doc.filename}</p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {doc.tags.slice(0, 2).map((tag, i) => (
                        <span key={i} className="text-[9px] uppercase font-bold px-1.5 py-0.5 bg-white/10 text-white/60">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      )}

      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
          <div className="absolute inset-0 bg-black/95 backdrop-blur-xl" onClick={() => setSelectedDoc(null)} />
          <div className="relative w-full max-w-5xl bg-black border border-white/20 flex flex-col md:flex-row max-h-[90vh] overflow-hidden">
            <button
              className="absolute top-4 right-4 z-10 p-2 bg-white/10 hover:bg-white hover:text-black rounded-none text-white transition-all"
              onClick={() => setSelectedDoc(null)}
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <div className="md:w-2/3 bg-black flex items-center justify-center p-4 group/preview">
              <img
                src={getImageUrl(selectedDoc.relative_path)}
                alt={selectedDoc.filename}
                className="max-w-full max-h-full object-contain shadow-2xl grayscale group-hover/preview:grayscale-0 transition-all duration-700"
              />
            </div>

            <div className="md:w-1/3 p-8 border-l border-white/10 overflow-y-auto bg-black flex flex-col justify-between">
              <div>
                <div className="mb-8">
                  <h2 className="text-xl font-black uppercase tracking-tighter mb-1">{selectedDoc.filename}</h2>
                  <div className="h-1 w-12 bg-white mt-2" />
                </div>

                <div className="mb-8 p-6 bg-white/5 border border-white/5">
                  <h3 className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em] mb-4">Transcription</h3>
                  <p className="text-white text-sm leading-relaxed font-medium lowercase">
                    {selectedDoc.caption || 'PENDING...'}
                  </p>
                </div>

                <div>
                  <h3 className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em] mb-4">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedDoc.tags.map((tag, i) => (
                      <span key={i} className="px-3 py-1.5 bg-white text-black text-[10px] font-black uppercase tracking-widest">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <button
                onClick={() => setSelectedDoc(null)}
                className="mt-8 w-full py-4 bg-white text-black text-[10px] font-black uppercase tracking-[0.3em] hover:invert transition-all"
              >
                HIDE PREVIEW
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;