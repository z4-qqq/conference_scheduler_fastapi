# Conference Scheduling Service

![API](https://img.shields.io/badge/API-FastAPI-blue)
![Database](https://img.shields.io/badge/Database-SQLite-green)
![Auth](https://img.shields.io/badge/Auth-JWT-orange)

A RESTful API service for managing conference presentations, rooms, and schedules with intelligent scheduling capabilities.

## Features

- **User Management**:
  - Registration and authentication
  - Role-based access control (Admin/Speaker)
  - JWT token authentication

- **Conference Management**:
  - Room management (create, view)
  - Presentation submission
  - Schedule optimization algorithm
  - Conflict detection (room/speaker availability)

- **API Features**:
  - RESTful endpoints
  - Comprehensive input validation
  - Detailed error responses
  - Automated documentation (Swagger UI)

## Getting Started

### Prerequisites

- Python 3.10+
- pip package manager
- SQLite (included with Python)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/conference-scheduler.git
cd conference-scheduler
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies:
```
pip install -r requirements.txt
```
### Configuration:

1. Create ```.env``` file in the project root:

```
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./conference.db
ADMIN_EMAIL=admin-email
ADMIN_PASSWORD=strong-secure-password
```

### Run application:
```
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

### API Documentation

Interactive documentation is automatically available at:

* Swagger UI: http://localhost:8000/docs

* ReDoc: http://localhost:8000/redoc


### Usage Examples
#### Authentication

**Register a new user:**

```bash
curl -X POST "http://localhost:8000/register" \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"password"}'

```
**Get access token:**
```bash
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@example.com&password=password"
```
###Managing Presentations

**Create a new presentation (requires authentication):**
```bash
curl -X POST "http://localhost:8000/presentations/" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"title":"AI in Healthcare","description":"Latest trends","duration_minutes":45}'
```
**Schedule Optimization**

Optimize the conference schedule (admin only):
```bash
curl -X POST "http://localhost:8000/schedule/optimize" \
     -H "Authorization: Bearer ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"conference_days":2,"day_start_time":"09:00","day_end_time":"18:00","break_duration":15}'
```

### Testing

To run the test suite:
```bash
pytest app
```