import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const PredictiveMaintenance = ({ dcIdProp }) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [datacenters, setDatacenters] = useState([]);
  const [selectedDc, setSelectedDc] = useState(dcIdProp || '');
  const [actionSimValue, setActionSimValue] = useState({});
  const navigate = useNavigate();

  // Sync prop changes
  useEffect(() => {
    if (dcIdProp) setSelectedDc(dcIdProp);
  }, [dcIdProp]);

  useEffect(() => {
    // Fetch available data centers on mount
    const fetchDatacenters = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/agent/datacenters');
        if (response.ok) {
          const result = await response.json();
          if (result.status === 'success') {
            setDatacenters(result.datacenters);
            if (result.datacenters.length > 0 && !dcIdProp) {
              setSelectedDc(result.datacenters[0].id);
            }
          }
        }
      } catch (err) {
        console.error("Failed to fetch datacenters:", err);
      }
    };
    fetchDatacenters();
  }, []);

  // Auto-run analysis initially when a Data Center is active
  useEffect(() => {
    if (selectedDc) {
      runAnalysis();
    }
  }, [selectedDc]);

  const runAnalysis = async () => {
    if (!selectedDc) return;

    setLoading(true);
    setError(null);
    setActionSimValue({});
    try {
      const response = await fetch(`http://localhost:8000/api/agent/predictive_maintenance/${selectedDc}`);
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

  const handleNextLog = () => {
    // Just check the real-time data for the current datacenter again (fetch new log)
    runAnalysis();
  };

  return (
    <div className={dcIdProp ? "" : "agent-page-container"}>
      {!dcIdProp && <Link to="/" className="back-button">← BACK TO HUB</Link>}
      
      <div className="agent-header" style={dcIdProp ? { padding: '0', background: 'transparent', border: 'none', marginBottom: '1rem', minHeight: 'auto' } : {}}>
        {!dcIdProp && (
          <>
            <div className="card-icon">🔧</div>
            <div style={{ flex: 1 }}>
              <h1 className="hero-title" style={{ fontSize: '3rem', margin: '0', textAlign: 'left' }}>Predictive Maintenance</h1>
              <p className="hero-subtitle" style={{ margin: 0, textAlign: 'left' }}>System Health & Analytics</p>
            </div>
          </>
        )}
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginLeft: dcIdProp ? 'auto' : '0' }}>
            {selectedDc && <span style={{ color: '#00ea93', fontWeight: 'bold' }}>Active Target: {datacenters.find(d => d.id === selectedDc)?.name}</span>}
            <button 
                className="action-button" 
                onClick={runAnalysis} 
                disabled={loading || !selectedDc}
                style={{ padding: '0.8rem 1.5rem', background: '#00ea93', color: '#0a0a0a', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: (loading || !selectedDc) ? 'not-allowed' : 'pointer' }}
            >
              {loading ? 'Analyzing...' : 'Re-Analyze Outcome'}
            </button>
            <button 
                className="action-button" 
                onClick={handleNextLog} 
                disabled={loading || datacenters.length === 0}
                style={{ padding: '0.8rem 1.5rem', background: 'transparent', color: '#00ea93', border: '1px solid #00ea93', borderRadius: '8px', fontWeight: 'bold', cursor: (loading || datacenters.length === 0) ? 'not-allowed' : 'pointer' }}
            >
              Next Log &rarr;
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
                            <p style={{ margin: '0 0 1rem 0', fontSize: '0.85rem', color: '#00ea93', fontWeight: 'bold' }}>&rarr; Result: {action.expected_outcome}</p>
                            
                            {action.simulation && (() => {
                                const sim = action.simulation;
                                const currentVal = actionSimValue[idx] !== undefined ? actionSimValue[idx] : sim.current;
                                const val = Number(currentVal);
                                
                                let prodScore = 0;
                                if (val >= sim.optimal_min && val <= sim.optimal_max) {
                                    prodScore = 100;
                                } else if (val < sim.optimal_min) {
                                    const dist = sim.optimal_min - val;
                                    const maxDist = sim.optimal_min - sim.min;
                                    const penalty = maxDist > 0 ? (dist / maxDist) * 60 : 60;
                                    prodScore = Math.max(0, Math.floor(95 - penalty));
                                } else {
                                    const dist = val - sim.optimal_max;
                                    const maxDist = sim.max - sim.optimal_max;
                                    const penalty = maxDist > 0 ? (dist / maxDist) * 60 : 60;
                                    prodScore = Math.max(0, Math.floor(95 - penalty));
                                }
                                
                                return (
                                    <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                            <div>
                                                <h4 style={{ margin: 0, color: '#00ccff' }}>⚙️ Simulate: {sim.name}</h4>
                                                <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: '#ffcc00' }}>
                                                    Target Optimal Zone: {sim.optimal_min} - {sim.optimal_max} {sim.unit}
                                                </p>
                                            </div>
                                            <div style={{ background: '#1a1a1a', padding: '0.5rem 1rem', borderRadius: '4px', border: '1px solid #333' }}>
                                                <span style={{ fontSize: '0.8rem', color: '#888' }}>Productivity Score</span>
                                                <div style={{ fontSize: '1.5rem', color: prodScore > 75 ? '#00ea93' : (prodScore > 50 ? '#ffcc00' : '#ff4d4d'), fontWeight: 'bold' }}>
                                                    {prodScore}%
                                                </div>
                                            </div>
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                            <span style={{ color: '#888', fontSize: '0.8rem' }}>{sim.min}</span>
                                            <input 
                                                type="range" 
                                                min={sim.min} 
                                                max={sim.max} 
                                                step={(sim.max - sim.min) <= 10 ? 0.1 : 1}
                                                value={currentVal} 
                                                onChange={(e) => setActionSimValue({...actionSimValue, [idx]: e.target.value})}
                                                style={{ flex: 1, accentColor: '#00ccff' }} 
                                            />
                                            <span style={{ color: '#888', fontSize: '0.8rem' }}>{sim.max} {sim.unit}</span>
                                        </div>
                                        <div style={{ textAlign: 'center', marginTop: '0.5rem', color: '#fff', fontWeight: 'bold' }}>
                                            Selected: {currentVal} {sim.unit}
                                        </div>
                                        {/* Visual alignment hint for optimal zone based on value */}
                                        <div style={{ textAlign: 'center', fontSize: '0.85rem', marginTop: '0.2rem', color: prodScore === 100 ? '#00ea93' : '#ff4d4d' }}>
                                            {prodScore === 100 ? "✓ Hardware operation is within strictly optimal limits!" : "⚠ Outside optimal limits!"}
                                        </div>
                                    </div>
                                );
                            })()}
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
