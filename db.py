"""Persistencia SQLite. Sin ORM ni dependencias externas."""
import os
import sqlite3
import hashlib
import hmac
import secrets
from contextlib import closing
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent

def get_db_path():
    _db_url = os.getenv('DATABASE_URL', '').strip()
    if _db_url.startswith('sqlite:///'):
        return Path(_db_url.removeprefix('sqlite:///'))
    elif _db_url.startswith('sqlite:'):
        return Path(_db_url.removeprefix('sqlite:'))
    else:
        data_dir = Path(os.getenv('EF_DATA_DIR', str(ROOT / 'datos')))
        return data_dir / 'educacion_fisica.sqlite3'


def connect():
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=15000')
    return db


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 310000)
    return f'pbkdf2_sha256$310000${salt.hex()}${digest.hex()}'


def check_password(password: str, encoded: str) -> bool:
    try:
        alg, iterations, salt, actual = encoded.split('$')
        if alg != 'pbkdf2_sha256': return False
        expected = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(expected, bytes.fromhex(actual))
    except (ValueError, TypeError):
        return False


def init_db():
    with closing(connect()) as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'docente', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          CHECK(role IN ('admin','docente'))
        );
        CREATE TABLE IF NOT EXISTS sessions (
          token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          csrf_token TEXT NOT NULL, expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sections (
          id INTEGER PRIMARY KEY, school_year TEXT NOT NULL, grade TEXT NOT NULL, name TEXT NOT NULL,
          teacher_id INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(school_year, grade, name)
        );
        CREATE TABLE IF NOT EXISTS students (
          id INTEGER PRIMARY KEY, code TEXT, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
          birth_date TEXT, section_id INTEGER NOT NULL REFERENCES sections(id),
          active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(code)
        );
        CREATE TABLE IF NOT EXISTS anthropometry (
          id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL REFERENCES students(id),
          user_id INTEGER NOT NULL REFERENCES users(id), measured_at TEXT NOT NULL,
          weight_kg REAL NOT NULL, height_cm REAL NOT NULL,
          waist_cm REAL, hip_cm REAL, armspan_cm REAL,
          resting_hr INTEGER, after_hr INTEGER, recovery_hr INTEGER,
          notes TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          CHECK(weight_kg > 0 AND height_cm > 0)
        );
        CREATE TABLE IF NOT EXISTS fitness_tests (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, unit TEXT NOT NULL,
          protocol TEXT NOT NULL, better TEXT NOT NULL DEFAULT 'none'
        );
        CREATE TABLE IF NOT EXISTS fitness_results (
          id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL REFERENCES students(id),
          user_id INTEGER NOT NULL REFERENCES users(id), test_id INTEGER NOT NULL REFERENCES fitness_tests(id),
          measured_at TEXT NOT NULL, value REAL NOT NULL, notes TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS activity_attempts (
          id INTEGER PRIMARY KEY, activity_slug TEXT NOT NULL, score INTEGER NOT NULL,
          total INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_students_section ON students(section_id);
        CREATE INDEX IF NOT EXISTS idx_anthro_student_date ON anthropometry(student_id, measured_at);
        CREATE INDEX IF NOT EXISTS idx_fitness_student_date ON fitness_results(student_id, measured_at);
        ''')
        tests = [
            ('Velocidad de 30 metros', 's', 'Recorrer 30 metros desde una salida indicada y registrar el tiempo.', 'lower'),
            ('Salto horizontal', 'cm', 'Salto desde posición estable, medir la distancia alcanzada.', 'higher'),
            ('Flexibilidad sentado', 'cm', 'Medir alcance con protocolo de flexibilidad sentado.', 'higher'),
            ('Resistencia: caminata', 'm', 'Registrar distancia recorrida durante el tiempo acordado.', 'higher'),
            ('Equilibrio unipodal', 's', 'Registrar tiempo manteniendo apoyo sobre un pie en condiciones seguras.', 'higher'),
        ]
        db.executemany('INSERT OR IGNORE INTO fitness_tests(name,unit,protocol,better) VALUES (?,?,?,?)', tests)
        db.commit()


def add_admin(email, password, name='Administración'):
    with closing(connect()) as db:
        db.execute('INSERT INTO users (name,email,password_hash,role) VALUES (?,?,?,?)',
                   (name, email.strip().lower(), hash_password(password), 'admin'))
        db.commit()
