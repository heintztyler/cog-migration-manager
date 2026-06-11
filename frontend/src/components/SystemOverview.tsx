export function SystemOverview() {
  return (
    <section className="system-overview">
      <div className="system-flow">
        <div className="system-card legacy">
          <div className="system-icon">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <rect x="2" y="4" width="24" height="20" rx="2" stroke="currentColor" strokeWidth="1.5" />
              <line x1="2" y1="10" x2="26" y2="10" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="6" cy="7" r="1" fill="currentColor" />
              <circle cx="10" cy="7" r="1" fill="currentColor" />
              <line x1="6" y1="14" x2="22" y2="14" stroke="currentColor" strokeWidth="1" opacity="0.5" />
              <line x1="6" y1="17" x2="18" y2="17" stroke="currentColor" strokeWidth="1" opacity="0.5" />
              <line x1="6" y1="20" x2="20" y2="20" stroke="currentColor" strokeWidth="1" opacity="0.5" />
            </svg>
          </div>
          <h3>GCSS-Army</h3>
          <p className="system-type">Legacy System Alpha</p>
          <ul className="system-tables">
            <li>Equipment Master</li>
            <li>Work Orders</li>
            <li>Supply/Materials</li>
            <li>Unit Readiness</li>
          </ul>
          <span className="system-count">4 tables</span>
        </div>

        <div className="flow-arrow">
          <svg width="60" height="40" viewBox="0 0 60 40">
            <defs>
              <linearGradient id="arrowGrad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#ef5350" />
                <stop offset="100%" stopColor="#66bb6a" />
              </linearGradient>
            </defs>
            <line x1="0" y1="20" x2="50" y2="20" stroke="url(#arrowGrad)" strokeWidth="2" />
            <polygon points="48,14 58,20 48,26" fill="#66bb6a" />
          </svg>
          <span className="flow-label">Devin AI</span>
        </div>

        <div className="system-card unified">
          <div className="system-icon">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <rect x="2" y="4" width="24" height="20" rx="2" stroke="currentColor" strokeWidth="1.5" />
              <line x1="2" y1="10" x2="26" y2="10" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="6" cy="7" r="1" fill="currentColor" />
              <circle cx="10" cy="7" r="1" fill="currentColor" />
              <circle cx="14" cy="7" r="1" fill="currentColor" />
              <path d="M10 15l3 3 5-6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h3>ALERP</h3>
          <p className="system-type">Unified Target System</p>
          <ul className="system-tables">
            <li>Assets</li>
            <li>Maintenance Orders</li>
            <li>Supply Items</li>
            <li>Vendors</li>
            <li>Procurement</li>
            <li>Inventory</li>
            <li>Shipments</li>
            <li>Readiness Reports</li>
          </ul>
          <span className="system-count">8 tables</span>
        </div>

        <div className="flow-arrow flow-arrow-reverse">
          <svg width="60" height="40" viewBox="0 0 60 40" style={{ transform: 'scaleX(-1)' }}>
            <defs>
              <linearGradient id="arrowGrad2" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#ef5350" />
                <stop offset="100%" stopColor="#66bb6a" />
              </linearGradient>
            </defs>
            <line x1="0" y1="20" x2="50" y2="20" stroke="url(#arrowGrad2)" strokeWidth="2" />
            <polygon points="48,14 58,20 48,26" fill="#66bb6a" />
          </svg>
          <span className="flow-label">Devin AI</span>
        </div>

        <div className="system-card legacy">
          <div className="system-icon">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <rect x="2" y="4" width="24" height="20" rx="2" stroke="currentColor" strokeWidth="1.5" />
              <line x1="2" y1="10" x2="26" y2="10" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="6" cy="7" r="1" fill="currentColor" />
              <circle cx="10" cy="7" r="1" fill="currentColor" />
              <line x1="6" y1="14" x2="22" y2="14" stroke="currentColor" strokeWidth="1" opacity="0.5" />
              <line x1="6" y1="17" x2="18" y2="17" stroke="currentColor" strokeWidth="1" opacity="0.5" />
              <line x1="6" y1="20" x2="20" y2="20" stroke="currentColor" strokeWidth="1" opacity="0.5" />
            </svg>
          </div>
          <h3>LMP</h3>
          <p className="system-type">Legacy System Bravo</p>
          <ul className="system-tables">
            <li>Vendor Master</li>
            <li>Purchase Orders</li>
            <li>PO Line Items</li>
            <li>Warehouse Inventory</li>
            <li>Shipment Tracking</li>
          </ul>
          <span className="system-count">5 tables</span>
        </div>
      </div>
    </section>
  );
}
