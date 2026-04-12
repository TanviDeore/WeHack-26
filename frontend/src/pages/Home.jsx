import { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps';

const geoUrl = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json";

// Approximate coordinates for state hubs
const STATE_COORDS = {
  "California": [-119.4179, 36.7783],
  "Florida": [-81.5158, 27.9944],
  "Illinois": [-89.3985, 40.6331],
  "Nevada": [-116.4194, 38.8026],
  "New York": [-74.0060, 40.7128],
  "Ohio": [-82.9071, 40.4173],
  "Texas": [-99.9018, 31.9686],
  "Virginia": [-78.6569, 37.4316],
  "Washington": [-120.7401, 47.7511]
};

// Deterministic pseudo-random number generator
const prng = (seed) => {
  let x = Math.sin(seed++) * 10000;
  return x - Math.floor(x);
};

const Home = () => {
  const navigate = useNavigate();
  const [datacenters, setDatacenters] = useState([]);
  const [hoveredDc, setHoveredDc] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/agent/datacenters')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') setDatacenters(data.datacenters);
      })
      .catch(err => console.error(err));
  }, []);

  const markers = useMemo(() => {
    return datacenters.map((dc, index) => {
      // Find the state name by matching against our coords keys
      const stateMatch = Object.keys(STATE_COORDS).find(st => dc.name.includes(st));
      if (!stateMatch) return null;
      
      const baseCoord = STATE_COORDS[stateMatch];
      
      // Jitter so they don't overlap exactly (deterministic based on index)
      const jitterX = (prng(index) - 0.5) * 3.5; // +/- longitude
      const jitterY = (prng(index + 100) - 0.5) * 3.5; // +/- latitude

      return {
        ...dc,
        coordinates: [baseCoord[0] + jitterX, baseCoord[1] + jitterY]
      };
    }).filter(Boolean);
  }, [datacenters]);

  return (
    <div className="home-container" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <section className="hero-section" style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1 className="hero-title" style={{ fontSize: '3.5rem', marginBottom: '1rem', color: '#fff' }}>Intelligent Nexus</h1>
        <p className="hero-subtitle" style={{ fontSize: '1.2rem', color: '#ccc', maxWidth: '800px', margin: '0 auto' }}>
          Select a Data Center to enter its predictive operations dashboard, or coordinate organization-wide tasks.
        </p>
      </section>

      {/* Map Section */}
      <div 
        className="map-container" 
        style={{ 
          width: '100%', 
          maxWidth: '1000px', 
          backgroundColor: '#111', 
          borderRadius: '16px', 
          border: '1px solid #333',
          padding: '2rem',
          position: 'relative'
        }}
      >
        {hoveredDc && (
          <div style={{
            position: 'absolute',
            top: '2rem',
            right: '2rem',
            background: 'rgba(0,0,0,0.8)',
            border: '1px solid #00ea93',
            padding: '1rem',
            borderRadius: '8px',
            color: '#fff',
            zIndex: 10,
            pointerEvents: 'none'
          }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: '#00ea93' }}>{hoveredDc.name}</h3>
            <p style={{ margin: 0, fontSize: '0.8rem', color: '#aaa' }}>ID: {hoveredDc.id}</p>
            <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.8rem', fontStyle: 'italic' }}>Click to view dashboard</p>
          </div>
        )}

        <ComposableMap projection="geoAlbersUsa">
          <Geographies geography={geoUrl}>
            {({ geographies }) =>
              geographies.map(geo => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill="#1a1a1a"
                  stroke="#333"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: "none" },
                    hover: { outline: "none", fill: "#222" },
                    pressed: { outline: "none" },
                  }}
                />
              ))
            }
          </Geographies>

          {markers.map((marker) => (
            <Marker 
              key={marker.id} 
              coordinates={marker.coordinates}
              onClick={() => navigate(`/datacenter/${marker.id}`)}
              onMouseEnter={() => setHoveredDc(marker)}
              onMouseLeave={() => setHoveredDc(null)}
              style={{ cursor: 'pointer' }}
            >
              <circle r={hoveredDc?.id === marker.id ? 8 : 4} fill={hoveredDc?.id === marker.id ? "#00ea93" : "#00ccff"} />
              <circle r={12} fill="transparent" /> {/* Larger hit area */}
            </Marker>
          ))}
        </ComposableMap>
      </div>

      {/* Call to Actions below map */}
      <div style={{ marginTop: '3rem', width: '100%', maxWidth: '1000px', display: 'flex', justifyContent: 'center' }}>
        <Link 
          to="/planning" 
          className="agent-card" 
          style={{ 
            textDecoration: 'none', 
            background: 'rgba(255,255,255,0.05)', 
            border: '1px solid rgba(255,255,255,0.1)',
            padding: '2rem',
            borderRadius: '12px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
            maxWidth: '400px',
            transition: 'all 0.2s ease',
            textAlign: 'center'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = 'translateY(-5px)';
            e.currentTarget.style.borderColor = 'var(--accent-2)';
            e.currentTarget.style.boxShadow = '0 10px 30px rgba(0, 234, 147, 0.1)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = 'none';
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          <div className="card-icon" style={{ fontSize: '3rem', marginBottom: '1rem' }}>🧠</div>
          <h2 className="card-title" style={{ color: '#fff', marginBottom: '0.5rem' }}>Global Planning Agent</h2>
          <p className="card-description" style={{ color: '#aaa', fontSize: '0.9rem', lineHeight: '1.5' }}>
            Coordinates strategic timelines, visualizes workflows, and prepares actionable tasks across all data centers globally.
          </p>
        </Link>
      </div>

    </div>
  );
};

export default Home;
