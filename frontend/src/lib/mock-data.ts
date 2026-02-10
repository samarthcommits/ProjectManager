import type { AgentStep, Ticket, AgentStepStatus } from '@/types/project';

export const mockAgentSteps: AgentStep[] = [
  { id: '1', agent: 'BA Agent', emoji: '🕵️', message: 'Analyzing requirements...', status: 'pending' as AgentStepStatus },
  { id: '2', agent: 'BA Agent', emoji: '🕵️', message: 'Extracting user stories...', status: 'pending' as AgentStepStatus },
  { id: '3', agent: 'Planner Agent', emoji: '📋', message: 'Breaking down modules...', status: 'pending' as AgentStepStatus },
  { id: '4', agent: 'Planner Agent', emoji: '📋', message: 'Generating stories for Auth Module', status: 'pending' as AgentStepStatus },
  { id: '5', agent: 'Planner Agent', emoji: '📋', message: 'Generating stories for Dashboard Module', status: 'pending' as AgentStepStatus },
  { id: '6', agent: 'Planner Agent', emoji: '📋', message: 'Generating stories for API Module', status: 'pending' as AgentStepStatus },
  { id: '7', agent: 'Estimator Agent', emoji: '🧮', message: 'Calculating story points...', status: 'pending' as AgentStepStatus },
  { id: '8', agent: 'Allocator Agent', emoji: '🎯', message: 'Assigning tickets to team...', status: 'pending' as AgentStepStatus },
];

