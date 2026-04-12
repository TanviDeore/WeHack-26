import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps';

const geoUrl = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json";

// State name → FIPS code mapping for Geography fills
const STATE_FIPS = {
  "Alabama": "01", "Alaska": "02", "Arizona": "04", "Arkansas": "05", "California": "06",
  "Colorado": "08", "Connecticut": "09", "Delaware": "10", "Florida": "12", "Georgia": "13",
  "Hawaii": "15", "Idaho": "16", "Illinois": "17", "Indiana": "18", "Iowa": "19", "Kansas": "20",
  "Kentucky": "21", "Louisiana": "22", "Maine": "23", "Maryland": "24", "Massachusetts": "25",
  "Michigan": "26", "Minnesota": "27", "Mississippi": "28", "Missouri": "29", "Montana": "30",
  "Nebraska": "31", "Nevada": "32", "New Hampshire": "33", "New Jersey": "34", "New Mexico": "35",
  "New York": "36", "North Carolina": "37", "North Dakota": "38", "Ohio": "39", "Oklahoma": "40",
  "Oregon": "41", "Pennsylvania": "42", "Rhode Island": "44", "South Carolina": "45",
  "South Dakota": "46", "Tennessee": "47", "Texas": "48", "Utah": "49", "Vermont": "50",
  "Virginia": "51", "Washington": "53", "West Virginia": "54", "Wisconsin": "55", "Wyoming": "56"
};

const FIPS_STATE = Object.fromEntries(Object.entries(STATE_FIPS).map(([k, v]) => [v, k]));

const riskColor = (r) => r === 'Low' ? '#00ea93' : r === 'Medium' ? '#ffcc00' : '#ff4d4d';
const scoreColor = (s) => s >= 80 ? '#00ea93' : s >= 65 ? '#ffcc00' : '#ff4d4d';

