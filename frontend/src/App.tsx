import { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Download, Building2, Calendar, FileText } from 'lucide-react';

interface Report {
  id?: number;
  report_key?: string;
  source_name?: string;
  institution?: string;
  title: string;
  author?: string | null;
  publish_date?: string | null;
  date?: string;
  filename?: string;
  url?: string;
  summary_data?: any;
}

const INSTITUTIONS = [
  "한국은행", "국제금융센터", "산업연구원", "KDI", "금융감독원", "IMF"
];

function App() {
  const [reports, setReports] = useState<Report[]>([]);
  const [search, setSearch] = useState("");
  const [selectedSource, setSelectedSource] = useState<string>("");

  useEffect(() => {
    fetchReports();
  }, [search, selectedSource]);

  const fetchReports = async () => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const res = await axios.get(`${API_BASE_URL}/api/reports`, {
        params: { search, source: selectedSource },
        headers: { 'Bypass-Tunnel-Remainder': 'true' }
      });
      setReports(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDownload = (report: Report) => {
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    if (report.filename) {
      window.open(`${API_BASE_URL}/pdfs/${report.filename}`, '_blank');
    } else if (report.url) {
      window.open(report.url, '_blank');
    } else if (report.id) {
      window.open(`${API_BASE_URL}/api/reports/${report.id}/pdf`, '_blank');
    }
  };

  const filteredReports = reports.filter(r => {
    const inst = r.institution || r.source_name || '';
    const titleMatches = r.title.toLowerCase().includes(search.toLowerCase());
    const sourceMatches = selectedSource === "" || inst.includes(selectedSource);
    return titleMatches && sourceMatches;
  });

  return (
    <div className="min-h-screen bg-background text-textPrimary font-sans">
      <header className="border-b border-surface p-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary flex items-center gap-2">
            <Building2 /> 외부 리포트 검색
          </h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-4 gap-8">
        <aside className="lg:col-span-1">
          <div className="bg-surface p-6 rounded-xl">
            <h2 className="text-lg font-semibold mb-4 text-primary">기관 필터</h2>
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
              <button 
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${selectedSource === "" ? 'bg-primary text-background font-medium' : 'hover:bg-background text-textSecondary'}`}
                onClick={() => setSelectedSource("")}
              >
                전체보기
              </button>
              {INSTITUTIONS.map(inst => (
                <button 
                  key={inst}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${selectedSource === inst ? 'bg-primary text-background font-medium' : 'hover:bg-background text-textSecondary'}`}
                  onClick={() => setSelectedSource(inst)}
                >
                  {inst}
                </button>
              ))}
            </div>
          </div>
        </aside>

        <div className="lg:col-span-3 space-y-6">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-textSecondary" />
            <input 
              type="text" 
              placeholder="리포트 제목, 요약 키워드 검색..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-surface border border-surface text-textPrimary pl-12 pr-4 py-4 rounded-xl focus:outline-none focus:border-primary transition-colors"
            />
          </div>

          <div className="space-y-4">
            {filteredReports.length === 0 ? (
              <div className="text-center py-12 text-textSecondary bg-surface rounded-xl">
                조건에 맞는 리포트가 없습니다.
              </div>
            ) : (
              filteredReports.map((r, idx) => (
                <div key={r.id || idx} className="bg-surface p-6 rounded-xl hover:ring-1 hover:ring-primary transition-all">
                  <div className="flex justify-between items-start gap-4">
                    <div>
                      <span className="inline-block px-3 py-1 bg-background text-primary text-xs rounded-full mb-3 font-semibold">
                        {r.institution || r.source_name}
                      </span>
                      <h3 className="text-xl font-medium mb-2">{r.title}</h3>
                      <div className="flex items-center gap-4 text-sm text-textSecondary mb-4">
                        <span className="flex items-center gap-1"><Calendar size={14} /> {r.date || r.publish_date || '날짜 미상'}</span>
                        {r.author && <span className="flex items-center gap-1"><FileText size={14} /> {r.author}</span>}
                      </div>
                      
                      {r.summary_data && r.summary_data.summary && (
                        <ul className="space-y-1 text-sm text-textSecondary list-disc list-inside mb-4">
                          {r.summary_data.summary.map((s: string, sIdx: number) => (
                            <li key={sIdx}>{s}</li>
                          ))}
                        </ul>
                      )}
                      
                      {r.summary_data && r.summary_data.keywords && (
                        <div className="flex flex-wrap gap-2">
                          {r.summary_data.keywords.map((kw: string, kIdx: number) => (
                            <span key={kIdx} className="text-xs bg-background px-2 py-1 rounded text-textSecondary">
                              #{kw}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <button 
                      onClick={() => handleDownload(r)}
                      className="flex items-center gap-2 bg-primary text-background px-4 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity shrink-0"
                    >
                      <Download size={18} /> PDF
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