export function generateMockTickets(): Ticket[] {
  return [
    {
      id: '1', ticketId: 'PROJ-101', module: 'Authentication', title: 'Implement JWT Authentication Flow',
      priority: 'critical', status: 'in-progress', assignee: 'Alice', storyPoints: 8,
      userStory: 'As a user, I want to securely log in to the application so that my data is protected.\n\n## Details\nImplement JWT-based auth with refresh tokens, session management, and secure cookie handling.',
      acceptanceCriteria: ['JWT tokens are generated on successful login', 'Refresh tokens are rotated properly', 'Sessions expire after 24 hours of inactivity', 'Failed login attempts are rate-limited'],
      technicalNotes: '// Use PyJWT for token generation\nimport jwt\nfrom datetime import datetime, timedelta\n\ndef create_token(user_id: str):\n    payload = {\n        "sub": user_id,\n        "exp": datetime.utcnow() + timedelta(hours=24)\n    }\n    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")',
    },
    {
      id: '2', ticketId: 'PROJ-102', module: 'Authentication', title: 'OAuth2 Social Login Integration',
      priority: 'high', status: 'todo', assignee: 'Alice', storyPoints: 5,
      userStory: 'As a user, I want to sign in using my Google or GitHub account for convenience.',
      acceptanceCriteria: ['Google OAuth2 integration works', 'GitHub OAuth2 integration works', 'User profile is created on first social login', 'Accounts can be linked to existing email'],
      technicalNotes: '# Configure OAuth providers in settings\nOAUTH_PROVIDERS = {\n    "google": {"client_id": "...", "scope": ["openid", "email"]},\n    "github": {"client_id": "...", "scope": ["user:email"]}\n}',
    },
    {
      id: '3', ticketId: 'PROJ-103', module: 'Dashboard', title: 'Build Analytics Dashboard UI',
      priority: 'high', status: 'in-progress', assignee: 'Bob', storyPoints: 13,
      userStory: 'As a product manager, I want to see key metrics on a dashboard so I can make data-driven decisions.',
      acceptanceCriteria: ['Dashboard loads within 2 seconds', 'Charts are interactive and filterable', 'Date range picker works correctly', 'Data refreshes every 30 seconds'],
      technicalNotes: '// Use Recharts for visualization\nimport { LineChart, BarChart } from "recharts";\n\n// Key metrics: DAU, MAU, Conversion Rate, Revenue',
    },
    {
      id: '4', ticketId: 'PROJ-104', module: 'Dashboard', title: 'Responsive Layout & Mobile Navigation',
      priority: 'medium', status: 'todo', assignee: 'Bob', storyPoints: 5,
      userStory: 'As a mobile user, I want the dashboard to be responsive so I can check metrics on my phone.',
      acceptanceCriteria: ['Layout adjusts for screens < 768px', 'Navigation collapses into hamburger menu', 'Charts resize without data loss', 'Touch interactions work smoothly'],
      technicalNotes: '/* Use Tailwind breakpoints */\n/* sm: 640px, md: 768px, lg: 1024px, xl: 1280px */',
    },
    {
      id: '5', ticketId: 'PROJ-105', module: 'API Gateway', title: 'Rate Limiting Middleware',
      priority: 'critical', status: 'in-review', assignee: 'Alice', storyPoints: 8,
      userStory: 'As a system admin, I want rate limiting to protect the API from abuse.',
      acceptanceCriteria: ['Rate limiting is configurable per endpoint', '429 responses include Retry-After header', 'Rate limits reset correctly after window', 'Admin dashboard shows rate limit stats'],
      technicalNotes: 'from fastapi import Request\nfrom slowapi import Limiter\n\nlimiter = Limiter(key_func=get_remote_address)\n\n@app.get("/api/data")\n@limiter.limit("100/minute")\nasync def get_data(request: Request):\n    ...',
    },
    {
      id: '6', ticketId: 'PROJ-106', module: 'User Management', title: 'User Profile CRUD Operations',
      priority: 'medium', status: 'todo', assignee: 'Alice', storyPoints: 5,
      userStory: 'As a user, I want to view and edit my profile information.',
      acceptanceCriteria: ['Users can update display name and avatar', 'Email changes require verification', 'Profile changes are logged', 'Validation prevents invalid data'],
      technicalNotes: 'class UserProfileUpdate(BaseModel):\n    display_name: Optional[str] = Field(max_length=50)\n    avatar_url: Optional[HttpUrl]\n    bio: Optional[str] = Field(max_length=500)',
    },
    {
      id: '7', ticketId: 'PROJ-107', module: 'Dashboard', title: 'Real-time Notification Bell Component',
      priority: 'low', status: 'todo', assignee: 'Bob', storyPoints: 3,
      userStory: 'As a user, I want to see real-time notifications so I stay updated on important events.',
      acceptanceCriteria: ['Notification bell shows unread count', 'Clicking opens dropdown with recent notifications', 'Mark as read functionality works', 'WebSocket handles reconnection'],
      technicalNotes: '// Use WebSocket for real-time updates\nconst ws = new WebSocket("wss://api.example.com/ws/notifications");',
    },
    {
      id: '8', ticketId: 'PROJ-108', module: 'Authentication', title: 'E2E Auth Flow Test Suite',
      priority: 'high', status: 'in-progress', assignee: 'Charlie', storyPoints: 8,
      userStory: 'As a QA engineer, I want comprehensive E2E tests for the auth flow to ensure reliability.',
      acceptanceCriteria: ['Login flow is tested with valid/invalid credentials', 'OAuth flow is tested with mock providers', 'Token refresh is tested', 'Session timeout is tested'],
      technicalNotes: 'describe("Auth Flow", () => {\n  it("should login with valid credentials", () => { ... });\n  it("should reject invalid credentials", () => { ... });\n  it("should refresh expired tokens", () => { ... });\n});',
    },
    {
      id: '9', ticketId: 'PROJ-109', module: 'API Gateway', title: 'API Integration Test Suite',
      priority: 'medium', status: 'todo', assignee: 'Charlie', storyPoints: 5,
      userStory: 'As a QA engineer, I want integration tests for all API endpoints.',
      acceptanceCriteria: ['All CRUD endpoints are tested', 'Error responses are validated', 'Performance benchmarks are documented', 'Test data is cleaned up after tests'],
      technicalNotes: 'import pytest\nfrom httpx import AsyncClient\n\n@pytest.mark.asyncio\nasync def test_get_users(client: AsyncClient):\n    response = await client.get("/api/users")\n    assert response.status_code == 200',
    },
    {
      id: '10', ticketId: 'PROJ-110', module: 'Notifications', title: 'Email Notification Service',
      priority: 'medium', status: 'done', assignee: 'Alice', storyPoints: 5,
      userStory: 'As a user, I want to receive email notifications for important events.',
      acceptanceCriteria: ['Welcome email sent on registration', 'Password reset emails work', 'Email templates are customizable', 'Unsubscribe link works'],
      technicalNotes: 'from sendgrid import SendGridAPIClient\n\nasync def send_email(to: str, template_id: str, data: dict):\n    sg = SendGridAPIClient(SENDGRID_API_KEY)\n    message = Mail(from_email="noreply@app.com", to_emails=to)\n    sg.send(message)',
    },
    {
      id: '11', ticketId: 'PROJ-111', module: 'Dashboard', title: 'Data Export to CSV/PDF',
      priority: 'low', status: 'done', assignee: 'Bob', storyPoints: 3,
      userStory: 'As a user, I want to export my dashboard data to CSV or PDF format.',
      acceptanceCriteria: ['CSV export includes all visible columns', 'PDF export maintains chart formatting', 'Export triggered from dropdown menu', 'Large datasets are paginated'],
      technicalNotes: '// Use jsPDF for PDF generation\nimport jsPDF from "jspdf";\n\nconst exportToPDF = (data) => {\n  const doc = new jsPDF();\n  doc.save("export.pdf");\n};',
    },
    {
      id: '12', ticketId: 'PROJ-112', module: 'Notifications', title: 'Push Notification Integration Tests',
      priority: 'low', status: 'in-review', assignee: 'Charlie', storyPoints: 5,
      userStory: 'As a QA engineer, I want to verify push notification delivery across platforms.',
      acceptanceCriteria: ['Push notifications work on Chrome and Firefox', 'Permission prompts handled gracefully', 'Notification clicks navigate to correct page', 'Notifications respect user preferences'],
      technicalNotes: 'const testPushNotification = async () => {\n  const permission = await Notification.requestPermission();\n  if (permission === "granted") {\n    new Notification("Test", { body: "Push notification works!" });\n  }\n};',
    },
  ];
}
