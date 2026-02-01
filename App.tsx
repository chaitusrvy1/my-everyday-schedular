
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Calendar as CalendarIcon, 
  CheckCircle2, 
  Clock, 
  LayoutDashboard, 
  Plus, 
  Settings as SettingsIcon,
  Sun,
  Trash2,
  Mail,
  Sparkles,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { Task, TaskPriority, MorningBriefing, UserSettings } from './types';
import { generateMorningBriefing } from './services/geminiService';

// Helper for local storage
const STORAGE_KEY = 'morningzen_tasks';
const SETTINGS_KEY = 'morningzen_settings';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'calendar' | 'settings'>('dashboard');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [settings, setSettings] = useState<UserSettings>({
    email: '',
    preferredMorningTime: '08:00',
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [briefing, setBriefing] = useState<MorningBriefing | null>(null);
  const [isGeneratingBriefing, setIsGeneratingBriefing] = useState(false);

  // Load data
  useEffect(() => {
    const savedTasks = localStorage.getItem(STORAGE_KEY);
    const savedSettings = localStorage.getItem(SETTINGS_KEY);
    if (savedTasks) setTasks(JSON.parse(savedTasks));
    if (savedSettings) setSettings(JSON.parse(savedSettings));
  }, []);

  // Save tasks
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
  }, [tasks]);

  const addTask = (taskData: Omit<Task, 'id' | 'createdAt' | 'completed'>) => {
    const newTask: Task = {
      ...taskData,
      id: Math.random().toString(36).substr(2, 9),
      createdAt: Date.now(),
      completed: false
    };
    setTasks(prev => [newTask, ...prev]);
    setIsModalOpen(false);
  };

  const toggleTask = (id: string) => {
    setTasks(prev => prev.map(t => t.id === id ? { ...t, completed: !t.completed } : t));
  };

  const deleteTask = (id: string) => {
    setTasks(prev => prev.filter(t => t.id !== id));
  };

  const handleGenerateBriefing = async () => {
    setIsGeneratingBriefing(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      const todaysTasks = tasks.filter(t => t.date === today && !t.completed);
      const result = await generateMorningBriefing(todaysTasks);
      setBriefing(result);
    } catch (error) {
      console.error("Briefing failed:", error);
    } finally {
      setIsGeneratingBriefing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      {/* Sidebar - Navigation */}
      <nav className="w-full md:w-64 bg-white border-b md:border-r border-slate-200 p-6 flex flex-col gap-8 sticky top-0 z-50 md:h-screen">
        <div className="flex items-center gap-2 text-orange-500">
          <Sun className="w-8 h-8 fill-current" />
          <h1 className="text-2xl font-serif italic font-bold text-slate-900 tracking-tight">MorningZen</h1>
        </div>

        <div className="flex flex-col gap-2">
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeTab === 'dashboard' ? 'bg-orange-50 text-orange-600 font-medium' : 'text-slate-500 hover:bg-slate-50'}`}
          >
            <LayoutDashboard size={20} />
            Dashboard
          </button>
          <button 
            onClick={() => setActiveTab('calendar')}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeTab === 'calendar' ? 'bg-orange-50 text-orange-600 font-medium' : 'text-slate-500 hover:bg-slate-50'}`}
          >
            <CalendarIcon size={20} />
            Calendar
          </button>
          <button 
            onClick={() => setActiveTab('settings')}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeTab === 'settings' ? 'bg-orange-50 text-orange-600 font-medium' : 'text-slate-500 hover:bg-slate-50'}`}
          >
            <SettingsIcon size={20} />
            Settings
          </button>
        </div>

        <button 
          onClick={() => setIsModalOpen(true)}
          className="mt-auto bg-orange-500 hover:bg-orange-600 text-white font-medium py-3 rounded-xl shadow-lg shadow-orange-200 transition-all flex items-center justify-center gap-2"
        >
          <Plus size={20} />
          Add Task
        </button>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-4 md:p-8 max-w-5xl mx-auto w-full">
        {activeTab === 'dashboard' && (
          <Dashboard 
            tasks={tasks} 
            toggleTask={toggleTask} 
            deleteTask={deleteTask}
            briefing={briefing}
            onGenerateBriefing={handleGenerateBriefing}
            isGenerating={isGeneratingBriefing}
          />
        )}
        {activeTab === 'calendar' && (
          <CalendarView tasks={tasks} toggleTask={toggleTask} deleteTask={deleteTask} />
        )}
        {activeTab === 'settings' && (
          <SettingsView settings={settings} setSettings={setSettings} />
        )}
      </main>

      {/* Add Task Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[60] flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-md p-6 shadow-2xl animate-in fade-in zoom-in duration-200">
            <h2 className="text-xl font-bold mb-6">Create New Task</h2>
            <TaskForm onSubmit={addTask} onCancel={() => setIsModalOpen(false)} />
          </div>
        </div>
      )}
    </div>
  );
};

/* --- Component Definitions --- */

const Dashboard: React.FC<{
  tasks: Task[];
  toggleTask: (id: string) => void;
  deleteTask: (id: string) => void;
  briefing: MorningBriefing | null;
  onGenerateBriefing: () => void;
  isGenerating: boolean;
}> = ({ tasks, toggleTask, deleteTask, briefing, onGenerateBriefing, isGenerating }) => {
  const today = new Date().toISOString().split('T')[0];
  const todayTasks = tasks.filter(t => t.date === today);
  const pendingCount = todayTasks.filter(t => !t.completed).length;

  return (
    <div className="flex flex-col gap-8 animate-in slide-in-from-bottom-4 duration-500">
      {/* Header Summary */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 md:p-8 flex flex-col md:flex-row items-center justify-between gap-6 overflow-hidden relative">
        <div className="relative z-10 text-center md:text-left">
          <h2 className="text-3xl font-serif italic mb-2">Good morning, seeker.</h2>
          <p className="text-slate-500">
            You have {pendingCount} tasks awaiting your energy today.
          </p>
        </div>
        <button 
          onClick={onGenerateBriefing}
          disabled={isGenerating}
          className="relative z-10 flex items-center gap-2 bg-slate-900 text-white px-6 py-3 rounded-full hover:bg-slate-800 transition-all disabled:opacity-50"
        >
          {isGenerating ? <Clock className="animate-spin" size={18} /> : <Sparkles size={18} className="text-orange-400" />}
          {isGenerating ? "Consulting Stars..." : "Generate Morning Briefing"}
        </button>
        {/* Decorative element */}
        <div className="absolute -right-10 -bottom-10 w-48 h-48 bg-orange-100 rounded-full blur-3xl opacity-50"></div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Task List Main Section */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <Clock size={20} className="text-orange-500" />
              Today's Schedule
            </h3>
            <span className="text-sm font-medium text-slate-400">{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</span>
          </div>

          <div className="space-y-3">
            {todayTasks.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-2xl border border-dashed border-slate-300">
                <p className="text-slate-400 italic">No tasks planned for today. Enjoy the peace.</p>
              </div>
            ) : (
              todayTasks.map(task => (
                <TaskCard key={task.id} task={task} onToggle={toggleTask} onDelete={deleteTask} />
              ))
            )}
          </div>
        </div>

        {/* Gemini Briefing Sidebar */}
        <div className="space-y-6">
          <h3 className="text-lg font-bold flex items-center gap-2">
            <Mail size={20} className="text-orange-500" />
            Your Briefing
          </h3>
          <div className={`bg-white border border-slate-200 rounded-2xl p-6 h-full min-h-[400px] transition-all ${!briefing ? 'flex items-center justify-center text-center' : ''}`}>
            {!briefing ? (
              <div className="space-y-4">
                <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto">
                  <Mail className="text-slate-300" />
                </div>
                <p className="text-slate-400 text-sm max-w-[200px] mx-auto">
                  Generate your AI-powered morning brief to see your personalized outlook and goals.
                </p>
              </div>
            ) : (
              <div className="animate-in fade-in duration-700">
                <blockquote className="border-l-4 border-orange-400 pl-4 mb-6 italic text-slate-700 font-serif text-lg">
                  "{briefing.quote}"
                  <cite className="block text-sm font-sans font-medium text-slate-400 not-italic mt-2">— {briefing.author}</cite>
                </blockquote>
                
                <div className="space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-widest text-slate-400">Personal Insight</h4>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    {briefing.message}
                  </p>
                </div>

                <div className="mt-8 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-widest text-slate-400">Suggested Focus</h4>
                  <ul className="space-y-2">
                    {briefing.actionItems.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                        <span className="w-1.5 h-1.5 rounded-full bg-orange-400 mt-1.5 shrink-0"></span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const TaskCard: React.FC<{ 
  task: Task; 
  onToggle: (id: string) => void; 
  onDelete: (id: string) => void 
}> = ({ task, onToggle, onDelete }) => {
  return (
    <div className={`group bg-white border border-slate-200 rounded-xl p-4 flex items-center gap-4 transition-all hover:border-orange-200 hover:shadow-sm ${task.completed ? 'opacity-60' : ''}`}>
      <button 
        onClick={() => onToggle(task.id)}
        className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${task.completed ? 'bg-green-500 border-green-500 text-white' : 'border-slate-300 hover:border-orange-400'}`}
      >
        {task.completed && <CheckCircle2 size={16} />}
      </button>
      
      <div className="flex-1 min-w-0">
        <h4 className={`font-medium text-slate-900 truncate ${task.completed ? 'line-through text-slate-400' : ''}`}>
          {task.title}
        </h4>
        {task.description && (
          <p className="text-xs text-slate-500 truncate mt-0.5">{task.description}</p>
        )}
      </div>

      <div className="flex items-center gap-3">
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wide ${
          task.priority === TaskPriority.HIGH ? 'bg-red-50 text-red-600' :
          task.priority === TaskPriority.MEDIUM ? 'bg-orange-50 text-orange-600' :
          'bg-slate-50 text-slate-600'
        }`}>
          {task.priority}
        </span>
        <button 
          onClick={() => onDelete(task.id)}
          className="p-2 text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
        >
          <Trash2 size={18} />
        </button>
      </div>
    </div>
  );
};

const TaskForm: React.FC<{ 
  onSubmit: (task: Omit<Task, 'id' | 'createdAt' | 'completed'>) => void; 
  onCancel: () => void 
}> = ({ onSubmit, onCancel }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [priority, setPriority] = useState<TaskPriority>(TaskPriority.MEDIUM);

  return (
    <form className="space-y-4" onSubmit={(e) => {
      e.preventDefault();
      if (!title) return;
      onSubmit({ title, description, date, priority });
    }}>
      <div>
        <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Task Title</label>
        <input 
          autoFocus
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="What needs to be done?"
          className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
        />
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Date</label>
        <input 
          type="date"
          value={date}
          onChange={e => setDate(e.target.value)}
          className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
        />
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Priority</label>
        <div className="grid grid-cols-3 gap-2">
          {Object.values(TaskPriority).map(p => (
            <button
              key={p}
              type="button"
              onClick={() => setPriority(p)}
              className={`py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all border ${
                priority === p 
                  ? 'bg-slate-900 border-slate-900 text-white shadow-md' 
                  : 'bg-white border-slate-200 text-slate-500 hover:border-slate-300'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-3 pt-4">
        <button 
          type="button"
          onClick={onCancel}
          className="flex-1 py-3 rounded-xl border border-slate-200 text-slate-500 font-medium hover:bg-slate-50 transition-all"
        >
          Cancel
        </button>
        <button 
          type="submit"
          className="flex-1 py-3 rounded-xl bg-orange-500 text-white font-medium hover:bg-orange-600 shadow-lg shadow-orange-100 transition-all"
        >
          Create Task
        </button>
      </div>
    </form>
  );
};

