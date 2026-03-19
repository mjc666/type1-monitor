# type1-monitor

A Type 1 Diabetes management dashboard that synchronizes real-time Dexcom CGM data and Tandem insulin pump data into a local MariaDB database.

## Features
- **Dexcom Sync**: Real-time sensor glucose values (SGV) and trends.
- **Tandem Sync**: Insulin data (Basal, Bolus, IOB) from Tandem Source.
- **Visual Dashboard**: Modern, glassmorphism UI with live charts and status indicators.
- **Local MariaDB Storage**: Complete data history hosted on your own infrastructure.

## Setup Instructions

### 1. Database Setup
Create a new MariaDB database and user:
```sql
CREATE DATABASE type1_monitor;
CREATE USER 'type1'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON type1_monitor.* TO 'type1'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Backend Setup
- Navigate to `backend/`.
- Copy `.env.example` to `.env` and fill in your credentials.
- Install dependencies: `pip install -r requirements.txt`.
- Start the server: `uvicorn main:app --reload`.

### 3. Frontend Setup
- Navigate to `frontend/`.
- Install dependencies: `npm install`.
- Build the app: `npm run build`.

### 4. Deployment
- Use the provided `nginx/type1-monitor.conf` for your Nginx setup.
- Use `systemd/type1-monitor.service` to keep the backend running persistently.

## Technologies
- **Backend**: Python, FastAPI, SQLAlchemy, pydexcom, tconnectsync.
- **Frontend**: React, TypeScript, Vite, Recharts, Lucide React, Vanilla CSS.
- **Database**: MariaDB.
- **Proxy**: Nginx.
