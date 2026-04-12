import { useState } from 'react';
import { Link } from 'react-router-dom';

const PredictiveMaintenance = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/agent/predictive_maintenance/dc_texas_01');
      if (!response.ok) throw new Error('Network response was not ok');
      const result = await response.json();
      if (result.status === 'success') {
        setData(result.data);
      } else {
        throw new Error(result.error || 'Failed to fetch predictions');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="agent-page-container">
      <Link to="/" className="back-button">← BACK TO HUB</Link>
      
      <div className="agent-header">
        <div className="card-icon">🔧</div>
        <div style={{ flex: 1 }}>
          <h1 className="hero-title" style={{ fontSize: '3rem', margin: '0', textAlign: 'left' }}>Predictive Maintenance</h1>
          <p className="hero-subtitle" style={{ margin: 0, textAlign: 'left' }}>System Health & Analytics</p>
        </div>
        <div>
            <button 
                className="action-button" 
                onClick={runAnalysis} 
                disabled={loading}
                style={{ padding: '0.8rem 1.5rem', background: '#00ea93', color: '#0a0a0a', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: loading ? 'not-allowed' : 'pointer' }}
            >
              {loading ? 'Analyzing...' : 'Run Analysis'}
            </button>
        </div>
      </div>
      
      <div className="agent-workspace" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem', minHeight: '60vh' }}>
        {!data && !loading && !error && (
            <div className="workspace-status">SYSTEM IDLE // AWAITING COMMANDS</div>
        )}
        
        {loading && (
            <div className="workspace-status" style={{ color: '#00ea93' }}>GATHERING CONTEXT & ANALYZING GRAPH DATA...</div>
        )}

        {error && (
            <div style={{ color: '#ff4d4d', padding: '1rem', border: '1px solid #ff4d4d', borderRadius: '8px', background: 'rgba(255, 77, 77, 0.1)' }}>
                Error: {error}
            </div>
        )}

        {data && (
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: '2rem', color: '#fff', textAlign: 'left' }}>
                {/* Potential Incidents */}
                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1.5rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)' }}>
                    <h2 style={{ borderBottom: '1px solid rgba(255,255,255,0.2)', paddingBottom: '0.5rem', marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        ⚠️ Potential Incidents
                    </h2>
                    {data.potential_incidents?.length === 0 && <p>No immediate risks detected.</p>}
                    {data.potential_incidents?.map((incident, idx) => (
                        <div key={idx} style={{ marginBottom: '1rem', padding: '1rem', background: 'rgba(255,0,0,0.1)', borderRadius: '8px', borderLeft: '4px solid #ff4d4d' }}>
                            <h3 style={{ margin: '0 0 0.5rem 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '1.1rem' }}>{incident.incident_type}</span>
                                <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', background: '#ff4d4d', color: '#fff', borderRadius: '4px', textTransform: 'uppercase' }}>{incident.probability} Risk</span>
                            </h3>
                            <p style={{ margin: 0, fontSize: '0.9rem', color: 'rgba(255,255,255,0.8)', lineHeight: '1.4' }}>{incident.reason}</p>
                        </div>
                    ))}
                </div>

                {/* Recommended Actions */}
                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1.5rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)' }}>
                    <h2 style={{ borderBottom: '1px solid rgba(255,255,255,0.2)', paddingBottom: '0.5rem', marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        🛡️ Recommended Actions
                    </h2>
                    {data.recommended_actions?.length === 0 && <p>No recommended actions at this time.</p>}
                    {data.recommended_actions?.map((action, idx) => (
                        <div key={idx} style={{ marginBottom: '1rem', padding: '1rem', background: 'rgba(0,255,0,0.05)', borderRadius: '8px', borderLeft: '4px solid #00ea93' }}>
                            <h3 style={{ margin: '0 0 0.5rem 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '1.1rem' }}>{action.action_name}</span>
                                <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', textTransform: 'uppercase' }}>Priority: {action.priority}</span>
                            </h3>
                            <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', color: 'rgba(255,255,255,0.8)', lineHeight: '1.4' }}>{action.description}</p>
                            <p style={{ margin: 0, fontSize: '0.85rem', color: '#00ea93', fontWeight: 'bold' }}>&rarr; Result: {action.expected_outcome}</p>
                        </div>
                    ))}
                </div>
            </div>
        )}
      </div>
    </div>
  );
};

export default PredictiveMaintenance;
