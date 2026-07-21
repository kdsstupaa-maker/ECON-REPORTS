import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Download, Building2, Calendar, FileText } from 'lucide-react';

interface Report {
  id: number;
  report_key: string;
  source_name: string;
  title: string;
  author: string | null;
  publish_date: string | null;
  summary_data: any;
}

const INSTITUTIONS = [
  "한국은행", "KDI경제연구원", "국제금융센터", "금융연구원", "IMF", 
  "자본시장연구원", "우리금융경영연구소", "BIS", "산업연구원", "PIMCO", 
  "Fed San Francisco", "상공회의소", "금감원", "현대경제연구원", 
  "부동산연구원", "한국경영자협회", "조세재정연", "한국안보전략연구원", 
  "OECD", "한국리츠협회", "토지주택연구원", "무역협회국제무역통상연구원", 
  "예금보험공사", "주택산업연구원", "아산정책연구원", "한신평", "kb금융연구소", 
  "하나금융연구소", "포스코경영연구원", "나이스신평", "BlackRock", 
  "대외경제정책연구원", "한기평", "Fed New York", "국회예산정책보고서", 
  "국가데이터처", "금융위", "보험연구원"
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
        params: { search, source: selectedSource }
      });
      setReports(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDownload = (id: number) => {
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    window.open(`${API_BASE_URL}/api/reports/${id}/pdf`, '_blank');
  };

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
            {reports.length === 0 ? (
              <div className="text-center py-12 text-textSecondary bg-surface rounded-xl">
                조건에 맞는 리포트가 없습니다.
              </div>
            ) : (
              reports.map(r => (
                <div key={r.id} className="bg-surface p-6 rounded-xl hover:ring-1 hover:ring-primary transition-all">
                  <div className="flex justify-between items-start gap-4">
                    <div>
                      <span className="inline-block px-3 py-1 bg-background text-primary text-xs rounded-full mb-3">
                        {r.source_name}
                      </span>
                      <h3 className="text-xl font-medium mb-2">{r.title}</h3>
                      <div className="flex items-center gap-4 text-sm text-textSecondary mb-4">
                        <span className="flex items-center gap-1"><Calendar size={14} /> {r.publish_date || '날짜 미상'}</span>
                        {r.author && <span className="flex items-center gap-1"><FileText size={14} /> {r.author}</span>}
                      </div>
                      
                      {r.summary_data && r.summary_data.summary && (
                        <ul className="space-y-1 text-sm text-textSecondary list-disc list-inside mb-4">
                          {r.summary_data.summary.map((s: string, idx: number) => (
                            <li key={idx}>{s}</li>
                          ))}
                        </ul>
                      )}
                      
                      {r.summary_data && r.summary_data.keywords && (
                        <div className="flex flex-wrap gap-2">
                          {r.summary_data.keywords.map((kw: string, idx: number) => (
                            <span key={idx} className="text-xs bg-background px-2 py-1 rounded text-textSecondary">
                              #{kw}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <button 
                      onClick={() => handleDownload(r.id)}
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
