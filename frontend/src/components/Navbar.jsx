import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path ? 'nav-item active' : 'nav-item';
  };

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <span className="brand-accent">✦</span> Nexus
      </Link>
      <div className="navbar-links">
        <Link to="/planning" className={isActive('/planning')}>Planning</Link>
        <Link to="/operations" className={isActive('/operations')}>Operations</Link>
        <Link to="/maintenance" className={isActive('/maintenance')}>Maintenance</Link>
      </div>
    </nav>
  );
};

export default Navbar;
