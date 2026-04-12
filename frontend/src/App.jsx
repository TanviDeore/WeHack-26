import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import PlanningAgent from './pages/PlanningAgent';
import OperationsAgent from './pages/OperationsAgent';
import PredictiveMaintenance from './pages/PredictiveMaintenance';

import DataCenterDashboard from './pages/DataCenterDashboard';

function App() {
  return (
    <Router>
      <Navbar />
      <div className="page-container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/datacenter/:id" element={<DataCenterDashboard />} />
          <Route path="/planning" element={<PlanningAgent />} />
          <Route path="/operations" element={<OperationsAgent />} />
          <Route path="/maintenance" element={<PredictiveMaintenance />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
