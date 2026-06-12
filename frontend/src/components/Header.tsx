export function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <div className="logo">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="6" fill="#1a1a2e" />
              <path d="M8 12h16M8 16h16M8 20h12" stroke="#4fc3f7" strokeWidth="2" strokeLinecap="round" />
              <circle cx="24" cy="20" r="3" fill="#66bb6a" />
            </svg>
          </div>
          <div>
            <h1 className="header-title">ERP Migration Accelerator</h1>
            <p className="header-subtitle">Army Logistics Systems Consolidation</p>
          </div>
        </div>
        <div className="header-right">
          <span className="header-badge">GCSS-Army + LMP → ALERP</span>
          <span className="header-badge header-badge-ai">Powered by Devin AI</span>
        </div>
      </div>
    </header>
  );
}
