# Event Logistics Swarm

A production-grade multi-agent AI system for automating event logistics using LangGraph, FastAPI, and PostgreSQL.

## 🚀 Overview

Event Logistics Swarm is an intelligent orchestration platform that uses specialized AI agents to automate the complex logistics of organizing large technical events like hackathons and tech summits. The system leverages LangGraph for multi-agent coordination, enabling autonomous management of scheduling, marketing, communications, and analytics.

## 🏗️ Architecture

### Multi-Agent System

The platform consists of four specialized agents that collaborate through LangGraph:

1. **Content Strategist Agent**
   - Generates promotional posts for multiple platforms
   - Creates comprehensive marketing plans
   - Develops campaign timelines

2. **Communication/Mailing Agent**
   - Validates participant emails
   - Segments audiences
   - Generates personalized email templates
   - Manages bulk email campaigns

3. **Dynamic Scheduler Agent**
   - Generates optimized event schedules
   - Detects and resolves conflicts
   - Handles room allocation
   - Manages speaker assignments

4. **Analytics Agent**
   - Analyzes engagement data
   - Generates insights and trends
   - Provides actionable recommendations
   - Tracks KPIs and metrics

### Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Agent Orchestration**: LangGraph
- **LLM Interface**: OpenAI API
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLAlchemy 2.0
- **Vector Store**: ChromaDB / PGVector
- **Async Tasks**: Celery + Redis
- **Authentication**: JWT with passlib
- **Data Processing**: Pandas

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+
- Redis 7+ (optional, for Celery)
- OpenAI API key

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd event-logistics-swarm
```

2. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start services:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

4. Run database migrations:
```bash
docker-compose -f docker/docker-compose.yml exec api alembic upgrade head
```

### Manual Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
# OR using Poetry:
poetry install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize database:
```bash
alembic upgrade head
```

5. Run the application:
```bash
python run.py
# OR
uvicorn app.main:app --reload
```

## 🔧 Configuration

### Environment Variables

Key environment variables to configure:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/event_logistics

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# JWT
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Vector Store
VECTOR_STORE_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

## 📚 API Documentation

Once running, access interactive API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

#### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

#### Events
- `POST /events` - Create new event
- `GET /events` - List user's events
- `GET /events/{event_id}` - Get event details
- `PUT /events/{event_id}` - Update event
- `DELETE /events/{event_id}` - Delete event

#### Participants
- `POST /participants` - Add participant
- `POST /participants/upload-csv` - Bulk upload via CSV
- `GET /participants/event/{event_id}` - List event participants

#### AI Agents
- `POST /agents/workflow/run` - Run complete multi-agent workflow
- `POST /agents/marketing/generate` - Generate marketing content
- `POST /agents/email/prepare` - Prepare personalized emails
- `POST /agents/schedule/generate` - Generate event schedule
- `POST /agents/analytics/generate` - Generate analytics

## 🤖 Using the Multi-Agent Workflow

### Example: Complete Workflow

```python
import requests

# 1. Register and login
response = requests.post("http://localhost:8000/auth/register", json={
    "email": "organizer@example.com",
    "username": "organizer",
    "password": "securepassword123",
    "full_name": "Event Organizer"
})

login_response = requests.post("http://localhost:8000/auth/login", json={
    "username": "organizer",
    "password": "securepassword123"
})
token = login_response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# 2. Create event
event_response = requests.post("http://localhost:8000/events", 
    headers=headers,
    json={
        "name": "AI Summit 2024",
        "description": "Annual AI and ML conference",
        "event_type": "conference",
        "theme": "Future of AI",
        "target_audience": "Data scientists and ML engineers",
        "start_date": "2024-06-01T09:00:00",
        "end_date": "2024-06-03T18:00:00",
        "location": "San Francisco, CA",
        "venue": "Moscone Center",
        "max_participants": 500
    }
)
event_id = event_response.json()["id"]

# 3. Upload participants
with open("participants.csv", "rb") as f:
    files = {"file": f}
    requests.post(
        f"http://localhost:8000/participants/upload-csv?event_id={event_id}",
        headers=headers,
        files=files
    )

# 4. Run multi-agent workflow
workflow_response = requests.post("http://localhost:8000/agents/workflow/run",
    headers=headers,
    json={
        "event_id": event_id,
        "workflow_type": "full",
        "parameters": {
            "enable_content_agent": True,
            "enable_email_agent": True,
            "enable_scheduler_agent": True,
            "enable_analytics_agent": True
        }
    }
)

print(workflow_response.json())
```

### CSV Format for Participants

```csv
email,full_name,organization,role,is_speaker,is_sponsor
john@example.com,John Doe,TechCorp,Engineer,false,false
jane@example.com,Jane Smith,AI Labs,Researcher,true,false
sponsor@corp.com,Sponsor Corp,SponsorCo,Marketing,false,true
```

## 🧠 Agent Workflow Details

### LangGraph State Flow

```
User Input
    ↓
Load Context (Vector Memory)
    ↓
Scheduler Agent (Generate Schedule)
    ↓
Marketing Agent (Create Content)
    ↓
Email Agent (Prepare Communications)
    ↓
Analytics Agent (Generate Insights)
    ↓
Save Results (Database + Vector Store)
```

### State Schema

The agents share a common state that includes:
- Event information
- Participant data
- Generated schedules
- Marketing content
- Email templates
- Analytics insights
- Error tracking

## 🗄️ Database Schema

### Core Tables
- `users` - User accounts
- `events` - Event definitions
- `participants` - Event participants
- `schedules` - Session schedules
- `emails` - Email logs
- `marketing_posts` - Generated marketing content
- `agent_logs` - Agent execution logs
- `analytics_reports` - Generated reports

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Application Info
```bash
curl http://localhost:8000/info
```

### Logs
Application logs are stored in `logs/app.log`

## 🚢 Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY` in environment
- [ ] Configure production database with connection pooling
- [ ] Set up proper SMTP credentials
- [ ] Configure CORS for production domains
- [ ] Enable HTTPS/TLS
- [ ] Set `DEBUG=False`
- [ ] Configure log rotation
- [ ] Set up database backups
- [ ] Configure monitoring and alerting
- [ ] Review and set rate limits

### Scaling

The system can be scaled horizontally:
- Multiple API instances behind load balancer
- Separate Celery workers for async tasks
- Database read replicas
- Redis cluster for caching

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- GitHub Issues: <repository-issues-url>
- Documentation: <docs-url>
- Email: support@eventlogistics.com

## 🙏 Acknowledgments

- LangGraph for multi-agent orchestration
- FastAPI for the excellent web framework
- OpenAI for LLM capabilities
- The open-source community

---

**Built with ❤️ for event organizers worldwide**
