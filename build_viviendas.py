"""Genera planificacion_viviendas.html a partir de modelo_viviendas.py"""
import math
import numpy as np
import modelo_viviendas as M

IX, A_, NOMBRE, UNIDAD, ESC = M.IX, M.A_, M.NOMBRE, M.UNIDAD, M.ESC
COL_ESC = {"Extracción": "#a16207", "Energía": "#b45309", "Materiales": "#0e7490", "Componentes": "#4338ca", "Productos": "#be123c"}
COL_MET = {"trad": "#78716c", "pref": "#0e7490", "mod": "#4338ca", "lsf": "#d97706", "clt": "#15803d", "imp": "#be123c"}
CORTO_MET = {"trad": "Tradicional", "pref": "Prefabricado 2D", "mod": "Modular 3D", "lsf": "Acero ligero (LSF)", "clt": "Madera CLT", "imp": "Impresión 3D"}


def f(x, d=0):
    s = f"{x:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return "0" if s.lstrip("-").strip("0,") == "" else s


def fa(x):
    ax = abs(x)
    if ax >= 1000: return f(x, 0)
    if ax >= 100: return f(x, 1)
    if ax >= 1: return f(x, 2)
    if ax >= 0.01: return f(x, 3)
    return f(x, 5) if ax > 0 else "0"


def pct(x, d=1):
    return f(100 * x, d) + " %"


def T(txt, **kw):
    for k, v in kw.items():
        txt = txt.replace("[[" + k + "]]", str(v))
    assert "[[" not in txt, txt[txt.index("[["):txt.index("[[") + 30]
    return txt


def chip(e):
    return f"<span class='chip' style='--c:{COL_ESC[e]}'>{e}</span>"


def bar(v, vmax, c):
    w = 0 if vmax <= 0 else max(0.5, 100 * v / vmax)
    return f'<div class="bar"><span style="width:{w:.1f}%;background:{c}"></span></div>'


def stack(parts, tot):
    return '<div class="stack">' + "".join(f'<span title="{lab}" style="width:{100 * v / tot:.2f}%;background:{c}"></span>' for v, c, lab in parts if v > 0) + "</div>"


def mezcla_html(mz):
    return " + ".join(f"{pct(w, 0)} {CORTO_MET[m]}" for m, w in sorted(mz.items(), key=lambda kv: -kv[1]))


