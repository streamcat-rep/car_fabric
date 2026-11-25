"""Genera planificacion_ordenadores.html a partir de modelo_ordenadores.py"""
import math
import numpy as np
import modelo_ordenadores as M

IX, A_, NOMBRE, UNIDAD, ESC = M.IX, M.A_, M.NOMBRE, M.UNIDAD, M.ESC
COL_ESC = {"Extracción": "#a16207", "Energía": "#b45309", "Materiales": "#0e7490", "Obleas": "#7c3aed",
           "Componentes": "#4338ca", "Productos": "#be123c", "Infraestructura CPD": "#15803d", "Servicio": "#57534e"}


def f(x, d=0):
    s = f"{x:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return "0" if s.lstrip("-").strip("0,") == "" else s


def fa(x):
    ax = abs(x)
    if ax >= 1000: return f(x, 0)
    if ax >= 100: return f(x, 1)
    if ax >= 1: return f(x, 2)
    if ax >= 0.01: return f(x, 3)
    if ax >= 0.0001: return f(x, 5)
    return f(x, 7) if ax > 0 else "0"


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


CORTO = {"ace_bof": "acero alto horno", "ace_eaf": "acero con chatarra", "alu_p": "Al primario", "alu_s": "Al reciclado",
         "cob_p": "cobre primario", "cob_s": "cobre reciclado", "ele_t": "electricidad térmica", "ele_r": "electricidad renovable",
         "psi_s": "polisilicio Siemens", "psi_f": "polisilicio FBR", "cpd_m": "CPU monolítica", "cpd_c": "CPU de chiplets",
         "gpc_m": "GPU monolítica", "gpc_c": "GPU de chiplets", "psu": "fuente de silicio", "psu_g": "fuente GaN",
         "caj_a": "caja de acero", "caj_l": "caja de aluminio", "ref_ch": "enfriadoras", "ref_ad": "aire adiabático", "ref_lq": "líquida directa"}


def mezcla_html(mz):
    return "<br>".join(" + ".join(f"{pct(w, 0)} {CORTO.get(t, t)}" if w < 0.999 else CORTO.get(t, t) for t, w in p) for g, p in mz)


