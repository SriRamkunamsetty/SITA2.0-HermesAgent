import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Video, 
  BarChart3, 
  Settings, 
  LogOut,
  Activity,
  Cpu,
  Database,
  Wifi,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Eye,
  Play,
  Pause,
  RefreshCw
} from 'lucide-react';
import StarField from '@/components/StarField';
import GlassPanel from '@/components/GlassPanel';
import StatusIndicator from '@/components/StatusIndicator';
import AnimatedCounter from '@/components/AnimatedCounter';
import NeonButton from '@/components/NeonButton';
import { cn } from '@/lib/utils';

const sidebarItems = [
  { icon: LayoutDashboard, label: 'Overview', id: 'overview' },
  { icon: Video, label: 'Data Ingest', id: 'ingest' },
  { icon: BarChart3, label: 'Analytics', id: 'analytics' },
  { icon: Settings, label: 'System', id: 'system' },
];

const Dashboard = () => {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState('overview');
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const [stats, setStats] = useState({
    dataPoints: 2847592,
    latency: 23,
    accuracy: 99.7,
    activeNodes: 847,
  });

  // Simulate live data updates
  useEffect(() => {
    const interval = setInterval(() => {
      setStats(prev => ({
        dataPoints: prev.dataPoints + Math.floor(Math.random() * 1000),
        latency: 20 + Math.random() * 10,
        accuracy: 99.5 + Math.random() * 0.4,
        activeNodes: 840 + Math.floor(Math.random() * 20),
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-background flex overflow-hidden">
      <StarField />

      {/* Sidebar */}
      <aside className="w-20 lg:w-64 bg-card/50 border-r border-border/50 backdrop-blur-xl flex flex-col z-20">
        {/* Logo */}
        <div className="p-4 lg:p-6 border-b border-border/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/20 border border-primary/50 flex items-center justify-center">
              <Cpu className="w-5 h-5 text-primary" />
            </div>
            <div className="hidden lg:block">
              <h1 className="font-orbitron text-lg font-bold text-primary">SITA</h1>
              <p className="font-mono text-[10px] text-muted-foreground">CONTROL ROOM</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2 lg:p-4">
          <ul className="space-y-1">
            {sidebarItems.map(item => {
              const Icon = item.icon;
              const isActive = activeSection === item.id;
              return (
                <li key={item.id}>
                  <button
                    onClick={() => setActiveSection(item.id)}
                    className={cn(
                      'w-full flex items-center gap-3 p-3 rounded-lg transition-all duration-200',
                      isActive 
                        ? 'bg-primary/20 text-primary border border-primary/30' 
                        : 'text-muted-foreground hover:text-foreground hover:bg-muted/30'
                    )}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    <span className="hidden lg:block font-mono text-sm">{item.label}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Logout */}
        <div className="p-2 lg:p-4 border-t border-border/50">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 p-3 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all"
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            <span className="hidden lg:block font-mono text-sm">Disconnect</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto relative z-10">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-xl border-b border-border/50 px-4 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h2 className="font-orbitron text-xl font-semibold">
                {sidebarItems.find(i => i.id === activeSection)?.label || 'Dashboard'}
              </h2>
              <StatusIndicator status="online" label="NEURAL GRID ACTIVE" />
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Clock className="w-4 h-4" />
                <span className="font-mono text-sm">
                  {new Date().toLocaleTimeString('en-US', { hour12: false })}
                </span>
              </div>
              <div className="px-3 py-1 bg-primary/10 border border-primary/30 rounded-full">
                <span className="font-mono text-xs text-primary">CLEARANCE: ALPHA</span>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="p-4 lg:p-8">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <GlassPanel className="p-6" corners>
              <div className="flex items-center justify-between mb-4">
                <Activity className="w-5 h-5 text-primary" />
                <TrendingUp className="w-4 h-4 text-success" />
              </div>
              <div className="font-orbitron text-2xl lg:text-3xl font-bold text-foreground mb-1">
                <AnimatedCounter value={stats.dataPoints} suffix="" />
              </div>
              <p className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
                Data Points Processed
              </p>
            </GlassPanel>

            <GlassPanel className="p-6" corners>
              <div className="flex items-center justify-between mb-4">
                <Wifi className="w-5 h-5 text-primary" />
                <CheckCircle className="w-4 h-4 text-success" />
              </div>
              <div className="font-orbitron text-2xl lg:text-3xl font-bold text-foreground mb-1">
                <AnimatedCounter value={stats.latency} suffix="ms" decimals={1} />
              </div>
              <p className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
                System Latency
              </p>
            </GlassPanel>

            <GlassPanel className="p-6" corners>
              <div className="flex items-center justify-between mb-4">
                <Eye className="w-5 h-5 text-primary" />
                <CheckCircle className="w-4 h-4 text-success" />
              </div>
              <div className="font-orbitron text-2xl lg:text-3xl font-bold text-foreground mb-1">
                <AnimatedCounter value={stats.accuracy} suffix="%" decimals={1} />
              </div>
              <p className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
                Detection Accuracy
              </p>
            </GlassPanel>

            <GlassPanel className="p-6" corners>
              <div className="flex items-center justify-between mb-4">
                <Database className="w-5 h-5 text-primary" />
                <StatusIndicator status="online" />
              </div>
              <div className="font-orbitron text-2xl lg:text-3xl font-bold text-foreground mb-1">
                <AnimatedCounter value={stats.activeNodes} />
              </div>
              <p className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
                Active Nodes
              </p>
            </GlassPanel>
          </div>

          {/* Main Panels */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Video Feed Panel */}
            <GlassPanel className="lg:col-span-2 overflow-hidden" corners>
              <div className="p-4 border-b border-border/50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Video className="w-5 h-5 text-primary" />
                  <span className="font-orbitron text-sm font-semibold">DATA INGEST FEED</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsAnalyzing(!isAnalyzing)}
                    className={cn(
                      'p-2 rounded-lg transition-all',
                      isAnalyzing ? 'bg-primary/20 text-primary' : 'bg-muted/30 text-muted-foreground'
                    )}
                  >
                    {isAnalyzing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </button>
                  <button className="p-2 rounded-lg bg-muted/30 text-muted-foreground hover:text-foreground transition-colors">
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="aspect-video bg-background/50 relative">
                {/* Simulated video feed placeholder */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-20 h-20 rounded-full border-2 border-primary/30 flex items-center justify-center mb-4 mx-auto">
                      <Video className="w-10 h-10 text-primary/50" />
                    </div>
                    <p className="font-mono text-sm text-muted-foreground">
                      {isAnalyzing ? 'ANALYZING FEED...' : 'FEED PAUSED'}
                    </p>
                  </div>
                </div>
                {/* Overlay Grid */}
                <div 
                  className="absolute inset-0 opacity-20"
                  style={{
                    backgroundImage: 'linear-gradient(hsl(187 100% 48% / 0.1) 1px, transparent 1px), linear-gradient(90deg, hsl(187 100% 48% / 0.1) 1px, transparent 1px)',
                    backgroundSize: '40px 40px',
                  }}
                />
                {/* Status Overlay */}
                <div className="absolute top-4 left-4">
                  <StatusIndicator status={isAnalyzing ? 'processing' : 'offline'} label={isAnalyzing ? 'LIVE' : 'PAUSED'} />
                </div>
                <div className="absolute top-4 right-4 font-mono text-xs text-primary">
                  CAM-001 // SECTOR-A
                </div>
              </div>
            </GlassPanel>

            {/* System Status Panel */}
            <GlassPanel className="flex flex-col" corners>
              <div className="p-4 border-b border-border/50">
                <div className="flex items-center gap-3">
                  <Cpu className="w-5 h-5 text-primary" />
                  <span className="font-orbitron text-sm font-semibold">SYSTEM STATUS</span>
                </div>
              </div>
              <div className="flex-1 p-4 space-y-4">
                {/* CPU Usage */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs text-muted-foreground">CPU UTILIZATION</span>
                    <span className="font-mono text-xs text-primary">78%</span>
                  </div>
                  <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary rounded-full transition-all duration-1000"
                      style={{ width: '78%' }}
                    />
                  </div>
                </div>

                {/* Memory */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs text-muted-foreground">MEMORY ALLOCATION</span>
                    <span className="font-mono text-xs text-primary">64%</span>
                  </div>
                  <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary rounded-full transition-all duration-1000"
                      style={{ width: '64%' }}
                    />
                  </div>
                </div>

                {/* Neural Load */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs text-muted-foreground">NEURAL LOAD</span>
                    <span className="font-mono text-xs text-warning">92%</span>
                  </div>
                  <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-warning rounded-full transition-all duration-1000"
                      style={{ width: '92%' }}
                    />
                  </div>
                </div>

                {/* Status List */}
                <div className="pt-4 border-t border-border/50 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-muted-foreground">NEURAL CORE</span>
                    <StatusIndicator status="online" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-muted-foreground">DATA STREAMS</span>
                    <StatusIndicator status="processing" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-muted-foreground">THREAT MONITOR</span>
                    <StatusIndicator status="online" />
                  </div>
                </div>
              </div>
            </GlassPanel>
          </div>

          {/* Alert Panel */}
          <div className="mt-6">
            <GlassPanel className="p-4" corners>
              <div className="flex items-center gap-3 mb-4">
                <AlertTriangle className="w-5 h-5 text-warning" />
                <span className="font-orbitron text-sm font-semibold">RECENT ALERTS</span>
              </div>
              <div className="space-y-2">
                {[
                  { time: '14:23:47', message: 'ANOMALY DETECTED // SECTOR-7 // ANALYZING', level: 'warning' },
                  { time: '14:21:12', message: 'DATA STREAM RECONNECTED // NODE-847', level: 'success' },
                  { time: '14:18:55', message: 'PATTERN MATCH // INCIDENT-TYPE-4 IDENTIFIED', level: 'info' },
                ].map((alert, index) => (
                  <div 
                    key={index}
                    className="flex items-center gap-4 p-3 bg-muted/10 rounded-lg"
                  >
                    <span className="font-mono text-xs text-muted-foreground">{alert.time}</span>
                    <div className={cn(
                      'w-2 h-2 rounded-full',
                      alert.level === 'warning' && 'bg-warning',
                      alert.level === 'success' && 'bg-success',
                      alert.level === 'info' && 'bg-primary'
                    )} />
                    <span className="font-mono text-xs text-foreground">{alert.message}</span>
                  </div>
                ))}
              </div>
            </GlassPanel>
          </div>
        </div>

        {/* Status Strip */}
        <footer className="sticky bottom-0 bg-background/90 backdrop-blur-xl border-t border-border/50 px-4 lg:px-8 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <StatusIndicator status="online" label="SYSTEM ONLINE" />
              <div className="flex items-center gap-2 text-muted-foreground">
                <Wifi className="w-4 h-4" />
                <span className="font-mono text-xs">LATENCY: {stats.latency.toFixed(1)}ms</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Database className="w-4 h-4" />
                <span className="font-mono text-xs">NODES: {stats.activeNodes}</span>
              </div>
            </div>
            <div className="font-mono text-xs text-muted-foreground">
              CLEARANCE LEVEL: ALPHA // SESSION ENCRYPTED
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default Dashboard;
