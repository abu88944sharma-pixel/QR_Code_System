# QR_Code_System# QR System - Multi-Tenant FastAPI Backend

This is a production-grade multi-tenant backend built with **FastAPI**, **PostgreSQL**, and **Auth0**. It securely manages user resources across isolated clients.

## Setup Instructions for the Server

This project uses **Alembic** for robust, automated database migrations. The database tables correspond directly to the python scripts already included in the `alembic/versions/` directory of this codebase. **Do NOT delete the `alembic` folder or `alembic.ini` file.**

### Step 1: Environment Setup
1. Copy the sample environment file to create your local `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open the newly created `.env` file and replace the placeholder fields (Auth0 configuration and PostgreSQL Database URL) with your own actual production keys.

### Step 2: Install Virtual Environment & Dependencies
Create an isolated Python environment and install the required modules.

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # (On Windows, use: \venv\Scripts\activate)

# Install required backend dependencies
pip install -r requirements.txt
```

### Step 3: Database Migration (Automated)


If you are setting up the database migrations for the very first time on a fresh pull (or if the `alembic` folder is missing), follow this exact sequence:

**Step 1: Initialize Alembic**
Create the base Alembic scaffolding in your project:
```bash
alembic init alembic
```

**Step 2: Configure `alembic/env.py`**
Open the newly created `alembic/env.py` file and add these critical imports at the very top so Alembic can read your FastAPI SQL Models and `.env` file credentials:
```python
import os
from dotenv import load_dotenv
from app.db.base import Base
from app.db import models  # Force-loads all SQLAlchemy models

load_dotenv()
target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))
```

**Step 3: Generate the Initial Migration Script**
Now, scan your Python models and generate the very first migration blueprint:
```bash
alembic revision --autogenerate -m "initial_schema"
```
*(This commands creates a python script inside `alembic/versions/` containing the exact blueprint for your database).*

**Step 4: Apply to Database**
Finally, push this schema configuration into your live PostgreSQL database:
```bash
alembic upgrade head
```

**Step 5: Subsequent Changes**
Whenever you modify `app/db/models.py` in the future, you **skip Step 1 and Step 2**, and only run **Step 3 and Step 4** to generate and apply updates. Always remember to push your `alembic/versions/` scripts to Git!
