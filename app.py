"""Aplicación web monolítica de Educación Física: Python 3 + SQLite + HTTP estándar.
Ejecuta: python app.py init | python app.py | python -m unittest discover -s tests
Diseñada para desarrollo y demostraciones en localhost. Para uso institucional remoto,
colocar detrás de HTTPS, aplicar controles y realizar revisión de seguridad.
"""
import os
import re
import io
import csv
import json
import math
import secrets
import hashlib
import getpass
import sqlite3
import mimetypes
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from html import escape
from urllib.parse import urlsplit, parse_qs, urlencode, quote
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie

from db import connect, init_db, add_admin, check_password, hash_password
from content import LESSONS, ACTIVITIES
from ui import e, icon, layout, page_header, panel, stat, field, selection, textarea, empty, table, badge, svg_line

HERE = Path(__file__).resolve().parent
MIMES={'.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp'}


def bmi(weight, height_cm):
    return round(float(weight) / (float(height_cm)/100)**2, 2)

def waist_hip(waist, hip):
    return round(float(waist) / float(hip), 3)

def bpm(pulses, seconds):
    if seconds <= 0: raise ValueError('Tiempo inválido')
    return round(float(pulses)*60/float(seconds), 1)

def parse_number(value, label, minimum=None, maximum=None, optional=False):
    value = str(value or '').strip().replace(',', '.')
    if not value and optional: return None
    try: result=float(value)
    except ValueError: raise ValueError(f'{label}: introduce un número válido.')
    if not math.isfinite(result): raise ValueError(f'{label}: introduce un número finito.')
    if minimum is not None and result < minimum: raise ValueError(f'{label}: valor demasiado pequeño.')
    if maximum is not None and result > maximum: raise ValueError(f'{label}: valor demasiado grande.')
    return result

def dt_today(): return date.today().isoformat()

def as_date(v):
    try: return date.fromisoformat(str(v)).strftime('%d/%m/%Y')
    except (ValueError, TypeError): return str(v or '—')

def full_name(s): return f"{s['first_name']} {s['last_name']}"

def csv_safe(value):
    s=str('' if value is None else value)
    if s[:1] in ('=','+','-','@','\t','\r','\n'): return "'"+s
    return s

