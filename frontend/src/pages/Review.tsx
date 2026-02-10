import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ListChecks, Loader2 } from 'lucide-react';
import { PrioritizationGrid } from '@/components/review/PrioritizationGrid'; 
import { useProjectStore } from '@/stores/useProjectStore';
import { consumeSSE } from '@/lib/sse';
import { toast } from 'sonner';

// Your Python Backend URL
const API_URL = "http://127.0.0.1:8200/allocate";

const Review = () => {
  const navigate = useNavigate();
  // --- IMPORT sessionId FROM STORE ---
  const { tickets, setTickets, setCurrentPhase, sessionId } = useProjectStore();
  const [isAllocating, setIsAllocating] = useState(false);

  // This function replaces the simple navigation
  const handleApprove = async () => {
    setIsAllocating(true);

    try {
      // 1. Prepare Payload: Map Lovable tickets -> Python 'approved_stories'
      const approvedStories = tickets.map((t: any) => ({
        // Check if the ticket content is nested in 'story' (common in LangGraph outputs) or flat
        story: t.story || t, 
        priority: t.priority || "medium",
        role: t.role || "unknown",
        module: t.module || "general"
      }));

      // 2. Stream the Allocation
      await consumeSSE(
        API_URL,
        {
          // --- FIX: USE REAL SESSION ID CAPTURED IN PREVIOUS STEP ---
          session_id: sessionId || "session-fallback", 
          approved_stories: approvedStories
        },
        (event) => {
          // A. Handle Status Updates
          if (event.type === 'status') {
            toast.info(event.msg);
          }
          
          // B. Handle Final Result (The Allocation)
          if (event.type === 'result') {
            // FIX: Cast event.data to 'any' so we can read 'assigned_tasks'
            const data = event.data as any; 
            const assignments = data.assigned_tasks;
            
            const newKanbanTickets: any[] = [];
            
            if (assignments) {
                // Transform Python { "Alice": [task1, task2] } -> Lovable Flat List
                Object.keys(assignments).forEach(person => {
                  assignments[person].forEach((task: any, idx: number) => {
                    newKanbanTickets.push({
                      id: `${person}-${idx}-${Date.now()}`, // Unique ID
                      title: task.ticket_title || "Untitled Task",
                      // If description is missing, fallback to JSON string so data isn't lost
                      userStory: task.user_story || "No details provided",
                      status: 'todo', // Initial column in Kanban
                      assignee: person === 'Unassigned' ? null : person,
                      // Ensure priority matches lowercase type
                      priority: (task.priority || 'medium').toLowerCase(),
                      storyPoints: task.story_points || 3, // Mock points if backend doesn't provide
                      acceptanceCriteria: task.acceptance_criteria || [],
                      technicalNotes: task.technical_notes || ""
                    });
                  });
                });
    
                // Update Store & Navigate
                setTickets(newKanbanTickets);
                setCurrentPhase('dashboard');
                toast.success("Resources Allocated Successfully!");
                navigate('/dashboard');
            }
          }
          
          // C. Handle Errors
          if (event.type === 'error') {
            throw new Error(event.msg);
          }
        },
        (err) => {
          console.error("Allocation Error:", err);
          toast.error(`Allocation Failed: ${err.message}`);
          setIsAllocating(false);
        },
        () => {
          setIsAllocating(false);
          console.log("Allocation stream finished");
        }
      );
    } catch (e: any) {
      toast.error(e.message);
      setIsAllocating(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 md:px-6 md:py-12 animate-fade-in">
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary mb-4">
          <ListChecks className="h-3.5 w-3.5" />
          Review & Prioritize
        </div>
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Prioritization Grid</h1>
            <p className="mt-2 text-muted-foreground">
              Review the generated tickets, adjust priorities, and approve the allocation plan.
            </p>
          </div>
          {/* Optional: Add a Loading Indicator here if you want it visible next to the title */}
          {isAllocating && (
             <div className="flex items-center text-blue-600 animate-pulse">
                <Loader2 className="h-5 w-5 animate-spin mr-2" />
                Allocating Resources...
             </div>
          )}
        </div>
      </div>

      {/* Pass the loading state to the Grid component if it supports disabling the button */}
      <PrioritizationGrid onApprove={handleApprove} />
    </div>
  );
};

export default Review;