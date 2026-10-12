# HireHub — Online Job Search & Recruitment Platform

A full-stack demo for the Round 3 High-Level System Design Challenge.

## Features
- Search jobs by title, company, skills, description, location, and job type.
- View detailed job descriptions and required skills.
- Submit applications with name, email, resume filename, and optional cover letter.
- Prevent duplicate applications for the same email and job.
- View application history and current status using the same email address.
- Demo endpoint for changing an application status to show status tracking.
- Interactive architecture panel explaining how to scale the design.

## Technology
- Frontend: HTML, CSS, vanilla JavaScript
- Backend: Python, FastAPI
- Database: SQLite (created automatically on first run)
- API documentation: Swagger UI at `/docs`

## Run on Windows
1. Install Python 3.10 or newer.
2. Extract this ZIP file.
3. Open Command Prompt or the VS Code terminal inside the extracted `job_recruitment_platform` folder.
4. Create and activate a virtual environment (recommended):

   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   ```

5. Install dependencies:

   ```bat
   pip install -r requirements.txt
   ```

6. Start the server:

   ```bat
   uvicorn main:app --reload
   ```

7. Open `http://127.0.0.1:8000` in your browser.
8. Open `http://127.0.0.1:8000/docs` to test APIs.

## Run on Ubuntu / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Then visit `http://127.0.0.1:8000`.

## API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/jobs?q=python&location=Chennai` | Search/filter jobs |
| GET | `/api/jobs/{job_id}` | Job details |
| POST | `/api/jobs/{job_id}/applications` | Apply for a job |
| GET | `/api/applications/{application_id}/status?email=you@example.com` | Check one application status |
| GET | `/api/users/applications?email=you@example.com` | Application history |
| PATCH | `/api/demo/applications/{application_id}/status?status=SHORTLISTED` | Demo-only status update |

### Sample application request
```json
{
  "user_name": "Demo Candidate",
  "user_email": "candidate@example.com",
  "resume_name": "resume.pdf",
  "cover_letter": "I am interested in this role."
}
```

## Test application status
1. Apply for a job in the UI and note the application ID.
2. Open Swagger UI at `/docs`.
3. Expand `PATCH /api/demo/applications/{application_id}/status`.
4. Set the ID and a status such as `SHORTLISTED`.
5. Return to **My applications** and enter the same email.

## How to explain Round 3 architecture
- **Load balancer:** distributes traffic across multiple API instances.
- **API gateway:** authentication, routing, throttling, and request validation.
- **Microservices:** separate user, job, company, application, resume, and notification domains.
- **PostgreSQL:** production relational database for users, jobs, companies, and applications.
- **Object storage:** stores actual resume files; only a filename is recorded in this demo.
- **Redis:** caches popular job searches and company information; invalidate cache on job updates.
- **OpenSearch/Elasticsearch:** indexes job titles, skills, descriptions, and locations.
- **Kafka/RabbitMQ:** asynchronously processes application events and notifications.
- **CDN:** serves static assets near users.
- **Observability:** central logs, metrics, tracing, alerts, and health checks.

The local app intentionally uses SQLite and one FastAPI process to keep setup simple. For production, use managed PostgreSQL, Redis, object storage, a search engine, a message broker, authentication/authorization, rate limiting, database migrations, backups, and horizontally scaled service instances.

## Important demo limitations
- This is an educational prototype, not production-ready recruitment software.
- No user login is implemented; history lookup uses email and is not secure enough for real personal data.
- The resume field records a filename only; it does not upload a file.
- The demo status-update endpoint has no recruiter authentication. Do not expose it publicly.
- Apply proper validation, authorization, HTTPS, auditing, and privacy controls before production use.
