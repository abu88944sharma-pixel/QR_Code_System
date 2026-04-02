from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def run_schema_migrations():
    with engine.begin() as connection:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                auth0_role_id VARCHAR UNIQUE,
                auth0_role_name VARCHAR NOT NULL UNIQUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                delete_at TIMESTAMPTZ NULL,
                is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                client_id VARCHAR UNIQUE NOT NULL,
                name VARCHAR NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                delete_at TIMESTAMPTZ NULL,
                is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                auth0_id VARCHAR UNIQUE,
                name VARCHAR NOT NULL,
                email VARCHAR UNIQUE,
                created_by VARCHAR NULL,
                role_id INTEGER NULL,
                client_id INTEGER NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                delete_at TIMESTAMPTZ NULL,
                is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            )
            """,
            """
            ALTER TABLE roles
            ADD COLUMN IF NOT EXISTS auth0_role_id VARCHAR
            """,
            """
            ALTER TABLE roles
            ADD COLUMN IF NOT EXISTS auth0_role_name VARCHAR
            """,
            """
            ALTER TABLE roles
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """,
            """
            ALTER TABLE roles
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """,
            """
            ALTER TABLE roles
            ADD COLUMN IF NOT EXISTS delete_at TIMESTAMPTZ NULL
            """,
            """
            ALTER TABLE roles
            ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE
            """,
            """
            ALTER TABLE roles
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE
            """,
            """
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS client_id VARCHAR
            """,
            """
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS name VARCHAR
            """,
            """
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """,
            """
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """,
            """
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS delete_at TIMESTAMPTZ NULL
            """,
            """
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE
            """,
            """
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS auth0_id VARCHAR
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS name VARCHAR
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS email VARCHAR
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS created_by VARCHAR NULL
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS role_id INTEGER
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS client_id INTEGER
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS delete_at TIMESTAMPTZ NULL
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE
            """,
            """
            ALTER TABLE roles
            DROP COLUMN IF EXISTS name
            """,
            """
            ALTER TABLE clients
            DROP CONSTRAINT IF EXISTS fk_clients_role_id_roles
            """,
            """
            DROP INDEX IF EXISTS ix_clients_role_id
            """,
            """
            ALTER TABLE clients
            DROP COLUMN IF EXISTS role_id
            """,
            """
            ALTER TABLE clients
            DROP COLUMN IF EXISTS email
            """,
            """
            ALTER TABLE users
            DROP COLUMN IF EXISTS role
            """,
        ]

        for statement in statements:
            connection.execute(text(statement))

        connection.execute(
            text(
                """
                DO $$
                DECLARE clients_client_id_type TEXT;
                BEGIN
                    SELECT data_type
                    INTO clients_client_id_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'clients'
                      AND column_name = 'client_id';

                    IF clients_client_id_type IS NOT NULL AND clients_client_id_type = 'integer' THEN
                        ALTER TABLE clients
                        ALTER COLUMN client_id TYPE VARCHAR
                        USING client_id::VARCHAR;
                    END IF;
                END
                $$;
                """
            )
        )

        connection.execute(
            text(
                """
                DO $$
                DECLARE roles_id_type TEXT;
                BEGIN
                    SELECT data_type
                    INTO roles_id_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'roles'
                      AND column_name = 'id';

                    IF roles_id_type IS NOT NULL AND roles_id_type <> 'integer' THEN
                        ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_role_id_roles;
                        ALTER TABLE roles ADD COLUMN IF NOT EXISTS new_id SERIAL;
                        UPDATE roles SET new_id = DEFAULT WHERE new_id IS NULL;

                        ALTER TABLE users ADD COLUMN IF NOT EXISTS new_role_id INTEGER;
                        UPDATE users AS u
                        SET new_role_id = r.new_id
                        FROM roles AS r
                        WHERE u.role_id IS NOT NULL
                          AND u.new_role_id IS NULL
                          AND u.role_id::TEXT = r.id::TEXT;

                        DROP INDEX IF EXISTS ix_users_role_id;
                        ALTER TABLE users DROP COLUMN IF EXISTS role_id;
                        ALTER TABLE users RENAME COLUMN new_role_id TO role_id;

                        ALTER TABLE roles DROP CONSTRAINT IF EXISTS roles_pkey;
                        ALTER TABLE roles DROP COLUMN IF EXISTS id;
                        ALTER TABLE roles RENAME COLUMN new_id TO id;
                        ALTER TABLE roles ALTER COLUMN id SET NOT NULL;
                        ALTER TABLE roles ADD PRIMARY KEY (id);
                    END IF;
                END
                $$;
                """
            )
        )

        connection.execute(
            text(
                """
                DO $$
                DECLARE clients_id_type TEXT;
                BEGIN
                    SELECT data_type
                    INTO clients_id_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'clients'
                      AND column_name = 'id';

                    IF clients_id_type IS NOT NULL AND clients_id_type <> 'integer' THEN
                        ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_client_id_clients;
                        ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_client_fk_clients;
                        ALTER TABLE clients ADD COLUMN IF NOT EXISTS new_id SERIAL;
                        UPDATE clients SET new_id = DEFAULT WHERE new_id IS NULL;

                        ALTER TABLE users ADD COLUMN IF NOT EXISTS new_client_id INTEGER;

                        IF EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                              AND table_name = 'users'
                              AND column_name = 'client_id'
                        ) THEN
                            UPDATE users AS u
                            SET new_client_id = c.new_id
                            FROM clients AS c
                            WHERE u.client_id IS NOT NULL
                              AND u.new_client_id IS NULL
                              AND u.client_id::TEXT = c.id::TEXT;
                        END IF;

                        IF EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                              AND table_name = 'users'
                              AND column_name = 'client_fk'
                        ) THEN
                            UPDATE users AS u
                            SET new_client_id = c.new_id
                            FROM clients AS c
                            WHERE u.client_fk IS NOT NULL
                              AND u.new_client_id IS NULL
                              AND u.client_fk::TEXT = c.id::TEXT;
                        END IF;

                        DROP INDEX IF EXISTS ix_users_client_id;
                        DROP INDEX IF EXISTS ix_users_client_fk;
                        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_client_id_fkey;
                        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_client_fk_fkey;
                        ALTER TABLE users DROP COLUMN IF EXISTS client_id;
                        ALTER TABLE users DROP COLUMN IF EXISTS client_fk;
                        ALTER TABLE users RENAME COLUMN new_client_id TO client_id;

                        ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_pkey;
                        ALTER TABLE clients DROP COLUMN IF EXISTS id;
                        ALTER TABLE clients RENAME COLUMN new_id TO id;
                        ALTER TABLE clients ALTER COLUMN id SET NOT NULL;
                        ALTER TABLE clients ADD PRIMARY KEY (id);
                    END IF;
                END
                $$;
                """
            )
        )

        connection.execute(
            text(
                """
                DO $$
                DECLARE users_id_type TEXT;
                BEGIN
                    SELECT data_type
                    INTO users_id_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'users'
                      AND column_name = 'id';

                    IF users_id_type IS NOT NULL AND users_id_type <> 'integer' THEN
                        ALTER TABLE users ADD COLUMN IF NOT EXISTS new_id SERIAL;
                        UPDATE users SET new_id = DEFAULT WHERE new_id IS NULL;

                        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey;
                        ALTER TABLE users DROP COLUMN IF EXISTS id;
                        ALTER TABLE users RENAME COLUMN new_id TO id;
                        ALTER TABLE users ALTER COLUMN id SET NOT NULL;
                        ALTER TABLE users ADD PRIMARY KEY (id);
                    END IF;
                END
                $$;
                """
            )
        )

        connection.execute(
            text(
                """
                DO $$
                DECLARE users_role_type TEXT;
                BEGIN
                    SELECT data_type
                    INTO users_role_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'users'
                      AND column_name = 'role_id';

                    IF users_role_type IS NOT NULL AND users_role_type <> 'integer' THEN
                        ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_role_id_roles;
                        ALTER TABLE users ADD COLUMN IF NOT EXISTS new_role_id INTEGER;
                        UPDATE users AS u
                        SET new_role_id = r.id
                        FROM roles AS r
                        WHERE u.role_id IS NOT NULL
                          AND u.new_role_id IS NULL
                          AND u.role_id::TEXT = r.id::TEXT;

                        DROP INDEX IF EXISTS ix_users_role_id;
                        ALTER TABLE users DROP COLUMN IF EXISTS role_id;
                        ALTER TABLE users RENAME COLUMN new_role_id TO role_id;
                    END IF;
                END
                $$;
                """
            )
        )

        connection.execute(
            text(
                """
                DO $$
                DECLARE users_client_id_type TEXT;
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'users'
                          AND column_name = 'client_fk'
                    ) THEN
                        UPDATE users
                        SET client_id = client_fk
                        WHERE client_id IS NULL
                          AND client_fk IS NOT NULL;

                        DROP INDEX IF EXISTS ix_users_client_fk;
                        ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_client_fk_clients;
                        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_client_fk_fkey;
                        ALTER TABLE users DROP COLUMN IF EXISTS client_fk;
                    END IF;

                    SELECT data_type
                    INTO users_client_id_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'users'
                      AND column_name = 'client_id';

                    IF users_client_id_type IS NOT NULL AND users_client_id_type <> 'integer' THEN
                        ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_client_id_clients;
                        ALTER TABLE users ADD COLUMN IF NOT EXISTS new_client_id INTEGER;

                        UPDATE users AS u
                        SET new_client_id = c.id
                        FROM clients AS c
                        WHERE u.client_id IS NOT NULL
                          AND u.new_client_id IS NULL
                          AND u.client_id::TEXT = c.id::TEXT;

                        UPDATE users AS u
                        SET new_client_id = c.id
                        FROM clients AS c
                        WHERE u.client_id IS NOT NULL
                          AND u.new_client_id IS NULL
                          AND u.client_id::TEXT = c.client_id::TEXT;

                        DROP INDEX IF EXISTS ix_users_client_id;
                        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_client_id_fkey;
                        ALTER TABLE users DROP COLUMN IF EXISTS client_id;
                        ALTER TABLE users RENAME COLUMN new_client_id TO client_id;
                    END IF;
                END
                $$;
                """
            )
        )

        connection.execute(text("UPDATE users SET created_at = NOW() WHERE created_at IS NULL"))
        connection.execute(text("UPDATE users SET updated_at = NOW() WHERE updated_at IS NULL"))
        connection.execute(text("UPDATE users SET name = email WHERE name IS NULL"))
        connection.execute(text("UPDATE roles SET created_at = NOW() WHERE created_at IS NULL"))
        connection.execute(text("UPDATE roles SET updated_at = NOW() WHERE updated_at IS NULL"))
        connection.execute(text("UPDATE clients SET created_at = NOW() WHERE created_at IS NULL"))
        connection.execute(text("UPDATE clients SET updated_at = NOW() WHERE updated_at IS NULL"))
        connection.execute(text("UPDATE clients SET client_id = id::VARCHAR WHERE client_id IS NULL"))
        connection.execute(text("ALTER TABLE users ALTER COLUMN name SET NOT NULL"))

        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ix_roles_auth0_role_name
                ON roles (auth0_role_name)
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ix_clients_client_id
                ON clients (client_id)
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_users_role_id
                ON users (role_id)
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_users_client_id
                ON users (client_id)
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_users_created_by
                ON users (created_by)
                """
            )
        )

        connection.execute(text("ALTER TABLE clients ALTER COLUMN client_id SET NOT NULL"))

        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.key_column_usage kcu
                        JOIN information_schema.referential_constraints rc
                          ON kcu.constraint_name = rc.constraint_name
                         AND kcu.constraint_schema = rc.constraint_schema
                        JOIN information_schema.constraint_column_usage ccu
                          ON rc.unique_constraint_name = ccu.constraint_name
                         AND rc.unique_constraint_schema = ccu.constraint_schema
                        WHERE kcu.table_name = 'users'
                          AND kcu.column_name = 'role_id'
                          AND ccu.table_name = 'roles'
                          AND ccu.column_name = 'id'
                    ) THEN
                        ALTER TABLE users
                        ADD CONSTRAINT fk_users_role_id_roles
                        FOREIGN KEY (role_id) REFERENCES roles (id);
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.key_column_usage kcu
                        JOIN information_schema.referential_constraints rc
                          ON kcu.constraint_name = rc.constraint_name
                         AND kcu.constraint_schema = rc.constraint_schema
                        JOIN information_schema.constraint_column_usage ccu
                          ON rc.unique_constraint_name = ccu.constraint_name
                         AND rc.unique_constraint_schema = ccu.constraint_schema
                        WHERE kcu.table_name = 'users'
                          AND kcu.column_name = 'client_id'
                          AND ccu.table_name = 'clients'
                          AND ccu.column_name = 'id'
                    ) THEN
                        ALTER TABLE users
                        ADD CONSTRAINT fk_users_client_id_clients
                        FOREIGN KEY (client_id) REFERENCES clients (id);
                    END IF;
                END
                $$;
                """
            )
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
