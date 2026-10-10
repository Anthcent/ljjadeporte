"""Componentes HTML simples, sin plantillas o bibliotecas externas."""
from html import escape
from urllib.parse import quote


def e(v): return escape('' if v is None else str(v), quote=True)

def icon(name, size=20):
    paths={
      'home':'<path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-7h6v7"/>',
      'users':'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
      'layers':'<rect x="3" y="3" width="18" height="6" rx="1"/><rect x="3" y="11" width="18" height="10" rx="1"/>',
      'ruler':'<path d="m21.3 8.7-6-6a1 1 0 0 0-1.4 0l-11.2 11a1 1 0 0 0 0 1.4l6 6a1 1 0 0 0 1.4 0L21.3 10a1 1 0 0 0 0-1.4Z"/><path d="m7.5 10.5 2 2m1-5 2 2m1-5 2 2"/>',
      'calc':'<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M8 6h8M8 10h2m4 0h2M8 14h2m4 0h2M8 18h2m4 0h2"/>',
      'activity':'<path d="M3 12h4l3-8 4 16 3-8h4"/>',
      'chart':'<path d="M3 3v18h18M7 16l4-5 4 2 5-7"/>',
      'book':'<path d="M12 7C8 4 5 4 2 5v15c3-1 6-1 10 2m0-15c4-3 7-3 10-2v15c-3-1-6-1-10 2V7Z"/>',
      'qr':'<rect x="2" y="2" width="7" height="7"/><rect x="15" y="2" width="7" height="7"/><rect x="2" y="15" width="7" height="7"/><path d="M15 15h2v2h-2m7-2v3h-2m-4 4h3v-3h3"/>',
      'file':'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8m-8 4h8"/>',
      'settings':'<circle cx="12" cy="12" r="3"/><path d="M12 2v2m0 16v2M4.9 4.9l1.5 1.5m11.2 11.2 1.5 1.5M2 12h2m16 0h2M4.9 19.1l1.5-1.5M17.6 6.4l1.5-1.5"/>',
      'plus':'<path d="M12 5v14M5 12h14"/>',
      'arrow':'<path d="M5 12h14m-6-6 6 6-6 6"/>',
      'check':'<path d="m4 12 5 5L20 6"/>',
      'logout':'<path d="M10 17l5-5-5-5M15 12H3"/><path d="M12 3h6a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3h-6"/>',
      'menu':'<path d="M4 6h16M4 12h16M4 18h16"/>',
      'search':'<circle cx="10" cy="10" r="7"/><path d="m16 16 5 5"/>',
      'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 3"/>',
      'heart':'<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>',
      'download':'<path d="M12 3v12m-4-4 4 4 4-4M4 18v3h16v-3"/>',
      'back':'<path d="m15 18-6-6 6-6"/>',
    }
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths.get(name,paths["book"])}</svg>'


def layout(title, body, user=None, active='', message='', csrf='', public=False):
    links=[('panel','/panel','home','Panel principal'),('estudiantes','/estudiantes','users','Estudiantes'),('secciones','/secciones','layers','Años y secciones'),('antropometria','/antropometria/nueva','ruler','Antropometría'),('calculadoras','/calculadoras','calc','Calculadoras'),('evaluaciones','/evaluaciones','activity','Pruebas físicas'),('cronometro','/cronometro','clock','Cronómetro'),('estadisticas','/estadisticas','chart','Estadísticas'),('biblioteca','/aprender','book','Biblioteca'),('actividades','/actividades','qr','Retos QR'),('informes','/informes','file','Informes')]
    if user and user['role']=='admin': links += [('usuarios','/usuarios','settings','Usuarios')]
    nav=''.join(f'<a href="{url}" class="nav-link {"active" if active==key else ""}">{icon(ic)}<span>{e(name)}</span></a>' for key,url,ic,name in links)
    flash=f'<div class="notice" role="status">{e(message)}</div>' if message else ''
    if user:
        sidebar=f'''<aside class="sidebar" id="sidebar"><a href="/panel" class="brand"><span class="brand-symbol">EF<span>+</span></span><span class="brand-label">Educación <b>Física</b><small>TECNOLOGÍA · APRENDIZAJE</small></span></a><div class="sidebar-group">MENÚ DE GESTIÓN</div><nav>{nav}</nav><div class="side-bottom"><a href="/" class="nav-link">{icon('book')}<span>Ver sitio público</span></a><form method="post" action="/salir"><input type="hidden" name="csrf" value="{e(csrf)}"><button class="nav-link nav-button">{icon('logout')}<span>Cerrar sesión</span></button></form></div></aside>'''
        top=f'''<header class="topbar"><button class="icon-button mobile-menu" type="button" aria-label="Abrir menú" id="toggleSidebar">{icon('menu')}</button><div class="crumb">Plataforma / <strong>{e(title)}</strong></div><div class="top-user"><span class="avatar">{e(user['name'][0].upper())}</span><span class="top-user-name">{e(user['name'])}<small>{'Administrador' if user['role']=='admin' else 'Docente'}</small></span></div></header>'''
        shell=f'{sidebar}<div class="main-shell">{top}<main class="dashboard-content">{flash}{body}</main><footer class="app-footer">Educación Física · Tecnología y aprendizaje · Liceo José Antonio Abreu</footer></div>'
    else:
        header=f'''<header class="public-header"><a class="brand public-brand" href="/"><span class="brand-symbol">EF<span>+</span></span><span class="brand-label">Educación <b>Física</b><small>APRENDER CON TECNOLOGÍA</small></span></a><nav class="public-nav"><a href="/">Inicio</a><a href="/aprender">Aprendizaje</a><a href="/actividades">Retos</a><a href="/calculadoras">Calculadoras</a></nav><a class="btn btn-sm btn-dark" href="/ingresar">Acceso docente {icon('arrow',16)}</a></header>'''
        shell=f'{header}<main class="public-content">{flash}{body}</main><footer class="public-footer"><span><b>EF+</b> · Plataforma educativa de Educación Física</span><span>Proyecto de vinculación tecnológica · Trujillo, Venezuela</span></footer>'
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#0B326B"><meta name="description" content="Plataforma educativa de Educación Física, aprendizaje y seguimiento pedagógico."><title>{e(title)} · Educación Física</title><link rel="icon" href="/static/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/static/styles.css"></head><body class="{'private-body' if user else 'public-body'}"><div class="{'app-layout' if user else 'public-layout'}">{shell}</div><script src="/static/app.js" defer></script></body></html>'''