const CalendarView: React.FC<{
  tasks: Task[];
  toggleTask: (id: string) => void;
  deleteTask: (id: string) => void;
}> = ({ tasks, toggleTask, deleteTask }) => {
  const [viewDate, setViewDate] = useState(new Date());
  
  const getDaysInMonth = (year: number, month: number) => new Date(year, month + 1, 0).getDate();
  const getFirstDayOfMonth = (year: number, month: number) => new Date(year, month, 1).getDay();

  const daysInMonth = getDaysInMonth(viewDate.getFullYear(), viewDate.getMonth());
  const firstDay = getFirstDayOfMonth(viewDate.getFullYear(), viewDate.getMonth());

  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const emptyDays = Array.from({ length: firstDay }, (_, i) => i);

  const selectedMonthTasks = tasks.filter(t => {
    const d = new Date(t.date);
    return d.getMonth() === viewDate.getMonth() && d.getFullYear() === viewDate.getFullYear();
  });

  const nextMonth = () => setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() + 1));
  const prevMonth = () => setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() - 1));

  return (
    <div className="animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-serif italic flex items-center gap-3">
          <CalendarIcon className="text-orange-500" />
          {viewDate.toLocaleString('default', { month: 'long', year: 'numeric' })}
        </h2>
        <div className="flex gap-2">
          <button onClick={prevMonth} className="p-2 hover:bg-white rounded-lg border border-transparent hover:border-slate-200 transition-all">
            <ChevronLeft />
          </button>
          <button onClick={nextMonth} className="p-2 hover:bg-white rounded-lg border border-transparent hover:border-slate-200 transition-all">
            <ChevronRight />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-px bg-slate-200 border border-slate-200 rounded-2xl overflow-hidden mb-8">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div key={day} className="bg-slate-50 p-4 text-center text-[10px] font-bold uppercase tracking-widest text-slate-400">
            {day}
          </div>
        ))}
        {emptyDays.map(i => <div key={`empty-${i}`} className="bg-white/50 h-24 md:h-32"></div>)}
        {days.map(day => {
          const dateStr = `${viewDate.getFullYear()}-${String(viewDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
          const dayTasks = selectedMonthTasks.filter(t => t.date === dateStr);
          const isToday = new Date().toISOString().split('T')[0] === dateStr;

          return (
            <div key={day} className={`bg-white h-24 md:h-32 p-2 flex flex-col gap-1 border-t border-slate-100 group transition-all hover:bg-slate-50`}>
              <span className={`text-xs font-medium w-6 h-6 flex items-center justify-center rounded-full ${isToday ? 'bg-orange-500 text-white' : 'text-slate-400 group-hover:text-slate-900'}`}>
                {day}
              </span>
              <div className="flex flex-col gap-1 overflow-y-auto scrollbar-hide">
                {dayTasks.map(t => (
                  <div key={t.id} className={`text-[9px] px-1.5 py-0.5 rounded truncate ${t.completed ? 'bg-slate-100 text-slate-400' : 'bg-orange-100 text-orange-700 font-medium'}`}>
                    {t.title}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Tasks Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {selectedMonthTasks.length === 0 ? (
             <div className="col-span-full py-12 text-center text-slate-400 italic">No tasks recorded for this month.</div>
          ) : (
            selectedMonthTasks.map(t => (
              <TaskCard key={t.id} task={t} onToggle={toggleTask} onDelete={deleteTask} />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const SettingsView: React.FC<{
  settings: UserSettings;
  setSettings: (s: UserSettings) => void;
}> = ({ settings, setSettings }) => {
  const [form, setForm] = useState(settings);

  const handleSave = () => {
    setSettings(form);
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(form));
    alert('Settings updated successfully. Your morning briefings will be tailored to these details.');
  };

  return (
    <div className="max-w-xl mx-auto animate-in fade-in slide-in-from-left-4 duration-500">
      <h2 className="text-2xl font-serif italic mb-8 flex items-center gap-3">
        <SettingsIcon className="text-orange-500" />
        Configuration & Deployment
      </h2>

      <div className="bg-white border border-slate-200 rounded-3xl p-8 space-y-8">
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 pb-2">Morning Notification</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Email Address</label>
              <input 
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={e => setForm({...form, email: e.target.value})}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Briefing Time</label>
              <input 
                type="time"
                value={form.preferredMorningTime}
                onChange={e => setForm({...form, preferredMorningTime: e.target.value})}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
              />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 pb-2">Infrastructure (External)</h3>
          <p className="text-xs text-slate-500 italic">Configure your free-tier keys here to connect your personal backend services.</p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Brevo API Key (Email Delivery)</label>
              <input 
                type="password"
                placeholder="xkeysib-..."
                value={form.brevoApiKey || ''}
                onChange={e => setForm({...form, brevoApiKey: e.target.value})}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Supabase URL</label>
              <input 
                placeholder="https://xyz.supabase.co"
                value={form.supabaseUrl || ''}
                onChange={e => setForm({...form, supabaseUrl: e.target.value})}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
              />
            </div>
          </div>
        </div>

        <button 
          onClick={handleSave}
          className="w-full py-4 rounded-xl bg-slate-900 text-white font-bold hover:bg-slate-800 transition-all shadow-xl shadow-slate-200"
        >
          Save Configuration
        </button>
      </div>

      <div className="mt-8 p-6 bg-orange-50 rounded-3xl border border-orange-100">
        <h4 className="font-bold text-orange-800 mb-2 text-sm uppercase tracking-wider">Free Deployment Guide</h4>
        <ul className="text-xs text-orange-700 space-y-2">
          <li className="flex gap-2"><span>1.</span> <strong>Supabase:</strong> Use their free tier for a permanent PostgreSQL DB.</li>
          <li className="flex gap-2"><span>2.</span> <strong>Brevo:</strong> Get 300 free transactional emails per day.</li>
          <li className="flex gap-2"><span>3.</span> <strong>FastAPI Backend:</strong> Deploy to Railway or Render's free tier.</li>
          <li className="flex gap-2"><span>4.</span> <strong>Scheduler:</strong> Use <code>APScheduler</code> in your FastAPI app to trigger emails at your saved time.</li>
        </ul>
      </div>
    </div>
  );
};

export default App;
