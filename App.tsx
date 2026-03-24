
import React, { useState, useEffect } from 'react';
import { 
  Calendar as CalendarIcon, 
  CheckCircle2, 
  LayoutDashboard, 
  Plus, 
  Settings as SettingsIcon,
  Sun,
  Trash2,
  Mail,
  Sparkles,
  RefreshCw,
  Activity,
  AlertCircle
} from 'lucide-react';
import { Task, TaskPriority } from './types';
import { apiService } from './services/apiService';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'calendar' | 'settings'>('dashboard');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [emailSending, setEmailSending] = useState(false);
  const [health, setHealth] = useState<any>(null);
  const [settings, setSettings] = useState({ email: '', name: '' });
  const [newTask, setNewTask] = useState({ title: '', priority: 'medium' as TaskPriority });

  useEffect(() => {
    loadTasks();
    checkHealth();
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await apiService.getSettings();
      setSettings(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiService.saveSettings(settings);
      alert("Settings saved successfully!");
    } catch (e) {
      alert("Failed to save settings.");
    }
  };

  const checkHealth = async () => {
    try {
      const res = await fetch('/api/health');
      const data = await res.json();
      setHealth(data);
    } catch (e) {
      setHealth({ status: 'offline' });
    }
  };

  const loadTasks = async () => {
    setIsSyncing(true);
    try {
      const data = await apiService.getTasks();
      setTasks(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleAddTask = async (data: any) => {
    await apiService.createTask(data);
    loadTasks();
    setIsModalOpen(false);
  };

  const handleToggle = async (id: string) => {
    await apiService.toggleTask(id);
    setTasks(prev => prev.map(t => t.id === id ? {...t, completed: !t.completed} : t));
  };

  const handleDelete = async (id: string) => {
    await apiService.deleteTask(id);
    setTasks(prev => prev.filter(t => t.id !== id));
  };

  const triggerEmail = async () => {
    setEmailSending(true);
    try {
      await apiService.triggerManualBriefing();
      alert("Zen Briefing sent! Check your inbox.");
    } catch (e) {
      alert("Briefing failed. Check Config tab for health status.");
    } finally {
      setEmailSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row text-slate-900 selection:bg-orange-100">
      <nav className="w-full md:w-72 bg-white border-b md:border-r border-slate-200 p-8 flex flex-col gap-8 sticky top-0 z-50 md:h-screen">
        <div className="flex items-center gap-3">
          <div className="bg-orange-500 p-2 rounded-xl shadow-lg shadow-orange-100">
            <Sun className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-serif italic font-extrabold tracking-tight">MorningZen</h1>
        </div>

        <div className="flex flex-col gap-1">
          <button onClick={() => setActiveTab('dashboard')} className={`flex items-center gap-3 px-5 py-4 rounded-2xl transition-all ${activeTab === 'dashboard' ? 'bg-orange-50 text-orange-600 font-bold' : 'text-slate-500 hover:bg-slate-50'}`}>
            <LayoutDashboard size={20}/> Daily Flow
          </button>
          <button onClick={() => setActiveTab('calendar')} className={`flex items-center gap-3 px-5 py-4 rounded-2xl transition-all ${activeTab === 'calendar' ? 'bg-orange-50 text-orange-600 font-bold' : 'text-slate-500 hover:bg-slate-50'}`}>
            <CalendarIcon size={20}/> Timeline
          </button>
          <button onClick={() => setActiveTab('settings')} className={`flex items-center gap-3 px-5 py-4 rounded-2xl transition-all ${activeTab === 'settings' ? 'bg-orange-50 text-orange-600 font-bold' : 'text-slate-500 hover:bg-slate-50'}`}>
            <SettingsIcon size={20}/> Config
          </button>
        </div>

        <div className="mt-auto space-y-4">
          <button 
            onClick={() => setIsModalOpen(true)}
            className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 rounded-2xl shadow-xl transition-all flex items-center justify-center gap-2 active:scale-95"
          >
            <Plus size={22} /> New Intention
          </button>
          <div className="flex items-center justify-center gap-2 text-[10px] text-slate-400 font-bold uppercase tracking-widest">
            {isSyncing ? (
              <><RefreshCw size={12} className="animate-spin text-orange-500" /> Connecting...</>
            ) : (
              <><div className={`w-2 h-2 rounded-full ${health?.status === 'online' ? 'bg-green-500' : 'bg-red-400'}`} /> {health?.status === 'online' ? 'System Live' : 'System Error'}</>
            )}
          </div>
        </div>
      </nav>

      <main className="flex-1 overflow-y-auto p-6 md:p-12 max-w-6xl mx-auto w-full">
        {activeTab === 'dashboard' && (
          <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <header className="bg-white p-10 md:p-16 rounded-[3rem] border border-slate-200 relative overflow-hidden group shadow-sm">
               <div className="relative z-10 space-y-4">
                  <h2 className="text-5xl font-serif italic tracking-tight">Today is yours.</h2>
                  <p className="text-slate-500 text-xl font-medium">You have <span className="text-orange-600 font-bold">{tasks.filter(t => !t.completed).length} intentions</span> for this sunrise.</p>
                  <button 
                    onClick={triggerEmail} 
                    disabled={emailSending}
                    className="bg-orange-500 hover:bg-orange-600 text-white px-10 py-4 rounded-full font-bold shadow-2xl shadow-orange-100 transition-all flex items-center gap-3 active:scale-95 disabled:opacity-50"
                  >
                    {emailSending ? <RefreshCw className="animate-spin" size={20}/> : <Mail size={20}/>}
                    {emailSending ? "Sending Zen..." : "Email My Briefing"}
                  </button>
               </div>
               <div className="absolute -right-20 -bottom-20 w-80 h-80 bg-orange-50 rounded-full blur-[100px] opacity-40 group-hover:opacity-60 transition-opacity"></div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-7 gap-10">
              <div className="lg:col-span-4 space-y-6">
                 <h3 className="text-2xl font-serif italic font-bold flex items-center gap-3">The Path Ahead</h3>
                 <div className="space-y-4">
                    {tasks.length === 0 ? (
                      <div className="p-20 text-center border-2 border-dashed border-slate-100 rounded-[2rem] text-slate-400 italic bg-white">No plans yet. Pure potential.</div>
                    ) : (
                      tasks.map(t => (
                        <div key={t.id} className={`group bg-white border border-slate-200 p-6 rounded-[1.8rem] flex items-center gap-6 transition-all hover:border-orange-200 hover:shadow-lg hover:shadow-orange-100/20 ${t.completed ? 'opacity-40 grayscale' : ''}`}>
                          <button onClick={() => handleToggle(t.id)} className={`w-8 h-8 rounded-xl border-2 flex items-center justify-center transition-all ${t.completed ? 'bg-orange-500 border-orange-500 text-white' : 'border-slate-200 hover:border-orange-500'}`}>
                            {t.completed && <CheckCircle2 size={18}/>}
                          </button>
                          <div className="flex-1 min-w-0">
                            <h4 className={`text-xl font-bold tracking-tight ${t.completed ? 'line-through' : ''}`}>{t.title}</h4>
                            <p className="text-sm text-slate-500 font-medium">{new Date(t.date).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}</p>
                          </div>
                          <button onClick={() => handleDelete(t.id)} className="text-slate-200 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 p-2">
                            <Trash2 size={20}/>
                          </button>
                        </div>
                      ))
                    )}
                 </div>
              </div>
              
              <div className="lg:col-span-3">
                 <div className="bg-white p-10 rounded-[2.5rem] border border-slate-200 h-fit sticky top-12 shadow-sm">
                    <Sparkles className="text-orange-400 mb-6" size={36}/>
                    <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-4">Automation Heartbeat</h4>
                    <p className="text-slate-600 italic leading-relaxed text-sm mb-6">
                      Vercel Cron is active. Every sunrise at 08:00 IST (02:30 UTC), the AI coach summarizes your intentions and sends them to your inbox.
                    </p>
                    <div className="pt-6 border-t border-slate-50 flex items-center gap-3 text-orange-500 font-bold text-xs">
                       <Activity size={14}/>
                       Next Trigger: Daily 08:00 AM IST
                    </div>
                 </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'calendar' && (
          <div className="p-10 bg-white rounded-[3rem] border border-slate-200 shadow-sm animate-in fade-in duration-700">
             <h2 className="text-3xl font-serif italic font-bold mb-8">History & Horizon</h2>
             <div className="space-y-4">
                {tasks.map(t => (
                  <div key={t.id} className="p-4 bg-slate-50 rounded-2xl flex justify-between items-center">
                    <span className="font-bold">{t.title}</span>
                    <span className="text-slate-400 text-sm font-mono">{t.date}</span>
                  </div>
                ))}
             </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="max-w-xl mx-auto space-y-8 animate-in fade-in duration-700">
             <div className="bg-white p-12 rounded-[3rem] border border-slate-200 shadow-sm space-y-10">
                <header>
                   <h2 className="text-3xl font-serif italic font-bold">Personalize Your Zen</h2>
                   <p className="text-slate-400 text-sm mt-2">Configure your identity and delivery address.</p>
                </header>
                
                <form onSubmit={handleSaveSettings} className="space-y-6">
                   <div className="space-y-2">
                      <label className="text-xs font-black uppercase tracking-widest text-slate-400">Your Name</label>
                      <input 
                        type="text" 
                        value={settings.name}
                        onChange={e => setSettings({...settings, name: e.target.value})}
                        className="w-full bg-slate-50 border border-slate-100 rounded-2xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-orange-500/20 transition-all font-bold"
                        placeholder="Zen Master"
                        required
                      />
                   </div>
                   <div className="space-y-2">
                      <label className="text-xs font-black uppercase tracking-widest text-slate-400">Email Address</label>
                      <input 
                        type="email" 
                        value={settings.email}
                        onChange={e => setSettings({...settings, email: e.target.value})}
                        className="w-full bg-slate-50 border border-slate-100 rounded-2xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-orange-500/20 transition-all font-bold"
                        placeholder="you@example.com"
                        required
                      />
                   </div>
                   <button 
                    type="submit"
                    className="w-full bg-orange-500 hover:bg-orange-600 text-white font-bold py-5 rounded-2xl shadow-xl shadow-orange-100 transition-all active:scale-[0.98]"
                   >
                     Save Configuration
                   </button>
                </form>

                <div className="pt-10 border-t border-slate-100 space-y-6">
                   <h3 className="text-[10px] font-black uppercase tracking-widest text-slate-400">Environment Diagnostics</h3>
                   <div className="space-y-3">
                      <HealthStatus label="Supabase DB" status={health?.supabase} />
                      <HealthStatus label="Gemini AI" status={health?.api_ready} />
                      <HealthStatus label="Brevo (Email)" status={health?.brevo} />
                   </div>
                </div>
             </div>
          </div>
        )}
      </main>

      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-md z-[60] flex items-center justify-center p-4">
          <div className="bg-white rounded-[2.5rem] w-full max-w-lg p-10 shadow-2xl animate-in zoom-in duration-200">
             <h2 className="text-3xl font-serif italic font-bold mb-8">Set Intention</h2>
              <form className="space-y-6" onSubmit={(e) => {
                e.preventDefault();
                handleAddTask({
                  ...newTask,
                  date: new Date().toISOString().split('T')[0]
                });
              }}>
                <input 
                  name="title" 
                  required 
                  autoFocus 
                  placeholder="Goal Title" 
                  value={newTask.title}
                  onChange={e => setNewTask({...newTask, title: e.target.value})}
                  className="w-full text-2xl font-serif border-b-2 py-2 focus:outline-none focus:border-orange-500 transition-colors" 
                />
                <div className="space-y-2">
                  <label className="text-xs font-black uppercase tracking-widest text-slate-400">Priority</label>
                  <div className="flex gap-2">
                    {(['low', 'medium', 'high'] as const).map(p => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setNewTask({...newTask, priority: p as TaskPriority})}
                        className={`flex-1 py-3 rounded-xl font-bold capitalize transition-all ${newTask.priority === p ? 'bg-orange-500 text-white shadow-lg shadow-orange-100' : 'bg-slate-50 text-slate-400 hover:bg-slate-100'}`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex gap-4 pt-4">
                  <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 font-bold text-slate-400 hover:text-slate-600">Dismiss</button>
                  <button type="submit" className="flex-1 py-4 bg-slate-900 text-white rounded-2xl font-bold shadow-xl shadow-slate-200 hover:bg-slate-800 transition-all">Seal Intention</button>
                </div>
              </form>
          </div>
        </div>
      )}
    </div>
  );
};

const HealthStatus = ({ label, status }: { label: string, status: boolean }) => (
  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100">
    <span className="text-sm font-medium text-slate-600">{label}</span>
    <div className={`flex items-center gap-2 text-[10px] font-black uppercase tracking-widest ${status ? 'text-green-500' : 'text-red-400'}`}>
       <div className={`w-2 h-2 rounded-full ${status ? 'bg-green-500' : 'bg-red-400'}`} />
       {status ? 'Connected' : 'Missing Key'}
    </div>
  </div>
);

export default App;
