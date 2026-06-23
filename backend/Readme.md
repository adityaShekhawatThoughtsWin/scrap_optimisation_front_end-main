# Tejas Backend

A Node.js + Express + TypeScript backend that manages file uploads, stores metadata in PostgreSQL via Prisma, orchestrates an ML pipeline through a Flask service, and serves processed outputs through structured APIs.

---

## Tech Stack

- **Node.js / Express / TypeScript** — API server
- **Prisma / PostgreSQL** — ORM and database
- **Multer** — file upload handling
- **Axios** — Flask service communication
- **Pino** — logging
- **Flask (Python)** — ML backend (Kalman Filter + PuLP optimizer)

---

## Base URL

```
/api/v1
```

---

## Architecture

```
Client
  ↓
Express API (Node.js)
  ↓
PostgreSQL (Prisma) + Local File Storage (uploaded_files/)
  ↓
Flask ML Service (Kalman Filter + Planner)
```

---

## ML Pipeline Overview

The system runs a two-step ML pipeline.

### Step 1 — Kalman Filter (KF)

Triggered automatically when `heat-query-all` and `heat-chem` are uploaded together using a `pairedId`.

```
POST /upload/heat-query-all  (with pairedId pointing to heat-chem record)
  OR
POST /upload/heat-chem       (with pairedId pointing to heat-query-all record)
          ↓
    Flask POST /upload
          ↓
    Flask POST /run
          ↓
  KF output file (base64 xlsx in response)
```

The KF output file is then uploaded via `POST /upload/scrap-chem` to store it in the DB for use in Step 2.

---

### Step 2 — Planner

Triggered explicitly via `POST /model/run_model` using DB record IDs.

```
scrapChemId       → KF output file (from Step 1)
heatQueryScheduleId → Heat Query Schedule file
scrapInventoryId  → Scrap Daily Inventory file
gradeFileId       → Grade List file (optional)
          ↓
  Fetch all filepaths from DB (single query)
          ↓
    Flask POST /planner
          ↓
  Scarp_Mix_Recommendation_File.xlsx (base64 in response)
```

---

## Modules

---

### 1. Upload Module

Handles all file ingestion and persistence.

#### Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/upload/heat-query-all` | Upload Heat Query All file |
| POST | `/upload/heat-chem` | Upload Heat Chemistry file |
| POST | `/upload/heat-query-schedule` | Upload Heat Query Schedule file |
| POST | `/upload/scrap-data-inventory` | Upload Scrap Daily Inventory file |
| POST | `/upload/scrap-chem` | Upload Scrap Chemistry / KF output file |
| POST | `/upload/grade-list` | Upload Grade List file |

#### Request

All endpoints accept `multipart/form-data` with a single `file` field.

```
Content-Type: multipart/form-data
Body: file=<your file>
```

For paired uploads (Step 1 trigger), include `pairedId` in the form body:

```
Content-Type: multipart/form-data
Body:
  file=<your file>
  pairedId=<id of the paired file record>
```

#### Behavior

- Files are stored in `uploaded_files/` with the naming format `{timestamp}-{original_filename}`
- A DB record is created for every upload with the file path and upload type
- Returns the created DB record on success
- When `pairedId` is provided on `heat-query-all` or `heat-chem`, Step 1 ML execution is triggered automatically

#### Response (standard upload)

```json
{
  "message": "File uploaded successfully",
  "data": {
    "id": 1,
    "filepath": "uploaded_files/1748123456789-HeatQuery_All_xyz.csv",
    "upload_type": "heat_query_all",
    "created_at": "2025-01-01T00:00:00.000Z",
    "is_deleted": false
  }
}
```

#### Response (paired upload — Step 1 triggered)

```json
{
  "message": "File uploaded successfully",
  "data": {
    "record": { ...upload record... },
    "modelResult": {
      "success": true,
      "output_filename": "KF_Scarp_Chemistry_File_27495.xlsx",
      "output_file": {
        "filename": "KF_Scarp_Chemistry_File_27495.xlsx",
        "content_base64": "...",
        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      }
    }
  }
}
```

