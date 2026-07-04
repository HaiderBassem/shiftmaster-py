import os
import sys
import pytest
import pytest_asyncio
import psycopg
import subprocess
from httpx import AsyncClient, ASGITransport
from psycopg_pool import AsyncConnectionPool

# Set env vars BEFORE importing app
os.environ.setdefault("PROJECT_NAME", "Shiftmaster-Test")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "haidercpp")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "shiftmaster_test_db")
os.environ.setdefault("JWT_SECRET", "supersecrettestkeythatisatleast32byteslong")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from app.main import app
from app.api.deps import get_db_pool
from app.core.security import create_access_token

TEST_DB_NAME = "shiftmaster_test_db"
TEST_DB_HOST = os.environ.get("DB_HOST", "localhost")
TEST_DB_PORT = os.environ.get("DB_PORT", "5432")
DEFAULT_DB_URL = f"postgresql://postgres:haidercpp@{TEST_DB_HOST}:{TEST_DB_PORT}/postgres"
TEST_DB_URL = f"postgresql://postgres:haidercpp@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # 1. Create Test Database
    with psycopg.connect(DEFAULT_DB_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME} WITH (FORCE);")
            cur.execute(f"CREATE DATABASE {TEST_DB_NAME};")
            
    # 2. Run Migrations
    migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations")
    subprocess.run([
        sys.executable, "-m", "yoyo", "apply", "--batch", "--database", TEST_DB_URL, migrations_dir
    ], check=True)
    
    yield
    
    # 3. Teardown Test Database
    with psycopg.connect(DEFAULT_DB_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME} WITH (FORCE);")

@pytest_asyncio.fixture(scope="function")
async def db_pool():
    pool = AsyncConnectionPool(conninfo=TEST_DB_URL, min_size=1, max_size=5, open=False)
    await pool.open()
    yield pool
    await pool.close()

@pytest_asyncio.fixture(scope="function")
async def async_client(db_pool):
    app.dependency_overrides[get_db_pool] = lambda: db_pool
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()

TEST_PASSWORD = "password"
TEST_HASHED_PASSWORD = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

@pytest_asyncio.fixture
async def admin_token(db_pool):
    # Insert an admin user into the DB
    user_id = "test-admin-id"
    async with db_pool.connection() as conn:
        # Check if user exists
        async with conn.cursor() as cur:
            await cur.execute("SELECT id FROM employees WHERE email = 'admin@test.com'")
            if not await cur.fetchone():
                await cur.execute("""
                    INSERT INTO employees (
                        id, employee_code, first_name, last_name, gender, email, 
                        password_hash, role, status, hire_date, created_at, updated_at
                    )
                    VALUES (
                        %s, 'ADM-001', 'Admin', 'Test', 'male', 'admin@test.com', 
                        %s, 'admin', 'active', CURRENT_DATE, NOW(), NOW()
                    )
                """, (user_id, TEST_HASHED_PASSWORD))
    
    token = create_access_token({"sub": user_id, "role": "admin"})
    return token

@pytest_asyncio.fixture
async def user_token(db_pool):
    # Insert a regular user into the DB
    user_id = "test-user-id"
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id FROM employees WHERE email = 'user@test.com'")
            if not await cur.fetchone():
                await cur.execute("""
                    INSERT INTO employees (
                        id, employee_code, first_name, last_name, gender, email, 
                        password_hash, role, status, hire_date, created_at, updated_at
                    )
                    VALUES (
                        %s, 'EMP-001', 'User', 'Test', 'male', 'user@test.com', 
                        %s, 'employee', 'active', CURRENT_DATE, NOW(), NOW()
                    )
                """, (user_id, TEST_HASHED_PASSWORD))
    
    token = create_access_token({"sub": user_id, "role": "employee"})
    return token