class Web(BaseHTTPRequestHandler):
    server_version='EFPlus/1.0'

    def log_message(self, fmt, *args):
        if os.getenv('EF_QUIET') != '1': super().log_message(fmt, *args)

    def send(self, html, status=200, headers=None):
        payload=html.encode('utf-8') if isinstance(html,str) else html
        self.send_response(status)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
        if headers:
            for k,v in headers.items():self.send_header(k,v)
        self.send_header('Content-Length',str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def text_response(self, data, ctype='text/plain; charset=utf-8', headers=None):
        payload=data.encode('utf-8') if isinstance(data,str) else data
        self.send_response(200)
        self.send_header('Content-Type',ctype)
        self.send_header('X-Content-Type-Options','nosniff')
        if headers:
            for k,v in headers.items():self.send_header(k,v)
        self.send_header('Content-Length',str(len(payload)))
        self.end_headers();self.wfile.write(payload)

    def redirect(self,url, cookie=None):
        self.send_response(303)
        self.send_header('Location',url)
        self.send_header('Cache-Control','no-store')
        if cookie:self.send_header('Set-Cookie',cookie)
        self.send_header('Content-Length','0');self.end_headers()

    def do_GET(self):
        try:
            self.route('GET')
        except (BrokenPipeError, ConnectionResetError): pass
        except Exception as ex:
            if os.getenv('EF_DEBUG')=='1':
                import traceback;traceback.print_exc()
            self.fail(500,'Se produjo un error interno. Revisa los registros de la aplicación.')

    def do_POST(self):
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<=0 or n>500_000: return self.fail(413,'Solicitud demasiado grande.')
            ctype=self.headers.get('Content-Type','')
            if not ctype.startswith('application/x-www-form-urlencoded'): return self.fail(415,'Formato de solicitud no admitido.')
            data=self.rfile.read(n).decode('utf-8',errors='replace')
            self.form={k:v[0] for k,v in parse_qs(data,keep_blank_values=True).items()}
            origin=self.headers.get('Origin','')
            if origin:
                host=self.headers.get('Host','')
                if urlsplit(origin).netloc != host: return self.fail(403,'Origen de formulario inválido.')
            self.route('POST')
        except (BrokenPipeError, ConnectionResetError):pass
        except Exception as ex:
            if os.getenv('EF_DEBUG')=='1':
                import traceback;traceback.print_exc()
            self.fail(500,'No se pudo completar la operación.')

    def fail(self,status,message):
        try:self.render('Aviso',f'<div class="error-page"><h1>{status}</h1><p>{e(message)}</p><a class="btn btn-primary" href="/">Volver al inicio</a></div>',status=status)
        except Exception:pass

    def query(self): return {k:v[0] for k,v in parse_qs(urlsplit(self.path).query).items()}

    def authenticate(self):
        self.db=connect()
        self.user=None;self.session=None;self.cookie_token=None
        try:
            cookie=SimpleCookie();cookie.load(self.headers.get('Cookie',''))
            if 'ef_session' in cookie:
                token=cookie['ef_session'].value
                if len(token)==64 and re.fullmatch('[0-9a-f]+',token):
                    row=self.db.execute('''SELECT sessions.csrf_token, sessions.expires_at, users.*
                        FROM sessions JOIN users ON users.id=sessions.user_id
                        WHERE sessions.token_hash=?''',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
                    if row and row['expires_at'] > datetime.now(timezone.utc).isoformat():
                        self.user=dict(row)
                        self.session=row['csrf_token']
                        self.cookie_token=token
        except Exception: pass

    def render(self,title,body,active='',status=200,message=''):
        self.send(layout(title,body,getattr(self,'user',None),active,message,getattr(self,'session','') or ''),status=status)

    def require(self):
        if not self.user:
            self.redirect('/ingresar');return False
        return True

    def csrf_check(self):
        if not self.user or not secrets.compare_digest(self.form.get('csrf',''),self.session or ''):
            self.fail(403,'Formulario vencido o solicitud no autorizada. Recarga la página.');return False
        return True

    def form_csrf(self): return f'<input type="hidden" name="csrf" value="{e(self.session)}">'

    def sections(self):
        if self.user['role']=='admin':return self.db.execute('SELECT s.*,u.name AS teacher FROM sections s JOIN users u ON u.id=s.teacher_id ORDER BY s.school_year DESC,s.grade,s.name').fetchall()
        return self.db.execute('SELECT s.*,u.name AS teacher FROM sections s JOIN users u ON u.id=s.teacher_id WHERE teacher_id=? ORDER BY s.school_year DESC,s.grade,s.name',(self.user['id'],)).fetchall()

    def students(self):
        wh='' if self.user['role']=='admin' else 'WHERE s.teacher_id=?'
        params=[] if self.user['role']=='admin' else [self.user['id']]
        return self.db.execute(f'''SELECT p.*,s.name AS section_name,s.grade,s.school_year,s.teacher_id
            FROM students p JOIN sections s ON p.section_id=s.id {wh}
            ORDER BY p.active DESC,p.last_name,p.first_name''',params).fetchall()

    def student(self,identifier):
        try: sid=int(identifier)
        except (ValueError,TypeError):return None
        wh='' if self.user['role']=='admin' else 'AND s.teacher_id=?'
        params=[sid] if self.user['role']=='admin' else [sid,self.user['id']]
        return self.db.execute(f'''SELECT p.*, s.name AS section_name,s.grade,s.school_year,s.teacher_id
          FROM students p JOIN sections s ON s.id=p.section_id WHERE p.id=? {wh}''',params).fetchone()

    def choose_student(self, selected='', required=True):
        return selection('student_id','Estudiante',[(s['id'],f"{full_name(s)} · {s['grade']} {s['section_name']}") for s in self.students() if s['active']],selected,required)

    def route(self,method):
        url=urlsplit(self.path)
        path=url.path.rstrip('/') or '/'
        if path.startswith('/static/') and method=='GET':return self.static(path)
        self.authenticate()
        try:
            if method=='GET':
                if path=='/': return self.public_home()
                if path=='/aprender':return self.learn()
                if path.startswith('/leccion/'):return self.lesson(path.split('/')[-1])
                if path=='/actividades':return self.activities()
                if path.startswith('/reto/'):return self.challenge(path.split('/')[-1])
                if path=='/calculadoras':return self.calculators()
                if path=='/ingresar':return self.login_page()
                if path.startswith('/qr/'):return self.qr_image(path.split('/')[-1])
                if not self.require():return
                if path=='/panel':return self.dashboard()
                if path=='/secciones':return self.sections_page()
                if path=='/estudiantes':return self.students_page()
                if path=='/estudiantes/nuevo':return self.student_form()
                m=re.fullmatch(r'/estudiantes/(\d+)/editar',path)
                if m:return self.student_form(m.group(1))
                m=re.fullmatch(r'/estudiantes/(\d+)',path)
                if m:return self.student_page(m.group(1))
                if path=='/antropometria/nueva':return self.anthro_form()
                if path=='/evaluaciones':return self.evaluations()
                if path=='/cronometro':return self.timer_page()
                if path=='/estadisticas':return self.analytics()
                if path=='/informes':return self.reports()
                m=re.fullmatch(r'/exportar/estudiante/(\d+)',path)
                if m:return self.export_student(m.group(1))
                if path=='/usuarios' and self.user['role']=='admin':return self.users_page()
            elif method=='POST':
                if path=='/ingresar':return self.login_submit()
                if path.startswith('/reto/'):return self.challenge(path.split('/')[-1])
                if not self.csrf_check():return
                if path=='/salir':return self.logout()
                if path=='/secciones/nueva':return self.new_section()
                if path=='/estudiantes/nuevo':return self.save_student()
                m=re.fullmatch(r'/estudiantes/(\d+)/editar',path)
                if m:return self.save_student(m.group(1))
                m=re.fullmatch(r'/estudiantes/(\d+)/estado',path)
                if m:return self.toggle_student(m.group(1))
                if path=='/antropometria/nueva':return self.save_anthro()
                if path=='/evaluaciones/nueva':return self.save_fitness()
                if path=='/usuarios/nuevo' and self.user['role']=='admin':return self.new_user()
            self.fail(404,'La página que buscas no existe o no está disponible.')
        finally:
            self.db.close()

    def static(self,path):
        name=path.removeprefix('/static/')
        if '/' in name or '\\' in name or name.startswith('.'):return self.fail(404,'Archivo no encontrado')
        f=HERE/'static'/name
        if not f.is_file():return self.fail(404,'Archivo no encontrado')
        self.text_response(f.read_bytes(),MIMES.get(f.suffix,'application/octet-stream'),{'Cache-Control':'public, max-age=3600'})

    def login_page(self,message=''):
        if self.user:return self.redirect('/panel')
        no_users = False
        try:
            no_users = (self.db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0)
        except Exception:
            pass
        notice = ''
        if no_users:
            notice = '<div class="alert alert-info"><b>Configuración inicial:</b> Aún no hay cuentas en el sistema. Configura <code>EF_ADMIN_EMAIL</code> y <code>EF_ADMIN_PASSWORD</code> en las variables de entorno de Dokploy y redespliega la aplicación.</div>'
        elif message:
            notice = f'<div class="alert alert-error">{e(message)}</div>'
        form=f'''<div class="login-shell"><div class="login-art"><span class="pill pill-light">Plataforma educativa</span><h1>Enseñar el movimiento. <em>Comprender el cuerpo.</em></h1><p>Contenidos científicos, registros y evaluación pedagógica en un solo lugar.</p><div class="login-art-detail">EF+ <span>Educación · Ciencia · Tecnología</span></div></div><section class="login-card"><span class="eyebrow">ACCESO SEGURO</span><h2>Bienvenido de nuevo</h2><p>Ingresa con tu cuenta de docente o administrador.</p>{notice}<form method="post" action="/ingresar" class="stack-form">{field('email','Correo electrónico',fieldtype='email',required=True,placeholder='docente@liceo.edu')}{field('password','Contraseña',fieldtype='password',required=True,placeholder='Tu contraseña')}<button class="btn btn-primary btn-block">Ingresar al panel {icon('arrow',17)}</button></form><a href="/" class="under-link">← Regresar al sitio educativo</a><p class="login-footnote">Las cuentas son creadas por el administrador. Si olvidaste tu contraseña, solicítale restablecerla.</p></section></div>'''
        return self.render('Ingresar',form)

    def login_submit(self):
        email=self.form.get('email','').strip().lower()
        password=self.form.get('password','')
        row=self.db.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        if not row or not check_password(password,row['password_hash']):return self.login_page('Correo o contraseña incorrectos.')
        raw=secrets.token_hex(32)
        csrf=secrets.token_hex(24)
        exp=(datetime.now(timezone.utc)+timedelta(hours=10)).isoformat()
        self.db.execute('DELETE FROM sessions WHERE expires_at < ?', (datetime.now(timezone.utc).isoformat(),))
        self.db.execute('INSERT INTO sessions(token_hash,user_id,csrf_token,expires_at) VALUES (?,?,?,?)',(hashlib.sha256(raw.encode()).hexdigest(),row['id'],csrf,exp))
        self.db.commit()
        return self.redirect('/panel',f'ef_session={raw}; HttpOnly; SameSite=Lax; Path=/; Max-Age=36000')

    def logout(self):
        self.db.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(self.cookie_token.encode()).hexdigest(),));self.db.commit()
        return self.redirect('/', 'ef_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0')

    def public_home(self):
        cards=''.join(f'''<a class="lesson-mini" href="/leccion/{l['slug']}"><div class="lesson-icon">{e(l['icon'])}</div><span class="eyebrow">{e(l['tag'])}</span><h3>{e(l['title'])}</h3><p>{e(l['intro'])}</p><span class="text-link">Explorar contenido {icon('arrow',15)}</span></a>''' for l in LESSONS[:3])
        body=f'''<section class="hero"><div class="hero-content"><div class="pill">TECNOLOGÍA AL SERVICIO DEL MOVIMIENTO</div><h1>Educación Física que <span>inspira, enseña y conecta.</span></h1><p>Un espacio para descubrir cómo funciona el cuerpo, aprender mediante actividades y acompañar la práctica física con ciencia y tecnología.</p><div class="hero-actions"><a class="btn btn-white" href="/aprender">Explorar lecciones {icon('arrow',18)}</a><a class="btn btn-outline-light" href="/actividades">Resolver retos</a></div><div class="hero-note">Inspirado en la investigación de la Lcda. Rosanny A. Terán V. · Liceo José Antonio Abreu</div></div><div class="hero-visual"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><div class="hero-center"><span>EF</span><strong>+</strong><small>MOVIMIENTO + CIENCIA</small></div><div class="floating-label label-a">Fisiología</div><div class="floating-label label-b">Anatomía</div><div class="floating-label label-c">Tecnología</div></div></section><section class="landing-intro"><span class="eyebrow">UNA FORMA DIFERENTE DE APRENDER</span><h2>La ciencia también se mueve.</h2><p>Relaciona la teoría con la práctica, comprende tus movimientos y experimenta con actividades interactivas.</p><div class="features-row"><div>{icon('book',24)}<strong>Conocimiento</strong><small>Lecciones sencillas</small></div><div>{icon('activity',24)}<strong>Experiencias</strong><small>Retos y práctica física</small></div><div>{icon('calc',24)}<strong>Herramientas</strong><small>Cálculos explicados</small></div></div></section><section class="landing-lessons"><div class="section-header"><div><span class="eyebrow">BIBLIOTECA EDUCATIVA</span><h2>Comienza por aquí</h2></div><a href="/aprender" class="text-link">Ver todos los temas {icon('arrow',17)}</a></div><div class="lesson-grid">{cards}</div></section><section class="promo-banner"><div><span class="eyebrow">PROYECTO EDUCATIVO</span><h2>Tecnología que acompaña cada aprendizaje.</h2><p>Página web didáctica, visualizaciones del movimiento y gamificación con códigos QR son recursos de la propuesta investigativa.</p></div><a class="btn btn-white" href="/actividades">Conocer los retos {icon('arrow',16)}</a></section>'''
        return self.render('Inicio',body)

    def learn(self):
        cards=''.join(f'<a class="resource-card" href="/leccion/{l["slug"]}"><div class="resource-icon">{e(l["icon"])}</div><span class="eyebrow">{e(l["tag"])}</span><h3>{e(l["title"])}</h3><p>{e(l["intro"])}</p><span class="resource-bottom">{icon("clock",15)} {e(l["time"])} <b>Ver lección →</b></span></a>' for l in LESSONS)
        return self.render('Aprendizaje',f'<section class="public-pagehead"><span class="eyebrow">APRENDER EN MOVIMIENTO</span><h1>Biblioteca educativa</h1><p>Contenido desarrollado como apoyo didáctico al área de Educación Física. No sustituye la enseñanza presencial.</p></section><div class="resource-grid">{cards}</div>',active='biblioteca')

    def lesson(self,slug):
        l=next((x for x in LESSONS if x['slug']==slug),None)
        if not l:return self.fail(404,'La lección no existe.')
        sections=''.join(f'<section class="lesson-section"><h2>{e(t)}</h2><p>{e(b)}</p></section>' for t,b in l['sections'])
        body=f'<section class="article-top"><a class="back-link" href="/aprender">{icon("back",16)} Biblioteca educativa</a><span class="eyebrow">{e(l["tag"])}</span><h1>{e(l["title"])}</h1><p>{e(l["intro"])}</p><span class="article-time">{icon("clock",16)} Lectura: {e(l["time"])}</span></section><article class="article-card">{sections}<div class="reference-box"><strong>Fuente y contextualización</strong><p>{e(l["reference"])}</p></div></article><div class="article-end"><a class="btn btn-primary" href="/actividades">Continuar con retos {icon("arrow",16)}</a></div>'
        return self.render(l['title'],body)

    def activities(self):
        cards=''.join(f'<div class="activity-card"><div class="activity-icon">{icon("qr",26)}</div><h3>{e(a["name"])}</h3><p>{e(a["intro"])}</p><div class="activity-bottom"><span>{len(a["questions"])} preguntas</span><a class="btn btn-primary btn-sm" href="/reto/{a["slug"]}">Iniciar reto {icon("arrow",15)}</a></div></div>' for a in ACTIVITIES)
        return self.render('Retos educativos',f'<section class="public-pagehead"><span class="eyebrow">GAMIFICACIÓN EDUCATIVA</span><h1>Aprende con retos</h1><p>Actividades de práctica sin registro de datos personales. Puedes generar un QR imprimible para cada reto desde su página.</p></section><div class="activity-grid">{cards}</div>')

    def challenge(self,slug):
        a=next((x for x in ACTIVITIES if x['slug']==slug),None)
        if not a:return self.fail(404,'El reto no existe.')
        if self.command=='POST':
            score=0;details=''
            for i,q in enumerate(a['questions']):
                answer=self.form.get('q'+str(i),'')
                ok=answer.isdecimal() and int(answer)==q['answer']
                if ok:score+=1
                details+=f'<div class="answer-item"><strong>{e(q["question"])}</strong><p>{badge("Correcto" if ok else "Para revisar", "success" if ok else "neutral")} {e(q["feedback"])}</p></div>'
            return self.render('Resultado del reto',f'<section class="challenge-result"><span class="eyebrow">EVALUACIÓN FORMATIVA</span><h1>¡Reto completado!</h1><div class="result-score">{score}<small>/{len(a["questions"])}</small></div><p>Estas respuestas sirven para aprender, no generan calificaciones ni expedientes.</p>{details}<a class="btn btn-primary" href="/reto/{e(slug)}">Volver a intentar</a> <a class="btn btn-soft" href="/actividades">Otros retos</a></section>')
        fields=''
        for i,q in enumerate(a['questions']):
            opts=''.join(f'<label class="answer-option"><input type="radio" name="q{i}" value="{j}" required><span>{e(option)}</span></label>' for j,option in enumerate(q['options']))
            fields+=f'<fieldset class="question"><legend><span class="number-dot">{i+1}</span>{e(q["question"])}</legend>{opts}</fieldset>'
        url=f'http://{self.headers.get("Host","localhost:8000")}/reto/{quote(slug)}'
        # QR image may be opened from another device when the app is reachable on that device's network.
        qr=f'<img class="qr-image" src="/qr/{e(slug)}" alt="Código QR para abrir este reto" width="150" height="150">'
        body=f'<section class="public-pagehead"><a href="/actividades" class="back-link">{icon("back",16)} Volver a retos</a><span class="eyebrow">CUESTIONARIO INTERACTIVO</span><h1>{e(a["name"])}</h1><p>{e(a["intro"])}</p></section><div class="challenge-layout"><form class="challenge-form" method="post" action="/reto/{e(slug)}">{fields}<button class="btn btn-primary">Comprobar respuestas {icon("arrow",16)}</button></form><aside class="panel qr-panel"><h3>Estación con código QR</h3>{qr}<p>Imprime el código para acceder a este reto.</p><small>Si vas a usarlo desde otro dispositivo, abre la aplicación mediante la IP local de la computadora, no mediante localhost.</small><button class="btn btn-soft btn-block" type="button" id="printQr">Imprimir estación</button></aside></div>'
        return self.render(a['name'],body)

    def qr_image(self,slug):
        if not next((a for a in ACTIVITIES if a['slug']==slug),None):return self.fail(404,'Código no disponible.')
        try:
            # qrcode empaquetado localmente, sin instalación adicional.
            import qrcode
            hostname=self.headers.get('Host','localhost:8000')
            if not re.fullmatch(r'[a-zA-Z0-9.\-:\[\]]{1,80}',hostname):hostname='localhost:8000'
            url=f'http://{hostname}/reto/{slug}'
            qr=qrcode.QRCode(border=2,box_size=7, error_correction=qrcode.constants.ERROR_CORRECT_M)
            qr.add_data(url);qr.make(fit=True)
            matrix=qr.get_matrix()
            n=len(matrix)
            pixels=''.join(f'<path d="M{x} {y}h1v1h-1z"/>' for y,row in enumerate(matrix) for x,is_dark in enumerate(row) if is_dark)
            svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges"><rect width="{n}" height="{n}" fill="white"/><g fill="#0B326B">{pixels}</g></svg>'
            self.text_response(svg,'image/svg+xml; charset=utf-8',{'Cache-Control':'no-store'})
        except ImportError:
            self.fail(503,'Módulo QR no incluido.')

    def calculators(self):
        body='''<section class="public-pagehead calculators-head"><span class="eyebrow">HERRAMIENTAS DIDÁCTICAS</span><h1>Calculadoras para Educación Física</h1><p>Calcula y comprende indicadores con fórmulas transparentes. Las mediciones de adolescentes no se interpretan con categorías de adultos.</p></section>
        <div class="calc-grid">
        <section class="calc-card" data-calculator="imc"><div class="calc-header"><span class="calc-symbol">IMC</span><div><h2>Índice de masa corporal</h2><p>Resultado descriptivo, no diagnóstico</p></div></div><div class="form-grid"><label class="field"><span>Peso (kg)</span><input type="number" step="0.01" min="1" max="400" data-in="weight" placeholder="Ej. 50"></label><label class="field"><span>Estatura (cm)</span><input type="number" step="0.1" min="30" max="260" data-in="height" placeholder="Ej. 158"></label></div><div class="calc-output"><small>IMC calculado</small><b data-out>—</b><span>peso (kg) ÷ estatura (m)²</span></div><p class="calc-disclaimer">Para menores se requieren referencias específicas por edad y sexo para cualquier interpretación. No se realizan clasificaciones clínicas.</p></section>
        <section class="calc-card" data-calculator="rcc"><div class="calc-header"><span class="calc-symbol">RCC</span><div><h2>Relación cintura / cadera</h2><p>Cociente de dos mediciones</p></div></div><div class="form-grid"><label class="field"><span>Cintura (cm)</span><input type="number" step="0.1" min="1" data-in="waist" placeholder="Ej. 68"></label><label class="field"><span>Cadera (cm)</span><input type="number" step="0.1" min="1" data-in="hip" placeholder="Ej. 82"></label></div><div class="calc-output"><small>Relación calculada</small><b data-out>—</b><span>cintura ÷ cadera</span></div><p class="calc-disclaimer">Información educativa sin clasificación automática de riesgo.</p></section>
        <section class="calc-card" data-calculator="heart"><div class="calc-header"><span class="calc-symbol">♥</span><div><h2>Frecuencia cardíaca</h2><p>Convertir pulsaciones a latidos/minuto</p></div></div><div class="form-grid"><label class="field"><span>Pulsaciones contadas</span><input type="number" min="0" step="1" data-in="pulse" placeholder="Ej. 20"></label><label class="field"><span>Tiempo de conteo</span><select data-in="seconds"><option value="15">15 segundos</option><option value="30">30 segundos</option><option value="60">60 segundos</option></select></label></div><div class="calc-output"><small>Frecuencia cardíaca</small><b data-out>—</b><span>pulsaciones × 60 ÷ segundos</span></div><p class="calc-disclaimer">El valor no sirve por sí solo para emitir diagnósticos.</p></section>
        <section class="calc-card" data-calculator="pace"><div class="calc-header"><span class="calc-symbol">↗</span><div><h2>Ritmo de carrera</h2><p>Distancia, tiempo y velocidad media</p></div></div><div class="form-grid"><label class="field"><span>Distancia (m)</span><input type="number" min="1" step="1" data-in="distance" placeholder="Ej. 1000"></label><label class="field"><span>Tiempo (segundos)</span><input type="number" min="1" step="1" data-in="duration" placeholder="Ej. 360"></label></div><div class="calc-output"><small>Ritmo por km</small><b data-out>—</b><span data-extra>Velocidad media — km/h</span></div><p class="calc-disclaimer">Una herramienta matemática para interpretar la actividad, no una valoración de salud.</p></section></div>'''
        return self.render('Calculadoras',body,active='calculadoras')

    def dashboard(self):
        st=self.students(); ids=[x['id'] for x in st]
        group=self.sections();num_records=0;num_tests=0
        if ids:
            marks=','.join('?' for _ in ids)
            num_records=self.db.execute(f'SELECT COUNT(*) FROM anthropometry WHERE student_id IN ({marks})',ids).fetchone()[0]
            num_tests=self.db.execute(f'SELECT COUNT(*) FROM fitness_results WHERE student_id IN ({marks})',ids).fetchone()[0]
        stats='<div class="stats-grid">'+stat('Estudiantes activos',sum(x['active'] for x in st),'users','Registrados en tus secciones')+stat('Secciones',len(group),'layers','Grupos escolares')+stat('Mediciones',num_records,'ruler','Registros antropométricos')+stat('Pruebas físicas',num_tests,'activity','Evaluaciones realizadas')+'</div>'
        actions=f'<div class="quick-actions"><a href="/estudiantes/nuevo" class="btn btn-primary">{icon("plus",17)} Nuevo estudiante</a><a href="/antropometria/nueva" class="btn btn-soft">{icon("ruler",17)} Nueva medición</a><a href="/evaluaciones" class="btn btn-soft">{icon("activity",17)} Registrar prueba</a></div>'
        recent=[]
        if ids:
            marks=','.join('?' for _ in ids)
            recent=self.db.execute(f'''SELECT a.*,p.first_name,p.last_name FROM anthropometry a JOIN students p ON p.id=a.student_id WHERE a.student_id IN ({marks}) ORDER BY a.measured_at DESC,a.id DESC LIMIT 6''',ids).fetchall()
        recent_html=table(['Fecha','Estudiante','Peso','Estatura','IMC'],[[e(as_date(r['measured_at'])),f'<a href="/estudiantes/{r["student_id"]}">{e(full_name(r))}</a>',f'{r["weight_kg"]:g} kg',f'{r["height_cm"]:g} cm',f'{bmi(r["weight_kg"],r["height_cm"]):.2f}'] for r in recent])
        tip=panel('Bienvenido al sistema','<div class="welcome-message"><h3>Todo lo que necesitas para acompañar el aprendizaje.</h3><p>Registra estudiantes, organiza mediciones y conecta el conocimiento científico con la práctica motriz. Cada resultado guardado aparecerá en el historial correspondiente.</p><a class="text-link" href="/aprender">Abrir biblioteca educativa →</a></div>',classes='welcome-panel')
        body=page_header('Panel principal','Una visión general de tu trabajo pedagógico.')+stats+actions+f'<div class="dashboard-grid">{panel("Últimas mediciones",recent_html,"Registros guardados recientemente")}{tip}</div>'
        self.render('Panel principal',body,'panel')

    def sections_page(self):
        sections=self.sections()
        rows=[[e(s['school_year']),e(s['grade']),e(s['name']),e(s['teacher'])] for s in sections]
        teachers=self.db.execute('SELECT id,name FROM users ORDER BY name').fetchall() if self.user['role']=='admin' else []
        te=selection('teacher_id','Docente responsable',[(t['id'],t['name']) for t in teachers],self.user['id']) if teachers else ''
        form=f'<form class="stack-form" method="post" action="/secciones/nueva">{self.form_csrf()}<div class="form-grid">{field("school_year","Año escolar",f"{date.today().year}-{date.today().year+1}",required=True,placeholder="2026-2027")}{field("grade","Año / grado","1.º",required=True,placeholder="1.º")}{field("name","Sección","B",required=True,placeholder="B")}{te}</div><button class="btn btn-primary">{icon("plus",17)} Crear sección</button></form>'
        self.render('Años y secciones',page_header('Años y secciones','Organiza los grupos que estarán a cargo de cada docente.')+panel('Nueva sección',form)+panel('Secciones registradas',table(['Año escolar','Año / grado','Sección','Docente'],rows)),active='secciones')

    def new_section(self):
        year=self.form.get('school_year','').strip();grade=self.form.get('grade','').strip();name=self.form.get('name','').strip().upper()
        try:
            if not (re.fullmatch(r'\d{4}-\d{4}',year) and 0<len(grade)<25 and 0<len(name)<16):raise ValueError('Completa los datos del año escolar y la sección.')
            teacher=int(self.form.get('teacher_id',self.user['id'])) if self.user['role']=='admin' else self.user['id']
            if not self.db.execute('SELECT 1 FROM users WHERE id=?',(teacher,)).fetchone():raise ValueError('El docente no existe.')
            self.db.execute('INSERT INTO sections (school_year,grade,name,teacher_id) VALUES (?,?,?,?)',(year,grade,name,teacher));self.db.commit()
            return self.redirect('/secciones')
        except (ValueError,sqlite3.IntegrityError) as ex:
            self.render('Error al crear sección',f'<div class="alert alert-error">{e(str(ex))}</div><a class="btn btn-soft" href="/secciones">Volver a secciones</a>','secciones',400)

    def students_page(self):
        q=self.query().get('q','').strip().lower()
        students=[s for s in self.students() if q in full_name(s).lower() or q in str(s['code'] or '').lower()]
        rows=[]
        for s in students:
            rows.append([f'<a class="table-person" href="/estudiantes/{s["id"]}"><span class="mini-avatar">{e(s["first_name"][0])}</span><span><b>{e(full_name(s))}</b><small>{e(s["code"] or "Sin código")}</small></span></a>',e(f"{s['grade']} · {s['section_name']}"),e(s['school_year']),badge('Activo' if s['active'] else 'Inactivo','success' if s['active'] else 'neutral'),f'<a class="table-action" href="/estudiantes/{s["id"]}">Ver ficha →</a>'])
        action=f'<a class="btn btn-primary" href="/estudiantes/nuevo">{icon("plus",17)} Agregar estudiante</a>'
        filters=f'<form method="get" action="/estudiantes" class="search-form"><input aria-label="Buscar estudiantes" name="q" value="{e(q)}" placeholder="Buscar por nombre o código…"><button class="btn btn-soft">{icon("search",17)} Buscar</button></form>'
        self.render('Estudiantes',page_header('Estudiantes','Registro y seguimiento de cada estudiante.',action)+panel('Listado de estudiantes',filters+table(['Estudiante','Sección','Año escolar','Estado',''],rows)),active='estudiantes')

    def student_form(self,identifier=None):
        item=self.student(identifier) if identifier else None
        if identifier and not item:return self.fail(404,'Estudiante no disponible.')
        sections=self.sections()
        if not sections:
            return self.render('Registrar estudiante',page_header('Registrar estudiante','Primero necesitas crear una sección.')+empty('Aún no tienes secciones.','/secciones','Crear sección'),active='estudiantes')
        action=f'/estudiantes/{identifier}/editar' if item else '/estudiantes/nuevo'
        frm=f'<form method="post" action="{action}" class="stack-form">{self.form_csrf()}<div class="form-grid">{field("first_name","Nombres",item["first_name"] if item else "",required=True)}{field("last_name","Apellidos",item["last_name"] if item else "",required=True)}{field("code","Código escolar (opcional)",item["code"] if item else "",placeholder="Código interno")}{field("birth_date","Fecha de nacimiento (opcional)",item["birth_date"] if item else "",fieldtype="date")}{selection("section_id","Sección",[(s["id"],f"{s['grade']} · {s['name']} ({s['school_year']})") for s in sections],item["section_id"] if item else '')}</div><div class="form-actions"><button class="btn btn-primary">{icon("check",17)} {"Guardar cambios" if item else "Registrar estudiante"}</button><a class="btn btn-soft" href="{f"/estudiantes/{identifier}" if item else "/estudiantes"}">Cancelar</a></div></form>'
        self.render('Editar estudiante' if item else 'Nuevo estudiante',page_header('Editar ficha' if item else 'Nuevo estudiante','Datos académicos básicos y mínimos para seguimiento.')+panel('Datos del estudiante',frm),active='estudiantes')

    def save_student(self,identifier=None):
        try:
            first=self.form.get('first_name','').strip();last=self.form.get('last_name','').strip()
            code=self.form.get('code','').strip() or None
            born=self.form.get('birth_date','').strip() or None
            section_id=int(self.form.get('section_id','0'))
            if not first or not last or len(first)>80 or len(last)>80 or (code and len(code)>45):raise ValueError('Nombres y apellidos son obligatorios y deben ser breves.')
            if born:
                if not date(1900,1,1)<=date.fromisoformat(born)<=date.today():raise ValueError('La fecha de nacimiento es inválida.')
            if not any(s['id']==section_id for s in self.sections()):raise ValueError('La sección no está autorizada.')
            if identifier:
                if not self.student(identifier):return self.fail(404,'No disponible.')
                self.db.execute('UPDATE students SET first_name=?,last_name=?,code=?,birth_date=?,section_id=? WHERE id=?',(first,last,code,born,section_id,int(identifier)))
                sid=int(identifier)
            else:
                c=self.db.execute('INSERT INTO students(first_name,last_name,code,birth_date,section_id) VALUES (?,?,?,?,?)',(first,last,code,born,section_id));sid=c.lastrowid
            self.db.commit()
            return self.redirect(f'/estudiantes/{sid}')
        except (ValueError,sqlite3.IntegrityError) as ex:
            self.render('Datos no guardados',f'<div class="alert alert-error">{e(str(ex))}</div><a class="btn btn-soft" href="/estudiantes">Volver a estudiantes</a>','estudiantes',400)

    def toggle_student(self,identifier):
        p=self.student(identifier)
        if not p:return self.fail(404,'No disponible')
        self.db.execute('UPDATE students SET active=? WHERE id=?',(0 if p['active'] else 1,p['id']))
        self.db.commit();self.redirect(f'/estudiantes/{p["id"]}')

    def student_page(self,identifier):
        s=self.student(identifier)
        if not s:return self.fail(404,'Estudiante no disponible.')
        records=self.db.execute('SELECT * FROM anthropometry WHERE student_id=? ORDER BY measured_at DESC,id DESC',(s['id'],)).fetchall()
        fitness=self.db.execute('''SELECT r.*,t.name,t.unit FROM fitness_results r JOIN fitness_tests t ON t.id=r.test_id WHERE student_id=? ORDER BY measured_at DESC,r.id DESC''',(s['id'],)).fetchall()
        latest=records[0] if records else None
        metrics='<div class="mini-metrics">'+stat('Mediciones',len(records),'ruler')+stat('Último peso',f'{latest["weight_kg"]:g} kg' if latest else '—','chart')+stat('Última estatura',f'{latest["height_cm"]:g} cm' if latest else '—','activity')+'</div>'
        anthro_rows=[[e(as_date(r['measured_at'])),e(f'{r["weight_kg"]:g} kg'),e(f'{r["height_cm"]:g} cm'),e(f'{bmi(r["weight_kg"],r["height_cm"]):.2f}'),e(r['notes'] or '—')] for r in records]
        fit_rows=[[e(as_date(r['measured_at'])),e(r['name']),e(f'{r["value"]:g} {r["unit"]}'),e(r['notes'] or '—')] for r in fitness]
        chart=svg_line([(as_date(r['measured_at'])[:5],r['weight_kg']) for r in list(reversed(records))[-9:]],label='Evolución del peso en kg')
        actions=f'<div class="quick-actions"><a class="btn btn-primary" href="/antropometria/nueva?student_id={s["id"]}">{icon("plus",16)} Añadir medición</a><a class="btn btn-soft" href="/evaluaciones?student_id={s["id"]}">{icon("activity",16)} Añadir prueba</a><a class="btn btn-soft" href="/estudiantes/{s["id"]}/editar">Editar datos</a><a class="btn btn-soft" href="/exportar/estudiante/{s["id"]}">{icon("download",16)} Exportar CSV</a></div>'
        state=f'<form method="post" action="/estudiantes/{s["id"]}/estado" data-confirm="¿Cambiar el estado del estudiante?">{self.form_csrf()}<button class="btn btn-text">{"Desactivar" if s["active"] else "Activar"} estudiante</button></form>'
        info=f'<div class="student-banner"><div class="student-initial">{e(s["first_name"][0])}{e(s["last_name"][0])}</div><div><span class="eyebrow">FICHA ESTUDIANTIL</span><h2>{e(full_name(s))}</h2><p>{e(s["grade"])} · Sección {e(s["section_name"])} · {e(s["school_year"])} · {e(s["code"] or "Sin código")}</p></div><span class="student-status">{badge("Activo" if s["active"] else "Inactivo","success" if s["active"] else "neutral")}</span></div>'
        body=page_header('Ficha del estudiante','Historial de mediciones y evaluaciones autorizadas.')+info+actions+metrics+f'<div class="dashboard-grid">{panel("Evolución del peso",chart,"Valores registrados, sin calificación clínica")}{panel("Últimas mediciones",table(["Fecha","Peso","Estatura","IMC","Observación"],anthro_rows[:6]),"Historial antropométrico")}</div>'+panel('Evaluaciones físicas',table(['Fecha','Prueba','Resultado','Observaciones'],fit_rows))+f'<div class="page-end-actions">{state}</div>'
        self.render('Ficha estudiantil',body,active='estudiantes')

    def anthro_form(self):
        s_id=self.query().get('student_id','')
        frm=f'''<form method="post" action="/antropometria/nueva" class="stack-form" id="measurementForm">{self.form_csrf()}{self.choose_student(s_id)}<div class="form-grid">{field('measured_at','Fecha de la medición',dt_today(),'date',True)}{field('weight_kg','Peso (kg)',fieldtype='number',required=True,placeholder='Ej. 48.5',attrs='min="1" max="400" step="0.01"')}{field('height_cm','Estatura (cm)',fieldtype='number',required=True,placeholder='Ej. 158',attrs='min="30" max="260" step="0.1"')}{field('waist_cm','Cintura (cm) · opcional',fieldtype='number',attrs='min="1" max="300" step="0.1"')}{field('hip_cm','Cadera (cm) · opcional',fieldtype='number',attrs='min="1" max="300" step="0.1"')}{field('armspan_cm','Envergadura (cm) · opcional',fieldtype='number',attrs='min="1" max="300" step="0.1"')}</div><div class="form-divider">Frecuencia cardíaca (opcional)</div><div class="form-grid grid-3">{field('resting_hr','Reposo (lpm)',fieldtype='number',attrs='min="1" max="280" step="1"')}{field('after_hr','Después de actividad (lpm)',fieldtype='number',attrs='min="1" max="280" step="1"')}{field('recovery_hr','Recuperación (lpm)',fieldtype='number',attrs='min="1" max="280" step="1"')}</div>{textarea('notes','Observaciones pedagógicas')}<div class="live-measure" id="liveMeasure">Introduce peso y estatura para ver el cálculo del IMC.</div><p class="muted-small">El IMC es descriptivo. No se clasifica la composición corporal de menores ni se generan diagnósticos.</p><div class="form-actions"><button class="btn btn-primary">{icon('check',18)} Guardar medición</button><a class="btn btn-soft" href="/estudiantes">Cancelar</a></div></form>'''
        self.render('Nueva medición',page_header('Nueva medición antropométrica','Registra datos reales de forma clara y consulta el IMC calculado automáticamente.')+panel('Formulario de medición',frm),active='antropometria')

    def save_anthro(self):
        try:
            student=self.student(self.form.get('student_id'))
            if not student or not student['active']:raise ValueError('Selecciona un estudiante activo de tus secciones.')
            measured=self.form.get('measured_at','')
            if not date(2000,1,1)<=date.fromisoformat(measured)<=date.today():raise ValueError('La fecha de medición no es válida o es futura.')
            weight=parse_number(self.form.get('weight_kg'),'Peso',1,400)
            height=parse_number(self.form.get('height_cm'),'Estatura',30,260)
            waist=parse_number(self.form.get('waist_cm'),'Cintura',1,300,True)
            hip=parse_number(self.form.get('hip_cm'),'Cadera',1,300,True)
            armspan=parse_number(self.form.get('armspan_cm'),'Envergadura',1,300,True)
            hrs=[parse_number(self.form.get(t),label,1,280,True) for t,label in [('resting_hr','Pulso reposo'),('after_hr','Pulso actividad'),('recovery_hr','Pulso recuperación')]]
            if any(v is not None and int(v)!=v for v in hrs):raise ValueError('Las pulsaciones se registran en números enteros.')
            notes=self.form.get('notes','').strip()[:750]
            self.db.execute('''INSERT INTO anthropometry(student_id,user_id,measured_at,weight_kg,height_cm,waist_cm,hip_cm,armspan_cm,resting_hr,after_hr,recovery_hr,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',(student['id'],self.user['id'],measured,weight,height,waist,hip,armspan,*hrs,notes))
            self.db.commit();self.redirect(f'/estudiantes/{student["id"]}')
        except (ValueError,sqlite3.IntegrityError) as ex:
            self.render('Error de medición',f'<div class="alert alert-error">{e(str(ex))}</div><a class="btn btn-soft" href="/antropometria/nueva">Regresar al formulario</a>','antropometria',400)

    def timer_page(self):
        body=page_header('Cronómetro y temporizador','Herramienta de apoyo para las estaciones de actividades motrices.')+        '<div class="timer-layout"><section class="panel"><div class="panel-heading"><h2>Cronómetro de clase</h2><p>Inicia, pausa y guarda vueltas durante una actividad.</p></div><div class="panel-body"><div class="timer-display" id="watchDisplay" role="timer">00:00.00</div><div class="timer-buttons"><button class="btn btn-primary" id="watchStart" type="button">Iniciar</button><button class="btn btn-soft" id="watchLap" type="button">Vuelta</button><button class="btn btn-soft" id="watchReset" type="button">Reiniciar</button></div><h3>Vueltas</h3><ol id="watchLaps" class="lap-list"><li class="muted-small">Todavía no hay vueltas registradas.</li></ol></div></section><section class="panel"><div class="panel-heading"><h2>Temporizador</h2><p>Ideal para circuitos de actividades por estaciones.</p></div><div class="panel-body"><label class="field"><span>Duración en segundos</span><input type="number" id="countdownSeconds" value="60" min="1" max="3600" step="1"></label><div class="timer-display" id="countdownDisplay" role="timer">01:00</div><div class="timer-buttons"><button class="btn btn-primary" id="countdownStart" type="button">Iniciar / Pausar</button><button class="btn btn-soft" id="countdownReset" type="button">Reiniciar</button></div><p class="muted-small">Los tiempos son locales al navegador y no se guardan como registros del estudiante.</p></div></section></div>'
        self.render('Cronómetro',body,'cronometro')

    def evaluations(self):
        selected=self.query().get('student_id','')
        tests=self.db.execute('SELECT * FROM fitness_tests ORDER BY name').fetchall()
        if not self.students():return self.render('Evaluaciones físicas',page_header('Evaluaciones físicas','Registro de pruebas motrices.')+empty('Registra estudiantes antes de guardar evaluaciones.','/estudiantes/nuevo','Nuevo estudiante'),active='evaluaciones')
        choices=[(t['id'],f"{t['name']} ({t['unit']})") for t in tests]
        form=f'<form method="post" action="/evaluaciones/nueva" class="stack-form">{self.form_csrf()}{self.choose_student(selected)}<div class="form-grid">{selection("test_id","Prueba física",choices)}{field("measured_at","Fecha de aplicación",dt_today(),"date",True)}{field("value","Resultado (unidad según prueba)",fieldtype="number",required=True,attrs="step=\"0.01\" min=\"0\"")}</div>{textarea("notes","Observaciones pedagógicas")}<button class="btn btn-primary">{icon("check",18)} Guardar resultado</button></form>'
        testrows=[[e(t['name']),e(t['unit']),e(t['protocol'])] for t in tests]
        body=page_header('Evaluaciones físicas','Registra pruebas motrices y acompaña su evolución a lo largo del año.')+panel('Nueva evaluación',form)+panel('Pruebas disponibles',table(['Nombre','Unidad','Protocolo básico'],testrows),'Estos protocolos deben adaptarse a las condiciones y seguridad de cada grupo.')
        self.render('Evaluaciones físicas',body,'evaluaciones')

    def save_fitness(self):
        try:
            student=self.student(self.form.get('student_id'))
            if not student or not student['active']:raise ValueError('Selecciona un estudiante activo.')
            test=int(self.form.get('test_id','0'))
            if not self.db.execute('SELECT 1 FROM fitness_tests WHERE id=?',(test,)).fetchone():raise ValueError('Prueba no válida.')
            value=parse_number(self.form.get('value'),'Resultado',0,100000)
            measured=self.form.get('measured_at','')
            if not date(2000,1,1)<=date.fromisoformat(measured)<=date.today():raise ValueError('Fecha inválida.')
            self.db.execute('INSERT INTO fitness_results(student_id,user_id,test_id,measured_at,value,notes) VALUES (?,?,?,?,?,?)',(student['id'],self.user['id'],test,measured,value,self.form.get('notes','').strip()[:750]))
            self.db.commit();self.redirect(f'/estudiantes/{student["id"]}')
        except (ValueError,sqlite3.IntegrityError) as ex:
            self.render('Error de evaluación',f'<div class="alert alert-error">{e(str(ex))}</div><a href="/evaluaciones" class="btn btn-soft">Regresar</a>','evaluaciones',400)

    def analytics(self):
        students=self.students()
        if not students:return self.render('Estadísticas',page_header('Estadísticas','Información registrada sin diagnósticos.')+empty('Aún no tienes estudiantes para mostrar estadísticas.','/secciones','Configurar secciones'),'estadisticas')
        student_id=self.query().get('student_id',str(students[0]['id']))
        s=self.student(student_id) or students[0]
        history=list(reversed(self.db.execute('SELECT * FROM anthropometry WHERE student_id=? ORDER BY measured_at DESC,id DESC LIMIT 12',(s['id'],)).fetchall()))
        menu=f'<form class="chart-filter" method="get" action="/estadisticas">{selection("student_id","Selecciona estudiante",[(x["id"],full_name(x)) for x in students],s["id"])}<button class="btn btn-soft">Mostrar</button></form>'
        weight=svg_line([(as_date(r['measured_at'])[:5],r['weight_kg']) for r in history],label='Evolución del peso')
        height=svg_line([(as_date(r['measured_at'])[:5],r['height_cm']) for r in history],label='Evolución de la estatura')
        bmi_chart=svg_line([(as_date(r['measured_at'])[:5],bmi(r['weight_kg'],r['height_cm'])) for r in history],label='Evolución del IMC descriptivo')
        sections=self.sections();rows=[]
        for sc in sections:
            n=sum(x['section_id']==sc['id'] for x in students)
            rows.append([e(f"{sc['grade']} · {sc['name']}"),e(sc['school_year']),e(n)])
        body=page_header('Estadísticas','Resultados descriptivos basados en registros reales. No son interpretaciones clínicas.')+panel('Seguimiento individual',menu)+f'<div class="charts-grid">{panel("Peso (kg)",weight)}{panel("Estatura (cm)",height)}{panel("IMC (descriptivo)",bmi_chart)}</div>'+panel('Resumen por sección',table(['Sección','Año escolar','Estudiantes registrados'],rows))+'<p class="muted-small">No se muestran públicamente comparaciones de características corporales entre estudiantes.</p>'
        self.render('Estadísticas',body,'estadisticas')

    def reports(self):
        rows=[[e(full_name(s)),e(f"{s['grade']} {s['section_name']}"),f'<a href="/exportar/estudiante/{s["id"]}" class="btn btn-soft btn-sm">{icon("download",15)} CSV</a>'] for s in self.students()]
        self.render('Informes',page_header('Informes y exportaciones','Descarga el historial autorizado de un estudiante para análisis e impresión.')+panel('Historiales disponibles',table(['Estudiante','Sección','Exportar'],rows))+panel('Cómo usar los informes','<p>Los archivos CSV se abren directamente con Excel o LibreOffice. Contienen datos de seguimiento y no emiten diagnósticos ni clasificaciones del peso corporal.</p>'),active='informes')

    def export_student(self,identifier):
        s=self.student(identifier)
        if not s:return self.fail(404,'No autorizado.')
        records=self.db.execute('SELECT * FROM anthropometry WHERE student_id=? ORDER BY measured_at DESC,id DESC',(s['id'],)).fetchall()
        output=io.StringIO();w=csv.writer(output)
        w.writerow(['Estudiante','Fecha','Peso (kg)','Estatura (cm)','IMC descriptivo','Cintura (cm)','Cadera (cm)','Envergadura (cm)','Pulso reposo','Pulso actividad','Pulso recuperación','Observaciones'])
        for r in records:
            w.writerow([csv_safe(full_name(s)),r['measured_at'],r['weight_kg'],r['height_cm'],bmi(r['weight_kg'],r['height_cm']),r['waist_cm'],r['hip_cm'],r['armspan_cm'],r['resting_hr'],r['after_hr'],r['recovery_hr'],csv_safe(r['notes'])])
        self.text_response('\ufeff'+output.getvalue(),'text/csv; charset=utf-8',{'Content-Disposition':f'attachment; filename="estudiante_{s["id"]}_mediciones.csv"','Cache-Control':'no-store'})

    def users_page(self):
        users=self.db.execute('SELECT id,name,email,role,created_at FROM users ORDER BY name').fetchall()
        rows=[[e(u['name']),e(u['email']),badge('Administrador' if u['role']=='admin' else 'Docente')] for u in users]
        form=f'<form method="post" action="/usuarios/nuevo" class="stack-form">{self.form_csrf()}<div class="form-grid">{field("name","Nombre completo",required=True)}{field("email","Correo",fieldtype="email",required=True)}{field("password","Contraseña inicial (mínimo 12 caracteres)",fieldtype="password",required=True)}{selection("role","Rol",[("docente","Docente"),("admin","Administrador")],"docente")}</div><button class="btn btn-primary">{icon("plus",17)} Crear cuenta</button></form>'
        self.render('Usuarios',page_header('Usuarios','Accesos del sistema. Nunca compartas las contraseñas.')+panel('Nueva cuenta',form)+panel('Usuarios registrados',table(['Nombre','Correo','Rol'],rows)),'usuarios')

    def new_user(self):
        name=self.form.get('name','').strip();email=self.form.get('email','').strip().lower();password=self.form.get('password','');role=self.form.get('role','')
        if not name or len(name)>100 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(password)<12 or role not in ('admin','docente'):
            return self.render('Error de usuario','<div class="alert alert-error">Revisa nombre, correo, rol y contraseña (mínimo 12 caracteres).</div><a href="/usuarios">Volver</a>','usuarios',400)
        try:
            self.db.execute('INSERT INTO users(name,email,password_hash,role) VALUES (?,?,?,?)',(name,email,hash_password(password),role));self.db.commit()
        except sqlite3.IntegrityError:
            return self.render('Error de usuario','<div class="alert alert-error">El correo ya existe.</div><a href="/usuarios">Volver</a>','usuarios',400)
        return self.redirect('/usuarios')


def main():
    import sys
    # Inicialización segura e idempotente del esquema de base de datos
    init_db()

    # Creación interactiva de administrador si se invoca con 'python app.py init'
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        with connect() as db:
            if db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
                print('Ya hay un administrador. Inicia el sistema con: python app.py')
                return
        print('CONFIGURACIÓN INICIAL: cuenta de administrador')
        name = os.getenv('EF_ADMIN_NAME', '').strip() or input('Nombre del administrador: ').strip() or 'Administrador'
        email = os.getenv('EF_ADMIN_EMAIL', '').strip().lower() or input('Correo electrónico: ').strip().lower()
        password = os.getenv('EF_ADMIN_PASSWORD') or getpass.getpass('Contraseña (mínimo 12 caracteres): ')
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(password) < 12:
            print('Correo inválido o contraseña con menos de 12 caracteres.')
            raise SystemExit(1)
        add_admin(email, password, name)
        print('Cuenta creada. Puedes iniciar el sistema con: python app.py')
        return

    # Auto-aprovisionamiento seguro e idempotente de administrador mediante variables de entorno
    admin_email = os.getenv('EF_ADMIN_EMAIL', '').strip().lower()
    admin_pass = os.getenv('EF_ADMIN_PASSWORD', '').strip()
    admin_name = os.getenv('EF_ADMIN_NAME', '').strip() or 'Administrador'

    with connect() as db:
        if admin_email and admin_pass:
            if re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', admin_email) and len(admin_pass) >= 6:
                existing = db.execute("SELECT id FROM users WHERE email=?", (admin_email,)).fetchone()
                if existing:
                    db.execute("UPDATE users SET password_hash=?, role='admin' WHERE id=?",
                               (hash_password(admin_pass), existing['id']))
                    db.commit()
                    print(f'[EF+] Credenciales de administrador actualizadas para: {admin_email}')
                else:
                    add_admin(admin_email, admin_pass, admin_name)
                    print(f'[EF+] Administrador inicial configurado exitosamente para: {admin_email}')
            else:
                print('[EF+] Advertencia: EF_ADMIN_EMAIL debe ser un correo válido y EF_ADMIN_PASSWORD tener al menos 6 caracteres.')

        has_admin = bool(db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone())
        if not has_admin:
            print('[EF+] Aviso: No se detectó cuenta de administrador creada.')
            print('[EF+] Para crearla automáticamente en producción, define EF_ADMIN_EMAIL y EF_ADMIN_PASSWORD.')
            print('[EF+] O ejecuta interactivamente en la terminal: python app.py init')

    # Configuración de host y puerto HTTP
    # En producción / contenedor escucha en 0.0.0.0:8080
    is_prod = os.getenv('EF_ENV', '').lower() in ('prod', 'production') or os.getenv('PRODUCTION') == '1' or os.getenv('DOCKER') == '1'
    default_host = '0.0.0.0' if is_prod else '127.0.0.1'
    default_port = '8080' if is_prod else '8000'

    host = os.getenv('EF_HOST', os.getenv('HOST', default_host))
    port = int(os.getenv('PORT', os.getenv('EF_PORT', default_port)))

    try:
        server = ThreadingHTTPServer((host, port), Web)
        print(f'EF+ INICIADA: http://{host}:{port}  (Ctrl+C para detener)')
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor detenido.')

if __name__=='__main__': main()
