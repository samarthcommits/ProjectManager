import { useState } from 'react';
import { Send, MessageCircle } from 'lucide-react';
import { useProjectStore } from '@/stores/useProjectStore';
import { Button } from '@/components/ui/button';
import type { Comment } from '@/types/project';

interface CommentSectionProps {
  ticketId: string;
}

export function CommentSection({ ticketId }: CommentSectionProps) {
  const { comments, addComment } = useProjectStore();
  const [newComment, setNewComment] = useState('');
  const ticketComments = comments[ticketId] || [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    const comment: Comment = {
      id: `comment-${Date.now()}`,
      author: 'You',
      content: newComment.trim(),
      timestamp: new Date(),
    };
    addComment(ticketId, comment);
    setNewComment('');
  };

  const formatTime = (date: Date) =>
    new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }).format(date);

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <MessageCircle className="h-4 w-4 text-primary" />
        Comments ({ticketComments.length})
      </h3>

      {ticketComments.length > 0 && (
        <div className="space-y-3">
          {ticketComments.map((comment) => (
            <div key={comment.id} className="flex gap-3 animate-fade-in">
              <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary shrink-0">
                {comment.author.charAt(0)}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{comment.author}</span>
                  <span className="text-xs text-muted-foreground">{formatTime(comment.timestamp)}</span>
                </div>
                <p className="text-sm text-muted-foreground mt-0.5">{comment.content}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="Add a comment..."
          className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <Button type="submit" size="sm" disabled={!newComment.trim()}>
          <Send className="h-3.5 w-3.5" />
        </Button>
      </form>
    </div>
  );
}