const PlanningAgent = () => {
  const [allStates, setAllStates] = useState([]);
  const [budget, setBudget] = useState('');
  const [capacity, setCapacity] = useState('');
  const [preferredStates, setPreferredStates] = useState([]);
  const [stateSearch, setStateSearch] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/agent/planning/states')
      .then(r => r.json())
      .then(d => { if (d.status === 'success') setAllStates(d.states); })
      .catch(() => setAllStates([
        "California", "Florida", "Illinois", "Nevada", "New York", "Ohio", "Texas", "Virginia", "Washington",
        "Arizona", "Colorado", "Georgia", "Michigan", "Minnesota", "Oregon", "Pennsylvania", "Utah"
      ]));
  }, []);

  const filteredStates = allStates.filter(s =>
    s.toLowerCase().includes(stateSearch.toLowerCase()) && !preferredStates.includes(s)
  );

  const addState = (s) => {
    setPreferredStates(p => [...p, s]);
    setStateSearch('');
    setShowDropdown(false);
  };

  const removeState = (s) => setPreferredStates(p => p.filter(x => x !== s));

  const handleRun = async () => {
    if (!budget || !capacity) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch('http://localhost:8000/api/agent/planning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          budget_million_usd: parseFloat(budget),
          capacity_mw: parseFloat(capacity),
          preferred_states: preferredStates
        })
      });
      const json = await res.json();
      if (json.status === 'success') setResult(json.data);
      else setError(json.error || 'Analysis failed');
    } catch (e) {
      setError('Failed to connect to the planning agent backend.');
    } finally {
      setLoading(false);
    }
  };

  // Determine state fill color on the map
  const getStateFill = (geoId) => {
    const stateName = FIPS_STATE[geoId];
    if (!stateName || !result) return '#1a1a1a';
    if (stateName === result.recommended_state) return 'rgba(0, 234, 147, 0.4)';
    const isAlt = result.alternates?.some(a => a.state === stateName);
    if (isAlt) return 'rgba(0, 204, 255, 0.25)';
    return '#1a1a1a';
  };

  const getStateBorder = (geoId) => {
    const stateName = FIPS_STATE[geoId];
    if (!stateName || !result) return '#333';
    if (stateName === result.recommended_state) return '#00ea93';
    if (result.alternates?.some(a => a.state === stateName)) return '#00ccff';
    return '#333';
  };

  const sortedTable = result?.comparison_table
    ? [...result.comparison_table].sort((a, b) => b.overall_score - a.overall_score)
    : [];

  return (
    <div className="agent-page-container">
      <Link to="/" className="back-button">← BACK TO MAP</Link>

      <div className="agent-header">
        <div className="card-icon" style={{ width: '80px', height: '80px', marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>

          <img src="/planning_icon.png" alt="Planning Agent" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} />

        </div>
        <div>
          <h1 className="hero-title" style={{ fontSize: '3rem', marginBottom: '0.2rem', textAlign: 'left' }}>
            Global Planning Agent
          </h1>
          <p className="hero-subtitle" style={{ margin: 0, textAlign: 'left' }}>
            AI-Powered Data Center Site Selection &amp; Strategic Expansion
          </p>
        </div>
      </div>

      <div className="agent-workspace" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>

        {/* --- Input Form Panel --- */}
        <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: '2rem' }}>
          <div style={{ fontSize: '0.75rem', letterSpacing: '3px', color: '#888', marginBottom: '1.5rem' }}>STRATEGIC PARAMETERS</div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
            {/* Budget */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#aaa', marginBottom: '0.5rem', letterSpacing: '1px' }}>
                BUDGET (MILLION USD)
              </label>
              <div style={{ position: 'relative' }}>
                <span style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#00ea93', fontWeight: 'bold' }}>$</span>
                <input
                  type="number"
                  value={budget}
                  onChange={e => setBudget(e.target.value)}
                  placeholder="e.g. 250"
                  style={{ width: '100%', background: 'rgba(0,0,0,0.4)', border: '1px solid #333', borderRadius: '8px', padding: '0.8rem 1rem 0.8rem 2rem', color: '#fff', fontSize: '1rem', outline: 'none', boxSizing: 'border-box' }}
                />
              </div>
            </div>

            {/* Capacity */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#aaa', marginBottom: '0.5rem', letterSpacing: '1px' }}>
                CAPACITY REQUIREMENT (MW)
              </label>
              <input
                type="number"
                value={capacity}
                onChange={e => setCapacity(e.target.value)}
                placeholder="e.g. 50"
                style={{ width: '100%', background: 'rgba(0,0,0,0.4)', border: '1px solid #333', borderRadius: '8px', padding: '0.8rem 1rem', color: '#fff', fontSize: '1rem', outline: 'none', boxSizing: 'border-box' }}
              />
            </div>
          </div>

          {/* Preferred States multi-select */}
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#aaa', marginBottom: '0.5rem', letterSpacing: '1px' }}>
              PREFERRED STATES (OPTIONAL — SELECT MULTIPLE)
            </label>
            {/* Tags */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
              {preferredStates.map(s => (
                <span key={s} style={{ background: 'rgba(0,234,147,0.15)', border: '1px solid #00ea93', borderRadius: '20px', padding: '0.3rem 0.8rem', fontSize: '0.85rem', color: '#00ea93', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  {s}
                  <button onClick={() => removeState(s)} style={{ background: 'none', border: 'none', color: '#00ea93', cursor: 'pointer', fontWeight: 'bold', lineHeight: 1, padding: 0 }}>×</button>
                </span>
              ))}
            </div>
            {/* Search Input */}
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                value={stateSearch}
                onChange={e => { setStateSearch(e.target.value); setShowDropdown(true); }}
                onFocus={() => setShowDropdown(true)}
                placeholder="Search and add a state..."
                style={{ width: '100%', background: 'rgba(0,0,0,0.4)', border: '1px solid #333', borderRadius: '8px', padding: '0.8rem 1rem', color: '#fff', fontSize: '1rem', outline: 'none', boxSizing: 'border-box' }}
              />
              {showDropdown && filteredStates.length > 0 && (
                <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: '#1a1a1a', border: '1px solid #333', borderRadius: '8px', zIndex: 100, maxHeight: '200px', overflowY: 'auto', marginTop: '4px' }}>
                  {filteredStates.map(s => (
                    <div key={s} onClick={() => addState(s)} style={{ padding: '0.7rem 1rem', cursor: 'pointer', color: '#ccc', fontSize: '0.9rem', borderBottom: '1px solid #222', transition: 'background 0.1s' }}
                      onMouseOver={e => e.currentTarget.style.background = 'rgba(0,234,147,0.1)'}
                      onMouseOut={e => e.currentTarget.style.background = 'transparent'}
                    >{s}</div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Run Button */}
          <button
            onClick={handleRun}
            disabled={loading || !budget || !capacity}
            style={{ marginTop: '1.5rem', width: '100%', padding: '1rem', background: (!budget || !capacity || loading) ? '#333' : 'linear-gradient(135deg, #00ea93, #00ccff)', color: '#0a0a0a', border: 'none', borderRadius: '8px', fontWeight: 'bold', fontSize: '1rem', cursor: (!budget || !capacity || loading) ? 'not-allowed' : 'pointer', letterSpacing: '2px', transition: 'all 0.2s' }}
          >
            {loading ? '⟳  RUNNING STRATEGIC ANALYSIS...' : '🧠  RUN PLANNING ANALYSIS'}
          </button>
        </div>

        {/* --- Error --- */}
        {error && (
          <div style={{ color: '#ff4d4d', padding: '1rem', border: '1px solid #ff4d4d', borderRadius: '8px', background: 'rgba(255,77,77,0.1)' }}>
            ⚠ {error}
          </div>
        )}

        {/* --- Results --- */}
        {result && (
          <>
            {/* Recommendation Banner */}
            <div style={{ background: 'rgba(0,234,147,0.08)', border: '1px solid #00ea93', borderRadius: '12px', padding: '1.5rem', display: 'flex', gap: '2rem', alignItems: 'flex-start' }}>
              <div style={{ minWidth: '140px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', letterSpacing: '2px', color: '#888', marginBottom: '0.5rem' }}>TOP RECOMMENDATION</div>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#00ea93' }}>{result.recommended_state}</div>
                <div style={{ marginTop: '0.5rem', background: '#00ea93', color: '#0a0a0a', borderRadius: '20px', fontSize: '0.8rem', fontWeight: 'bold', padding: '0.2rem 0.8rem', display: 'inline-block' }}>
                  {result.confidence_score}% Confidence
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.7rem', letterSpacing: '2px', color: '#888', marginBottom: '0.5rem' }}>AI REASONING</div>
                <p style={{ color: '#ddd', lineHeight: '1.6', margin: 0 }}>{result.recommendation_reasoning}</p>
                <div style={{ display: 'flex', gap: '2rem', marginTop: '1rem' }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: '#888', letterSpacing: '1px' }}>BUDGET ASSESSMENT</div>
                    <div style={{ fontSize: '0.85rem', color: '#ffcc00', marginTop: '0.2rem' }}>{result.budget_assessment}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: '#888', letterSpacing: '1px' }}>CAPACITY FEASIBILITY</div>
                    <div style={{ fontSize: '0.85rem', color: '#00ccff', marginTop: '0.2rem' }}>{result.capacity_feasibility}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* US Map */}
            <div style={{ background: '#0e0e0e', border: '1px solid #222', borderRadius: '12px', padding: '1.5rem' }}>
              <div style={{ fontSize: '0.75rem', letterSpacing: '3px', color: '#888', marginBottom: '1rem' }}>SITE SELECTION MAP</div>
              <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: '#aaa' }}>
                  <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#00ea93', display: 'inline-block' }} /> Recommended
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: '#aaa' }}>
                  <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#00ccff', display: 'inline-block' }} /> Alternate
                </span>
              </div>

              <ComposableMap projection="geoAlbersUsa" style={{ width: '100%', height: 'auto' }}>
                <Geographies geography={geoUrl}>
                  {({ geographies }) =>
                    geographies.map(geo => {
                      const fips = geo.id?.toString().padStart(2, '0');
                      return (
                        <Geography
                          key={geo.rsmKey}
                          geography={geo}
                          fill={getStateFill(fips)}
                          stroke={getStateBorder(fips)}
                          strokeWidth={getStateBorder(fips) !== '#333' ? 1.5 : 0.5}
                          style={{
                            default: { outline: 'none' },
                            hover: { outline: 'none', opacity: 0.8 },
                            pressed: { outline: 'none' },
                          }}
                        />
                      );
                    })
                  }
                </Geographies>

                {/* Recommended marker */}
                {result.recommended_zone_coords && (
                  <Marker coordinates={[result.recommended_zone_coords.lon, result.recommended_zone_coords.lat]}>
                    <circle r={10} fill="#00ea93" stroke="#fff" strokeWidth={2} />
                    <text textAnchor="middle" y={-16} style={{ fontSize: '11px', fill: '#00ea93', fontWeight: 'bold' }}>
                      ★ {result.recommended_state}
                    </text>
                  </Marker>
                )}

                {/* Alternate markers */}
                {result.alternates?.map(alt => (
                  alt.zone_coords && (
                    <Marker key={alt.state} coordinates={[alt.zone_coords.lon, alt.zone_coords.lat]}>
                      <circle r={7} fill="#00ccff" stroke="#fff" strokeWidth={1.5} />
                      <text textAnchor="middle" y={-12} style={{ fontSize: '9px', fill: '#00ccff' }}>
                        {alt.state}
                      </text>
                    </Marker>
                  )
                ))}
              </ComposableMap>
            </div>

            {/* Comparison Table */}
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: '1.5rem', overflowX: 'auto' }}>
              <div style={{ fontSize: '0.75rem', letterSpacing: '3px', color: '#888', marginBottom: '0.5rem' }}>LOCATION COMPARISON TABLE</div>
              <div style={{ fontSize: '0.7rem', color: '#444', marginBottom: '1.5rem', fontStyle: 'italic' }}>All values sourced directly from Graph Database — no estimated metrics</div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', color: '#ddd' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #333' }}>
                    {[
                      'State', 'Score', 'Energy\nCost Idx', 'Avg Temp\n(°C)', 'Humidity\n(%)', 'Avg PUE',
                      'Uptime (%)', 'Latency\n(ms)', 'Cooling\nEfficiency', 'Incidents\n/ DC', 'Avg Cap\n(MW)'
                    ].map(h => (
                      <th key={h} style={{ padding: '0.7rem 0.8rem', textAlign: 'left', fontSize: '0.65rem', letterSpacing: '1px', color: '#888', whiteSpace: 'pre-line' }}>{h.toUpperCase()}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sortedTable.map((row, idx) => (
                    <tr key={row.zone_id || row.state} style={{ borderBottom: '1px solid #1e1e1e', background: row.is_recommended ? 'rgba(0,234,147,0.05)' : (idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)') }}>
                      <td style={{ padding: '0.8rem', fontWeight: 'bold', whiteSpace: 'nowrap' }}>
                        {row.is_recommended && <span style={{ color: '#00ea93', marginRight: '0.4rem' }}>★</span>}
                        <span style={{ color: row.is_recommended ? '#00ea93' : '#ddd' }}>{row.state}</span>
                        {row.score_rationale && (
                          <div style={{ fontSize: '0.65rem', color: '#555', marginTop: '0.2rem', fontWeight: 'normal', maxWidth: '140px' }}>{row.score_rationale}</div>
                        )}
                      </td>
                      <td style={{ padding: '0.8rem' }}>
                        <span style={{ color: scoreColor(row.overall_score), fontWeight: 'bold' }}>{row.overall_score}</span>
                        <span style={{ color: '#555' }}>/100</span>
                      </td>
                      <td style={{ padding: '0.8rem', color: row.energy_cost_index <= 0.8 ? '#00ea93' : row.energy_cost_index <= 1.2 ? '#ffcc00' : '#ff4d4d' }}>
                        {row.energy_cost_index?.toFixed(2)}
                      </td>
                      <td style={{ padding: '0.8rem', color: row.avg_temp_c >= 38 ? '#ff4d4d' : row.avg_temp_c <= 20 ? '#00ccff' : '#ffcc00' }}>
                        {row.avg_temp_c}°C
                      </td>
                      <td style={{ padding: '0.8rem', color: row.humidity_pct >= 70 ? '#ff4d4d' : row.humidity_pct <= 30 ? '#00ea93' : '#ffcc00' }}>
                        {row.humidity_pct}%
                      </td>
                      <td style={{ padding: '0.8rem', color: row.avg_pue <= 1.35 ? '#00ea93' : row.avg_pue <= 1.5 ? '#ffcc00' : '#ff4d4d' }}>
                        {typeof row.avg_pue === 'number' ? row.avg_pue.toFixed(3) : (row.avg_pue_expected?.toFixed(3) ?? '—')}
                      </td>
                      <td style={{ padding: '0.8rem', color: row.avg_uptime_pct >= 99.5 ? '#00ea93' : row.avg_uptime_pct >= 99 ? '#ffcc00' : '#ff4d4d' }}>
                        {typeof row.avg_uptime_pct === 'number' ? row.avg_uptime_pct.toFixed(2) : '—'}%
                      </td>
                      <td style={{ padding: '0.8rem', color: row.avg_latency_ms <= 70 ? '#00ea93' : row.avg_latency_ms <= 90 ? '#ffcc00' : '#ff4d4d' }}>
                        {typeof row.avg_latency_ms === 'number' ? row.avg_latency_ms.toFixed(1) : '—'}ms
                      </td>
                      <td style={{ padding: '0.8rem', color: row.avg_cooling_efficiency >= 0.85 ? '#00ea93' : row.avg_cooling_efficiency >= 0.7 ? '#ffcc00' : '#ff4d4d' }}>
                        {typeof row.avg_cooling_efficiency === 'number' ? (row.avg_cooling_efficiency * 100).toFixed(1) : '—'}%
                      </td>
                      <td style={{ padding: '0.8rem', color: row.incidents_per_dc <= 15 ? '#00ea93' : row.incidents_per_dc <= 25 ? '#ffcc00' : '#ff4d4d' }}>
                        {typeof row.incidents_per_dc === 'number' ? row.incidents_per_dc.toFixed(1) : '—'}
                      </td>
                      <td style={{ padding: '0.8rem', color: '#ccc' }}>
                        {typeof row.avg_capacity_mw === 'number' ? row.avg_capacity_mw.toFixed(1) : '—'} MW
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Alternates reasoning */}
              {result.alternates?.length > 0 && (
                <div style={{ marginTop: '1.5rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}>
                  {result.alternates.map(alt => (
                    <div key={alt.state || alt.zone_id} style={{ background: 'rgba(0,204,255,0.06)', border: '1px solid rgba(0,204,255,0.2)', borderRadius: '8px', padding: '1rem' }}>
                      <div style={{ color: '#00ccff', fontWeight: 'bold', marginBottom: '0.4rem' }}>{alt.state}</div>
                      <div style={{ fontSize: '0.8rem', color: '#aaa', lineHeight: '1.4' }}>{alt.brief_reason}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default PlanningAgent;