---

### 2. Model Module

Runs the planner pipeline using stored file record IDs.

#### Endpoint

```
POST /model/run_model
```

#### Request

```
Content-Type: application/json
```

```json
{
  "scrapChemId": 1,
  "heatQueryScheduleId": 2,
  "scrapInventoryId": 3,
  "gradeFileId": 4
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scrapChemId` | number | Yes | DB record ID of the KF output file (uploaded via `/upload/scrap-chem`) |
| `heatQueryScheduleId` | number | Yes | DB record ID of the Heat Query Schedule file |
| `scrapInventoryId` | number | Yes | DB record ID of the Scrap Daily Inventory file |
| `gradeFileId` | number | No | DB record ID of the Grade List file |

#### Response

```json
{
  "message": "Planner run successful",
  "data": {
    "success": true,
    "message": "Planner optimization completed",
    "output_filename": "Scarp_Mix_Recommendation_File.xlsx",
    "output_file": {
      "filename": "Scarp_Mix_Recommendation_File.xlsx",
      "content_base64": "...",
      "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
  }
}
```

---

### 3. Download Module

Returns the latest available file for each upload type as a Base64 payload.

#### Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/download/heat-query-all` | Download latest Heat Query All file |
| GET | `/download/heat-chem` | Download latest Heat Chemistry file |
| GET | `/download/heat-query-schedule` | Download latest Heat Query Schedule file |
| GET | `/download/scrap-data-inventory` | Download latest Scrap Daily Inventory file |
| GET | `/download/scrap-chem` | Download latest Scrap Chemistry / KF output file |
| GET | `/download/grade-list` | Download latest Grade List file |

#### Behavior

- Fetches the latest non-deleted record for the given upload type from DB
- Reads the file from disk
- Returns Base64-encoded content

#### Response

```json
{
  "filename": "HeatQuery_All_xyz.csv",
  "mimeType": "text/csv",
  "size": 12345,
  "data": "<base64_encoded_content>"
}
```

---

## Cleanup System

Runs automatically on the first upload of each day.

- Determines the previous working day boundary
- Soft deletes old DB records (`is_deleted = true`)
- Deletes corresponding files from disk
- Preserves the current working dataset

---

## Database Schema

Table: `data`

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Primary key |
| `filepath` | string | Path to stored file |
| `upload_type` | enum | File category |
| `created_at` | datetime | Upload timestamp |
| `is_deleted` | boolean | Soft delete flag |

### Upload Type Enum

| Value | Description |
|-------|-------------|
| `heat_query_all` | Heat Query All file |
| `heat_chem` | Heat Chemistry file |
| `heat_query_schedule` | Heat Query Schedule file |
| `scrap_data_inventory` | Scrap Daily Inventory file |
| `scrap_chem` | Scrap Chemistry / KF output file |
| `grade_list` | Grade List file |

---

## File Storage

All uploaded files are stored locally:

```
/uploaded_files
```

Naming format:

```
{timestamp}-{original_filename}
```

---

## Environment Variables

```env
DATABASE_URL=postgresql://user:password@localhost:5432/tejas
FLASK_BASE_URL=http://127.0.0.1:5000
PORT=8000
NODE_ENV=development
LOG_LEVEL=info
```

---

## Project Structure

```
src/
  modules/
    upload/
      upload.controller.ts
      upload.service.ts
      upload.repository.ts
      upload.router.ts
    model/
      model.controller.ts
      model.service.ts
      model.repository.ts
      model.router.ts
    download/
      download.controller.ts
      download.service.ts
      download.repository.ts
      download.router.ts
  lib/
    kalmanClient.ts    # Flask integration (sendToModel, sendToPlanner)
    prisma.ts          # Prisma client
  constants/
    types.ts           # FileType enum
    route.ts           # Route constants
  server.ts
```