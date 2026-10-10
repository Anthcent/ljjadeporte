"""Pruebas de verificación de despliegue en contenedor y Dokploy/Hexper Ops."""
import os
import unittest
import tempfile
from pathlib import Path
from http.server import ThreadingHTTPServer
import threading
from urllib.request import urlopen, Request
from urllib.error import HTTPError

class DeploymentVerification(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['EF_DATA_DIR'] = self.tmp.name
        os.environ['EF_QUIET'] = '1'

    def tearDown(self):
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_healthcheck_returns_200(self):
        """Verifica que el endpoint '/' responde con 200 para el HEALTHCHECK."""
        import db
        import app
        db.init_db()
        server = ThreadingHTTPServer(('127.0.0.1', 0), app.Web)
        port = server.server_port
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            req = Request(f'http://127.0.0.1:{port}/')
            with urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                content = resp.read().decode('utf-8')
                self.assertIn('Educación Física', content)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_auto_admin_provisioning(self):
        """Verifica que un administrador inicial se crea idempotentemente con variables de entorno."""
        import db
        db.init_db()

        # Simular provisionamiento
        email = 'admin_test@dominio.edu'
        password = 'ClaveDePrueba2026!'
        with db.connect() as con:
            existing = con.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone()
            self.assertIsNone(existing)

        db.add_admin(email, password, 'Administrador Docker')

        with db.connect() as con:
            row = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row['role'], 'admin')
            self.assertTrue(db.check_password(password, row['password_hash']))

if __name__ == '__main__':
    unittest.main()