H = []
H.append(r"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Planificación de 1.000.000 de viviendas y de comedores comunales — Leontief, Kantorovich y algoritmos de localización</title>
<script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},chtml:{scale:0.97}};</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<style>
:root{--bg:#fafaf9;--panel:#fff;--ink:#1c1917;--mut:#57534e;--line:#e7e5e4;--acc:#4338ca;--acc2:#0e7490;--warn:#b45309;--red:#be123c;--ok:#15803d}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.62 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif}
nav{position:fixed;top:0;left:0;bottom:0;width:270px;overflow:auto;padding:22px 16px;border-right:1px solid var(--line);background:#f5f5f4;font-size:13.5px;z-index:5}
nav b{display:block;margin:0 0 8px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut)}
nav a{display:block;color:var(--ink);text-decoration:none;padding:3px 8px;border-radius:6px}nav a:hover{background:#e7e5e4}
nav a.sub{padding-left:22px;color:var(--mut);font-size:12.5px}
main{margin-left:270px;max-width:1300px;padding:40px 48px 140px}
@media (max-width:1500px){nav{display:none}main{margin-left:0;padding:28px 32px;max-width:none}}
h1{font-size:33px;line-height:1.2;margin:0 0 10px}
h2{font-size:27px;margin:72px 0 12px;padding-top:14px;border-top:3px solid var(--ink)}
h3{font-size:21px;margin:44px 0 8px;padding-top:8px;border-top:1px solid var(--line)}
h4{font-size:16.5px;margin:28px 0 6px}
p,li{max-width:88ch}.lead{font-size:18px;color:var(--mut)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:12px;margin:24px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:13px 15px}
.kpi .v{font-size:24px;font-weight:700;font-variant-numeric:tabular-nums}.kpi .l{font-size:13px;color:var(--mut)}
.box{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:14px 0;overflow-x:auto}
.formula{background:#eef2ff;border:1px solid #c7d2fe;border-left:4px solid var(--acc);border-radius:8px;padding:10px 18px;margin:14px 0;overflow-x:auto}
.formula.k{background:#ecfeff;border-color:#a5f3fc;border-left-color:var(--acc2)}
.formula.t{background:#fff7ed;border-color:#fed7aa;border-left-color:var(--warn)}
.tt{font-size:11.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--mut)}
.nota{font-size:14px;color:var(--mut);border-left:3px solid var(--line);padding-left:12px}
.res{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:12px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;font-size:12.8px;font-variant-numeric:tabular-nums}
th,td{padding:5px 7px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);font-weight:600}
th mjx-container{font-size:135%!important}
td.n{text-align:right;white-space:nowrap}td.w{width:15%;min-width:80px}.mut{color:var(--mut)}
tr.hl td{background:#eef2ff}tr.rec td{background:#f0fdf4}tr.sep td{background:#fafaf9;font-weight:600;color:var(--mut);font-size:11.5px;text-transform:uppercase;letter-spacing:.04em}
.bar{height:11px;background:#f5f5f4;border-radius:3px;overflow:hidden;margin-top:4px}.bar span{display:block;height:100%;border-radius:3px}
.stack{display:flex;height:12px;background:#f5f5f4;border-radius:3px;overflow:hidden;margin-top:5px;min-width:90px}.stack span{display:block;height:100%}
.chip{display:inline-block;font-size:10.5px;padding:0 7px;border-radius:999px;border:1px solid var(--c);color:var(--c);white-space:nowrap}
.ok{color:var(--ok);font-weight:600}.no{color:var(--red);font-weight:600}.warn{color:var(--warn);font-weight:600}
.leg{font-size:12.5px;color:var(--mut);margin-top:6px}.leg span{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 4px 0 12px;vertical-align:middle}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}@media (max-width:1100px){.two{grid-template-columns:1fr}}
.three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}@media (max-width:1100px){.three{grid-template-columns:1fr}}
td.tree{min-width:240px}
.gantt .row{display:flex;align-items:center;gap:8px;font-size:12.5px;margin:4px 0}.gantt .lab{width:360px;flex-shrink:0}
.gantt .track{flex:1;position:relative;height:20px;background:#f5f5f4;border:1px solid var(--line);border-radius:4px}
.gantt .b{position:absolute;top:2px;bottom:2px;border-radius:3px;color:#fff;font-size:11px;display:flex;align-items:center;justify-content:center}
.gantt .crit{background:var(--red)}.gantt .nc{background:#78716c}
svg.chart{width:100%;height:auto}svg .tk{font-size:11px;fill:#78716c}svg .ax{font-size:12px;fill:#57534e}
code{font-family:ui-monospace,Menlo,monospace;font-size:13px;background:#f5f5f4;padding:1px 5px;border-radius:4px}
</style></head><body>""")
H.append("""<nav><b>Índice</b><a href='planificacion_viviendas_balance.html' style='background:#1c1917;color:#fff;margin-bottom:8px'>→ Balance con la producción nacional 2025</a><a href='#resumen'>Resumen</a><a href='#programa'>1. Programa y supuestos</a>
<a href='#metodos'>2. Métodos constructivos</a><a class='sub' href='#m-catalogo'>2.1 Catálogo</a><a class='sub' href='#m-leontief'>2.2 Cada método con Leontief</a><a class='sub' href='#m-materiales'>2.3 Técnicas de materiales</a>
<a href='#piezas'>3. Descomposición en piezas</a>
<a href='#maxprod'>4. Máxima producción (Kantorovich)</a><a class='sub' href='#k-max'>4.1 Máximo de viviendas al año</a><a class='sub' href='#k-plan'>4.2 Plan de 200.000/año</a><a class='sub' href='#k-pareto'>4.3 Frontera horas–CO₂</a>
<a href='#comedores'>5. Comedores comunales</a><a class='sub' href='#c-modelo'>5.1 Algoritmo de localización</a><a class='sub' href='#c-result'>5.2 Resultados por tipología</a><a class='sub' href='#c-mapas'>5.3 Mapas</a><a class='sub' href='#c-nacional'>5.4 Plan nacional</a>
<a href='#fabricas'>6. Ubicación de fábricas</a><a href='#taller'>7. Taller y obra</a><a href='#avsb'>8. Comparación A frente a B</a><a href='#supuestos'>9. Supuestos</a></nav><main>""")

# =============================================================================
# RESUMEN
# =============================================================================
mA, mB = M.MAXP["A"], M.MAXP["B"]
pA, pB = M.PLAN["A"]["comp"], M.PLAN["B"]["comp"]
lmA = M.leontief(pA["z"]); lmB = M.leontief(pB["z"])
plz_viv = M.PLZ_PROV.sum() / M.N_VIV
vA = lmA["v"][IX["VIVA"]]; vB = lmB["v"][IX["VIVB"]] + plz_viv * lmB["v"][IX["PLZ"]]
eA = lmA["e"][IX["VIVA"]]; eB = lmB["e"][IX["VIVB"]] + plz_viv * lmB["e"][IX["PLZ"]]
opA, opB = M.OPER["A"], M.OPER["B"]
hopA = opA["h_trabajo"]; hopB = opB["h_trabajo"] + M.W_PASEO * opB["paseo"]
H.append(T(r"""<h1>Planificación de 1.000.000 de viviendas en España, con cocina o con comedores comunales</h1>
<p class="lead">Dos programas para una superficie como la de España ([[SUP]] km², 52 provincias). <b>Caso A</b>: 1.000.000 de viviendas de <b>70 m² útiles</b> con cocina. <b>Caso B</b>: 1.000.000 de viviendas de <b>62 m² útiles sin cocina</b> (las mismas habitaciones, sin los 8 m² de cocina), más los <b>comedores comunales</b> necesarios para que coma todo el mundo, situados cerca de cada bloque. Se calcula todo: materiales y horas (Leontief), los métodos constructivos que maximizan la producción (Kantorovich), dónde poner los comedores (algoritmos de localización) y dónde poner las fábricas (problema de transporte).</p>
<div class="kpis">
<div class="kpi"><div class="v">[[MAXA]]</div><div class="l">viviendas A/año como máximo con los recursos del programa → 1.000.000 en <b>[[ANA]] años</b></div></div>
<div class="kpi"><div class="v">[[MAXB]]</div><div class="l">viviendas B/año como máximo (con sus comedores) → 1.000.000 en <b>[[ANB]] años</b></div></div>
<div class="kpi"><div class="v">−[[RH]]</div><div class="l">horas por vivienda del plan recomendado frente al todo tradicional ([[VA]] h frente a [[VT]] h)</div></div>
<div class="kpi"><div class="v">[[NCOM]]</div><div class="l">comedores comunales en España para el caso B ([[PLZ]] plazas)</div></div>
<div class="kpi"><div class="v">[[DMED]] m</div><div class="l">distancia media a pie del bloque al comedor (máximo 300–450 m en ciudad)</div></div>
<div class="kpi"><div class="v">[[NFAB]]</div><div class="l">fábricas de construcción industrializada, situadas en [[NSIT]] provincias</div></div>
</div>
<div class="res"><b>Conclusiones.</b><ol>
<li><b>Para producir el máximo no hay un único método.</b> Se combinan todos los recursos: el acero ligero (LSF) aprovecha las fábricas, el tradicional aprovecha los albañiles que sobran y la impresión 3D aprovecha las impresoras. Con un solo método la producción cae entre un 36 % y un 93 %.</li>
<li><b>Con un ritmo de 200.000 viviendas al año</b>, el método recomendado (coste social mínimo: horas + 3·CO₂) es <b>[[MEZA]]</b>, con cemento bajo en clínker, acero de chatarra y electricidad renovable. Gasta [[VA]] h y [[EA]] t de CO₂ por vivienda, frente a [[VT]] h y [[ET]] t con el método tradicional.</li>
<li><b>El caso B ahorra en la construcción y, sobre todo, en el uso.</b> Hay que construir 8 m² menos y ninguna cocina, a cambio de 1 plaza de comedor por vivienda. Cada hogar pasa de [[HOPA]] h al año de cocina doméstica a [[HOPB]] h de personal de comedor, más [[PASEO]] h de paseo de ida y vuelta.</li>
<li><b>Los comedores tienen que estar cerca.</b> Con el tiempo de paseo dentro del objetivo, el algoritmo óptimo pone en la ciudad un comedor cada 3–4 bloques. Un único gran comedor por barrio cuesta entre 5 y 12 veces más en horas totales, porque obliga a todos a caminar.</li>
</ol></div>""", SUP=f(M.SUP_TOTAL), MAXA=f(mA["t"]), ANA=f(M.N_VIV / mA["t"], 1), MAXB=f(mB["t"]), ANB=f(M.N_VIV / mB["t"], 1),
           RH=pct(1 - vA / M.COMP_MET[("VIVA", "trad")]["v"], 0), VA=f(vA), VT=f(M.COMP_MET[("VIVA", "trad")]["v"]),
           NCOM=f(M.COM_PROV.sum()), PLZ=f(M.PLZ_PROV.sum()), DMED=f(M.DMED_NAC), NFAB=int(M.FAB["y"].sum()), NSIT=int((M.FAB["y"] > 0).sum()),
           MEZA=mezcla_html(M.mezcla_viv(pA["z"], "VIVA")).lower().replace("lsf", "LSF"), EA=f(eA, 1), ET=f(M.COMP_MET[("VIVA", "trad")]["e"], 1),
           HOPA=f(hopA), HOPB=f(opB["h_trabajo"]), PASEO=f(opB["paseo"])))

# =============================================================================
# 1. PROGRAMA
# =============================================================================
H.append(T(r"""<h2 id="programa">1. Programa y supuestos</h2>
<div class="box"><table><thead><tr><th></th><th>Caso A</th><th>Caso B</th></tr></thead><tbody>
<tr><td>Viviendas</td><td class="n">1.000.000</td><td class="n">1.000.000</td></tr>
<tr><td>Superficie útil</td><td class="n">70 m² (3 dormitorios, salón, cocina, 1,2 baños)</td><td class="n">62 m² (lo mismo, sin cocina)</td></tr>
<tr><td>Superficie construida (con muros y zonas comunes)</td><td class="n">84 m²</td><td class="n">74 m²</td></tr>
<tr><td>Comedores</td><td class="n">—</td><td class="n">Para el 100 % de residentes: 2,5 personas/vivienda, 3 comidas al día, 3 turnos por servicio → [[PLZ]] plazas por vivienda</td></tr>
<tr><td>Reparto territorial</td><td colspan="2">Proporcional a la población de cada provincia (editable). Bloques de 6 plantas y 20 viviendas por ascensor.</td></tr>
<tr><td>Ritmo de referencia</td><td colspan="2">200.000 viviendas al año (1.000.000 en 5 años); el máximo posible se calcula en §4.</td></tr>
</tbody></table></div>
<div class="formula t">\[ \text{plazas por vivienda} = \frac{2{,}5\ \text{personas}\times 1{,}05}{3\ \text{turnos}} = [[PLZ]] \qquad
\text{viviendas en la provincia } p = 1.000.000\cdot\frac{\text{población}_p}{\sum \text{población}} \]</div>""", PLZ=f(M.PLZ_POR_VIV, 3)))

# =============================================================================
# 2. MÉTODOS
# =============================================================================
H.append("<h2 id='metodos'>2. Métodos constructivos</h2><h3 id='m-catalogo'>2.1 Catálogo de métodos (por m² construido)</h3>"
         "<p>Cada método es una actividad de Kantorovich: materiales por m², horas de obra, horas de fábrica y uso de impresoras 3D. La instalación y el acabado de la vivienda (420 h en el tradicional) también cambian de sitio y de productividad: en el modular, el 70 % se hace en fábrica, con un 25 % menos de horas.</p>"
         "<div class='box'><table><thead><tr><th>Método</th><th>Hormigón t/m²</th><th>Acero kg/m²</th><th>Cerámica t/m²</th><th>Madera m³/m²</th><th>Yeso t/m²</th><th>Obra h/m²</th><th>Fábrica h/m²</th><th>Instalación: factor / parte en obra</th><th>Impresora h/m²</th></tr></thead><tbody>")
for mid, (nom, mat, hob, hfab, fi, sh, imp, co2) in M.METODOS.items():
    H.append(f"<tr><td><span class='chip' style='--c:{COL_MET[mid]}'>{CORTO_MET[mid]}</span> {nom}</td><td class='n'>{fa(mat.get('HOR', 0))}</td><td class='n'>{f(1000 * mat.get('ACE', 0))}</td>"
             f"<td class='n'>{fa(mat.get('CER', 0))}</td><td class='n'>{fa(mat.get('MAD', 0))}</td><td class='n'>{fa(mat.get('YSO', 0))}</td><td class='n'>{fa(hob)}</td><td class='n'>{fa(hfab)}</td>"
             f"<td class='n'>{f(fi, 2)} / {pct(sh, 0)}</td><td class='n'>{fa(imp)}</td></tr>")
H.append("</tbody></table></div>")
H.append(r"""<h3 id="m-leontief">2.2 Cada método con Leontief: qué cuesta una vivienda</h3>
<div class="formula">\[ v_{\text{viv}} = l_{\text{viv}} + \sum_i v_i\,a_{i,\text{viv}},\qquad \mathbf r^{\top} = R\,(I-A)^{-1}\ \ \text{(horas de obra, de fábrica, cemento y madera incorporados)} \]</div>
<div class='box'><table><thead><tr><th>Método</th><th>Caso</th><th>Horas totales</th><th>de obra</th><th>de fábrica</th><th>resto de la cadena</th><th>t CO₂</th><th>t cemento</th><th>m³ madera en rollo</th><th></th></tr></thead><tbody>""")
vmax = max(d["v"] for d in M.COMP_MET.values())
for tipo in ("VIVA", "VIVB"):
    for mid in M.METODOS:
        d = M.COMP_MET[(tipo, mid)]
        resto = d["v"] - d["obra"] - d["fab"]
        H.append(f"<tr><td><span class='chip' style='--c:{COL_MET[mid]}'>{CORTO_MET[mid]}</span></td><td>{'A (70 m²)' if tipo == 'VIVA' else 'B (62 m²)'}</td><td class='n'><b>{f(d['v'])}</b></td>"
                 f"<td class='n'>{f(d['obra'])}</td><td class='n'>{f(d['fab'])}</td><td class='n'>{f(resto)}</td><td class='n'>{fa(d['e'])}</td><td class='n'>{fa(d['cem'])}</td><td class='n'>{fa(d['mdr'])}</td>"
                 f"<td class='w'>{stack([(d['obra'], '#78716c', 'obra'), (d['fab'], '#4338ca', 'fábrica'), (resto, '#0e7490', 'cadena')], vmax)}</td></tr>")
H.append("</tbody></table><div class='leg'><span style='background:#78716c'></span>horas de obra<span style='background:#4338ca'></span>horas de fábrica<span style='background:#0e7490'></span>horas en materiales y componentes</div></div>")
H.append(T("<p><b>Lectura.</b> El modular 3D es el que menos horas totales gasta: [[MOD]] h frente a [[TRAD]] h del tradicional, y reduce un 83 % las horas en obra, porque las pasa a la fábrica. El de madera CLT es el de menos CO₂ ([[CLT]] t), pero cada vivienda consume [[MDR]] m³ de madera en rollo, y el bosque disponible limita su escala. La impresión 3D ahorra horas de obra, pero gasta más cemento que nadie.</p>",
           MOD=f(M.COMP_MET[("VIVA", "mod")]["v"]), TRAD=f(M.COMP_MET[("VIVA", "trad")]["v"]), CLT=fa(M.COMP_MET[("VIVA", "clt")]["e"]), MDR=f(M.COMP_MET[("VIVA", "clt")]["mdr"])))
# técnicas de materiales
H.append(r"""<h3 id="m-materiales">2.3 Técnicas de los materiales</h3><div class="formula k">\[ \alpha_k=\frac{v_k-v_{\text{base}}}{\varepsilon_{\text{base}}-\varepsilon_k}\ \ \text{(horas por t de CO}_2\text{ evitada; se adopta si } \alpha_k\le\mu=3) \]</div><div class='box'><table><thead><tr><th>Bien</th><th>Técnica</th><th>Horas/ud</th><th>t CO₂/ud</th><th>\(\alpha\)</th><th>Veredicto</th><th>Límite</th></tr></thead><tbody>""")
for g in ["CEM", "HOR", "ACE", "ALU", "ELE"]:
    ks = [k for k, a in enumerate(A_) if a["bien"] == g]
    vals = {k: (A_[k]["h"] + sum(q * M.LB["v"][IX[i]] for i, q in A_[k]["ins"].items()), A_[k]["co2"] + sum(q * M.LB["e"][IX[i]] for i, q in A_[k]["ins"].items())) for k in ks}
    b = M.BASE[g]
    for k in ks:
        v, e = vals[k]
        if k == b:
            ver, al = "<span class='mut'>base</span>", "—"
        else:
            dv, de = v - vals[b][0], e - vals[b][1]
            if dv <= 0 and de <= 0: ver, al = "<span class='ok'>dominante</span>", "—"
            elif dv >= 0 and de >= 0: ver, al = "<span class='no'>dominada</span>", "—"
            else:
                a_ = dv / -de; al = f(a_, 2)
                ver = "<span class='ok'>compensa</span>" if a_ <= M.MU else "<span class='warn'>no compensa</span>"
        H.append(f"<tr><td><b>{g}</b></td><td>{A_[k]['nombre']}</td><td class='n'>{fa(v)}</td><td class='n'>{fa(e)}</td><td class='n'>{al}</td><td>{ver}</td><td class='mut'>{A_[k]['nota']}</td></tr>")
H.append("</tbody></table></div>")

# =============================================================================
# 3. DESCOMPOSICIÓN EN PIEZAS
# =============================================================================


def arbol(g, qty, lm, nivel=0, out=None, maxn=3):
    out = [] if out is None else out
    j = IX[g]
    out.append(dict(g=g, nivel=nivel, q=qty, h=qty * lm["v"][j], c=qty * lm["e"][j], obra=qty * lm["rec"][0, j], fab=qty * lm["rec"][1, j],
                    ele=qty * lm["L"][IX["ELE"], j], cem=qty * lm["L"][IX["CEM"], j]))
    if nivel < maxn and ESC[g] in ("Productos", "Componentes"):
        cols = lm["A"][:, j]
        for i in sorted(np.nonzero(cols)[0], key=lambda i: -cols[i] * lm["v"][i]):
            if M.COD[i] in ("ELE", "DIE"):
                continue
            arbol(M.COD[i], qty * cols[i], lm, nivel + 1, out, maxn)
    return out


H.append("<h2 id='piezas'>3. Descomposición en piezas y necesidad productiva</h2><p>Lista de materiales multinivel de cada producto con la mezcla de técnicas del plan recomendado. Para cada pieza: la cantidad por unidad y para 200.000 unidades al año, las horas incorporadas (con las de obra y de fábrica aparte), la electricidad, el cemento y el CO₂.</p>")
for g, lm, q, tit in [("VIVA", lmA, M.Q_ANUAL, "Vivienda A (70 m², con cocina)"), ("VIVB", lmB, M.Q_ANUAL, "Vivienda B (62 m², sin cocina)"),
                      ("PLZ", lmB, M.Q_ANUAL * plz_viv, "Plaza de comedor comunal")]:
    tree = arbol(g, 1.0, lm)
    hmax = tree[0]["h"]
    H.append(f"<h3>{tit}</h3><div class='box'><table><thead><tr><th>Pieza / material</th><th>Por unidad</th><th>Plan anual</th><th>Horas incorporadas</th><th>de obra</th><th>de fábrica</th><th>kWh</th><th>t cemento</th><th>t CO₂</th><th></th></tr></thead><tbody>")
    for n in tree:
        sang = "&nbsp;" * 5 * n["nivel"] + ("└ " if n["nivel"] else "")
        H.append(f"<tr{' class=hl' if n['nivel'] == 0 else ''}><td class='tree'>{sang}{chip(ESC[n['g']])} {NOMBRE[n['g']]}</td><td class='n'>{fa(n['q'])} {UNIDAD[n['g']]}</td>"
                 f"<td class='n'>{fa(n['q'] * q)} {UNIDAD[n['g']]}</td><td class='n'><b>{fa(n['h'])}</b></td><td class='n'>{fa(n['obra'])}</td><td class='n'>{fa(n['fab'])}</td>"
                 f"<td class='n'>{fa(n['ele'] * 1000)}</td><td class='n'>{fa(n['cem'])}</td><td class='n'>{fa(n['c'])}</td><td class='w'>{bar(n['h'], hmax, COL_ESC[ESC[n['g']]])}</td></tr>")
    H.append("</tbody></table></div>")

# =============================================================================
# 4. MÁXIMA PRODUCCIÓN
# =============================================================================
H.append(T(r"""<h2 id="maxprod">4. Máxima producción: Kantorovich a escala nacional</h2>
<h3 id="k-max">4.1 ¿Cuántas viviendas al año como máximo?</h3>
<p>Recursos disponibles cada año para el programa: <b>[[HOB]] M de horas de obra</b> (200.000 trabajadores), <b>[[HFA]] M de horas de fábrica</b>, [[IMP]] M de horas de impresora 3D, [[CEM]] Mt de cemento y [[BOS]] M m³ de madera en rollo.</p>
<div class="formula k">\[ \max\ t\quad\text{s.a.}\quad B\mathbf z\ \ge\ t\,(\mathbf e_{\text{viv}}+p\,\mathbf e_{\text{plaza}}),\qquad R\,\mathbf z\le\mathbf r\ \ (\text{obra, fábrica, impresoras, cemento, bosque}),\qquad \text{cuotas de reciclado},\ \ \mathbf z\ge0 \]
<p>Después, con \(t\) fijado en su máximo, se minimiza el CO₂: es una optimización lexicográfica. Así se obtiene la máxima producción con el mínimo CO₂ posible.</p></div>""",
           HOB=f(M.CAP["HOBRA"] / 1e6), HFA=f(M.CAP["HFAB"] / 1e6), IMP=f(M.CAP["IMPR"] / 1e6, 1), CEM=f(M.CAP["CEMENTO"] / 1e6), BOS=f(M.CAP["BOSQUE"] / 1e6, 1)))
H.append("<div class='box'><table><thead><tr><th>Método</th><th>Caso A: viviendas/año</th><th>Caso B: viviendas/año</th><th>Recurso que lo frena</th></tr></thead><tbody>")
limita = {"trad": "horas de obra", "pref": "horas de fábrica + obra", "mod": "horas de fábrica", "lsf": "horas de fábrica", "clt": "madera del bosque", "imp": "impresoras"}
for mid in M.METODOS:
    H.append(f"<tr><td><span class='chip' style='--c:{COL_MET[mid]}'>{CORTO_MET[mid]}</span> sólo este método</td><td class='n'>{f(M.MAXP_SOLO[('A', mid)]['t'])}</td><td class='n'>{f(M.MAXP_SOLO[('B', mid)]['t'])}</td><td class='mut'>{limita[mid]}</td></tr>")
H.append(f"<tr class='rec'><td><b>Mezcla óptima de Kantorovich</b></td><td class='n'><b>{f(mA['t'])}</b></td><td class='n'><b>{f(mB['t'])}</b></td><td>todos a la vez</td></tr></tbody></table></div>")
H.append("<div class='two'>")
for c, s, s2 in (("A", mA, M.MAXP_CO2["A"]), ("B", mB, M.MAXP_CO2["B"])):
    mz = M.mezcla_viv(s2["z"], "VIV" + c)
    du = s["dual"]
    H.append(f"<div class='box'><b>Caso {c}: {f(s['t'])} viviendas/año</b> → 1.000.000 en {f(M.N_VIV / s['t'], 1)} años"
             + stack([(w, COL_MET[m], CORTO_MET[m]) for m, w in mz.items()], 1)
             + f"<p>Métodos: {mezcla_html(mz)}. CO₂: {f(s2['co2'] / s['t'], 1)} t/vivienda tras minimizarlo en la segunda etapa.</p>"
             "<table><thead><tr><th>Recurso</th><th>Usado / disponible</th><th>Multiplicador: viviendas extra por cada…</th></tr></thead><tbody>"
             + "".join(f"<tr><td>{nm}</td><td class='n'>{f(s['rec'][r] / 1e6, 2)} / {f(M.CAP[r] / 1e6, 2)} M</td><td class='n'>{('<b>' + f(du.get(r, 0) * mult, 1) + '</b> por ' + lab) if du.get(r, 0) > 1e-9 else '0 (sobra)'}</td></tr>"
                       for r, nm, mult, lab in [("HOBRA", "Horas de obra", 1000, "1.000 h"), ("HFAB", "Horas de fábrica", 1000, "1.000 h"),
                                                ("IMPR", "Horas de impresora 3D", 1000, "1.000 h"), ("CEMENTO", "Cemento (t)", 1000, "1.000 t"), ("BOSQUE", "Madera en rollo (m³)", 1000, "1.000 m³")])
             + "</tbody></table></div>")
H.append("</div>")
H.append(T("<div class='res'><b>Qué método maximiza la producción.</b> Ningún método solo: el máximo lo da la <b>mezcla</b>. LSF en las fábricas, tradicional con la mano de obra de obra que sobra, e impresión 3D con las impresoras. Los multiplicadores dicen dónde invertir: <b>1.000 h más de fábrica dan [[F]] viviendas más, y 1.000 h de obra solo [[O]]</b>. Ampliar la capacidad de las fábricas es la palanca más rentable para producir más.</div>",
           F=f(mA["dual"]["HFAB"] * 1000, 2), O=f(mA["dual"]["HOBRA"] * 1000, 2)))

H.append("<h3 id='k-plan'>4.2 Plan de 200.000 viviendas al año: método según el objetivo</h3><div class='box'><table><thead><tr><th>Caso</th><th>Objetivo</th><th>Métodos elegidos</th><th>Horas/vivienda</th><th>t CO₂/vivienda</th><th>Horas de obra (M/año)</th><th>Horas de fábrica (M/año)</th><th>Cemento (Mt/año)</th></tr></thead><tbody>")
nomobj = {"base": "Base (todo tradicional, técnica base)", "h": "Mínimo trabajo", "c": "Mínimo CO₂", "comp": "Coste social mínimo (recomendado)"}
for c in ("A", "B"):
    for k in ("base", "h", "c", "comp"):
        s = M.PLAN[c][k]
        H.append(f"<tr{' class=rec' if k == 'comp' else ''}><td>{c}</td><td><b>{nomobj[k]}</b></td><td>{mezcla_html(M.mezcla_viv(s['z'], 'VIV' + c))}</td><td class='n'>{f(s['horas'] / M.Q_ANUAL)}</td>"
                 f"<td class='n'>{f(s['co2'] / M.Q_ANUAL, 1)}</td><td class='n'>{f(s['rec']['HOBRA'] / 1e6, 1)}</td><td class='n'>{f(s['rec']['HFAB'] / 1e6, 1)}</td><td class='n'>{f(s['rec']['CEMENTO'] / 1e6, 2)}</td></tr>")
H.append("</tbody></table><p class='nota'>En el caso B, las horas y el CO₂ por vivienda incluyen su parte de plaza de comedor.</p></div>")
H.append("<h3 id='k-pareto'>4.3 Frontera horas–CO₂ (200.000 viviendas/año)</h3><div class='two'>")
for c in ("A", "B"):
    H.append(f"<div class='box'><b>Caso {c}</b><table><thead><tr><th>t CO₂/vivienda</th><th>Horas/vivienda</th><th>μ (h/t)</th><th>Métodos</th></tr></thead><tbody>"
             + "".join(f"<tr><td class='n'>{f(p['co2'] / M.Q_ANUAL, 2)}</td><td class='n'>{f(p['horas'] / M.Q_ANUAL)}</td><td class='n'>{fa(p['mu'])}</td><td>{mezcla_html({m: w / M.Q_ANUAL for m, w in p['mix'].items() if w > 1})}</td></tr>" for p in M.PARETO[c])
             + "</tbody></table></div>")
H.append("</div>")

# =============================================================================
# 5. COMEDORES
# =============================================================================
H.append(T(r"""<h2 id="comedores">5. Comedores comunales: cuántos, de qué tamaño y dónde</h2>
<h3 id="c-modelo">5.1 Algoritmo de localización</h3>
<p>Es un problema de <b>localización de instalaciones con capacidad</b>. Hay que decidir en qué bloques se abre un comedor (en la planta baja), de cuántas plazas y qué bloques come en cada uno. Se busca el equilibrio entre dos fuerzas: <b>pocos comedores grandes</b> ahorran personal fijo, y <b>muchos pequeños</b> ahorran paseo a los vecinos. Además, nadie puede quedar más lejos de una distancia máxima.</p>
<div class="formula k"><div class="tt">Programa lineal entero mixto (MILP)</div>
\[ \begin{aligned}
\min\ & \underbrace{\sum_j F\,y_j}_{\text{equipo mínimo}} + \underbrace{\sum_j G\,m_j}_{\text{módulos de 50 plazas}} + \underbrace{\omega\sum_{i,j} \tau\,d_{ij}\,n_i\,x_{ij}}_{\text{paseo de los vecinos}} + \underbrace{\sum_i \rho\,n_i\,r_i}_{\text{reparto (diseminado)}}\\
\text{s.a.}\ & \sum_{j:\,d_{ij}\le d_{\max}} x_{ij} + r_i = 1\ \ \forall i,\qquad \sum_i p\,n_i\,x_{ij}\le 50\,m_j,\qquad m_j\le 12\,y_j,\qquad x_{ij}\le y_j\\
& y_j\in\{0,1\},\ m_j\in\mathbb Z_{\ge0},\ 0\le x_{ij}\le1
\end{aligned} \]
<p>\(n_i\): viviendas del bloque \(i\). \(d_{ij}\): distancia por la calle (Manhattan). \(F\) = [[F]] h/año (3 personas durante los servicios). \(G\) = [[G]] h/año por módulo de 50 plazas (edificio a 50 años y equipo a 15, con Leontief). \(\tau\) = [[TAU]] h de paseo al año por vivienda y metro (2,5 personas × 3 comidas × ida y vuelta a 4,5 km/h). \(\omega\) = [[W]]: el tiempo de paseo vale la mitad que una hora de trabajo. \(p\) = [[P]] plazas/vivienda. \(\rho\) = [[RHO]] h/año por vivienda con reparto a domicilio, solo para el diseminado.</p></div>
<p>Se compara con tres algoritmos más simples:</p>
<ul>
<li><b>Voraz de cobertura</b>: abre comedores donde cubren más viviendas aún no cubiertas, hasta cubrirlas todas, y asigna cada bloque al más cercano.</li>
<li><b>k-medias</b> ponderado por viviendas, con el mismo número de comedores que el óptimo y cada centro llevado al bloque más cercano.</li>
<li><b>Un comedor central</b> por barrio.</li>
</ul>""", F=f(M.FIJO_COM), G=f(M.H_MOD), TAU=f(M.H_PASEO_M, 3), W=f(M.W_PASEO, 1), P=f(M.PLZ_POR_VIV, 3), RHO=f(M.REPARTO_H)))
H.append("<h3 id='c-result'>5.2 Resultados por tipología urbana</h3><div class='box'><table><thead><tr><th>Tipología</th><th>Algoritmo</th><th>Comedores</th><th>Plazas</th><th>Viviendas por comedor</th><th>Distancia media</th><th>Distancia máxima</th><th>Horas de comedor/año</th><th>Horas de paseo/año</th><th>Objetivo (h/año)</th></tr></thead><tbody>")
for k, L in M.LOC.items():
    tip = L["tip"]
    H.append(f"<tr class='sep'><td colspan='10'>{tip['nombre']}: {f(L['milp']['viv'])} viviendas en {len(L['viv'])} bloques, {f(tip['lado'] / 1000, 1)} × {f(tip['lado'] / 1000, 1)} km, distancia máxima {tip['dmax']} m</td></tr>")
    for alg, nom in (("milp", "MILP óptimo"), ("kmedias", "k-medias"), ("voraz", "Voraz de cobertura"), ("uno", "Un comedor central")):
        e = L[alg]
        H.append(f"<tr{' class=rec' if alg == 'milp' else ''}><td>{tip['nombre']}</td><td><b>{nom}</b></td><td class='n'>{e['n']}</td><td class='n'>{f(e['plazas'])}</td><td class='n'>{f(e['viv'] / e['n'])}</td>"
                 f"<td class='n'>{f(e['dmed'])} m</td><td class='n'>{f(e['dmax'])} m</td><td class='n'>{f(e['h_inst'] + e['h_rep'])}</td><td class='n'>{f(e['paseo'])}</td><td class='n'><b>{f(e['obj'])}</b></td></tr>")
H.append("</tbody></table></div>")
dn = M.LOC["denso"]
H.append(T("<div class='res'>El MILP óptimo gana a los tres algoritmos simples en todas las tipologías. Frente al <b>voraz</b>, que busca el mínimo número de comedores, ahorra un [[V]] de horas en ciudad densa: el voraz abre pocos comedores y obliga a caminar más. Frente a <b>k-medias</b> con el mismo número de comedores, ahorra un [[K]], porque k-medias no respeta la capacidad ni la distancia máxima. <b>Un único comedor por barrio</b> multiplica el coste por [[U]] por el paseo. En el medio rural, el óptimo pone un comedor en cada pueblo y solo lleva la comida a domicilio al diseminado ([[REP]] de las viviendas).</div>",
           V=pct(1 - dn["milp"]["obj"] / dn["voraz"]["obj"], 0), K=pct(1 - dn["milp"]["obj"] / dn["kmedias"]["obj"], 0), U=f(dn["uno"]["obj"] / dn["milp"]["obj"], 1),
           REP=pct(M.TASA["rural"]["rep"], 1)))


def mapa(L, sol_ab, sol_as, titulo, reparto=()):
    pts, viv = L["pts"], L["viv"]
    lado = L["tip"]["lado"]
    W = 360
    s = W / lado
    cols = ["#4338ca", "#0e7490", "#d97706", "#15803d", "#be123c", "#7c3aed", "#a16207", "#0f766e", "#9f1239", "#1d4ed8"]
    cidx = {j: cols[n % len(cols)] for n, j in enumerate(sol_ab)}
    out = [f'<svg viewBox="0 0 {W} {W + 22}" class="chart"><text x="2" y="14" class="ax">{titulo}</text><rect x="0" y="20" width="{W}" height="{W}" fill="#fafaf9" stroke="#e7e5e4"/>']
    for i, (x, y) in enumerate(pts):
        j = sol_as.get(i)
        if j is not None:
            out.append(f'<line x1="{x * s:.1f}" y1="{20 + y * s:.1f}" x2="{pts[j][0] * s:.1f}" y2="{20 + pts[j][1] * s:.1f}" stroke="{cidx[j]}" stroke-width="0.6" opacity="0.6"/>')
    for i, (x, y) in enumerate(pts):
        j = sol_as.get(i)
        col = cidx[j] if j is not None else "#a8a29e"
        r = 1.2 + math.sqrt(viv[i]) * 0.35
        out.append(f'<circle cx="{x * s:.1f}" cy="{20 + y * s:.1f}" r="{r:.1f}" fill="{col}" opacity="{0.45 if i not in reparto else 0.9}"/>')
    for j in sol_ab:
        x, y = pts[j]
        out.append(f'<rect x="{x * s - 4:.1f}" y="{20 + y * s - 4:.1f}" width="8" height="8" fill="{cidx[j]}" stroke="#1c1917" stroke-width="1.2"/>')
    out.append("</svg>")
    return "".join(out)


H.append("<h3 id='c-mapas'>5.3 Mapas: bloques, comedores y asignación</h3><p>Cada círculo es un bloque, con tamaño según sus viviendas. Cada cuadrado es un comedor, y las líneas unen cada bloque con su comedor. En gris quedan las viviendas del diseminado servidas a domicilio.</p>")
for k, L in M.LOC.items():
    sol = L["sol"]
    H.append(f"<h4>{L['tip']['nombre']}</h4><div class='three'><div class='box'>{mapa(L, sol['abiertos'], sol['asign'], 'MILP óptimo', sol['reparto'])}</div>"
             f"<div class='box'>{mapa(L, *L['voraz_sol'], 'Voraz de cobertura')}</div><div class='box'>{mapa(L, *L['km_sol'], 'k-medias')}</div></div>")

# nacional
H.append(T(r"""<h3 id="c-nacional">5.4 Plan nacional de comedores</h3>
<p>Cada provincia se reparte en tres tipologías según su densidad (hab/km²): \(s_{\text{denso}}=\min(0{,}85,\max(0,(d-100)/900))\), \(s_{\text{rural}}=\min(0{,}6,\max(0{,}05,(150-d)/150))\) y el resto, medio. A cada tipología se le aplican las tasas del MILP: comedores por cada 1.000 viviendas, plazas por vivienda y porcentaje con reparto a domicilio.</p>
<div class="box"><table><thead><tr><th>Tipología</th><th>Comedores por 1.000 viviendas</th><th>Plazas por vivienda</th><th>Distancia media</th><th>Reparto a domicilio</th></tr></thead><tbody>[[TAS]]</tbody></table></div>""",
           TAS="".join(f"<tr><td>{M.TIPOLOGIAS[k]['nombre']}</td><td class='n'>{fa(t['com_por_mil'])}</td><td class='n'>{fa(t['plz_por_viv'])}</td><td class='n'>{f(t['dmed'])} m</td><td class='n'>{pct(t['rep'], 1)}</td></tr>" for k, t in M.TASA.items())))
H.append("<div class='box'><table><thead><tr><th>Provincia</th><th>Habitantes</th><th>hab/km²</th><th>Viviendas</th><th>% denso / medio / rural</th><th>Comedores</th><th>Plazas</th><th>Viviendas con reparto</th></tr></thead><tbody>")
for i in np.argsort(-M.POB):
    H.append(f"<tr><td><b>{M.PROV[i][0]}</b></td><td class='n'>{f(M.POB[i])}</td><td class='n'>{f(M.DENS[i])}</td><td class='n'>{f(M.VIV_PROV[i])}</td><td class='n'>{f(100 * M.SH[i, 0])} / {f(100 * M.SH[i, 1])} / {f(100 * M.SH[i, 2])}</td>"
             f"<td class='n'>{f(M.COM_PROV[i])}</td><td class='n'>{f(M.PLZ_PROV[i])}</td><td class='n'>{f(M.REP_PROV[i])}</td></tr>")
v_plz = lmB["v"][IX["PLZ"]]
H.append(f"<tr class='hl'><td><b>España</b></td><td class='n'>{f(M.POB.sum())}</td><td class='n'>{f(M.POB.sum() / M.SUP_TOTAL)}</td><td class='n'><b>{f(M.N_VIV)}</b></td><td></td><td class='n'><b>{f(M.COM_PROV.sum())}</b></td><td class='n'><b>{f(M.PLZ_PROV.sum())}</b></td><td class='n'>{f(M.REP_PROV.sum())}</td></tr></tbody></table></div>")
n_com = M.COM_PROV.sum()
rac = M.RACIONES * (M.N_VIV - M.REP_PROV.sum())
fte = (M.FIJO_COM * n_com + M.H_RACION * rac) / 1650
H.append(T("<div class='res'>España necesita <b>[[N]] comedores</b> con <b>[[P]] plazas</b>. Construirlos y equiparlos cuesta [[HC]] M de horas ([[VP]] h por plaza). Para servir [[RAC]] millones de raciones al año hacen falta <b>[[FTE]] personas</b> de cocina, sala y limpieza, a [[HR]] h por ración. Sustituyen a las [[HD]] M de horas al año de cocina doméstica del caso A.</div>",
           N=f(n_com), P=f(M.PLZ_PROV.sum()), HC=f(M.PLZ_PROV.sum() * v_plz / 1e6, 1), VP=f(v_plz), RAC=f(rac / 1e6), FTE=f(fte), HR=f(M.H_RAC_EF, 3),
           HD=f(opA["h_trabajo"] * M.N_VIV / 1e6)))

# =============================================================================
# 6. FÁBRICAS
# =============================================================================
H.append(T(r"""<h2 id="fabricas">6. Ubicación de las fábricas: localización y transporte de Kantorovich</h2>
<p>El plan recomendado industrializa el [[IND]] de las viviendas, con una media de [[VJ]] viajes de camión por vivienda. Cada fábrica produce 2.500 viviendas al año. ¿Cuántas fábricas hacen falta y dónde se ponen para minimizar la construcción, la plantilla fija y el transporte? Es el <b>problema de transporte</b> de Kantorovich (1942) combinado con la decisión de abrir fábricas.</p>
<div class="formula k">\[ \min\ \sum_j F_{\text{fab}}\,y_j + \sum_{i,j} c\,v\,d_{ij}\,x_{ij}\quad\text{s.a.}\quad \sum_j x_{ij}=D_i,\qquad \sum_i x_{ij}\le 2.500\,y_j,\qquad y_j\in\mathbb Z_{\ge0} \]
<p>\(D_i\): viviendas industrializadas al año en la provincia \(i\). \(d_{ij}\): km por carretera (gran círculo × 1,25, más una penalización en km equivalentes por los trayectos en barco a Baleares, Canarias, Ceuta y Melilla). \(c\) = [[HKM]] h por camión·km (conductor + gasóleo + μ·CO₂). \(F_{\text{fab}}\) = [[FF]] h/año por fábrica.</p></div>""",
           IND=pct(M.CUOTA_IND, 0), VJ=f(M.VIAJES_MED, 1), HKM=f(M.H_KM, 3), FF=f(M.FIJO_FAB)))
# mapa de España
W, Hh = 760, 560


def proj(lat, lon):
    if lon < -12:      # Canarias: recuadro
        lat, lon = lat + 7.0, lon + 8.5
    return (lon + 10) / 14.5 * W, (44.2 - lat) / 9.5 * Hh


svg = [f'<svg viewBox="0 0 {W} {Hh}" class="chart"><rect x="0" y="0" width="{W}" height="{Hh}" fill="#f8fafc"/>'
       f'<rect x="{proj(29.6, -18.3)[0]:.0f}" y="{proj(29.6, -18.3)[1]:.0f}" width="{proj(27.5, -13.2)[0] - proj(29.6, -18.3)[0]:.0f}" height="{proj(27.5, -13.2)[1] - proj(29.6, -18.3)[1]:.0f}" fill="none" stroke="#cbd5e1" stroke-dasharray="4 3"/>']
fl = M.FAB["flujo"]
for i in range(M.NP):
    for j in range(M.NP):
        if fl[i, j] > 1 and i != j:
            x1, y1 = proj(M.PROV[i][3], M.PROV[i][4]); x2, y2 = proj(M.PROV[j][3], M.PROV[j][4])
            svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#4338ca" stroke-width="{0.5 + fl[i, j] / 1500:.2f}" opacity="0.5"/>')
for i in range(M.NP):
    x, y = proj(M.PROV[i][3], M.PROV[i][4])
    svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{2 + math.sqrt(M.VIV_PROV[i]) / 25:.1f}" fill="#0e7490" opacity="0.35"/>')
    nf = M.FAB["y"][i]
    if nf:
        svg.append(f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="#be123c"/><text x="{x + 8:.1f}" y="{y + 4:.1f}" font-size="11" fill="#1c1917">{M.PROV[i][0]} ×{nf}</text>')
svg.append(f'<text x="{proj(29.6, -18.3)[0] + 4:.0f}" y="{proj(29.6, -18.3)[1] + 14:.0f}" class="tk">Canarias (desplazada)</text></svg>')
H.append("<div class='box'>" + "".join(svg) + "<div class='leg'><span style='background:#be123c'></span>fábricas (×n = número de fábricas)<span style='background:#0e7490'></span>viviendas por provincia<span style='background:#4338ca'></span>suministro desde otra provincia</div></div>")
H.append(T("<div class='res'><b>[[N]] fábricas en [[S]] provincias.</b> Las provincias pequeñas se abastecen desde las vecinas, y Baleares y Canarias tienen fábricas propias porque el barco sale caro. Recorren [[KM]] M de camión·km al año. Frente a una o más fábricas en cada provincia ([[NT]] fábricas), el óptimo ahorra [[AH]] h al año.</div>",
           N=int(M.FAB["y"].sum()), S=int((M.FAB["y"] > 0).sum()), KM=f(M.FAB["camion_km"] / 1e6, 1), NT=int(M.FAB_TODAS["y"].sum()),
           AH=f(M.FAB_TODAS["obj"] - M.FAB["obj"])))

# =============================================================================
# 7. TALLER Y OBRA
# =============================================================================
H.append(T(r"""<h2 id="taller">7. Taller y obra</h2>
<h3>Fábrica modular de 2.500 viviendas al año</h3>
<div class="formula t">\[ \text{takt}=\frac{3.450\ \text{h}\times60}{2.500\times[[MPV]]\ \text{módulos}} = [[TAKT]]\ \text{min por módulo},\qquad \text{operarios simultáneos}=\frac{[[HF]]\ \text{h}/[[MPV]]}{[[TAKT]]/60}\approx[[OP]] \]
<p>Unas [[EST]] estaciones de 16 personas en línea: bastidor de acero soldado por robot, forjado, tabiques, instalaciones, baño, carpinterías, acabados, prueba de estanqueidad y de instalaciones, y embalaje. Sale un módulo terminado cada [[TAKT]] minutos.</p></div>""",
           MPV=f(M.MOD_POR_VIV, 1), TAKT=f(M.TAKT_MOD_MIN, 1), HF=f(M.H_FAB_VIV), OP=f(M.H_FAB_VIV / M.MOD_POR_VIV / (M.TAKT_MOD_MIN / 60)),
           EST=math.ceil(M.H_FAB_VIV / M.MOD_POR_VIV / (M.TAKT_MOD_MIN / 60) / 16)))
for k, nom in (("trad", "Bloque de 40 viviendas: obra tradicional"), ("mod", "Bloque de 40 viviendas: modular 3D")):
    c = M.CPM[k]; TT = c["T"]
    rows = [f"<div class='box'><b>{nom}: {TT} días</b><div class='gantt'>"]
    for a in M.OBRA_CPM[k]:
        crit = c["H"][a[0]] == 0
        rows.append(f"<div class='row'><div class='lab'><b>{a[0]}</b> {a[1]}</div><div class='track'><span class='b {'crit' if crit else 'nc'}' style='left:{100 * c['ES'][a[0]] / 460:.2f}%;width:{100 * a[2] / 460:.2f}%'>{a[2]} d</span></div></div>")
    rows.append("</div></div>")
    H.append("".join(rows))
H.append(T("<p>El modular reduce el plazo de obra de [[T1]] a [[T2]] días (−[[R]]), porque la cimentación y la fabricación de los módulos van en paralelo. En rojo, la ruta crítica.</p>",
           T1=M.CPM["trad"]["T"], T2=M.CPM["mod"]["T"], R=pct(1 - M.CPM["mod"]["T"] / M.CPM["trad"]["T"], 0)))

# =============================================================================
# 8. A vs B
# =============================================================================
H.append(T(r"""<h2 id="avsb">8. Comparación: vivienda con cocina (A) frente a vivienda sin cocina con comedor (B)</h2>
<div class="box"><table><thead><tr><th>Por vivienda</th><th>Caso A</th><th>Caso B</th><th>Diferencia</th></tr></thead><tbody>
<tr class="sep"><td colspan="4">Construcción (plan recomendado)</td></tr>
<tr><td>Horas de construcción (B incluye [[PV]] plazas de comedor)</td><td class="n">[[VA]]</td><td class="n">[[VB]]</td><td class="n">[[DV]]</td></tr>
<tr><td>t CO₂ de construcción</td><td class="n">[[EA]]</td><td class="n">[[EB]]</td><td class="n">[[DE]]</td></tr>
<tr class="sep"><td colspan="4">Uso anual (2,5 personas, 3 comidas al día)</td></tr>
<tr><td>Horas de preparar comida (A: en casa; B: personal de comedor)</td><td class="n">[[HA]]</td><td class="n">[[HB]]</td><td class="n">[[DH]]</td></tr>
<tr><td>Horas de paseo al comedor (ida y vuelta)</td><td class="n">0</td><td class="n">[[PB]]</td><td class="n">+[[PB]]</td></tr>
<tr><td>Electricidad para cocinar, conservar y fregar (kWh)</td><td class="n">[[KA]]</td><td class="n">[[KB]]</td><td class="n">[[DK]]</td></tr>
<tr><td>Comida desperdiciada</td><td class="n">[[WA]]</td><td class="n">[[WB]]</td><td class="n">—</td></tr>
<tr class="sep"><td colspan="4">Para 1.000.000 de viviendas</td></tr>
<tr><td>Horas de construcción (millones)</td><td class="n">[[TVA]]</td><td class="n">[[TVB]]</td><td class="n">[[TDV]]</td></tr>
<tr><td>Horas anuales de preparar comida (millones)</td><td class="n">[[THA]]</td><td class="n">[[THB]]</td><td class="n">[[TDH]]</td></tr>
</tbody></table></div>
<div class="res">El caso B construye menos (sin cocina y con 8 m² menos por vivienda, a cambio de [[PV]] plazas de comedor) y, sobre todo, <b>libera [[LIB]] h al año por hogar</b> aun contando el paseo a medio valor, además de un [[RK]] de electricidad y la mitad del desperdicio de comida. Para 1.000.000 de hogares son <b>[[TLIB]] millones de horas al año</b>. A cambio, la planificación debe garantizar distancias cortas: con comedores a más de 400–500 m, el paseo se come la ventaja.</div>""",
           PV=f(plz_viv, 2), VA=f(vA), VB=f(vB), DV=f(vB - vA), EA=f(eA, 1), EB=f(eB, 1), DE=f(eB - eA, 1), HA=f(opA["h_trabajo"]), HB=f(opB["h_trabajo"]),
           DH=f(opB["h_trabajo"] - opA["h_trabajo"]), PB=f(opB["paseo"]), KA=f(opA["kwh"]), KB=f(opB["kwh"]), DK=f(opB["kwh"] - opA["kwh"]),
           WA=pct(opA["desperdicio"], 0), WB=pct(opB["desperdicio"], 0), TVA=f(vA * M.N_VIV / 1e6), TVB=f(vB * M.N_VIV / 1e6), TDV=f((vB - vA) * M.N_VIV / 1e6),
           THA=f(opA["h_trabajo"] * M.N_VIV / 1e6), THB=f(opB["h_trabajo"] * M.N_VIV / 1e6), TDH=f((opB["h_trabajo"] - opA["h_trabajo"]) * M.N_VIV / 1e6),
           LIB=f(hopA - hopB), RK=pct(1 - opB["kwh"] / opA["kwh"], 0), TLIB=f((hopA - hopB) * M.N_VIV / 1e6)))

H.append(r"""<h2 id="supuestos">9. Supuestos y límites</h2><ul>
<li><b>Datos ilustrativos</b>, con órdenes de magnitud del sector: materiales por m², horas de obra y de fábrica, población y superficie provinciales aproximadas. Están en <code>modelo_viviendas.py</code>; el documento se regenera con <code>python build_viviendas.py</code>.</li>
<li><b>Tipologías urbanas sintéticas</b>: los barrios de los mapas son generados, no reales. Para una ciudad concreta se sustituyen por los bloques del catastro y la red de calles real (distancias de red en vez de Manhattan).</li>
<li><b>Paseo valorado a la mitad</b> de una hora de trabajo (ω = 0,5). Con ω = 1 el algoritmo pone comedores aún más cerca; con ω = 0, solo minimiza personal y abre pocos y grandes.</li>
<li><b>Fuera del modelo</b>: suelo, licencias, financiación, la producción de los alimentos (igual en A y B) y la energía de calefacción y refrigeración de las viviendas.</li>
<li><b>Reparto territorial</b> proporcional a la población. Si se quiere priorizar zonas tensionadas, basta cambiar el vector de demanda por provincia.</li>
</ul></main></body></html>""")

html = "\n".join(H)
with open("planificacion_viviendas.html", "w", encoding="utf-8") as fh:
    fh.write(html)
print("OK", len(html))
