# Hospital Management System (DBMS Project)

A beginner-friendly Flask + PostgreSQL hospital management website.

## Modules
- Dashboard: patient, doctor, appointment counts and paid revenue
- Patients: add, search, list, delete
- Doctors: add, list, delete (blocked when appointments exist)
- Appointments: book and update status
- Prescriptions: attach diagnosis, medicines and notes to an appointment
- Billing: create bills and update payment status
- Login: simple admin login

## Database design
- `patients` 1-to-many `appointments`
- `doctors` 1-to-many `appointments`
- `appointments` 1-to-zero-or-one `prescriptions`
- `appointments` 1-to-zero-or-one `bills`

Foreign keys preserve referential integrity. Unique appointment IDs in prescriptions and bills prevent duplicate one-to-one records.

## Run locally (Windows)
1. Install Python 3.11+.
2. Extract this ZIP and open the project folder in VS Code.
3. Open Terminal in that folder.
4. Create a virtual environment:
   `py -m venv venv`
5. Activate it:
   `venv\Scripts\activate`
6. Install packages:
   `pip install -r requirements.txt`
7. Initialize database and demo admin:
   `flask --app app init-db`
8. Run:
   `python app.py`
9. Open `http://127.0.0.1:5000`

Demo login: `admin` / `Admin@123`

Change the demo password before sharing or deploying. For a real deployment, set `SECRET_KEY` and `ADMIN_PASSWORD` environment variables.

## Deploy online (Render + PostgreSQL)
1. Create a GitHub account and a new repository.
2. Upload/push all project files to the repository.
3. On Render, create a managed PostgreSQL database and copy its **internal database URL** if the web service is in the same region (otherwise use the external URL).
4. Create a Render Web Service connected to the GitHub repository.
5. Build command: `pip install -r requirements.txt`
6. Start command: `flask --app app init-db && gunicorn app:app`
7. Add environment variables in Render:
   - `DATABASE_URL` = your PostgreSQL connection URL
   - `SECRET_KEY` = a long random secret value
   - `ADMIN_PASSWORD` = a strong admin password
8. Deploy. Open the generated `onrender.com` URL.

Free hosting/database availability and sleep/expiry policies can change; check the provider's current plan before relying on it for a long-term demo.

## Important project limitations
This is an educational prototype, not a production hospital system. Use fictional demo data only. Before real-world use, add role-based access, CSRF protection, audit logs, input validation, backups, HTTPS enforcement, privacy controls, and security review. Do not enter real patient medical information.

## Suggested viva points
- Primary key: uniquely identifies each row (for example, `patients.id`).
- Foreign key: links related tables and maintains referential integrity.
- 1:M relationship: one patient can have many appointments.
- 1:1 relationship: one appointment can have at most one prescription and one bill.
- CRUD: Create, Read, Update, Delete.
- DBA: manages users/permissions, backups/recovery, security, performance, integrity, availability and monitoring.
