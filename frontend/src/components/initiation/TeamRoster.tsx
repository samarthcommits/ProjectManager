import { useState } from 'react';
import { Users, Plus, X, Tag } from 'lucide-react';
import { useProjectStore } from '@/stores/useProjectStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { TeamMember } from '@/types/project';

export function TeamRoster() {
  const { teamMembers, addTeamMember, removeTeamMember } = useProjectStore();
  const [isAdding, setIsAdding] = useState(false);
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState('');
  const [newSkills, setNewSkills] = useState('');

  const handleAdd = () => {
    if (!newName.trim() || !newRole.trim()) return;
    const member: TeamMember = {
      id: `member-${Date.now()}`,
      name: newName.trim(),
      role: newRole.trim(),
      skills: newSkills
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    };
    addTeamMember(member);
    setNewName('');
    setNewRole('');
    setNewSkills('');
    setIsAdding(false);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold">Team Roster</h2>
        </div>
        <Button variant="outline" size="sm" onClick={() => setIsAdding(!isAdding)} className="h-8">
          <Plus className="h-3.5 w-3.5 mr-1" />
          Add
        </Button>
      </div>

      {isAdding && (
        <div className="rounded-lg border border-border bg-card p-4 space-y-3 animate-fade-in">
          <Input placeholder="Name" value={newName} onChange={(e) => setNewName(e.target.value)} className="h-9" />
          <Input
            placeholder="Role (e.g., Backend Developer)"
            value={newRole}
            onChange={(e) => setNewRole(e.target.value)}
            className="h-9"
          />
          <Input
            placeholder="Skills (comma-separated)"
            value={newSkills}
            onChange={(e) => setNewSkills(e.target.value)}
            className="h-9"
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={handleAdd} className="h-8">
              Add Member
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setIsAdding(false)} className="h-8">
              Cancel
            </Button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {teamMembers.map((member) => (
          <div
            key={member.id}
            className="flex items-start gap-3 rounded-lg border border-border bg-card p-3 group animate-fade-in"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-sm font-semibold">
              {member.name.charAt(0)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium">{member.name}</p>
              <p className="text-xs text-muted-foreground">{member.role}</p>
              <div className="flex flex-wrap gap-1 mt-1.5">
                {member.skills.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1 rounded-md bg-accent px-1.5 py-0.5 text-[10px] font-medium text-accent-foreground"
                  >
                    <Tag className="h-2.5 w-2.5" />
                    {skill}
                  </span>
                ))}
              </div>
            </div>
            <button
              onClick={() => removeTeamMember(member.id)}
              className="text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-destructive transition-all"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
