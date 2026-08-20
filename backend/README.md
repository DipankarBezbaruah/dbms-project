# HostelOut Backend — Digital Outpass & Leave Register

Flask + SQLAlchemy + MySQL backend for the Tezpur University hostel outpass system.

## Prerequisites

- Python 3.10+
- MySQL 8.0+ (running locally or remotely)

## Database Setup

1. Log into MySQL and create the database:

```sql
CREATE DATABASE hostelout;
```

2. (Optional) Create a dedicated MySQL user:

```sql
CREATE USER 'hostelout'@'localhost' IDENTIFIED BY 'hostelout123';
GRANT ALL PRIVILEGES ON hostelout.* TO 'hostelout'@'localhost';
FLUSH PRIVILEGES;
```

## Application Setup

1. Create and activate a virtual environment:

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure the database connection by creating a `.env` file in `backend/`:

```env
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost/hostelout
```

Replace `root:yourpassword` with your MySQL credentials.

4. Initialize the database tables and seed sample data:

```bash
python seed.py
```

This creates all tables and inserts sample hostels, wardens, rooms, students, security staff, and outpasses.

5. Start the Flask development server:

```bash
python app.py
```

The server runs at `http://127.0.0.1:5000`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/students` | Create a new student |
| POST | `/outpasses` | Submit a new outpass request |
| GET | `/outpasses/student/<student_id>` | View outpass history for a student |
| GET | `/outpasses/pending/<hostel_id>` | View pending outpasses for a hostel |
| POST | `/outpasses/<outpass_id>/approve` | Warden approves an outpass |
| POST | `/outpasses/<outpass_id>/reject` | Warden rejects an outpass |
| POST | `/gatelog/<outpass_id>/exit` | Security logs exit time |
| POST | `/gatelog/<outpass_id>/return` | Security logs return time |
| GET | `/reports/overdue/<hostel_id>` | List currently overdue students |

## Project Structure

```
backend/
├── app.py              # Flask application & API routes
├── models.py           # SQLAlchemy ORM models
├── config.py           # Configuration (reads .env)
├── seed.py             # Sample data seeder
├── requirements.txt    # Python dependencies
└── README.md           # This file
```
