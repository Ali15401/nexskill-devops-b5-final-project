# URL Shortener - Microservices Application

[![CI](https://github.com/Ali15401/nexskill-devops-b5-final-project/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Ali15401/nexskill-devops-b5-final-project/actions/workflows/ci.yml?query=branch%3Amain)

A simple microservices-based URL shortener built with Python, Node.js, and React.

## Services

- **Link Service** (Python/Flask) - Port 3000
- **Analytics Service** (Node.js/Express) - Port 4000
- **Frontend** (React) - Port 80/3000

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (remote database provided)

## Database Credentials
```
Host: 8.222.170.22
Port: 5432
Database: urlshortener
User: postgres
Password: postgres
```

**Note:** These credentials are needed to be configured in:
- `link-service/config.py`
- `analytics-service/config.js`

These changes are needed to use the correct database.

## Setup and Run

### 1. Link Service
```bash
cd link-service
python3 -m venv .
. ./bin/activate
pip3 install -r requirements.txt
python3 app.py
```

Runs on: http://localhost:3000

### 2. Analytics Service
```bash
cd analytics-service
npm install
npm start
```

Runs on: http://localhost:4000

### 3. Frontend
```bash
cd frontend
npm install

# Create .env file
echo "REACT_APP_LINK_SERVICE_URL=http://localhost:3000" > .env
echo "REACT_APP_ANALYTICS_SERVICE_URL=http://localhost:4000" >> .env

npm start
```

Runs on: http://localhost:3000 (React dev server)

**Note:** 3000 is the default port, however the Link Service uses the same port. In such a case, frontend will prompt to use a different port

## Testing

1. Open http://localhost:3000 in browser
2. Enter a long URL and click "Shorten"
3. Click the generated short link to test redirection
4. Refresh the page to see updated click counts

## API Endpoints

### Link Service (Port 3000)
- `GET /health` - Health check
- `POST /api/shorten` - Create short URL
- `GET /:short_code` - Redirect to original URL
- `GET /api/links` - Get all links

### Analytics Service (Port 4000)
- `GET /health` - Health check
- `POST /api/track` - Track a click
- `GET /api/analytics/:short_code` - Get analytics for specific link
- `GET /api/analytics` - Get all analytics
