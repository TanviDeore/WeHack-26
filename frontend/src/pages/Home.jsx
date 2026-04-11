import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <div className="home-container">
      <section className="hero-section">
        <h1 className="hero-title">Intelligent Nexus</h1>
        <p className="hero-subtitle">Central command for your autonomous AI agents. Monitor, plan, and optimize operations seamlessly.</p>
      </section>

      <div className="agents-grid">
        <Link to="/planning" className="agent-card">
          <div className="card-icon">🧠</div>
          <h2 className="card-title">Planning Agent</h2>
          <p className="card-description">Coordinates strategic timelines, visualizes workflows, and prepares actionable tasks for your organization.</p>
        </Link>
        
        <Link to="/operations" className="agent-card">
          <div className="card-icon">⚙️</div>
          <h2 className="card-title">Operations Agent</h2>
          <p className="card-description">Monitors real-time systems, automates daily tasks, and keeps the operational pipelines flowing.</p>
        </Link>
        
        <Link to="/maintenance" className="agent-card">
          <div className="card-icon">🔧</div>
          <h2 className="card-title">Predictive Maintenance</h2>
          <p className="card-description">Analyzes system health patterns to foresee critical failures and schedule pro-active repairs.</p>
        </Link>
      </div>
    </div>
  );
};

export default Home;