H = []
H.append(r"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Planificación de la producción de ordenadores y de un centro de datos 24/7/365 — Leontief, Kantorovich y método del taller</title>
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
.chip{display:inline-block;font-size:10.5px;padding:0 7px;border-radius:999px;border:1px solid var(--c);color:var(--c);white-space:nowrap}
.ok{color:var(--ok);font-weight:600}.no{color:var(--red);font-weight:600}.warn{color:var(--warn);font-weight:600}
.leg{font-size:12.5px;color:var(--mut);margin-top:6px}.leg span{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 4px 0 12px;vertical-align:middle}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}@media (max-width:1100px){.two{grid-template-columns:1fr}}
.ficha-cab{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:10px;margin:12px 0}
.ficha-cab div{background:#f5f5f4;border-radius:8px;padding:8px 12px;font-size:13px}.ficha-cab b{display:block;font-size:19px}
td.tree{white-space:nowrap}
.gantt .row{display:flex;align-items:center;gap:8px;font-size:12.5px;margin:4px 0}.gantt .lab{width:380px;flex-shrink:0}
.gantt .track{flex:1;position:relative;height:20px;background:#f5f5f4;border:1px solid var(--line);border-radius:4px}
.gantt .b{position:absolute;top:2px;bottom:2px;border-radius:3px;color:#fff;font-size:11px;display:flex;align-items:center;justify-content:center}
.gantt .crit{background:var(--red)}.gantt .nc{background:#78716c}
svg.chart{width:100%;height:auto}svg .grid{stroke:#e7e5e4}svg .tk{font-size:11px;fill:#78716c}svg .ax{font-size:12px;fill:#57534e}
code{font-family:ui-monospace,Menlo,monospace;font-size:13px;background:#f5f5f4;padding:1px 5px;border-radius:4px}
</style></head><body>""")

nav = ["<nav><b>Índice</b>", "<a href='#resumen'>Resumen</a>", "<a href='#metodo'>1. Qué se planifica y cómo</a>",
       "<a href='#tecnicas'>2. Técnicas y su comparación</a>", "<a href='#fichas'>3. Producción de cada ordenador</a>"]
for g in M.PRODUCTOS:
    nav.append(f"<a class='sub' href='#f-{g}'>{NOMBRE[g]}</a>")
nav += ["<a href='#cpd'>4. Centro de datos de 50 MW</a>", "<a class='sub' href='#cpd-comp'>4.1 Composición</a>",
        "<a class='sub' href='#cpd-ref'>4.2 Refrigeración (Kantorovich)</a>", "<a class='sub' href='#cpd-obra'>4.3 Construcción</a>",
        "<a class='sub' href='#cpd-247'>4.4 Operación 24/7/365</a>", "<a class='sub' href='#cpd-equipos'>4.5 Fabricación de los equipos de energía</a>",
        "<a class='sub' href='#cpd-anual'>4.6 Necesidades anuales</a>", "<a class='sub' href='#cpd-total'>4.7 Totales: materiales, horas y agua</a>", "<a href='#agregado'>5. Plan agregado</a>",
        "<a href='#supuestos'>6. Supuestos</a></nav>"]
H.append("\n".join(nav) + "<main>")

# =============================================================================
# RESUMEN
# =============================================================================
fo, fg = M.FICHAS["PCO"], M.FICHAS["PCG"]
fs, fgp = M.FICHAS["SRV"], M.FICHAS["SGP"]
do, dr = M.DESP["opt"], M.DESP["red"]
H.append(T(r"""<h1>Planificación de la producción de ordenadores y de un centro de datos funcionando 24/7/365</h1>
<p class="lead">Ordenadores de oficina, ordenadores gaming y un centro de datos (CPD) de <b>50 MW de TI</b>: 30 MW de servidores CPU y 20 MW de servidores GPU. Para cada producto: la <b>descomposición en piezas hasta la oblea de silicio y la mina</b>, con horas, energía, agua y CO₂ de cada pieza (Leontief); la <b>comparación de técnicas y procesos de fabricación</b> y la máxima producción (Kantorovich); y la <b>organización del taller</b>. Para el CPD, además: su construcción y su <b>operación continua durante las 8.760 horas del año</b>, con la fabricación de los paneles, aerogeneradores, baterías, turbinas y grupos electrógenos que la hacen posible.</p>
<div class="kpis">
<div class="kpi"><div class="v">[[HPCO]] h</div><div class="l">trabajo total por PC de oficina ([[EPCO]] h de montaje final)</div></div>
<div class="kpi"><div class="v">[[HPCG]] h</div><div class="l">trabajo total por PC gaming ([[EPCG]] h de montaje)</div></div>
<div class="kpi"><div class="v">[[HSGP]] h</div><div class="l">trabajo total por servidor de 8 GPU</div></div>
<div class="kpi"><div class="v">[[EANUAL]] MWh</div><div class="l">electricidad anual del CPD (PUE [[PUE]], refrigeración líquida)</div></div>
<div class="kpi"><div class="v">[[REN]]</div><div class="l">de esa energía es fotovoltaica + eólica en el plan recomendado; CO₂ −[[REDCO2]] frente a tomarla toda de la red</div></div>
<div class="kpi"><div class="v">[[TCPD]] días</div><div class="l">construcción del CPD (camino crítico: transformadores)</div></div>
</div>""", HPCO=fa(fo["met"]["comp"]["h_ud"]), EPCO=fa(fo["met"]["comp"]["ens"]), HPCG=fa(fg["met"]["comp"]["h_ud"]),
           EPCG=fa(fg["met"]["comp"]["ens"]), HSGP=f(fgp["met"]["comp"]["h_ud"]), EANUAL=f(do["e_tot"]), PUE=f(M.PUE_OPT, 2),
           REN=pct((do["fv"] + do["eol"]) / do["e_tot"], 0), REDCO2=pct(1 - do["co2"] / dr["co2"], 0), TCPD=M.T_CPD))

# =============================================================================
# 1. MÉTODO
# =============================================================================
H.append(r"""<h2 id="metodo">1. Qué se planifica y cómo</h2>
<div class="box"><table><thead><tr><th>Producto</th><th>Cantidad del plan</th><th>Para qué</th></tr></thead><tbody>
<tr><td>PC de oficina</td><td class="n">1.000.000 / año</td><td>Puesto de trabajo: CPU de 8 núcleos, 16 GB, SSD de 512 GB, fuente de 300 W</td></tr>
<tr><td>PC gaming</td><td class="n">250.000 / año</td><td>CPU de 8 núcleos, tarjeta gráfica de 16 GB, 32 GB, SSD de 2 TB, fuente de 850 W, refrigeración líquida</td></tr>
<tr><td>Servidor CPU</td><td class="n">30.000 (parque inicial) · 6.000 / año de reposición</td><td>2 CPU de 96 núcleos, 512 GB, 4 SSD de 3,84 TB; 1 kW</td></tr>
<tr><td>Servidor GPU</td><td class="n">2.000 (parque inicial) · 500 / año de reposición</td><td>8 aceleradores con 80 GB de HBM, 2 CPU, 2 TB de memoria; 10 kW</td></tr>
<tr><td>Centro de datos</td><td class="n">50 MW TI, 24/7/365</td><td>Edificio, refrigeración, transformadores, SAI 2N, grupos diésel N+2, abastecimiento eléctrico horario</td></tr>
</tbody></table></div>
<div class="formula"><div class="tt">Las tres herramientas (desarrolladas paso a paso en planificacion_integral.html, §1)</div>
\[ \textbf{Leontief:}\ \ \mathbf x=(I-A)^{-1}\mathbf y,\qquad \mathbf v^{\top}=\mathbf l^{\top}(I-A)^{-1}\ (\text{horas}),\qquad \boldsymbol\varepsilon^{\top}=\mathbf d^{\top}(I-A)^{-1}\ (\text{CO}_2),\qquad e_j = L_{\text{ELE},j},\ \ w_j=L_{\text{AGUA},j} \]
\[ \textbf{Kantorovich:}\ \ \min_{\mathbf z\ge0}\ \mathbf h^{\top}\mathbf z+\mu\,\mathbf c^{\top}\mathbf z\ \ \text{s.a.}\ \ B\mathbf z\ge\mathbf y,\ \text{cuotas de reciclado};\qquad \max\ \lambda\ \ \text{s.a.}\ \ \textstyle\sum_{p\in k}x_p\ge n_k\lambda,\ \ \sum_p u_{rp}x_p\le R_r \]
\[ \textbf{Taller:}\ \ \text{takt}=\frac{3.450\ \text{h}}{q},\qquad \text{puestos}=\left\lceil\frac{l_j}{\text{takt}}\right\rceil,\qquad \text{operarios}=\frac{l_j\,q}{1.650} \]
<p>μ = 3 h de trabajo por tonelada de CO₂ (≈ 75 €/t a 25 €/h). La matriz tiene 56 bienes y 69 actividades. \(\rho(A)=\) """ + f(M.RHO, 3) + r""" &lt; 1.</p></div>
<p><b>Por qué los chips dominan.</b> Un chip avanzado se hace en una oblea de 300 mm que pasa por unos 80 niveles de máscara y consume ≈1,5 MWh de electricidad y 9 m³ de agua ultrapura. Por eso la clave es <b>cuántos chips buenos salen de cada oblea</b>: depende del área del dado y del rendimiento de fabricación.</p>
<div class="formula t">\[ \text{dados por oblea}\approx\frac{\pi (D/2)^2}{S}-\frac{\pi D}{\sqrt{2S}},\qquad \text{rendimiento } Y = e^{-D_0 S},\qquad \text{obleas por chip bueno}=\frac{1}{\text{dados}\cdot Y} \]
<p>Para una oblea de 300 mm y una densidad de defectos \(D_0\approx 0{,}1\ \text{cm}^{-2}\): un dado de 200 mm² da ≈320 dados y un rendimiento del 82 %, unas 250 CPU buenas por oblea. Uno de 800 mm² (acelerador de CPD) da ≈64 dados y un 45–55 %, unos 35 buenos. Por eso los <b>chiplets</b> (varios dados pequeños) ahorran oblea avanzada.</p></div>""")

# =============================================================================
# 2. TÉCNICAS
# =============================================================================
H.append("<h2 id='tecnicas'>2. Técnicas de producción y su comparación</h2><p>Cuando un bien tiene varias filas, son métodos alternativos. La primera es la técnica base que usa Leontief.</p><div class='box'><table><thead><tr><th>Bien</th><th>Actividad</th><th>Insumos por unidad</th><th>Horas directas</th><th>CO₂ directo (t)</th><th>Nota</th></tr></thead><tbody>")
ult = None
for k, a in enumerate(A_):
    e = ESC[a["bien"]]
    if e != ult:
        H.append(f"<tr class='sep'><td colspan='6'>{e}</td></tr>"); ult = e
    alt = sum(1 for b in A_ if b["bien"] == a["bien"]) > 1
    ins = ", ".join(f"{fa(q)} {UNIDAD[g]} {NOMBRE[g].lower()}" for g, q in a["ins"].items()) or "—"
    marca = "" if not alt else (" <span class='mut'>(base)</span>" if M.BASE[a["bien"]] == k else " <span class='warn'>(alternativa)</span>")
    H.append(f"<tr><td><b>{a['bien']}</b> <span class='mut'>{UNIDAD[a['bien']]}</span></td><td>{a['nombre']}{marca}</td><td>{ins}</td><td class='n'>{fa(a['h'])}</td><td class='n'>{fa(M.C[k])}</td><td class='mut'>{a['nota']}</td></tr>")
H.append("</tbody></table></div>")
H.append(r"""<div class="formula k">\[ v_k = h_k+\sum_i v_i a_{ik},\quad \varepsilon_k=c_k+\sum_i\varepsilon_i a_{ik},\quad \alpha_k=\frac{v_k-v_{\text{base}}}{\varepsilon_{\text{base}}-\varepsilon_k}\ \ (\text{h por t CO}_2\text{ evitada}) \]</div>
<div class="box"><table><thead><tr><th>Bien</th><th>Técnica</th><th>Horas/ud</th><th>t CO₂/ud</th><th>MWh/ud</th><th>\(\alpha\) h/t</th><th>Veredicto (μ = 3)</th></tr></thead><tbody>""")
for g in [b[0] for b in M.BIENES]:
    ks = [k for k, a in enumerate(A_) if a["bien"] == g]
    if len(ks) < 2 or g == "CPDS":
        continue
    vals = {k: (A_[k]["h"] + sum(q * M.v0[IX[i]] for i, q in A_[k]["ins"].items()), M.C[k] + sum(q * M.e0[IX[i]] for i, q in A_[k]["ins"].items()),
                A_[k]["ins"].get("ELE", 0) + sum(q * M.L0[IX["ELE"], IX[i]] for i, q in A_[k]["ins"].items() if i != "ELE")) for k in ks}
    b = M.BASE[g]
    for k in ks:
        v, e, el = vals[k]
        if k == b:
            ver, al = "<span class='mut'>base</span>", "—"
        else:
            dv, de = v - vals[b][0], e - vals[b][1]
            if dv <= 0 and de <= 0: ver, al = "<span class='ok'>dominante</span>", "—"
            elif dv >= 0 and de >= 0: ver, al = "<span class='no'>dominada</span>", "—"
            else:
                a_ = dv / -de
                ver = "<span class='ok'>compensa</span>" if a_ <= M.MU_CO2 else "<span class='warn'>no compensa</span>"
                al = f(a_, 2)
        H.append(f"<tr><td><b>{g}</b></td><td>{A_[k]['nombre']}</td><td class='n'>{fa(v)}</td><td class='n'>{fa(e)}</td><td class='n'>{fa(el)}</td><td class='n'><b>{al}</b></td><td>{ver}</td></tr>")
H.append("</tbody></table></div>")

# =============================================================================
# 3. FICHAS
# =============================================================================
DESC = {"PCO": "Ordenador de sobremesa para oficina. Se fabrica en una planta de 1.000.000 al año.",
        "PCG": "Ordenador gaming montado bajo pedido. Planta de 250.000 al año.",
        "SRV": "Servidor de 2 sockets para el CPD. 30.000 para el parque inicial; 6.000 al año de reposición (vida de 5 años).",
        "SGP": "Servidor de entrenamiento e inferencia de IA con 8 aceleradores. 2.000 para el parque inicial (16.000 GPU); 500 al año de reposición (vida de 4 años)."}
NOTA = {"PCO": "Casi el 60 % del trabajo y del CO₂ está en la <b>placa base y los chips</b> (CPU, DRAM y SSD). La placa sola supone un tercio, por sus chips de nodo maduro y su soldadura. El montaje final es solo el 16 %. El método recomendado mantiene la CPU monolítica, porque con 200 mm² el rendimiento de oblea ya es alto, y cambia a fuente GaN y electricidad renovable.",
        "PCG": "La tarjeta gráfica (chip de 380 mm² y 16 GB de GDDR) es el componente que más pesa. Los chiplets reducen la oblea avanzada pero añaden encapsulado: solo compensan si se busca el mínimo CO₂ a cualquier coste en horas.",
        "SRV": "La memoria manda: 512 GB de DRAM y 15 TB de NAND suponen más obleas que las dos CPU. Ampliar memoria es lo que más trabajo incorporado añade a un servidor.",
        "SGP": "Cada servidor GPU incorpora 8 dados de 800 mm² (≈0,23 obleas avanzadas), 2 TB de memoria HBM/DRAM y encapsulado 2,5D. Es el producto con más horas y más agua por unidad: 1 servidor GPU equivale a unos 60 PC de oficina en horas."}
CREW = {"PCO": 1, "PCG": 1, "SRV": 2, "SGP": 3}
H.append(r"""<h2 id="fichas">3. Producción de cada ordenador</h2>
<p>Cada ficha: <b>(a)</b> qué es y cuánto; <b>(b)</b> <b>descomposición en piezas</b>, nivel a nivel, con la necesidad productiva de cada pieza (cantidad, horas, energía, agua y CO₂) por unidad y para el plan; <b>(c)</b> la cadena completa hasta la mina (Leontief); <b>(d)</b> los métodos comparados con Kantorovich y la máxima producción; <b>(e)</b> los procesos de fabricación (juegos completos); <b>(f)</b> el taller.</p>""")

for g in M.PRODUCTOS:
    fi = M.FICHAS[g]; q = fi["q"]; met = fi["met"]; mb, mr = met["base"], met["comp"]
    H.append(f"<h3 id='f-{g}'>3.{M.PRODUCTOS.index(g) + 1} {NOMBRE[g]}</h3><h4>(a) Qué es y cuánto se produce</h4><p>{DESC[g]}</p>")
    H.append(f"<div class='ficha-cab'><div>Producción del plan<b>{f(q)}</b></div><div>Montaje final<b>{fa(mr['ens'])} h/ud</b></div>"
             f"<div>Trabajo total (recomendado)<b>{fa(mr['h_ud'])} h/ud</b></div><div>Electricidad de toda la cadena<b>{fa(mr['e_ud'] * 1000)} kWh/ud</b></div>"
             f"<div>Agua<b>{fa(mr['agua_ud'] * 1000)} L/ud</b></div><div>CO₂ base → recomendado<b>{fa(mb['c_ud'] * 1000)} → {fa(mr['c_ud'] * 1000)} kg</b></div></div>")
    # (b) árbol
    H.append("<h4>(b) Descomposición en piezas y necesidad productiva de cada una</h4>"
             "<p>Lista de materiales multinivel con la receta base. Cada fila es una pieza o material con su cantidad por unidad de producto y para todo el plan. Las horas, la electricidad, el agua y el CO₂ son los <i>incorporados</i>: incluyen toda la cadena que hay debajo de esa pieza. La columna «montaje propio» es el trabajo directo de fabricar esa pieza a partir de sus subpiezas.</p>")
    rows = ["<div class='box'><table><thead><tr><th>Pieza / material</th><th>Por unidad</th><th>Plan</th><th>Montaje propio (h)</th><th>Horas incorporadas</th><th>Electricidad (kWh)</th><th>Agua (L)</th><th>CO₂ (kg)</th><th></th></tr></thead><tbody>"]
    tree = M.arbol(g, 1.0)
    hmax = tree[0]["h"]
    for n in tree:
        sangria = "&nbsp;" * 5 * n["nivel"] + ("└ " if n["nivel"] else "")
        cls = " class='hl'" if n["nivel"] == 0 else ""
        rows.append(f"<tr{cls}><td class='tree'>{sangria}{chip(ESC[n['g']])} {NOMBRE[n['g']]}</td>"
                    f"<td class='n'>{fa(n['q'])} {UNIDAD[n['g']]}</td><td class='n'>{fa(n['q'] * q)} {UNIDAD[n['g']]}</td>"
                    f"<td class='n'>{fa(n['ens'])}</td><td class='n'><b>{fa(n['h'])}</b></td><td class='n'>{fa(n['ele'] * 1000)}</td>"
                    f"<td class='n'>{fa(n['agu'] * 1000)}</td><td class='n'>{fa(n['c'] * 1000)}</td><td class='w'>{bar(n['h'], hmax, COL_ESC[ESC[n['g']]])}</td></tr>")
    rows.append("</tbody></table></div>")
    H.append("".join(rows))
    # (c) cadena completa
    H.append("<h4>(c) Cadena completa hasta la mina (columna de Leontief)</h4>")
    j = IX[g]
    req, reqo = M.L0[:, j], mr["lm"]["L"][:, j]
    rows = ["<div class='box'><table><thead><tr><th>Bien</th><th>Por unidad (base)</th><th>Plan (base)</th><th>Por unidad (recomendado)</th><th>Plan (recomendado)</th></tr></thead><tbody>"]
    ult = None
    for i in sorted(range(M.NB), key=lambda i: (M.ESCALONES.index(ESC[M.COD[i]]) if ESC[M.COD[i]] in M.ESCALONES else 9, i)):
        c_ = M.COD[i]
        if c_ in ("CPDS", g) or ESC[c_] in ("Componentes", "Productos", "Infraestructura CPD") or (req[i] < 1e-9 and reqo[i] < 1e-9):
            continue
        if ESC[c_] != ult:
            rows.append(f"<tr class='sep'><td colspan='5'>{ESC[c_]}</td></tr>"); ult = ESC[c_]
        rows.append(f"<tr><td>{NOMBRE[c_]} <span class='mut'>({UNIDAD[c_]})</span></td><td class='n'>{fa(req[i])}</td><td class='n'>{fa(req[i] * q)}</td><td class='n'>{fa(reqo[i])}</td><td class='n'>{fa(reqo[i] * q)}</td></tr>")
    rows.append("</tbody></table></div>")
    H.append("".join(rows))
    # (d) métodos
    H.append("<h4>(d) Métodos de producción comparados con Kantorovich</h4><div class='box'><table><thead><tr><th>Método</th><th>Técnicas elegidas</th><th>Horas/ud</th><th>kg CO₂/ud</th><th>kWh/ud</th><th>Producción con las mismas horas</th></tr></thead><tbody>")
    for key, m in met.items():
        r_ = mb["h_ud"] / m["h_ud"]
        H.append(f"<tr{' class=rec' if key == 'comp' else ''}><td><b>{m['nombre']}</b></td><td>{mezcla_html(m['mezcla'])}</td><td class='n'>{fa(m['h_ud'])}</td>"
                 f"<td class='n'>{fa(m['c_ud'] * 1000)}</td><td class='n'>{fa(m['e_ud'] * 1000)}</td><td class='n'>{f(q * r_)} <span class='mut'>({'+' if r_ >= 1 else ''}{pct(r_ - 1, 1)})</span></td></tr>")
    H.append("</tbody></table></div>")
    mh, mc = met["h"], met["c"]
    H.append(T("<div class='res'><b>Máxima producción</b>: el método de mínimo trabajo da [[QH]] unidades con las horas del método base ([[G]]). <b>Mínimo CO₂</b>: [[CC]] kg/ud (−[[RC]]). <b>Recomendado</b>: [[CR]] kg/ud con [[HR]] h/ud.</div>",
               QH=f(q * mb["h_ud"] / mh["h_ud"]), G="+" + pct(mb["h_ud"] / mh["h_ud"] - 1, 1), CC=fa(mc["c_ud"] * 1000),
               RC=pct(1 - mc["c_ud"] / mb["c_ud"], 0), CR=fa(mr["c_ud"] * 1000), HR=fa(mr["h_ud"])))
    H.append(f"<p>{NOTA[g]}</p>")
    # (e) procesos
    if g in M.PLANTAS:
        pl, r = M.PLANTAS[g], M.JUEGOS[g]
        o = r["opt"]; recs = pl["recursos"]
        H.append(f"<h4>(e) Procesos de fabricación: juegos completos de Kantorovich</h4><p>{pl['nombre']}. Cada pieza o etapa se puede hacer con varios procesos; el programa lineal reparte la producción entre ellos para sacar el máximo de productos completos con las máquinas y operarios disponibles.</p>")
        H.append("<div class='box'><table><thead><tr><th>Etapa</th><th>Proceso</th><th>Datos físicos</th>" + "".join(f"<th>{recs[x][0].split('(')[0]}</th>" for x in recs) + "<th>Unidades/año en el óptimo</th></tr></thead><tbody>")
        for p, pr in enumerate(pl["procesos"]):
            x = o["x"][p]
            H.append(f"<tr{' class=rec' if x > 1e-6 else ''}><td><b>{next(n for k, n, _ in pl['piezas'] if k == pr[0])}</b></td><td>{pr[1]}</td><td class='mut'>{pr[3]}</td>"
                     + "".join(f"<td class='n'>{fa(pr[2][x_]) if x_ in pr[2] else '—'}</td>" for x_ in recs) + f"<td class='n'><b>{f(x) if x > 1e-6 else '0'}</b></td></tr>")
        H.append("</tbody></table></div><div class='two'><div class='box'><table><tbody>"
                 f"<tr><td>Todo con el proceso tradicional</td><td class='n'>{f(r['trad']['lam'])}</td></tr><tr><td>Todo con el proceso nuevo</td><td class='n'>{f(r['nuevo']['lam'])}</td></tr>"
                 f"<tr class='rec'><td><b>Mezcla óptima</b></td><td class='n'><b>{f(o['lam'])}</b></td></tr></tbody></table></div>"
                 "<div class='box'><table><thead><tr><th>Recurso</th><th>Usado / disponible</th><th>Multiplicador (ud extra por unidad de recurso)</th></tr></thead><tbody>"
                 + "".join(f"<tr><td>{recs[x][0]}</td><td class='n'>{f(o['uso'][x])} / {f(recs[x][2])}</td><td class='n'>{('<b>' + fa(o['dual'][x]) + '</b>') if o['dual'][x] > 1e-9 else '0 (sobra)'}</td></tr>" for x in recs)
                 + "</tbody></table></div></div>")
    # (f) taller
    tk = fi["takt_s"]
    H.append("<h4>(f) Organización del taller</h4>" + T(
        "<p>Takt = 3.450 h / [[Q]] = <b>[[TK]]</b>. Montaje final de [[L]] h/ud → <b>[[P]] puestos simultáneos</b> ([[ORG]]). Plantilla de montaje: [[OP]] operarios-año.</p>",
        Q=f(q), TK=(f(tk, 1) + " s") if tk < 600 else (f(tk / 60, 0) + " min"), L=fa(mr["ens"]), P=f(fi["puestos"]),
        ORG="línea en cadena" if tk < 60 else ("células y línea por estaciones" if tk < 3600 else "células de integración por equipos"),
        OP=f(fi["operarios"], 0)))

# =============================================================================
# 4. CPD
# =============================================================================
zc = M.CPD["comp"]["z"]
lmc = M.leontief_mezcla(zc)
stock = {"SRV": M.CPU_MW * M.SRV_POR_MW, "SGP": M.GPU_MW * M.SGP_POR_MW, "RCK": M.RCK_POR_MW * M.MW_TI, "EDI": M.MW_TI, "REF": M.MW_TI,
         "TRF": 1.25 * M.PUE_OPT * M.MW_TI, "UPS": 2 * M.MW_TI, "GEN": M.N_GEN, "FV": do["S"], "EOL": do["W"], "BES": do["E"],
         "TGS": math.ceil(do["G"] / 10 - 1e-6) + (1 if do["G"] > 0.5 else 0)}
H.append(T(r"""<h2 id="cpd">4. Centro de datos de 50 MW</h2>
<h3 id="cpd-comp">4.1 Composición: qué hay que producir para un CPD de 50 MW</h3>
<div class="formula">\[ N_{\text{srv}}=\frac{30\ \text{MW}}{1\ \text{kW}}=30.000,\quad N_{\text{gpu}}=\frac{20\ \text{MW}}{10\ \text{kW}}=2.000,\quad \text{racks}=30\cdot34+20\cdot25=[[RCK]],\quad P_{\text{instalación}}=P_{\text{TI}}\cdot u\cdot\text{PUE}=50\cdot0{,}8\cdot[[PUE]]=[[PI]]\ \text{MW} \]
\[ \text{SAI 2N}=2\cdot 50=100\ \text{MW},\qquad \text{grupos N+2}=\left\lceil\frac{P_{\text{pico}}}{3\ \text{MW}}\right\rceil+2=[[NG]],\qquad \text{gasóleo para 48 h}=P_{\text{pico}}\cdot48\cdot0{,}25=[[DIE]]\ \text{t} \]</div>""",
           RCK=f(stock["RCK"]), PUE=f(M.PUE_OPT, 2), PI=f(M.MW_TI * M.UTIL_TI * M.PUE_OPT, 1), NG=M.N_GEN, DIE=f(M.DIESEL_48H)))
rows = ["<div class='box'><table><thead><tr><th>Producto</th><th>Cantidad</th><th>Equivale a</th><th>Montaje / obra por ud (h)</th><th>Horas totales por ud</th><th>Horas totales del parque</th><th>CO₂ del parque (t)</th></tr></thead><tbody>"]
equiv = {"FV": lambda x: f"{f(x * 1820)} módulos de 550 W", "EOL": lambda x: f"{math.ceil(x / 5)} aerogeneradores de 5 MW",
         "BES": lambda x: f"{f(x / 4, 0)} MW durante 4 h", "TGS": lambda x: f"{int(x)} turbinas de 10 MW" if x else "ninguna",
         "GEN": lambda x: f"{f(x * 3)} MW de respaldo", "TRF": lambda x: f"{math.ceil(x / 2.5)} transformadores de 2,5 MVA",
         "SGP": lambda x: f"{f(x * 8)} aceleradores", "SRV": lambda x: f"{f(x * 192)} núcleos", "UPS": lambda x: "2N",
         "RCK": lambda x: "", "EDI": lambda x: f"{f(x * 110)} m² de sala", "REF": lambda x: "líquida directa"}
th = tc = 0
for g, n in stock.items():
    j = IX[g]
    vv, ee = lmc["v"][j], lmc["e"][j]
    th += n * vv; tc += n * ee
    rows.append(f"<tr><td>{chip(ESC[g])} <b>{NOMBRE[g]}</b></td><td class='n'>{fa(n)} {UNIDAD[g]}</td><td class='mut'>{equiv[g](n)}</td><td class='n'>{fa(lmc['l'][j])}</td>"
                f"<td class='n'>{fa(vv)}</td><td class='n'>{f(n * vv)}</td><td class='n'>{f(n * ee)}</td></tr>")
rows.append(f"<tr class='hl'><td><b>Total para construir y equipar el CPD</b></td><td></td><td></td><td></td><td></td><td class='n'><b>{f(th)}</b></td><td class='n'><b>{f(tc)}</b></td></tr></tbody></table></div>")
H.append("".join(rows))
H.append(T("<p>Construir y equipar el CPD con su planta de energía incorpora <b>[[TH]] millones de horas</b> de trabajo (≈ [[FTE]] personas-año). Las partidas mayores son la planta fotovoltaica, los 30.000 servidores CPU y el edificio. Por unidad, el servidor GPU es con diferencia el producto más intensivo: 2.000 unidades suponen tantas horas como medio parque eólico.</p>",
           TH=f(th / 1e6, 1), FTE=f(th / 1650)))
# descomposición de los equipos de infraestructura
H.append("<h4>Descomposición de los equipos de infraestructura</h4><div class='box'><table><thead><tr><th>Equipo</th><th>Receta directa</th><th>Horas totales</th><th>Electricidad (MWh)</th><th>t CO₂</th></tr></thead><tbody>")
for g in ["EDI", "REF", "TRF", "UPS", "GEN", "TGS", "FV", "EOL", "BES", "RCK"]:
    k = M.BASE[g] if g != "REF" else M.ID[M.REF_OPT]
    a = A_[k]; j = IX[g]
    H.append(f"<tr><td><b>{a['nombre']}</b></td><td>{', '.join(f'{fa(q)} {UNIDAD[i]} {NOMBRE[i].lower()}' for i, q in a['ins'].items())}; <b>{fa(a['h'])} h de montaje u obra</b></td>"
             f"<td class='n'>{fa(lmc['v'][j])}</td><td class='n'>{fa(lmc['L'][IX['ELE'], j])}</td><td class='n'>{fa(lmc['e'][j])}</td></tr>")
H.append("</tbody></table></div>")

# 4.2 refrigeración
H.append(r"""<h3 id="cpd-ref">4.2 Método de refrigeración: comparación con Kantorovich</h3>
<p>El «producto» del CPD es <b>1 MW de TI funcionando un año</b>. Cada sistema de refrigeración es un método distinto de producirlo: cambia el PUE (energía total / energía de TI), el agua y los equipos.</p>
<div class="formula k">\[ E_{\text{año}} = 8.760\cdot u\cdot P_{\text{TI}}\cdot\text{PUE},\qquad W_{\text{año}} = 8.760\cdot u\cdot P_{\text{TI}}\cdot \text{WUE},\qquad \min\ \mathbf h^{\top}\mathbf z+\mu\,\mathbf c^{\top}\mathbf z\ \ \text{s.a.}\ \ B\mathbf z\ge 50\,\mathbf e_{\text{CPD}} \]</div>
<div class="box"><table><thead><tr><th>Refrigeración</th><th>PUE</th><th>Electricidad MWh/MW·año</th><th>Agua m³/MW·año</th><th>Horas/MW·año (todo incluido)</th><th>t CO₂/MW·año</th><th>Coste social</th></tr></thead><tbody>""")
for rid, sol in M.CPD_REF.items():
    k = M.ACT_CPD[rid]
    H.append(f"<tr{' class=rec' if rid == M.REF_OPT else ''}><td><b>{A_[M.ID[rid]]['nombre']}</b></td><td class='n'>{f(M.PUE[rid], 2)}</td><td class='n'>{f(A_[k]['ins']['ELE'])}</td>"
             f"<td class='n'>{f(A_[k]['ins']['AGU'])}</td><td class='n'>{f(sol['horas'] / M.MW_TI)}</td><td class='n'>{fa(sol['co2'] / M.MW_TI)}</td><td class='n'>{f((sol['horas'] + M.MU_CO2 * sol['co2']) / M.MW_TI)}</td></tr>")
H.append("</tbody></table></div>")
H.append(T("<div class='res'>La <b>refrigeración líquida directa</b> gana en las tres cosas: con PUE [[P]] ahorra [[AH]] MWh al año por MW frente a las enfriadoras, gasta casi nada de agua y necesita menos horas totales, porque la energía ahorrada pesa más que su equipo, algo más caro. Las horas por MW·año incluyen la reposición de servidores, que es la mayor partida: [[REP]] h/MW·año.</div>",
           P=f(M.PUE_OPT, 2), AH=f(8760 * M.UTIL_TI * (M.PUE["ref_ch"] - M.PUE_OPT)),
           REP=f((M.SRV_POR_MW * 0.6 / M.VIDA_SRV) * M.v0[IX["SRV"]] + (M.SGP_POR_MW * 0.4 / M.VIDA_SGP) * M.v0[IX["SGP"]])))

# 4.3 construcción
pl, r = M.PLANTAS["OBRA"], M.JUEGOS["OBRA"]
o = r["opt"]; recs = pl["recursos"]
H.append("<h3 id='cpd-obra'>4.3 Construcción: procesos y camino crítico</h3><p>Procesos de construcción por MW de TI y su mezcla óptima (juegos completos), con la capacidad de obra de un año:</p>")
H.append("<div class='box'><table><thead><tr><th>Parte</th><th>Proceso</th><th>Datos</th>" + "".join(f"<th>{recs[x][0].split('(')[0]}</th>" for x in recs) + "<th>MW/año en el óptimo</th></tr></thead><tbody>")
for p, pr in enumerate(pl["procesos"]):
    x = o["x"][p]
    H.append(f"<tr{' class=rec' if x > 1e-6 else ''}><td><b>{next(n for k, n, _ in pl['piezas'] if k == pr[0])}</b></td><td>{pr[1]}</td><td class='mut'>{pr[3]}</td>"
             + "".join(f"<td class='n'>{fa(pr[2][x_]) if x_ in pr[2] else '—'}</td>" for x_ in recs) + f"<td class='n'><b>{fa(x)}</b></td></tr>")
H.append(f"</tbody></table><p>Tradicional: {fa(r['trad']['lam'])} MW/año · prefabricado: {fa(r['nuevo']['lam'])} · <b>mezcla óptima: {fa(o['lam'])} MW/año</b>. Con la mezcla, los 50 MW caben en un año de obra.</p></div>")
TT = M.T_CPD
rows = ["<div class='box'><b>Camino crítico de la construcción</b><div class='gantt'>"]
for a in M.CPM:
    k = a[0]; crit = M.HOLG[k] == 0
    rows.append(f"<div class='row'><div class='lab'><b>{k}</b> {a[1]}</div><div class='track'><span class='b {'crit' if crit else 'nc'}' style='left:{100 * M.ES_[k] / TT:.2f}%;width:{100 * a[2] / TT:.2f}%'>{a[2]} d</span></div></div>")
rows.append("</div><table style='margin-top:10px'><thead><tr><th></th><th>Actividad</th><th>Días</th><th>Precede</th><th>Inicio</th><th>Fin</th><th>Holgura</th></tr></thead><tbody>")
for a in M.CPM:
    k = a[0]
    rows.append(f"<tr{' class=hl' if M.HOLG[k] == 0 else ''}><td><b>{k}</b></td><td>{a[1]}</td><td class='n'>{a[2]}</td><td>{', '.join(a[3]) or '—'}</td><td class='n'>{M.ES_[k]}</td><td class='n'>{M.EF_[k]}</td><td class='n'>{M.HOLG[k]}</td></tr>")
rows.append(f"</tbody></table><p><b>{TT} días (≈{f(TT / 30.4, 0)} meses). Ruta crítica: {' → '.join(a[0] for a in M.CPM if M.HOLG[a[0]] == 0)}</b>. Los transformadores de potencia (casi un año de plazo de fabricación) mandan; conviene pedirlos el primer día.</p></div>")
H.append("".join(rows))

# 4.4 24/7/365
H.append(r"""<h3 id="cpd-247">4.4 Operación 24/7/365: de dónde sale la electricidad cada hora del año</h3>
<p>El CPD consume sin parar: la carga varía solo con la temperatura exterior, que afecta a la refrigeración. El sol y el viento varían cada hora. Se resuelve un programa lineal con las <b>8.760 horas del año</b> que decide a la vez cuánta capacidad instalar de cada fuente y cómo usarla cada hora.</p>
<div class="formula k"><div class="tt">Programa de capacidad y despacho horario</div>
\[ \begin{aligned}
\min\ & \sum_{g\in\{\text{FV, EOL, BES, TGS}\}}\Big(\frac{v_g+\mu\,\varepsilon_g}{\text{vida}_g}+\text{O\&M}_g\Big)K_g \;+\; \sum_{t=1}^{8760}\big[(v_{\text{red}}+\mu\,\varepsilon^{\text{red}}_t)\,r_t + (v_{\text{gas}}+\mu\,0{,}52)\,q_t\big]\\
\text{s.a.}\ & s_t+w_t+r_t+q_t+d_t-c_t \;\ge\; P_t \quad\text{(carga de cada hora)}\\
& s_t\le K_{\text{FV}}\,f^{\text{FV}}_t,\quad w_t\le K_{\text{EOL}}\,f^{\text{EOL}}_t,\quad q_t\le K_{\text{TGS}},\quad r_t\le K_{\text{red}}\\
& \text{soc}_{t+1}=\text{soc}_t+0{,}92\,c_t-d_t/0{,}92,\qquad c_t,d_t\le K_{\text{BES}}/4,\qquad \text{soc}_t\le K_{\text{BES}}
\end{aligned} \]
<p>\(f_t\): factor de capacidad horario sintético de un emplazamiento del interior de España (FV ≈ 19 %, eólica ≈ 30 % de media anual). \(\varepsilon^{\text{red}}_t\): intensidad de CO₂ de la red, menor al mediodía y con viento. Los grupos diésel no entran en el despacho: son respaldo de emergencia (N+2) para fallos de red, con 48 h de gasóleo.</p></div>""")
H.append("<div class='box'><table><thead><tr><th>Escenario</th><th>FV (MW)</th><th>Eólica (MW)</th><th>Baterías (MWh)</th><th>Turbinas de gas (MW)</th><th>Acceso a red (MW)</th><th>Energía: FV / eólica / red / gas</th><th>Vertido</th><th>t CO₂/año</th><th>Horas/año</th></tr></thead><tbody>")
for k, nom in M.ESC_DESP:
    d = M.DESP[k]
    tot = d["e_tot"]
    H.append(f"<tr{' class=rec' if k == 'opt' else ''}><td><b>{nom}</b></td><td class='n'>{fa(d['S'])}</td><td class='n'>{fa(d['W'])}</td><td class='n'>{fa(d['E'])}</td><td class='n'>{fa(d['G'])}</td><td class='n'>{fa(d['R'])}</td>"
             f"<td class='n'>{pct(d['fv'] / tot, 0)} / {pct(d['eol'] / tot, 0)} / {pct(d['red'] / tot, 0)} / {pct(d['gas'] / tot, 0)}</td><td class='n'>{f(d['vert'])} MWh</td>"
             f"<td class='n'>{f(d['co2'])}</td><td class='n'>{f(d['horas'])}</td></tr>")
H.append("</tbody></table></div>")
H.append(T("""<div class="res"><b>Plan recomendado para el 24/7/365</b>: [[S]] MW de fotovoltaica ([[MOD]] módulos), [[W]] MW eólicos ([[AER]] aerogeneradores de 5 MW), [[E]] MWh de baterías y [[R]] MW de acceso a red para las horas sin sol ni viento. Cubre el [[REN]] de la energía con renovables propias y emite [[CO2]] t/año, frente a [[CO2R]] t si todo viniera de la red. Se vierte el [[VERT]] de la producción posible: es más barato sobredimensionar que almacenar. Además: [[NG]] grupos diésel de 3 MW (N+2) con [[DIE]] t de gasóleo para 48 h, y SAI 2N de 100 MW con 10 minutos de batería.</div>""",
           S=f(do["S"]), MOD=f(do["S"] * 1820), W=f(do["W"]), AER=math.ceil(do["W"] / 5), E=f(do["E"]), R=f(do["R"]), REN=pct((do["fv"] + do["eol"]) / do["e_tot"], 0),
           CO2=f(do["co2"]), CO2R=f(dr["co2"]), VERT=pct(do["vert"] / (do["vert"] + do["fv"] + do["eol"]), 0), NG=M.N_GEN, DIE=f(M.DIESEL_48H)))
H.append(T("<p>Sin valorar el CO₂ (μ = 0), el mínimo de horas lo dan <b>turbinas de gas</b> ([[G]] MW): menos trabajo, pero [[CG]] t de CO₂ al año. En isla 100 % renovable sin gas hacen falta [[S0]] MW de FV y [[E0]] MWh de baterías, con un [[H0]] más de horas que el recomendado. La última hora sin sol ni viento es la más cara de cubrir.</p>",
           G=f(M.DESP["gas"]["G"]), CG=f(M.DESP["gas"]["co2"]), S0=f(M.DESP["isla0"]["S"]), E0=f(M.DESP["isla0"]["E"]),
           H0=pct(M.DESP["isla0"]["horas"] / do["horas"] - 1, 0)))
# gráficos horarios


def grafico(d, t0, titulo):
    n = 168
    sl = slice(t0, t0 + n)
    s, w, r_, q_, dd, cc = (d["ser"][k][sl] for k in ("s", "w", "g", "q", "d", "c"))
    carga = d["carga"][sl]
    Wd, Hd, pad = 760, 260, 44
    ymax = max((s + w + r_ + q_ + dd).max(), carga.max(), 1) * 1.1
    ymin = -max(cc.max(), 1) * 1.1
    X = lambda i: pad + i / (n - 1) * (Wd - pad - 10)
    Y = lambda v: 20 + (ymax - v) / (ymax - ymin) * (Hd - 50)
    capas = [(s, "#eab308", "FV"), (w, "#0e7490", "eólica"), (dd, "#7c3aed", "batería (descarga)"), (r_, "#78716c", "red"), (q_, "#be123c", "gas")]
    base = np.zeros(n)
    out = [f'<svg viewBox="0 0 {Wd} {Hd}" class="chart"><text x="{pad}" y="14" class="ax">{titulo}</text>']
    for v in np.linspace(0, ymax, 4):
        out.append(f'<line x1="{pad}" x2="{Wd - 10}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="grid"/><text x="{pad - 4}" y="{Y(v) + 4:.1f}" class="tk" text-anchor="end">{f(v)}</text>')
    for arr, col, lab in capas:
        top = base + arr
        pts = " ".join(f"{X(i):.1f},{Y(top[i]):.1f}" for i in range(n)) + " " + " ".join(f"{X(i):.1f},{Y(base[i]):.1f}" for i in reversed(range(n)))
        out.append(f'<polygon points="{pts}" fill="{col}" opacity="0.85"/>')
        base = top
    pts = " ".join(f"{X(i):.1f},{Y(0):.1f}" for i in range(n)) + " " + " ".join(f"{X(i):.1f},{Y(-cc[i]):.1f}" for i in reversed(range(n)))
    out.append(f'<polygon points="{pts}" fill="#a78bfa" opacity="0.6"/>')
    out.append('<polyline fill="none" stroke="#1c1917" stroke-width="1.6" points="' + " ".join(f"{X(i):.1f},{Y(carga[i]):.1f}" for i in range(n)) + '"/>')
    for dday in range(8):
        out.append(f'<text x="{X(min(dday * 24, n - 1)):.1f}" y="{Hd - 14}" class="tk" text-anchor="middle">día {dday + 1}</text>')
    out.append(f'<text x="10" y="{Hd / 2}" class="ax" transform="rotate(-90 10 {Hd / 2})" text-anchor="middle">MW</text></svg>')
    return "".join(out)


H.append("<div class='box'>" + grafico(do, 24 * 14, "Semana de enero (plan recomendado)") + grafico(do, 24 * 196, "Semana de julio (plan recomendado)")
         + "<div class='leg'><span style='background:#eab308'></span>fotovoltaica<span style='background:#0e7490'></span>eólica<span style='background:#7c3aed'></span>descarga de baterías"
           "<span style='background:#78716c'></span>red<span style='background:#be123c'></span>gas<span style='background:#a78bfa'></span>carga de baterías (negativo)<span style='background:#1c1917'></span>consumo del CPD</div></div>")

# 4.5 equipos de energía: fabricación
H.append("<h3 id='cpd-equipos'>4.5 Fabricación de los equipos de energía (Leontief)</h3><p>Cada escenario energético exige fabricar equipos distintos. Materiales y horas incorporados de toda la planta de energía:</p>"
         "<div class='box'><table><thead><tr><th>Escenario</th><th>Acero (t)</th><th>Aluminio (t)</th><th>Cobre (t)</th><th>Hormigón (t)</th><th>Polisilicio (t)</th><th>Minerales de batería (t)</th><th>Horas de fabricación y obra</th><th>t CO₂ de fabricación</th></tr></thead><tbody>")
for k, nom in M.ESC_DESP:
    d = M.DESP[k]
    caps = {"FV": d["S"], "EOL": d["W"], "BES": d["E"], "TGS": d["G"] / 10, "GEN": M.N_GEN}
    tot = np.zeros(M.NB)
    for g, n in caps.items():
        tot += n * M.L0[:, IX[g]]
    hh = sum(n * M.v0[IX[g]] for g, n in caps.items()); cc = sum(n * M.e0[IX[g]] for g, n in caps.items())
    H.append(f"<tr{' class=rec' if k == 'opt' else ''}><td><b>{nom}</b></td>" + "".join(f"<td class='n'>{f(tot[IX[g]] / (1000 if g == 'PSI' else 1))}</td>" for g in ["ACE", "ALU", "COB", "HOR", "PSI", "LIT"])
             + f"<td class='n'>{f(hh)}</td><td class='n'>{f(cc)}</td></tr>")
H.append("</tbody></table><p class='nota'>Incluye los 18 grupos diésel de respaldo en todos los escenarios. La «red» usa infraestructura ya existente, que aquí no se imputa.</p></div>")

# 4.6 anual
an_srv = M.CPU_MW * M.SRV_POR_MW / M.VIDA_SRV
an_sgp = M.GPU_MW * M.SGP_POR_MW / M.VIDA_SGP
agua = 8760 * M.UTIL_TI * M.AGUA_L_KWH[M.REF_OPT] * M.MW_TI
H.append(T(r"""<h3 id="cpd-anual">4.6 Necesidades anuales para funcionar 24/7/365</h3>
<div class="formula t">\[ \text{personal 24/7}=\frac{\text{puestos}\times 8.760\ \text{h}}{1.650\ \text{h/persona}}\approx 5{,}3\ \text{personas por puesto},\qquad \text{reposición}=\frac{\text{parque}}{\text{vida}} \]</div>
<div class="box"><table><thead><tr><th>Necesidad anual</th><th>Cantidad</th><th>Horas incorporadas</th></tr></thead><tbody>
<tr><td>Reposición de servidores CPU (vida de 5 años)</td><td class="n">[[SRV]] ud</td><td class="n">[[HSRV]]</td></tr>
<tr><td>Reposición de servidores GPU (vida de 4 años)</td><td class="n">[[SGP]] ud</td><td class="n">[[HSGP]]</td></tr>
<tr><td>Electricidad</td><td class="n">[[E]] MWh</td><td class="n">[[HE]]</td></tr>
<tr><td>Agua (refrigeración líquida)</td><td class="n">[[AG]] m³</td><td class="n">—</td></tr>
<tr><td>Personal de operación, seguridad y mantenimiento 24/7</td><td class="n">[[FTE]] personas</td><td class="n">[[HOP]]</td></tr>
<tr><td>Gasóleo de pruebas de los grupos (1 h al mes a plena carga)</td><td class="n">[[DIEA]] t</td><td class="n">—</td></tr>
<tr><td>Reposición de baterías del SAI (12 años) y de baterías estacionarias (15 años)</td><td class="n">[[BAT]] MWh</td><td class="n">—</td></tr>
</tbody></table></div>""", SRV=f(an_srv), HSRV=f(an_srv * M.v0[IX["SRV"]]), SGP=f(an_sgp), HSGP=f(an_sgp * M.v0[IX["SGP"]]),
           E=f(do["e_tot"]), HE=f(do["horas"]), AG=f(agua), FTE=f(M.HORAS_OPER_MW * M.MW_TI / 1650), HOP=f(M.HORAS_OPER_MW * M.MW_TI),
           DIEA=f(M.N_GEN * 3 * 0.25 * 12 * 1), BAT=f(100 * 0.17 / 12 + do["E"] / 15, 1)))

# 4.7 totales generales del CPD (sin separar CPU y GPU)
VIDA_CPD = 30
y_ini = np.zeros(M.NB)
for g, n in stock.items():
    if g not in ("FV", "EOL", "BES", "TGS"):
        y_ini[IX[g]] = n
y_an = np.zeros(M.NB); y_an[IX["CPDS"]] = M.MW_TI
x_ini, x_an = lmc["L"] @ y_ini, lmc["L"] @ y_an
h_ini, h_an = float(lmc["v"] @ y_ini), float(lmc["v"] @ y_an)
c_ini, c_an = float(lmc["e"] @ y_ini), float(lmc["e"] @ y_an)
k_srv = M.ACT_CPD[M.REF_OPT]
agua_dir = A_[k_srv]["ins"]["AGU"] * M.MW_TI
ele_dir = A_[k_srv]["ins"]["ELE"] * M.MW_TI
h_ener_l = lmc["v"][IX["ELE"]] * ele_dir
h_an_desp = h_an - h_ener_l + do["horas"]
H.append(T(r"""<h3 id="cpd-total">4.7 Totales del centro de datos: materiales, horas y agua</h3>
<p>Aquí el CPD se trata como un todo: servidores, racks, edificio, refrigeración, electricidad y operación, sin separar CPU y GPU. Las cantidades son <b>totales</b>. Incluyen lo que se usa directamente y todo lo necesario para fabricar cada insumo, hasta la mina.</p>
<div class="formula">\[ \mathbf x^{\text{obra}}=(I-A^*)^{-1}\,\mathbf y^{\text{obra}},\qquad \mathbf x^{\text{año}}=(I-A^*)^{-1}\cdot 50\,\mathbf e_{\text{CPD}},\qquad \mathbf x^{\text{vida}}=[[V]]\cdot\mathbf x^{\text{año}},\qquad H=\mathbf v\,\mathbf y,\quad \mathbf v=\mathbf l\,(I-A^*)^{-1} \]</div>
<p>\(A^*\) es la matriz de la mezcla de técnicas que elige Kantorovich. \(\mathbf y^{\text{obra}}\) es el parque del apartado 4.1 sin la planta de energía propia. \(\mathbf e_{\text{CPD}}\) es 1 MW de TI funcionando un año. Ese año ya incluye la parte proporcional de la obra: los servidores se reponen cada 4–5 años, la refrigeración cada 15 y el edificio cada 30. Por eso los <b>[[V]] años de vida</b> son la <b>suma total</b>: ya contienen la construcción, todas las reposiciones y toda la operación. No hay que sumarles la columna de obra.</p>
<div class="kpis">
<div class="kpi"><div class="v">[[HV]] M h</div><div class="l">horas totales en [[V]] años (todo sumado)</div></div>
<div class="kpi"><div class="v">[[HA]] h</div><div class="l">horas al año en régimen (≈ [[FTE]] personas a jornada completa)</div></div>
<div class="kpi"><div class="v">[[HI]] h</div><div class="l">horas para construir y equipar el CPD (una vez)</div></div>
<div class="kpi"><div class="v">[[AA]] m³</div><div class="l">agua al año ([[AD]] m³ de refrigeración + [[AE]] m³ incorporados)</div></div>
<div class="kpi"><div class="v">[[EA]] MWh</div><div class="l">electricidad al año, total</div></div>
<div class="kpi"><div class="v">[[CA]] t</div><div class="l">CO₂ al año</div></div>
</div>""", V=VIDA_CPD, HV=f(h_an * VIDA_CPD / 1e6, 1), HA=f(h_an), FTE=f(h_an / 1650), HI=f(h_ini), AA=f(x_an[IX["AGU"]]), AD=f(agua_dir),
           AE=f(x_an[IX["AGU"]] - agua_dir), EA=f(x_an[IX["ELE"]]), CA=f(c_an)))
R = ["<div class='box'><table><thead><tr><th>Recurso</th><th>Unidad</th><th>Construir y equipar (una vez)</th><th>Un año de funcionamiento 24/7</th>"
     f"<th>Total en {VIDA_CPD} años (suma total)</th></tr></thead><tbody>"]
ult = None
for g in M.COD:
    if ESC[g] not in ("Extracción", "Energía", "Materiales", "Obleas") or max(x_ini[IX[g]], x_an[IX[g]]) < 1e-3:
        continue
    if ESC[g] != ult:
        R.append(f"<tr class='sep'><td colspan='5'>{ESC[g]}</td></tr>"); ult = ESC[g]
    j = IX[g]
    R.append(f"<tr{' class=hl' if g == 'AGU' else ''}><td><b>{NOMBRE[g]}</b></td><td>{UNIDAD[g]}</td><td class='n'>{fa(x_ini[j])}</td><td class='n'>{fa(x_an[j])}</td><td class='n'>{fa(x_an[j] * VIDA_CPD)}</td></tr>")
R.append("<tr class='sep'><td colspan='5'>Trabajo y emisiones</td></tr>")
R.append(f"<tr class='hl'><td><b>Horas de trabajo</b></td><td>h</td><td class='n'><b>{f(h_ini)}</b></td><td class='n'><b>{f(h_an)}</b></td><td class='n'><b>{f(h_an * VIDA_CPD)}</b></td></tr>")
R.append(f"<tr><td><b>Personas a jornada completa</b> (1.650 h/año)</td><td>personas</td><td class='n'>{f(h_ini / 1650)} personas-año</td><td class='n'>{f(h_an / 1650)}</td><td class='n'>{f(h_an / 1650)} cada año</td></tr>")
R.append(f"<tr><td><b>CO₂</b></td><td>t</td><td class='n'>{f(c_ini)}</td><td class='n'>{f(c_an)}</td><td class='n'>{f(c_an * VIDA_CPD)}</td></tr>")
R.append("</tbody></table><p class='nota'>Las cantidades son producción bruta \\(x_i\\): el acero incluye el del edificio, los chasis, los racks y el de las máquinas que fabrican los componentes. La electricidad del año incluye la del propio CPD ("
         + f(ele_dir) + " MWh) y la gastada en fabricar sus reposiciones. El agua incluye la de refrigeración y la de fabricar los chips (agua ultrapura) y el resto de materiales.</p></div>")
H.append("".join(R))
# horas por eslabón
ETQ = {"Productos": "Integración de equipos de TI (servidores y racks)", "Servicio": "Operación 24/7 (turnos, seguridad, mantenimiento)",
       "Infraestructura CPD": "Obra e instalaciones del CPD", "Componentes": "Componentes (procesadores, aceleradores, memoria, placas…)",
       "Obleas": "Obleas y fabricación de chips", "Energía": "Energía (electricidad y gasóleo)", "Materiales": "Materiales", "Extracción": "Extracción"}
hx = {}
for g in M.COD:
    hx[ESC[g]] = hx.get(ESC[g], 0) + lmc["l"][IX[g]] * x_an[IX[g]]
R = ["<h4>¿Dónde se trabajan esas horas? (un año en régimen)</h4><div class='box'><table><thead><tr><th>Eslabón</th><th>Horas al año</th><th>%</th><th></th>"
     f"<th>Horas en {VIDA_CPD} años</th></tr></thead><tbody>"]
hmax = max(hx.values())
for e, hh in sorted(hx.items(), key=lambda kv: -kv[1]):
    if hh < 1:
        continue
    R.append(f"<tr><td><b>{ETQ.get(e, e)}</b></td><td class='n'>{f(hh)}</td><td class='n'>{pct(hh / h_an)}</td><td class='w'>{bar(hh, hmax, '#4338ca')}</td><td class='n'>{f(hh * VIDA_CPD)}</td></tr>")
R.append(f"<tr class='hl'><td><b>Total</b></td><td class='n'><b>{f(h_an)}</b></td><td class='n'>100 %</td><td></td><td class='n'><b>{f(h_an * VIDA_CPD)}</b></td></tr></tbody></table></div>")
H.append("".join(R))
H.append(T(r"""<div class="res"><b>En resumen:</b> el CPD de 50 MW necesita <b>[[HA]] horas de trabajo al año</b>, unas [[FTE]] personas a jornada completa repartidas por toda la cadena. Solo [[FOP]] de ellas trabajan en el propio centro. También consume <b>[[AA]] m³ de agua</b> y <b>[[EA]] MWh</b> al año. En [[V]] años suma <b>[[HV]] millones de horas</b>, [[AV]] millones de m³ de agua, [[ACV]] t de acero, [[COV]] t de cobre y [[HOV]] t de hormigón.</div>
<p class="nota">Electricidad: la tabla valora cada MWh con las horas medias de la matriz (\(v_{\text{ELE}}\)). Si la energía sale de la planta propia del despacho horario recomendado (apartado 4.4), esa partida cambia de [[HE1]] a [[HE2]] horas. El total anual pasa entonces a <b>[[HD]] h</b>. Son dos formas de contar la misma energía: usa una u otra, nunca las dos.</p>""",
           HA=f(h_an), FTE=f(h_an / 1650), FOP=f(M.HORAS_OPER_MW * M.MW_TI / 1650), AA=f(x_an[IX["AGU"]]), EA=f(x_an[IX["ELE"]]), V=VIDA_CPD,
           HV=f(h_an * VIDA_CPD / 1e6, 1), AV=f(x_an[IX["AGU"]] * VIDA_CPD / 1e6, 2), ACV=f(x_an[IX["ACE"]] * VIDA_CPD), COV=f(x_an[IX["COB"]] * VIDA_CPD),
           HOV=f(x_an[IX["HOR"]] * VIDA_CPD), HE1=f(h_ener_l), HE2=f(do["horas"]), HD=f(h_an_desp)))

# =============================================================================
# 5. AGREGADO
# =============================================================================
y = np.zeros(M.NB)
y[IX["PCO"]] = M.Q["PCO"]; y[IX["PCG"]] = M.Q["PCG"]
sol = M.lp(M.H + M.MU_CO2 * M.C, y)
z = sol["z"]
H.append("<h2 id='agregado'>5. Plan de producción agregado: fábrica de PC (un año, método recomendado)</h2><p>Producción de cada sector para 1.000.000 de PC de oficina y 250.000 PC gaming, con las técnicas que elige Kantorovich (\\(\\mathbf x=A^*\\mathbf x+\\mathbf y\\)).</p><div class='box'><table><thead><tr><th>Bien</th><th>Producción anual</th><th>Técnicas</th><th>Horas directas</th><th>t CO₂ directo</th></tr></thead><tbody>")
ult = None
for g in M.COD:
    ks = [k for k, a in enumerate(A_) if a["bien"] == g]
    tot = z[ks].sum()
    if tot < 1e-6:
        continue
    if ESC[g] != ult:
        H.append(f"<tr class='sep'><td colspan='5'>{ESC[g]}</td></tr>"); ult = ESC[g]
    rep = " + ".join(f"{pct(z[k] / tot, 0)} {CORTO.get(A_[k]['id'], A_[k]['nombre'])}" for k in ks if z[k] / tot > 1e-3) if len(ks) > 1 else A_[ks[0]]["nombre"]
    H.append(f"<tr><td><b>{NOMBRE[g]}</b></td><td class='n'>{fa(tot)} {UNIDAD[g]}</td><td>{rep}</td><td class='n'>{f(sum(z[k] * A_[k]['h'] for k in ks))}</td><td class='n'>{f(sum(z[k] * M.C[k] for k in ks))}</td></tr>")
H.append(f"<tr class='hl'><td><b>Total</b></td><td></td><td></td><td class='n'><b>{f(sol['horas'])}</b></td><td class='n'><b>{f(sol['co2'])}</b></td></tr></tbody></table></div>")
H.append(T("<p>Con las horas del método base se podrían fabricar <b>[[A]] PC de oficina</b> (en vez de 1.000.000) o <b>[[B]] PC gaming</b> (en vez de 250.000) eligiendo las técnicas de mínimo trabajo.</p>",
           A=f(M.FAB["PCO"]["max_h"]), B=f(M.FAB["PCG"]["max_h"])))

H.append(r"""<h2 id="supuestos">6. Supuestos y límites</h2><ul>
<li><b>Datos ilustrativos</b>, con órdenes de magnitud del sector: energía y agua por oblea, dados por oblea, horas de montaje, PUE y factores de capacidad. No corresponden a ningún fabricante ni emplazamiento concreto. Todo está en <code>modelo_ordenadores.py</code>; el documento se regenera con <code>python build_ordenadores.py</code>.</li>
<li><b>Chips</b>: el modelo agrupa las obleas en tres tipos (avanzada, memoria y madura). Las emisiones directas de las fábricas de chips son sobre todo gases fluorados.</li>
<li><b>Perfiles horarios</b> sintéticos y reproducibles (semilla fija), no medidos. Para un emplazamiento real se sustituyen por series horarias de radiación y viento.</li>
<li><b>Fuera del modelo</b>: capital de las fábricas de chips (máquinas EUV, salas limpias), red de fibra, software y la energía de los PC durante su uso.</li>
<li><b>Fiabilidad</b>: el respaldo (grupos N+2, SAI 2N) se dimensiona por regla de diseño Tier III, no se optimiza.</li>
</ul></main></body></html>""")

html = "\n".join(H)
with open("planificacion_ordenadores.html", "w", encoding="utf-8") as fh:
    fh.write(html)
print("OK", len(html))
