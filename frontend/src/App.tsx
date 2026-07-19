import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, CheckCircle2, XCircle, Loader2 } from 'lucide-react';

export default function App() {
  const [spec, setSpec] = useState('Build a tiny python calculator.');
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState('Idle');
  
  const [telemetry, setTelemetry] = useState<any[]>([]);
  const [brainActivity, setBrainActivity] = useState<any[]>([]);

  const startWorkflow = async () => {
    setIsStreaming(true);
    setStatus('Running...');
    setTelemetry([]);
    setBrainActivity([]);
    
    try {
      const response = await fetch('/api/workflows/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: spec })
      });
      const data = await response.json();
      connectSSE(data.job_id);
    } catch (e) {
      console.error(e);
      setStatus('Failed to start');
      setIsStreaming(false);
    }
  };

  const connectSSE = (workflowId: string) => {
    const eventSource = new EventSource(`/api/workflows/${workflowId}/stream`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("SSE Event:", data);
      
      switch (data.event_type) {
        case "WorkflowStarted":
          setTelemetry(prev => [...prev, { id: 'start', type: 'WorkflowStarted', time: new Date().toLocaleTimeString(), message: 'Workflow Started' }]);
          break;
        case "StepStarted":
          setTelemetry(prev => [...prev, { id: data.step_name, type: 'StepStarted', step: data.step_name, status: 'running', time: new Date().toLocaleTimeString() }]);
          break;
        case "StepCompleted":
          setTelemetry(prev => prev.map(t => t.id === data.step_name ? { ...t, status: 'success', time: new Date().toLocaleTimeString() } : t));
          break;
        case "StepFailed":
          setTelemetry(prev => prev.map(t => t.id === data.step_name ? { ...t, status: 'failed', time: new Date().toLocaleTimeString() } : t));
          break;
        case "WorkflowCompleted":
          setStatus("Completed!");
          setIsStreaming(false);
          eventSource.close();
          break;
        case "WorkflowFailed":
          setStatus("Failed!");
          setIsStreaming(false);
          eventSource.close();
          break;
        case "LLMRequestStarted":
          setBrainActivity(prev => {
            const stepGroup = prev.find(g => g.step === data.step_name);
            if (stepGroup) {
              const updatedRequests = [...stepGroup.requests, { id: data.payload?.model + Date.now(), model: data.payload?.model, status: 'running' }];
              return prev.map(g => g.step === data.step_name ? { ...g, requests: updatedRequests } : g);
            } else {
              return [...prev, { step: data.step_name, requests: [{ id: data.payload?.model + Date.now(), model: data.payload?.model, status: 'running' }] }];
            }
          });
          break;
        case "LLMRequestFailed":
          setBrainActivity(prev => prev.map(g => {
            if (g.step === data.step_name) {
              const lastReq = g.requests[g.requests.length - 1];
              return { ...g, requests: g.requests.map((r: any) => r.id === lastReq.id ? { ...r, status: 'failed', error: data.payload?.error } : r) };
            }
            return g;
          }));
          break;
        case "LLMRequestSuccess":
           setBrainActivity(prev => prev.map(g => {
            if (g.step === data.step_name) {
              const lastReq = g.requests[g.requests.length - 1];
              return { ...g, requests: g.requests.map((r: any) => r.id === lastReq.id ? { ...r, status: 'success' } : r) };
            }
            return g;
          }));
          break;
      }
    };
    
    eventSource.onerror = () => {
      eventSource.close();
      setIsStreaming(false);
    };
  };

  return (
    <div className="min-h-screen bg-background text-gray-100 flex flex-col font-sans">
      <header className="px-6 py-4 border-b border-surface/50 bg-surface/20 backdrop-blur-md sticky top-0 z-50 flex items-center gap-3 shadow-xl">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold shadow-lg shadow-primary/20">
          LH
        </div>
        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-100 to-gray-400">
          Lively Hubble
        </h1>
        <div className="ml-auto flex items-center gap-2 text-sm text-secondary">
          <span className="relative flex h-3 w-3">
            {isStreaming ? (
               <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            ) : null}
            <span className={`relative inline-flex rounded-full h-3 w-3 ${isStreaming ? 'bg-green-500' : 'bg-secondary'}`}></span>
          </span>
          {status}
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Left Control Panel */}
        <div className="w-[400px] flex-shrink-0 border-r border-surface p-6 flex flex-col gap-6 bg-surface/30">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">Specification</label>
            <textarea 
              value={spec}
              onChange={(e) => setSpec(e.target.value)}
              className="w-full h-32 bg-background border border-surface rounded-xl p-4 text-sm focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition-all resize-none text-gray-200 placeholder:text-gray-600"
              placeholder="What would you like to build?"
              disabled={isStreaming}
            />
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={startWorkflow}
            disabled={isStreaming || !spec.trim()}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-medium flex items-center justify-center gap-2 shadow-lg shadow-primary/25 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-primary/40 transition-all"
          >
            {isStreaming ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
            {isStreaming ? 'Generating...' : 'Run Workflow'}
          </motion.button>
        </div>

        {/* Center Canvas */}
        <div className="flex-1 flex flex-col items-center justify-center p-8 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-surface/40 via-background to-background relative">
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none mix-blend-overlay"></div>
            
            <AnimatePresence mode="popLayout">
              {telemetry.map((item, idx) => (
                <motion.div
                  key={item.id + idx}
                  initial={{ opacity: 0, y: 20, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className={`w-full max-w-2xl mb-4 p-5 rounded-2xl border backdrop-blur-sm shadow-xl flex items-center gap-4 ${
                    item.status === 'success' ? 'bg-green-500/10 border-green-500/20 shadow-green-500/5' : 
                    item.status === 'failed' ? 'bg-red-500/10 border-red-500/20 shadow-red-500/5' :
                    item.status === 'running' ? 'bg-primary/10 border-primary/20 shadow-primary/5' :
                    'bg-surface/50 border-surface'
                  }`}
                >
                  <div className="flex-shrink-0">
                    {item.status === 'success' && <CheckCircle2 className="w-6 h-6 text-green-400" />}
                    {item.status === 'failed' && <XCircle className="w-6 h-6 text-red-400" />}
                    {item.status === 'running' && <Loader2 className="w-6 h-6 text-primary animate-spin" />}
                    {!item.status && <div className="w-6 h-6 rounded-full bg-secondary/20" />}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-200">{item.step || item.message}</h3>
                    <p className="text-sm text-gray-500">{item.time}</p>
                  </div>
                </motion.div>
              ))}
              
              {telemetry.length === 0 && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-gray-500 text-center">
                  <div className="w-16 h-16 rounded-2xl bg-surface/50 flex items-center justify-center mx-auto mb-4 border border-surface shadow-xl">
                    <Play className="w-8 h-8 text-secondary/50" />
                  </div>
                  <p>Awaiting instructions</p>
                </motion.div>
              )}
            </AnimatePresence>
        </div>

        {/* Right Brain Activity */}
        <div className="w-[400px] flex-shrink-0 border-l border-surface p-6 bg-surface/30 flex flex-col">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-2 h-2 rounded-full bg-accent animate-pulse shadow-[0_0_8px_rgba(139,92,246,0.8)]"></div>
            <h2 className="font-semibold text-gray-200">Brain Activity</h2>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 space-y-6">
            <AnimatePresence>
              {brainActivity.map((group, idx) => (
                <motion.div
                  key={group.step + idx}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="space-y-3"
                >
                  <div className="text-xs font-bold uppercase tracking-wider text-secondary/70">
                    {group.step}
                  </div>
                  <div className="space-y-2">
                    {group.requests.map((req: any) => (
                      <motion.div
                        key={req.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className={`p-3 rounded-xl border flex items-center gap-3 text-sm transition-all ${
                          req.status === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-300' :
                          req.status === 'failed' ? 'bg-red-500/10 border-red-500/20 text-red-300' :
                          'bg-surface/50 border-surface text-gray-300'
                        }`}
                      >
                        {req.status === 'success' && <CheckCircle2 className="w-4 h-4 flex-shrink-0" />}
                        {req.status === 'failed' && <XCircle className="w-4 h-4 flex-shrink-0" />}
                        {req.status === 'running' && <Loader2 className="w-4 h-4 animate-spin text-primary flex-shrink-0" />}
                        
                        <div className="flex-1 truncate font-mono text-xs">
                          {req.model}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  );
}
