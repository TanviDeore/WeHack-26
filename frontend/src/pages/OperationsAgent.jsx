import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const OperationsAgent = ({ dcIdProp }) => {
  const [dcId, setDcId] = useState(dcIdProp || 'dc_usa_1');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [actionStatus, setActionStatus] = useState({}); // { title: 'committing' | 'success' }
  const [liveMetrics, setLiveMetrics] = useState({});
  const [autoScan, setAutoScan] = useState(true);
  const [metricsHistory, setMetricsHistory] = useState([]);

  // Sync prop changes
  useEffect(() => {
    if (dcIdProp) setDcId(dcIdProp);
  }, [dcIdProp]);

  // Reset history on DC change
  useEffect(() => {
    setMetricsHistory([]);
  }, [dcId]);

  // Sentinel Auto-Pilot Polling
  useEffect(() => {
    let interval;
    if (autoScan) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/agent/telemetry/${dcId}`);
          if (!res.ok) throw new Error('Telemetry fetch failed');
          const telemetry = await res.json();
          setLiveMetrics(telemetry);

          setMetricsHistory(prev => {
            const now = new Date();
            const timeStr = `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`;
            const newHistory = [...prev, {
              time: timeStr,
              temp: telemetry.temp,
              cpu_load: telemetry.cpu_load,
              network: telemetry.network_bandwidth_gbps
            }];
            return newHistory.slice(-15); // keep last 15 points
          });

          // The Auto-Pilot Trigger Logic!
          if (telemetry.status === 'degraded' && !data && !loading) {
            handleRunAnalysis();
          }
        } catch (error) {
          console.error("Sentinel Error:", error);
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [dcId, autoScan, data, loading]);

  const handleRunAnalysis = async () => {
    setAutoScan(false); // Pause rapid scanning while LLM is parsing
    setLoading(true);
    setActionStatus({});
    try {
      const res = await fetch(`http://localhost:8000/api/agent/operations/${dcId}`);
      if (!res.ok) throw new Error('LangGraph fetch failed');
      const result = await res.json();
      setData(result);
    } catch (error) {
      console.error(error);
      setData({
        metrics_analyzed: liveMetrics,
        anomalies: ["Fallback Simulated Anomaly: API Error or Limits Exceeded"],
        recommended_actions: [
          {
            action_title: "Check API / Backend",
            action_explanation: "Ensure Uvicorn backend is running and Gemini API keys are valid.",
            confidence_score: 95,
            reasoning_pointers: ["Historical connectivity issues are typically resolved by checking application logs."]
          }
        ],
        status: "Error"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAction = async (actionTitle) => {
    const rootCauseTag = data.anomalies && data.anomalies[0]?.startsWith('TAGS: ') 
      ? data.anomalies[0].replace('TAGS: ', '').split(',')[0]
      : 'unknown';

    try {
      const res = await fetch(`http://localhost:8000/api/agent/operations/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dc_id: dcId,
          anomalies: data.anomalies,
          action_taken: actionTitle,
          root_cause: rootCauseTag,
          severity: liveMetrics.status === 'degraded' ? 'high' : 'medium'
        })
      });
      if (!res.ok) throw new Error('Feedback failed');
      setActionStatus(prev => ({ ...prev, [actionTitle]: 'success' }));
      
      // Auto-resume monitoring after 2 seconds
      setTimeout(() => {
        resumeScan();
      }, 2000);
    } catch (err) {
      console.error(err);
      setActionStatus(prev => ({ ...prev, [actionTitle]: 'success' }));
      setTimeout(() => resumeScan(), 2000);
    }
  };

  const handleRejectAction = async (actionTitle) => {
    setActionStatus(prev => ({ ...prev, [actionTitle]: 'committing' }));
    try {
      await fetch(`http://localhost:8000/api/agent/operations/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dc_id: dcId,
          anomalies: data.anomalies,
          action_taken: `REJECTED: ${actionTitle}`
        })
      });
      
      // Remove this action from local state
      setData(prev => ({
        ...prev,
        recommended_actions: prev.recommended_actions.filter(a => a.action_title !== actionTitle)
      }));

      // If no more actions, resume scan
      if (data.recommended_actions.length <= 1) {
        resumeScan();
      }
    } catch (err) {
      console.error(err);
      // Fallback: just remove it
      setData(prev => ({
        ...prev,
        recommended_actions: prev.recommended_actions.filter(a => a.action_title !== actionTitle)
      }));
      if (data.recommended_actions.length <= 1) {
        resumeScan();
      }
    }
  };

  const resumeScan = () => {
    setData(null);
    setActionStatus({});
    setAutoScan(true);
  };

  const hasAnomalies = data && data.anomalies && data.anomalies.length > 0;

  // Decide which metrics to show on the left panel (Frozen LLM snapshot vs Live feed)
  const displayMetrics = data && data.metrics_analyzed && Object.keys(data.metrics_analyzed).length > 0
    ? data.metrics_analyzed
    : liveMetrics;

  return (
    <div className={dcIdProp ? "" : "agent-page-container"}>
      {!dcIdProp && <Link to="/" className="back-button">← BACK TO HUB</Link>}

      {!dcIdProp && (
        <div className="agent-header">
          <div className="card-icon">⚙️</div>
          <div>
            <h1 className="hero-title" style={{ fontSize: '3rem', marginBottom: '0.2rem', textAlign: 'left' }}>Operations Agent</h1>
            <p className="hero-subtitle" style={{ margin: 0, textAlign: 'left' }}>Auto-Pilot GraphRAG System</p>
          </div>
        </div>
      )}

      <div className="agent-workspace" style={{ padding: '2rem' }}>
        <div className="operations-dashboard">

          {/* Left Panel: Telemetry & Controls */}
          <div className={`panel ${hasAnomalies || liveMetrics.status === 'degraded' ? 'critical' : ''}`}>
            <div className="panel-header">
              <span>Sentinel Feed</span>
              {!dcIdProp && (
                <input
                  type="text"
                  value={dcId}
                  onChange={(e) => setDcId(e.target.value)}
                  disabled={!autoScan}
                  style={{ background: 'rgba(0,0,0,0.5)', border: '1px solid var(--border)', color: '#fff', padding: '0.4rem 0.8rem', borderRadius: '4px', width: '100px' }}
                />
              )}
            </div>

            <button
              className="run-btn"
              onClick={() => autoScan ? setAutoScan(false) : resumeScan()}
              disabled={loading || actionStatus === 'success'}
              style={{ width: '100%', marginBottom: '2rem', background: autoScan ? 'rgba(0, 255, 100, 0.1)' : '', borderColor: autoScan ? '#00ff64' : '' }}
            >
              {loading ? 'AI RUNNING...' : autoScan ? '🟢 AUTO-SCAN ACTIVE' : 'MANUAL AI MODE'}
            </button>

            <div className="metric-grid">
              <div className="metric-item">
                <span className="metric-label">TEMP (°F)</span>
                <span className="metric-val" style={{ color: displayMetrics.temp >= 85 ? 'var(--accent-3)' : '#fff' }}>
                  {displayMetrics.temp || '--'}
                </span>
              </div>
              <div className="metric-item">
                <span className="metric-label">CPU LOAD (%)</span>
                <span className="metric-val" style={{ color: displayMetrics.cpu_load >= 85 ? 'var(--accent-3)' : '#fff' }}>
                  {displayMetrics.cpu_load || '--'}
                </span>
              </div>
              <div className="metric-item">
                <span className="metric-label">NETWORK (GBPS)</span>
                <span className="metric-val">{displayMetrics.network_bandwidth_gbps || '0'}</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">STATUS</span>
                <span className="metric-val" style={{ fontSize: '1rem', color: displayMetrics.status === 'degraded' ? 'var(--accent-3)' : '#00ff64' }}>
                  {displayMetrics.status ? displayMetrics.status.toUpperCase() : 'NO FEED'}
                </span>
              </div>
            </div>

            {metricsHistory.length > 0 && (
              <div style={{ marginTop: '2rem', height: '200px', width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={metricsHistory}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="time" stroke="#888" fontSize={10} />
                    <YAxis stroke="#888" fontSize={10} />
                    <Tooltip contentStyle={{ backgroundColor: '#1e1e1e', border: '1px solid #333' }} labelStyle={{ color: '#aaa' }} />
                    <Line type="monotone" dataKey="temp" stroke="#ff4d4f" strokeWidth={2} dot={false} name="Temp (°C)" />
                    <Line type="monotone" dataKey="cpu_load" stroke="#1890ff" strokeWidth={2} dot={false} name="CPU Load (%)" />
                    <Line type="monotone" dataKey="network" stroke="#52c41a" strokeWidth={2} dot={false} name="Network (GBPS)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            <div style={{ textAlign: 'center', opacity: 0.5, marginTop: '2rem' }}>
              {autoScan ? "Polling raw REDIS stream every 3s..." : "Telemetry paused. Reviewing anomaly."}
            </div>
          </div>

          {/* Right Panel: AI Resolution Engine */}
          <div className="panel" style={{ border: '1px solid var(--accent-1)' }}>
            <div className="panel-header" style={{ color: 'var(--accent-1)' }}>
              <span>LangGraph + Neo4j Engine</span>
              <span className="workspace-status">{loading ? 'ANALYZING...' : data ? data.status.toUpperCase() : 'SLEEPING'}</span>
            </div>

            <div className="ai-feed">
              {loading && <div>Executing GraphRAG memory retrieval nodes<span className="loading-cursor"></span></div>}

              {!loading && !data && (
                <div style={{ opacity: 0.5, marginTop: '6rem', textAlign: 'center' }}>
                  Awaiting anomaly signature to spawn AI nodes...
                </div>
              )}

              {!loading && data && (
                <>
                  <div style={{ marginBottom: '1rem', color: '#fff' }}>
                    {hasAnomalies
                      ? <span style={{ color: 'var(--accent-3)', fontWeight: 'bold' }}>⚠️ ANOMALY DETECTED</span>
                      : <span style={{ color: 'var(--accent-1)' }}>✅ SYSTEMS NOMINAL</span>}
                  </div>

                  {hasAnomalies && (
                    <ul style={{ marginLeft: '1.5rem', marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
                      {data.anomalies.map((anom, idx) => <li key={idx}>{anom}</li>)}
                    </ul>
                  )}

                  {data.recommended_actions && data.recommended_actions.length > 0 && (
                    <div className="ai-recommendation">
                      <div style={{ fontSize: '0.8rem', letterSpacing: '2px', marginBottom: '1rem', opacity: 0.8 }}>RECOMMENDED ACTIONS</div>
                      
                      {data.recommended_actions.map((action, idx) => (
                        <div key={idx} style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(0, 0, 0, 0.2)', borderRadius: '8px', borderLeft: '4px solid var(--accent-1)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: action.action_explanation ? '0.5rem' : '1.5rem' }}>
                            <div style={{ lineHeight: '1.6', fontWeight: 'bold', fontSize: '1.1rem', color: '#00ff64' }}>
                              {action.action_title}
                            </div>
                            {action.confidence_score !== undefined && (
                              <div style={{ fontSize: '0.9rem', color: '#00ff64', border: '1px solid currentColor', padding: '0.2rem 0.6rem', borderRadius: '4px' }}>
                                Confidence: {action.confidence_score}%
                              </div>
                            )}
                          </div>
                          
                          {action.action_explanation && (
                            <div style={{ lineHeight: '1.4', fontSize: '0.9rem', color: '#ccc', marginBottom: '1.5rem', fontStyle: 'italic' }}>
                              💡 {action.action_explanation}
                            </div>
                          )}

                          <div style={{ fontSize: '0.8rem', letterSpacing: '2px', marginBottom: '0.5rem', opacity: 0.8 }}>HISTORICAL GRAPHDB REASONING</div>
                          <ul style={{ marginLeft: '1.5rem', lineHeight: '1.6', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                            {action.reasoning_pointers && action.reasoning_pointers.map((ptr, ptrIdx) => (
                              <li key={ptrIdx} style={{ marginBottom: '0.5rem' }}>{ptr}</li>
                            ))}
                          </ul>

                          {actionStatus[action.action_title] !== 'success' && (
                            <div style={{ display: 'flex', gap: '1rem' }}>
                              <button
                                className="action-btn"
                                onClick={() => handleApproveAction(action.action_title)}
                                disabled={actionStatus[action.action_title] === 'committing'}
                                style={{ padding: '0.4rem 1rem', fontSize: '0.8rem', marginTop: '0.5rem' }}
                              >
                                {actionStatus[action.action_title] === 'committing' ? 'COMMITTING...' : 'APPROVE RESOLUTION'}
                              </button>
                              <button
                                className="reject-btn"
                                onClick={() => handleRejectAction(action.action_title)}
                                disabled={actionStatus[action.action_title] === 'committing'}
                                style={{ padding: '0.4rem 1rem', fontSize: '0.8rem', marginTop: '0.5rem' }}
                              >
                                {actionStatus[action.action_title] === 'committing' ? '...' : 'REJECT'}
                              </button>
                            </div>
                          )}

                          {actionStatus[action.action_title] === 'success' && (
                            <div style={{ color: 'var(--accent-1)', fontWeight: 'bold', marginTop: '1rem' }}>
                              ✓ Action Approved & Recorded.
                            </div>
                          )}
                        </div>
                      ))}

                      {data.recommended_actions.length > 0 && (
                        <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                          <button 
                            onClick={resumeScan} 
                            style={{ background: 'transparent', border: '1px solid rgba(255,255,255,0.2)', color: 'rgba(255,255,255,0.5)', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}
                          >
                            IGNORE ALL & RESUME MONITORING
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default OperationsAgent;
