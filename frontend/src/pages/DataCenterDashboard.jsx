import { useParams, Link } from 'react-router-dom';
import OperationsAgent from './OperationsAgent';
import PredictiveMaintenance from './PredictiveMaintenance';
import { useState } from 'react';

const DataCenterDashboard = () => {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState(null); // start as null to show selection screen

  return (
    <div className="agent-page-container">
      {activeTab === null ? (
        <Link to="/" className="back-button">← BACK TO MAP</Link>
      ) : (
        <button className="back-button" onClick={() => setActiveTab(null)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '1rem', color: '#ccc', textDecoration: 'none' }}>← BACK TO DATA CENTER Selection</button>
      )}
      
      <div className="agent-header" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <h1 className="hero-title" style={{ fontSize: '2.5rem', margin: '0', textAlign: 'left' }}>Data Center: {id.replace('dc_usa_', 'DC-USA-')}</h1>
          <p className="hero-subtitle" style={{ margin: 0, textAlign: 'left' }}>Unified diagnostic and operational view.</p>
        </div>
        
        {activeTab !== null && (
          <div className="tabs" style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <button 
              className={`tab-btn ${activeTab === 'operations' ? 'active' : ''}`}
              onClick={() => setActiveTab('operations')}
              style={{
                padding: '0.8rem 1.5rem',
                background: activeTab === 'operations' ? 'var(--accent-1)' : 'transparent',
                color: activeTab === 'operations' ? '#0a0a0a' : 'var(--accent-1)',
                border: '1px solid var(--accent-1)',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              Operations Agent
            </button>
            <button 
              className={`tab-btn ${activeTab === 'maintenance' ? 'active' : ''}`}
              onClick={() => setActiveTab('maintenance')}
              style={{
                padding: '0.8rem 1.5rem',
                background: activeTab === 'maintenance' ? 'var(--accent-2)' : 'transparent',
                color: activeTab === 'maintenance' ? '#0a0a0a' : 'var(--accent-2)',
                border: '1px solid var(--accent-2)',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              Predictive Maintenance
            </button>
          </div>
        )}
      </div>

      <div className="tab-content" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        {activeTab === null && (
          <div className="agents-grid" style={{ display: 'flex', gap: '2rem', justifyContent: 'center', marginTop: '2rem' }}>
            <div 
              className="agent-card" 
              onClick={() => setActiveTab('operations')}
              style={{ cursor: 'pointer', border: '1px solid var(--accent-1)', flex: 1, maxWidth: '400px' }}
            >
              <div className="card-icon">⚙️</div>
              <h2 className="card-title">Operations Agent</h2>
              <p className="card-description">Monitors real-time systems, automates daily tasks, and keeps the operational pipelines flowing.</p>
            </div>
            
            <div 
              className="agent-card" 
              onClick={() => setActiveTab('maintenance')}
              style={{ cursor: 'pointer', border: '1px solid var(--accent-2)', flex: 1, maxWidth: '400px' }}
            >
              <div className="card-icon">🔧</div>
              <h2 className="card-title">Predictive Maintenance</h2>
              <p className="card-description">Analyzes system health patterns to foresee critical failures and schedule pro-active repairs.</p>
            </div>
          </div>
        )}

        {/* We pass a prop `dcIdProp` so the child component knows to hide its own back button and fixed headers */}
        {activeTab === 'operations' && (
          <div>
            <OperationsAgent dcIdProp={id} />
          </div>
        )}
        
        {activeTab === 'maintenance' && (
          <div>
            <PredictiveMaintenance dcIdProp={id} />
          </div>
        )}
      </div>
    </div>
  );
};

export default DataCenterDashboard;
