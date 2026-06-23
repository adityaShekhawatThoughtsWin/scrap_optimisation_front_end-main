# Database Setup Guide

Guide for installing PostgreSQL, connecting from this project, and starting/stopping all local services on **macOS** and **Windows**.

---

## Prerequisites

| Tool        | Version |
|-------------|---------|
| Node.js     | 18+     |
| Python      | 3.12+   |
| PostgreSQL  | 16 (recommended) |

---

## 1. Install PostgreSQL

### macOS (Homebrew)

```bash
brew install postgresql@16

# Apple Silicon — add to PATH (~/.zshrc)
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc

# Intel Mac — use this path instead if needed
# echo 'export PATH="/usr/local/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc

source ~/.zshrc
psql --version
```

### Windows

**Option A — Installer (recommended)**

1. Download from [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
2. Run the installer (PostgreSQL 16)
3. Remember the password you set for the `postgres` superuser
4. Keep default port `5432`
5. Optionally install pgAdmin for a GUI

**Option B — winget**

```powershell
winget install PostgreSQL.PostgreSQL.16
```

**Option C — Chocolatey**

```powershell
choco install postgresql16
```

Add PostgreSQL to PATH if not already set:

```
C:\Program Files\PostgreSQL\16\bin
```

Verify:

```powershell
psql --version
```

---

## 2. Start / Stop / Restart PostgreSQL

### macOS

```bash
# Start
brew services start postgresql@16

# Stop
brew services stop postgresql@16

# Restart
brew services restart postgresql@16

# Check status
brew services list | grep postgres
pg_isready -h localhost -p 5432
```

### Windows

**PowerShell (Admin)**

```powershell
# Start
net start postgresql-x64-16

# Stop
net stop postgresql-x64-16

# Status
Get-Service *postgres*
```

> Service name may vary (e.g. `postgresql-x64-16`, `postgresql-x64-15`). Check in **Services** (`services.msc`).

**Alternative — pg_ctl**

```powershell
pg_ctl -D "C:\Program Files\PostgreSQL\16\data" start
pg_ctl -D "C:\Program Files\PostgreSQL\16\data" stop
pg_ctl -D "C:\Program Files\PostgreSQL\16\data" restart
```

**Check if accepting connections (both platforms)**

```bash
pg_isready -h localhost -p 5432
```

Expected output:

```
localhost:5432 - accepting connections
```

---

## 3. Create Database

### macOS

Homebrew Postgres usually uses your **macOS username** as the default DB user.

```bash
# List databases
psql -l

# Create project database
createdb tejasdb

# Or via psql
psql -d postgres -c "CREATE DATABASE tejasdb;"
```

### Windows

Default superuser is `postgres` (password set during install).

```powershell
psql -U postgres -h localhost -c "CREATE DATABASE tejasdb;"
```

Or interactively:

```powershell
psql -U postgres -h localhost
```

```sql
CREATE DATABASE tejasdb;
\q
```

### Optional — dedicated app user (both platforms)

```sql
CREATE USER tejas_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE tejasdb TO tejas_user;
\c tejasdb
GRANT ALL ON SCHEMA public TO tejas_user;
```

---

## 4. Connect to the Database

### macOS

```bash
psql -h localhost -p 5432 -U <your-macos-username> -d tejasdb
```

### Windows

```powershell
psql -h localhost -p 5432 -U postgres -d tejasdb
```

### Useful psql commands

```sql
\l              -- list databases
\dt             -- list tables
\d data         -- describe data table
SELECT * FROM data LIMIT 10;
\q              -- quit
```

### Test connection (one-liner)

**macOS:**

```bash
psql -h localhost -p 5432 -U <your-macos-username> -d tejasdb -c "SELECT 1;"
```

**Windows:**

```powershell
psql -h localhost -p 5432 -U postgres -d tejasdb -c "SELECT 1;"
```

---

## 5. Backend Environment (`backend/.env`)

Create `backend/.env` (do **not** commit to git):

```env
PORT=8000
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/tejasdb
FLASK_BASE_URL=http://127.0.0.1:5000
NODE_ENV=development
LOG_LEVEL=info
```

**Examples:**

| Platform                      | `DATABASE_URL` |
|-------------------------------|----------------|
| macOS (Homebrew, no password) | `postgresql://deepakgupta@localhost:5432/tejasdb` |
| macOS (with password)         | `postgresql://deepakgupta:your_password@localhost:5432/tejasdb` |
| Windows (`postgres` user)     | `postgresql://postgres:your_password@localhost:5432/tejasdb` |
| Custom user (both)            | `postgresql://tejas_user:your_password@localhost:5432/tejasdb` |

---

## 6. Prisma — Apply Schema

Run from the `backend/` directory:

```bash
cd backend
npm install
npx prisma generate
npx prisma db push
```

Verify tables were created:

```bash
psql -d tejasdb -c "\dt"
```

You should see the `data` table.

### Optional — Prisma Studio (DB GUI)

```bash
npx prisma studio
```

Opens at http://localhost:5555

---

## 7. Start All Application Services

Run each in a **separate terminal**.

### Terminal 1 — PostgreSQL

**macOS:**

```bash
brew services start postgresql@16
pg_isready -h localhost -p 5432
```

**Windows:**

```powershell
net start postgresql-x64-16
pg_isready -h localhost -p 5432
```

### Terminal 2 — Backend API (Express + Prisma)

```bash
cd backend
npm install
npx prisma generate
npm run dev
```

Runs at: http://localhost:8000

### Terminal 3 — Flask ML service (Kalman / Planner)

**macOS:**

```bash
cd "backend/src/modules/kalman script"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Windows (PowerShell):**

```powershell
cd "backend\src\modules\kalman script"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

> If script execution is blocked on Windows:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Runs at: http://127.0.0.1:5000

### Terminal 4 — Frontend (React + Vite)

Create `frontend/.env`:

```env
PORT=3000
VITE_API_BASE_URL=http://localhost:8000
```

```bash
cd frontend
npm install
npm run dev
```

Runs at: http://localhost:3000

---

## 8. Stop All Services

### Stop dev servers

Press **Ctrl + C** in each terminal running `npm run dev`, `python app.py`, or `npx prisma studio`.

### Deactivate Python venv

**macOS:**

```bash
deactivate
```

**Windows:**

```powershell
deactivate
```

### Stop PostgreSQL

**macOS:**

```bash
brew services stop postgresql@16
```

**Windows:**

```powershell
net stop postgresql-x64-16
```

### Confirm everything is stopped

**macOS:**

```bash
pg_isready -h localhost -p 5432    # should say "no response"
lsof -i :8000
lsof -i :3000
lsof -i :5000
```

**Windows:**

```powershell
pg_isready -h localhost -p 5432
netstat -ano | findstr :8000
netstat -ano | findstr :3000
netstat -ano | findstr :5000
```

Kill a stuck process on Windows:

```powershell
taskkill /PID <pid> /F
```

---

## 9. Troubleshooting

| Error | Cause | macOS fix | Windows fix |
|-------|-------|-----------|-------------|
| `P1001` — Can't reach database | Postgres not running | `brew services start postgresql@16` | `net start postgresql-x64-16` |
| `P1010` — User denied access | Wrong `DATABASE_URL` | Use macOS username; run `psql -l` | Use `postgres` + install password |
| `role "postgres" does not exist` | Homebrew has no `postgres` user | Use macOS username in URL | Use `postgres` superuser |
| Database does not exist | DB not created | `createdb tejasdb` | `psql -U postgres -c "CREATE DATABASE tejasdb;"` |
| Port in use | Old process still running | `lsof -i :<port>` then `kill <pid>` | `netstat -ano` then `taskkill /PID <pid> /F` |
| `psql: command not found` | Not in PATH | Add Homebrew bin to `~/.zshrc` | Add `C:\Program Files\PostgreSQL\16\bin` to PATH |

### Reset database (destructive — deletes all data)

**macOS:**

```bash
dropdb tejasdb
createdb tejasdb
cd backend && npx prisma db push
```

**Windows:**

```powershell
psql -U postgres -c "DROP DATABASE IF EXISTS tejasdb;"
psql -U postgres -c "CREATE DATABASE tejasdb;"
cd backend
npx prisma db push
```

---

## 10. Quick Reference

| Action         | macOS                              | Windows                                              |
|----------------|------------------------------------|------------------------------------------------------|
| Install        | `brew install postgresql@16`       | Installer / `winget install PostgreSQL.PostgreSQL.16` |
| Start          | `brew services start postgresql@16`| `net start postgresql-x64-16`                        |
| Stop           | `brew services stop postgresql@16` | `net stop postgresql-x64-16`                         |
| Create DB      | `createdb tejasdb`                 | `psql -U postgres -c "CREATE DATABASE tejasdb;"`       |
| Connect        | `psql -d tejasdb`                  | `psql -U postgres -d tejasdb`                        |
| Apply schema   | `npx prisma db push`               | `npx prisma db push`                                 |
| Start backend  | `npm run dev`                      | `npm run dev`                                        |
| Start frontend | `npm run dev`                      | `npm run dev`                                        |
| Activate venv  | `source venv/bin/activate`         | `.\venv\Scripts\Activate.ps1`                      |
| Stop server    | `Ctrl + C`                         | `Ctrl + C`                                           |

---

## Environment Variables Summary

| File            | Variable              | Example                                              |
|-----------------|-----------------------|------------------------------------------------------|
| `backend/.env`  | `DATABASE_URL`        | `postgresql://postgres:pass@localhost:5432/tejasdb`  |
| `backend/.env`  | `PORT`                | `8000`                                               |
| `backend/.env`  | `FLASK_BASE_URL`      | `http://127.0.0.1:5000`                              |
| `frontend/.env` | `VITE_API_BASE_URL`   | `http://localhost:8000`                              |
| `frontend/.env` | `PORT`                | `3000`                                               |
