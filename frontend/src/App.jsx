import React, { useState, useEffect } from 'react';

export default function App() {
  const [activeTab, setActiveTab] = useState('feed');
  const [community, setCommunity] = useState('kwasu_main');
  const [communities, setCommunities] = useState([]);
  const [reports, setReports] = useState([]);
  const [reportText, setReportText] = useState('');
  const [location, setLocation] = useState('Hostel Block A');
  const [ragQuestion, setRagQuestion] = useState('');
  const [ragAnswer, setRagAnswer] = useState(null);
  const [situationBrief, setSituationBrief] = useState(null);
  const [adminStats, setAdminStats] = useState(null);

  useEffect(() => {
    fetch('/api/communities')
      .then(res => res.json())
      .then(data => setCommunities(data.communities || []))
      .catch(err => console.error(err));
  }, []);

  useEffect(() => {
    if (activeTab === 'feed') {
      fetch(`/api/reports?community_id=${community}`)
        .then(res => res.json())
        .then(data => setReports(data.reports || []))
        .catch(err => console.error(err));
    } else if (activeTab === 'situation') {
      fetch(`/api/situation-room?community_id=${community}`)
        .then(res => res.json())
        .then(data => setSituationBrief(data))
        .catch(err => console.error(err));
    } else if (activeTab === 'admin') {
      fetch(`/api/admin/stats?community_id=${community}`, {
        headers: { 'x-admin-passcode': 'sentry_admin_passcode' }
      })
        .then(res => res.json())
        .then(data => setAdminStats(data))
        .catch(err => console.error(err));
    }
  }, [activeTab, community]);

  const handleReportSubmit = (e) => {
    e.preventDefault();
    if (!reportText.trim()) return;

    fetch('/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: reportText,
        location: location,
        community_id: community,
        anonymous: true
      })
    })
      .then(res => res.json())
      .then(data => {
        setReportText('');
        setActiveTab('feed');
      })
      .catch(err => console.error(err));
  };

  const handleRagAsk = (e) => {
    e.preventDefault();
    if (!ragQuestion.trim()) return;

    fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: ragQuestion,
        community_id: community
      })
    })
      .then(res => res.json())
      .then(data => setRagAnswer(data))
      .catch(err => console.error(err));
  };

  return (
    <div>
      <header className="top-header">
        <div className="header-row">
          <div className="header-title">
            <span>🛡️</span> SENTRY AI
          </div>
          <select 
            value={community} 
            onChange={(e) => setCommunity(e.target.value)}
            style={{ background: '#1a1d24', color: '#fff', border: '1px solid #2a2e37', padding: '4px 8px', borderRadius: '6px' }}
          >
            {communities.map(c => (
              <option key={c.community_id} value={c.community_id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div className="tabs-bar">
          <div className={`tab-item ${activeTab === 'feed' ? 'active' : ''}`} onClick={() => setActiveTab('feed')}>Feed</div>
          <div className={`tab-item ${activeTab === 'submit' ? 'active' : ''}`} onClick={() => setActiveTab('submit')}>Report</div>
          <div className={`tab-item ${activeTab === 'ask' ? 'active' : ''}`} onClick={() => setActiveTab('ask')}>Ask AI</div>
          <div className={`tab-item ${activeTab === 'situation' ? 'active' : ''}`} onClick={() => setActiveTab('situation')}>Brief</div>
          <div className={`tab-item ${activeTab === 'admin' ? 'active' : ''}`} onClick={() => setActiveTab('admin')}>Admin</div>
        </div>
      </header>

      <main className="content-area">
        {activeTab === 'feed' && (
          <div>
            <h3>Live Community Intelligence</h3>
            <p style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '12px' }}>Real-time reports triage powered by Gemma 4</p>
            {reports.length === 0 ? <p>No reports logged yet.</p> : reports.map(r => (
              <div key={r.id} className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span className={`badge badge-${r.category}`}>{r.category}</span>
                  <span style={{ fontSize: '11px', color: '#94a3b8' }}>{r.location}</span>
                </div>
                <p>{r.anonymized_text}</p>
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#00BA7C' }}>
                  🤖 {r.ai_reply}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'submit' && (
          <form onSubmit={handleReportSubmit} className="card">
            <h3>Log Incident Report</h3>
            <p style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '12px' }}>Anonymized automatically by Gemma AI</p>
            
            <label style={{ fontSize: '12px', display: 'block', marginBottom: '4px' }}>Location</label>
            <input 
              type="text" 
              className="input-text" 
              value={location} 
              onChange={e => setLocation(e.target.value)} 
            />

            <label style={{ fontSize: '12px', display: 'block', marginBottom: '4px' }}>Incident Details</label>
            <textarea 
              className="input-text" 
              rows="4" 
              value={reportText} 
              onChange={e => setReportText(e.target.value)} 
              placeholder="e.g. Broken streetlight causing security risk..." 
            />

            <button type="submit" className="btn">Submit Report</button>
          </form>
        )}

        {activeTab === 'ask' && (
          <div>
            <form onSubmit={handleRagAsk} className="card">
              <h3>Ask SENTRY AI Brain</h3>
              <p style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '12px' }}>Grounded RAG search over live community reports</p>
              <input 
                type="text" 
                className="input-text" 
                value={ragQuestion} 
                onChange={e => setRagQuestion(e.target.value)} 
                placeholder="e.g. Is there any active water issue in Block A?" 
              />
              <button type="submit" className="btn">Ask Gemma</button>
            </form>

            {ragAnswer && (
              <div className="card">
                <h4>AI Answer</h4>
                <p style={{ margin: '8px 0' }}>{ragAnswer.answer}</p>
                <span style={{ fontSize: '11px', color: '#94a3b8' }}>Confidence: {ragAnswer.confidence_score}%</span>
              </div>
            )}
          </div>
        )}

        {activeTab === 'situation' && situationBrief && (
          <div className="card">
            <h3>{situationBrief.period_title}</h3>
            <p style={{ fontSize: '12px', color: '#00BA7C', fontWeight: 'bold', margin: '8px 0' }}>Status: {situationBrief.overall_status}</p>
            <ul>
              {situationBrief.summary_bullets?.map((b, idx) => (
                <li key={idx} style={{ marginBottom: '6px' }}>{b}</li>
              ))}
            </ul>
          </div>
        )}

        {activeTab === 'admin' && adminStats && (
          <div>
            <h3>Dispatcher Dashboard</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', margin: '12px 0' }}>
              <div className="card">
                <h4>Total Reports</h4>
                <p style={{ fontSize: '24px', fontWeight: '800' }}>{adminStats.total_reports}</p>
              </div>
              <div className="card">
                <h4>Urgent</h4>
                <p style={{ fontSize: '24px', fontWeight: '800', color: '#F91880' }}>{adminStats.urgent_unresolved}</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