def page_header(title, subtitle='', action=''):
    return f'<div class="page-heading"><div><h1>{e(title)}</h1><p>{e(subtitle)}</p></div>{action}</div>'

def panel(title, content, subtitle='', classes=''):
    return f'<section class="panel {classes}"><div class="panel-heading"><div><h2>{e(title)}</h2>{f"<p>{e(subtitle)}</p>" if subtitle else ""}</div></div><div class="panel-body">{content}</div></section>'

def stat(title, value, ic='chart', description=''):
    return f'<div class="stat-card"><span class="stat-icon">{icon(ic,23)}</span><div class="stat-value">{e(value)}</div><div class="stat-title">{e(title)}</div><div class="stat-desc">{e(description)}</div></div>'

def field(name, label, value='', fieldtype='text', required=False, placeholder='', attrs='', helptext=''):
    return f'<label class="field"><span>{e(label)}{" *" if required else ""}</span><input name="{e(name)}" type="{e(fieldtype)}" value="{e(value)}" placeholder="{e(placeholder)}" {"required" if required else ""} {attrs}/>{f"<small>{e(helptext)}</small>" if helptext else ""}</label>'

def selection(name,label,options,selected='',required=True,attrs=''):
    opts='<option value="">Seleccionar…</option>'+''.join(f'<option value="{e(v)}" {"selected" if str(v)==str(selected) else ""}>{e(t)}</option>' for v,t in options)
    return f'<label class="field"><span>{e(label)}{" *" if required else ""}</span><select name="{e(name)}" {"required" if required else ""} {attrs}>{opts}</select></label>'

def textarea(name,label,value=''):
    return f'<label class="field"><span>{e(label)}</span><textarea name="{e(name)}" rows="3" placeholder="Observaciones opcionales…">{e(value)}</textarea></label>'

def empty(text, href='', link=''):
    return f'<div class="empty">{icon("book",36)}<p>{e(text)}</p>{f"<a class=\"btn btn-primary\" href=\"{e(href)}\">{e(link)}</a>" if href else ""}</div>'

def table(headers, rows):
    head=''.join(f'<th>{e(h)}</th>' for h in headers)
    row=''.join('<tr>'+''.join(f'<td>{c}</td>' for c in rr)+'</tr>' for rr in rows)
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{row}</tbody></table></div>' if rows else '<div class="empty-mini">No hay registros para mostrar.</div>'

def badge(text, kind='neutral'):
    return f'<span class="badge badge-{e(kind)}">{e(text)}</span>'

def svg_line(values, width=640, height=210, label='Evolución'):
    if not values: return '<div class="empty-mini">No hay suficientes registros para dibujar la evolución.</div>'
    nums=[float(y) for _,y in values]
    lo,hi=min(nums),max(nums)
    if hi==lo: lo-=1; hi+=1
    else:
        margin=(hi-lo)*.17;lo-=margin;hi+=margin
    W,H=width,height;L,R,T,B=42,20,22,40
    pts=[]
    for i,(lab,val) in enumerate(values):
        x=L+(W-L-R)*(i/max(1,len(values)-1));y=T+(H-T-B)*(1-(float(val)-lo)/(hi-lo));pts.append((x,y,lab,float(val)))
    poly=' '.join(f'{x:.1f},{y:.1f}' for x,y,_,_ in pts)
    lines=''.join(f'<line x1="{L}" y1="{T+i*(H-T-B)/4:.1f}" x2="{W-R}" y2="{T+i*(H-T-B)/4:.1f}" stroke="#e5edf4"/><text x="{L-7}" y="{T+i*(H-T-B)/4+4:.1f}" text-anchor="end" font-size="11" fill="#6a8199">{hi-i*(hi-lo)/4:.1f}</text>' for i in range(5))
    labels=''.join(f'<text x="{x:.1f}" y="{H-12}" text-anchor="middle" font-size="11" fill="#6a8199">{e(lab)}</text>' for x,y,lab,val in pts)
    dots=''.join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#0876bc" stroke="white" stroke-width="2"><title>{e(lab)}: {val:g}</title></circle>' for x,y,lab,val in pts)
    return f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{e(label)}"><title>{e(label)}</title>{lines}<polyline fill="none" stroke="#0876bc" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="{poly}"/>{dots}{labels}</svg>'
