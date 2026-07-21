import psycopg2
import psycopg2.extras
import os
import json
from datetime import datetime, timedelta

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    conn = psycopg2.connect(db_url, connection_factory=psycopg2.extras.RealDictConnection)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Reports Table with community_id Multi-Tenancy Architecture
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id SERIAL PRIMARY KEY,
        community_id TEXT NOT NULL DEFAULT 'kwasu_main',
        raw_text TEXT NOT NULL,
        anonymized_text TEXT NOT NULL,
        category TEXT NOT NULL,
        severity INTEGER NOT NULL DEFAULT 1,
        urgency_score REAL NOT NULL DEFAULT 0.0,
        is_urgent BOOLEAN NOT NULL DEFAULT FALSE,
        location TEXT NOT NULL,
        cluster_id TEXT,
        status TEXT NOT NULL DEFAULT 'open',
        confidence_score INTEGER NOT NULL DEFAULT 95,
        source_type TEXT NOT NULL DEFAULT 'web',
        reporter_handle TEXT DEFAULT 'Anon Student',
        ai_reply TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Clusters Table with community_id Support
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clusters (
        id TEXT PRIMARY KEY,
        community_id TEXT NOT NULL DEFAULT 'kwasu_main',
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        primary_location TEXT NOT NULL,
        severity INTEGER NOT NULL DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'active',
        report_count INTEGER NOT NULL DEFAULT 1,
        summary TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Situation Briefs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS briefs (
        id SERIAL PRIMARY KEY,
        community_id TEXT NOT NULL DEFAULT 'kwasu_main',
        period_title TEXT NOT NULL,
        summary_bullets TEXT NOT NULL,
        overall_status TEXT NOT NULL DEFAULT 'MODERATE',
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Admin Actions Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_actions (
        id SERIAL PRIMARY KEY,
        report_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        notes TEXT,
        actor TEXT NOT NULL DEFAULT 'Security Dispatcher',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (report_id) REFERENCES reports (id)
    );
    """)

    # Communities Directory Table (Multi-Tenancy Platform Registry)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS communities (
        community_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        region TEXT NOT NULL,
        type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()

    # Pre-seed directory if empty
    cursor.execute("SELECT COUNT(*) as count FROM communities;")
    if cursor.fetchone()["count"] == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    cursor = conn.cursor()

    # Seed Communities Registry
    communities = [
        {"community_id": "kwasu_main", "name": "KWASU Main Campus", "region": "Malete, Kwara State", "type": "University Campus"},
        {"community_id": "malete_town", "name": "Malete Town Community", "region": "Moro LGA, Kwara State", "type": "Local Community"},
        {"community_id": "ilorin_central", "name": "Ilorin Central Sector", "region": "Ilorin, Kwara State", "type": "Metropolitan Sector"}
    ]
    for comm in communities:
        cursor.execute("""
            INSERT INTO communities (community_id, name, region, type)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (community_id) DO NOTHING
        """, (comm["community_id"], comm["name"], comm["region"], comm["type"]))

    conn.commit()

if __name__ == "__main__":
    init_db()
    print("Database multi-tenancy initialized.")
