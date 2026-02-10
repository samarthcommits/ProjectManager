import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, ArrowRight, RotateCcw, Loader2 } from 'lucide-react';
import { AgentTimeline } from '@/components/agent/AgentTimeline';
import { useProjectStore } from '@/stores/useProjectStore';
import { Button } from '@/components/ui/button';
import { consumeSSE } from '@/lib/sse';
import { toast } from 'sonner';

// Your Python Backend URL
const API_URL = "http://127.0.0.1:8200/plan"; 

const AgentProcessing = () => {
  const navigate = useNavigate();
  const { 
    projectBrief, 
    teamMembers, 
    agentSteps,
    setAgentSteps, 
    updateAgentStep, 
    setTickets, 
    setCurrentPhase,
    setSessionId // <--- IMPORTANT: Get the setter
  } = useProjectStore();
  
  const [error, setError] = useState<string | null>(null);
  const startedRef = useRef(false);

  // 1. Initialize Steps
  const initializeSteps = () => {
    setAgentSteps([
      { 
        id: '1', 
        agent: 'System',
        emoji: '⚙️',
        message: 'Initializing System', 
        status: 'pending' 
      }, 
      { 
        id: '2', 
        agent: 'BA Agent',
        emoji: '🕵️‍♂️',
        message: 'Analyzing Requirements', 
        status: 'pending' 
      },
      { 
        id: '3', 
        agent: 'Planner Agent',
        emoji: '📋',
        message: 'Drafting User Stories', 
        status: 'pending' 
      },
      { 
        id: '4', 
        agent: 'Compiler',
        emoji: '📦',
        message: 'Compiling Final Plan', 
        status: 'pending' 
      }
    ]);
  };

  const startAnalysis = async () => {
    setError(null);
    initializeSteps();
    
    // Mark first step active
    updateAgentStep('1', { status: 'active' });

    try {
      await consumeSSE(
        API_URL, 
        {
          project_brief: projectBrief || "Build a software project",
          // Map Store Team -> API Roster
          roster: teamMembers.map(m => ({
            name: m.name,
            role: m.role.toLowerCase().replace(" ", "_"), 
            skills: Array.isArray(m.skills) ? m.skills.join(", ") : m.skills
          }))
        },
        (event) => {
           // Handle Status (Green Checkmarks)
           if (event.type === 'status') {
             const msg = (event.msg || "").toLowerCase();
             
             if (msg.includes('starting ba')) {
               updateAgentStep('1', { status: 'complete' });
               updateAgentStep('2', { status: 'active' });
             } else if (msg.includes('analysis done') || msg.includes('ba analysis')) {
               updateAgentStep('2', { status: 'complete' });
               updateAgentStep('3', { status: 'active' });
             } else if (msg.includes('planning complete')) {
               updateAgentStep('3', { status: 'complete' });
               updateAgentStep('4', { status: 'active' });
             }
           }
           
           // Handle Result
           if (event.type === 'result') {
             updateAgentStep('4', { status: 'complete' });
             const data = event.data as any;
             
             if (data) {
                // --- CRITICAL FIX: CAPTURE SESSION ID ---
                if (data.session_id) {
                    console.log("Captured Session ID:", data.session_id);
                    setSessionId(data.session_id);
                }
                // ----------------------------------------

                if (data.stories) {
                    const rawStories = data.stories as any[];
                    
                    const formattedTickets = rawStories.map((item: any, index: number) => {
                      const storyContent = item.story || {};
                      const isDict = typeof storyContent === 'object';

                      return {
                        // 1. ID Fields
                        id: `temp-${index}`, 
                        ticketId: `PROJ-${index + 100}`, 
                        
                        // 2. Main Content
                        title: isDict ? (storyContent.ticket_title || "Untitled Story") : "User Story",
                        userStory: isDict ? (storyContent.user_story || JSON.stringify(storyContent)) : String(storyContent),
                        module: item.module || "General",
                        
                        // 3. Status & Assignment
                        status: 'todo',      
                        assignee: 'Unassigned', 
                        priority: (item.priority || "medium").toLowerCase(), 
                        
                        // 4. Details
                        storyPoints: storyContent.story_points || 3, 
                        acceptanceCriteria: Array.isArray(storyContent.acceptance_criteria) 
                            ? storyContent.acceptance_criteria 
                            : [],
                        technicalNotes: storyContent.technical_notes || "",
                        
                        // 5. Keep raw data for Allocation later
                        story: storyContent 
                      };
                    });

                    // Cast to 'any' to avoid strict type checks on the 'story' hidden field
                    setTickets(formattedTickets as any[]); 
                    toast.success("Plan Generated!");
                }
             }
           }
           
           if (event.type === 'error') throw new Error(event.msg);
        },
        (err) => {
          console.error(err);
          setError(err.message);
        },
        () => console.log("Done")
      );
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    startAnalysis();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleProceed = () => {
    setCurrentPhase('review');
    navigate('/review');
  };

  const isComplete = agentSteps.length > 0 && agentSteps.every(s => s.status === 'complete');

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <div className="mb-8 text-center">
        <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary mb-4">
          <Bot className="h-3.5 w-3.5" />
          AI Processing
        </div>
        <h1 className="text-3xl font-bold tracking-tight">Agents at Work</h1>
        <p className="mt-2 text-muted-foreground">Connecting to Local LLM...</p>
      </div>

      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <AgentTimeline /> 
      </div>

      <div className="flex justify-center gap-3 mt-8">
        {error && (
          <Button variant="destructive" onClick={() => { startedRef.current = false; startAnalysis(); }} className="gap-2">
            <RotateCcw className="h-4 w-4" /> Retry
          </Button>
        )}
        
        {!error && !isComplete && (
           <Button disabled variant="outline" className="gap-2"><Loader2 className="h-4 w-4 animate-spin"/> Processing...</Button>
        )}

        {isComplete && (
          <Button onClick={handleProceed} size="lg" className="gap-2 font-semibold bg-green-600 hover:bg-green-700">
            Review Results <ArrowRight className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
};

export default AgentProcessing;