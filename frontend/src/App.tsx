import { useState, useEffect } from 'react';
import { Droplet, Zap, RefreshCw, ArrowUp, ArrowDown, ArrowRight, TrendingUp, History as HistoryIcon, ShieldCheck, Battery } from 'lucide-react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts';
import { format, parseISO, formatDistanceToNow, differenceInMinutes } from 'date-fns';
import './App.css';

const Logo = () => (
  <svg width="24" height="24" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="256" cy="256" r="240" fill="#4ade80" />
    <text x="50%" y="50%" dy=".35em" fill="white" font-family="Inter, sans-serif" font-weight="900" font-size="280" text-anchor="middle">t1</text>
  </svg>
);

function App() {
  const [status, setStatus] = useState<any>(null);
  const [history, setHistory] = useState<any>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  const fetchData = async () => {
    try {
      // Consolidate fetches to help Safari sync state updates
      const [statusRes, historyRes] = await Promise.all([
        fetch('/api/status', { cache: 'no-store' }),
        fetch('/api/history?hours=24', { cache: 'no-store' })
      ]);
      
      const statusData = await statusRes.json();
      const historyData = await historyRes.json();
      
      setStatus(statusData);
      setHistory(historyData);
    } catch (err) {
      console.error('Failed to fetch data', err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Poll every minute
    return () => clearInterval(interval);
  }, []);

  const triggerSync = async () => {
    setIsSyncing(true);
    try {
      await fetch('/api/sync', { method: 'POST' });
      await fetchData();
    } finally {
      setIsSyncing(false);
    }
  };

  const getTrendIcon = (arrow: string) => {
    switch (arrow) {
      case '↑': return <ArrowUp className="text-danger" />;
      case '↓': return <ArrowDown className="text-danger" />;
      case '→': return <ArrowRight className="text-primary" />;
      case '↗': return <ArrowUp style={{ transform: 'rotate(45deg)' }} className="text-accent" />;
      case '↘': return <ArrowDown style={{ transform: 'rotate(-45deg)' }} className="text-accent" />;
      default: return <ArrowRight />;
    }
  };

  const glucoseColor = (val: number) => {
    if (val < 70) return 'text-danger';
    if (val > 180) return 'text-accent';
    return 'text-primary';
  };

  const formatInsulin = (val: any) => {
    const num = parseFloat(val);
    return isNaN(num) ? '0.00' : num.toFixed(2);
  };

  // Combine and sort boluses and basals for the history list
  const combinedEvents = () => {
    if (!history) return [];
    const bols = (history.boluses || []).map((b: any) => ({ ...b, type: 'BOLUS' }));
    const bass = (history.basals || []).map((b: any) => ({ ...b, type: 'BASAL' }));
    return [...bols, ...bass].sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    ).slice(0, 10);
  };

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1><Logo /> Type1 Monitor</h1>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          {status?.pump_status && (
            <div className="sync-status" style={{ color: 'var(--text-muted)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: status.pump_status.battery_percent < 20 ? 'var(--danger)' : 'inherit' }}>
                <Battery size={16} />
                <span>{status.pump_status.battery_percent}%</span>
              </div>
              
              <div style={{ display: 'flex', gap: '0.75rem', marginLeft: '0.5rem', borderLeft: '1px solid var(--border)', paddingLeft: '0.75rem', fontSize: '0.7rem', opacity: 0.8 }}>
                {status.pump_status.last_event_time && (
                  <span>
                    <strong style={{ color: 'var(--text-main)' }}>Tandem:</strong> {formatDistanceToNow(parseISO(status.pump_status.last_event_time), { addSuffix: true })}
                  </span>
                )}
                {status.pump_status.dexcom_last_sync && (
                  <span style={{ 
                    color: differenceInMinutes(new Date(), parseISO(status.pump_status.dexcom_last_sync)) > 5 ? 'var(--danger)' : 'inherit',
                    fontWeight: differenceInMinutes(new Date(), parseISO(status.pump_status.dexcom_last_sync)) > 5 ? 'bold' : 'normal'
                  }}>
                    <strong style={{ color: 'var(--text-main)' }}>Dexcom:</strong> {formatDistanceToNow(parseISO(status.pump_status.dexcom_last_sync), { addSuffix: true })}
                  </span>
                )}
              </div>
            </div>
          )}
          <div className="sync-status">
            <ShieldCheck size={16} className="text-primary" />
            <span>System Active</span>
            <button 
              className="icon-btn" 
              onClick={triggerSync} 
              disabled={isSyncing}
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0 0.5rem' }}
            >
              <RefreshCw size={14} className={`${isSyncing ? 'spin' : ''} text-muted`} />
            </button>
          </div>
        </div>
      </header>

      <div className="main-grid">
        <section className="glass-card glucose-card">
          <span className="glucose-label">Current Glucose</span>
          <div className={`glucose-value ${glucoseColor(status?.glucose?.value)}`}>
            {status?.glucose?.value || '--'}
          </div>
          <div className="glucose-trend">
            {status?.glucose?.trend_arrow && getTrendIcon(status.glucose.trend_arrow)}
            <span>{status?.glucose?.trend || 'Stable'}</span>
          </div>
          <div className="glucose-label" style={{ marginTop: '1rem', fontSize: '0.75rem' }}>
            mg/dL · {status?.glucose?.timestamp ? format(parseISO(status.glucose.timestamp), 'h:mm a') : '--:--'}
          </div>
        </section>

        {/* Using a key based on status presence forces a full repaint in Safari when data arrives */}
        <div className="stats-container" key={status ? 'status-loaded' : 'status-loading'}>
          <section className="glass-card stat-card">
            <div className="stat-icon">
              <Zap className="text-secondary" />
            </div>
            <div className="stat-info">
              <h3>Insulin On Board</h3>
              <p className="text-secondary" key={status?.iob?.amount}>
                {status ? formatInsulin(status.iob?.amount) : '--.--'} U
              </p>
              {status?.iob?.created_at && (
                <div style={{ fontSize: '0.7rem', opacity: 0.6, marginTop: '0.2rem' }}>
                  Recorded {format(parseISO(status.iob.created_at), 'MMM d, h:mm a')}
                </div>
              )}
            </div>
          </section>

          <section className="glass-card stat-card">
            <div className="stat-icon">
              <Droplet className="text-primary" />
            </div>
            <div className="stat-info">
              <h3>Last / 24h Bolus</h3>
              <p className="text-primary" key={history?.boluses?.length}>
                {history ? (
                  <>
                    {history.boluses?.length > 0 ? formatInsulin(history.boluses[history.boluses.length - 1].amount) : '0.00'} U
                    <span style={{ opacity: 0.4, margin: '0 0.5rem', fontWeight: 400 }}>/</span>
                    {formatInsulin(history.boluses?.reduce((acc: number, curr: any) => acc + parseFloat(curr.amount), 0))} U
                  </>
                ) : '--.-- U'}
              </p>
            </div>
          </section>

          <section className="glass-card stat-card">
            <div className="stat-icon">
              <TrendingUp className="text-accent" />
            </div>
            <div className="stat-info">
              <h3>Time In Range</h3>
              <p className="text-accent">85%</p>
            </div>
          </section>
        </div>

        <section className="glass-card chart-card">
          <div className="chart-header">
            <h2><TrendingUp size={18} /> 24-Hour Trend</h2>
            <div className="glucose-label">Glucose (mg/dL) & Insulin</div>
          </div>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <AreaChart data={history?.glucose}>
                <defs>
                  <linearGradient id="colorGlucose" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(str) => format(parseISO(str), 'h a')}
                  stroke="var(--text-muted)"
                  fontSize={12}
                />
                <YAxis domain={[40, 300]} stroke="var(--text-muted)" fontSize={12} />
                <Tooltip 
                  contentStyle={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '1rem' }}
                  labelFormatter={(str) => format(parseISO(str as string), 'h:mm a, MMM d')}
                />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="var(--primary)" 
                  fillOpacity={1} 
                  fill="url(#colorGlucose)" 
                  strokeWidth={3}
                  animationDuration={1500}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="glass-card history-card">
          <div className="chart-header">
            <h2><HistoryIcon size={18} /> Recent Pump Events</h2>
          </div>
          <div className="history-list">
            {combinedEvents().map((e: any) => (
              <div key={e.id || e.basal_id || e.bolus_id} className="history-item">
                <div className="history-item-left">
                  <span className={`type-tag ${e.type === 'BOLUS' ? 'type-bolus' : 'type-basal'}`}>
                    {e.type}
                  </span>
                  <strong>{e.type === 'BOLUS' ? formatInsulin(e.amount) : formatInsulin(e.rate)} U{e.type === 'BASAL' ? '/hr' : ''}</strong>
                </div>
                <span className="history-time">{format(parseISO(e.timestamp), 'MMM d, h:mm a')}</span>
              </div>
            ))}
            {(!history || combinedEvents().length === 0) && (
              <p className="glucose-label" style={{ textAlign: 'center', padding: '1rem' }}>{history ? 'No recent events found' : 'Loading events...'}</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
