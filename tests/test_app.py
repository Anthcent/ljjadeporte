"""Pruebas integrales HTTP y de cálculos (biblioteca estándar)."""
import os
import tempfile
from pathlib import Path
# El directorio temporal debe configurarse antes de importar db.
TMP=tempfile.TemporaryDirectory()
os.environ['EF_DATA_DIR']=TMP.name
os.environ['EF_QUIET']='1'
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unittest
import threading
import http.cookiejar
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode
from datetime import date
import db
import app

class Calculations(unittest.TestCase):
    def test_bmi(self):self.assertEqual(app.bmi(50,158),20.03)
    def test_waist_hip(self):self.assertEqual(app.waist_hip(68,82),0.829)
    def test_pulses(self):self.assertEqual(app.bpm(20,15),80.0)
    def test_numeric_validation(self):
        with self.assertRaises(ValueError):app.parse_number('nan','Peso',1,300)
        with self.assertRaises(ValueError):app.parse_number('0','Peso',1,300)
    def test_csv_escape(self):self.assertTrue(app.csv_safe('=SUM(A1:A3)').startswith("'"))

class HttpFlows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db.init_db()
        db.add_admin('admin@example.test','pruebacompleja2026','Administrador de pruebas')
        with db.connect() as con:
            con.execute('INSERT INTO users(name,email,password_hash,role) VALUES (?,?,?,?)',('Docente Dos','docente@example.test',db.hash_password('docente2026seguro'),'docente'))
            t=con.execute("SELECT id FROM users WHERE email='docente@example.test'").fetchone()[0]
            con.execute('INSERT INTO sections(school_year,grade,name,teacher_id) VALUES (?,?,?,?)',('2026-2027','1.º','B',t))
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),app.Web)
        cls.port=cls.server.server_port
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.guest=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
        cls.admin=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
        cls.teacher=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
        cls.login(cls.admin,'admin@example.test','pruebacompleja2026')
        cls.login(cls.teacher,'docente@example.test','docente2026seguro')

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=4)

    @classmethod
    def open(cls,opener,path,form=None):
        url=f'http://127.0.0.1:{cls.port}{path}'
        data=urlencode(form).encode() if form is not None else None
        req=Request(url,data=data,headers={'Content-Type':'application/x-www-form-urlencoded'} if data else {})
        try:
            with opener.open(req,timeout=6) as response:
                return response.status,response.url,response.read().decode('utf-8',errors='replace'),dict(response.headers)
        except HTTPError as er:
            return er.code,er.url,er.read().decode('utf-8',errors='replace'),dict(er.headers)

    @classmethod
    def login(cls,opener,email,password):
        status,loc,body,_=cls.open(opener,'/ingresar',{'email':email,'password':password})
        assert status==200 and loc.endswith('/panel'),(status,loc,body[:300])

    @classmethod
    def csrf(cls,opener):
        st,loc,text,_=cls.open(opener,'/secciones')
        import re
        found=re.search(r'name="csrf" value="([^"]+)"',text)
        assert found,text[:200]
        return found.group(1)

    def test_01_public_site(self):
        for path,text in [('/', 'Educación Física'),('/aprender','Biblioteca educativa'),('/calculadoras','Índice de masa corporal'),('/actividades','Aprende con retos'),('/leccion/fisiologia','Fisiología del ejercicio')]:
            status,_,body,_=self.open(self.guest,path)
            self.assertEqual(status,200,path);self.assertIn(text,body)

    def test_02_private_not_public(self):
        status,url,body,_=self.open(self.guest,'/estudiantes')
        self.assertTrue(url.endswith('/ingresar'))
        self.assertNotIn('Listado de estudiantes',body)

    def test_03_crud_student_and_anthro(self):
        csrf=self.csrf(self.teacher)
        with db.connect() as con:
            sid=con.execute("SELECT id FROM sections WHERE name='B'").fetchone()[0]
        st,url,_,_=self.open(self.teacher,'/estudiantes/nuevo',{'csrf':csrf,'first_name':'Ana','last_name':'Ejemplo','code':'TEST-001','section_id':str(sid),'birth_date':''})
        self.assertEqual(st,200)
        self.assertRegex(url,r'/estudiantes/\d+$')
        stud_id=int(url.split('/')[-1])
        st,_,body,_=self.open(self.teacher,f'/estudiantes/{stud_id}')
        self.assertEqual(st,200);self.assertIn('Ana Ejemplo',body)
        st,url,_,_=self.open(self.teacher,'/antropometria/nueva',{'csrf':csrf,'student_id':str(stud_id),'measured_at':date.today().isoformat(),'weight_kg':'50','height_cm':'158','waist_cm':'68','hip_cm':'82','armspan_cm':'','resting_hr':'80','after_hr':'110','recovery_hr':'90','notes':'Observación de prueba'})
        self.assertTrue(url.endswith(f'/estudiantes/{stud_id}'))
        st,_,body,_=self.open(self.teacher,f'/estudiantes/{stud_id}')
        self.assertIn('20.03',body);self.assertIn('Observación de prueba',body)
        st,_,csv,_=self.open(self.teacher,f'/exportar/estudiante/{stud_id}')
        self.assertEqual(st,200);self.assertIn('50.0',csv)
        st,_,body,_=self.open(self.teacher,'/estadisticas')
        self.assertEqual(st,200)
        st,url,_,_=self.open(self.teacher,'/evaluaciones/nueva',{'csrf':csrf,'student_id':str(stud_id),'test_id':'1','measured_at':date.today().isoformat(),'value':'7.30','notes':'Prueba sin diagnóstico'})
        self.assertTrue(url.endswith(f'/estudiantes/{stud_id}'))
        st,_,body,_=self.open(self.teacher,f'/estudiantes/{stud_id}')
        self.assertIn('7.3 s',body)
        # Inyección SQL y XSS no ejecutables en el listado.
        st,_,body,_=self.open(self.teacher,'/estudiantes?q=%3Cscript%3E')
        self.assertEqual(st,200);self.assertNotIn('<script>',body)

    def test_04_access_control_and_csrf(self):
        csrf=self.csrf(self.teacher)
        st,_,text,_=self.open(self.teacher,'/usuarios')
        self.assertEqual(st,404)
        st,_,text,_=self.open(self.guest,'/usuarios')
        self.assertTrue('ingresar' in text.lower() or 'Acceso docente' in text)
        st,_,text,_=self.open(self.teacher,'/secciones/nueva',{'csrf':'not-csrf','school_year':'2026-2027','grade':'2.º','name':'C'})
        self.assertEqual(st,403)
        with db.connect() as con:
            # Sección del administrador; el docente no debe entrar a este estudiante.
            admin_id=con.execute("SELECT id FROM users WHERE role='admin'").fetchone()[0]
            con.execute('INSERT INTO sections(school_year,grade,name,teacher_id) VALUES (?,?,?,?)',('2026-2027','1.º','A',admin_id))
            sec=con.execute("SELECT id FROM sections WHERE name='A'").fetchone()[0]
            record=con.execute('INSERT INTO students(first_name,last_name,section_id) VALUES (?,?,?)',('Privado','Ejemplo',sec)).lastrowid
        st,_,body,_=self.open(self.teacher,f'/estudiantes/{record}')
        self.assertEqual(st,404)
        st,_,body,_=self.open(self.admin,f'/estudiantes/{record}')
        self.assertEqual(st,200)

    def test_05_qr_and_quiz(self):
        st,_,data,headers=self.open(self.guest,'/qr/pulso')
        self.assertEqual(st,200);self.assertIn('<svg',data)
        st,_,body,_=self.open(self.guest,'/reto/pulso',{'q0':'1','q1':'0','q2':'1'})
        self.assertEqual(st,200);self.assertIn('3<small>/3</small>',body)

if __name__=='__main__':unittest.main()
