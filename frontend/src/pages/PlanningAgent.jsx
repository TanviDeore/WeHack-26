import { Link } from 'react-router-dom';

const PlanningAgent = () => {
  return (
    <div className="agent-page-container">
      <Link to="/" className="back-button">← BACK TO HUB</Link>
      
      <div className="agent-header">
        <div className="card-icon">🧠</div>
        <div>
          <h1 className="hero-title" style={{ fontSize: '3rem', marginBottom: '0.2rem', textAlign: 'left' }}>Planning Agent</h1>
          <p className="hero-subtitle" style={{ margin: 0, textAlign: 'left' }}>Strategic Timeline & Task Coordination</p>
        </div>
      </div>
      
      <div className="agent-workspace">
        <div className="workspace-status">SYSTEM IDLE // AWAITING COMMANDS</div>
      </div>
    </div>
  );
};

export default PlanningAgent;
