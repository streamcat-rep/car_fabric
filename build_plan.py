"""Genera planificacion_integral.html a partir de modelo_plan.py (todo el texto está aquí)."""
import math
import numpy as np
import modelo_plan as M
import procesos as PR

IX, A_, MODOS, BIENES = M.IX, M.A_, M.MODOS, M.BIENES
NOMBRE = {b[0]: b[1] for b in BIENES}
UNIDAD = {b[0]: b[2] for b in BIENES}
ESC = {b[0]: b[3] for b in BIENES}
COL_ESC = {"Extracción": "#a16207", "Energía": "#b45309", "Materiales": "#0e7490", "Componentes": "#4338ca",
           "Productos": "#be123c", "Servicio": "#15803d"}


def f(x, d=0):
    s = f"{x:,.{d}f}"
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return "0" if s in ("-0", "-0,0", "-0,00") else s


def fa(x):
    """formato automático según magnitud"""
    ax = abs(x)
    if ax >= 1000: return f(x, 0)
    if ax >= 100: return f(x, 1)
    if ax >= 1: return f(x, 2)
    if ax >= 0.01: return f(x, 3)
    return f(x, 5)


def pct(x, d=1):
    return f(100 * x, d) + " %"


def T(txt, **kw):
    for k, v in kw.items():
        txt = txt.replace("[[" + k + "]]", str(v))
    assert "[[" not in txt, txt[txt.index("[["):txt.index("[[") + 30]
    return txt


def bar(v, vmax, color):
    w = 0 if vmax <= 0 else max(0.5, 100 * v / vmax)
    return f'<div class="bar"><span style="width:{w:.1f}%;background:{color}"></span></div>'


def stack(parts, tot):
    return '<div class="stack">' + "".join(
        f'<span title="{lab}: {fa(v)}" style="width:{100 * v / tot:.2f}%;background:{c}"></span>' for v, c, lab in parts if v > 0) + "</div>"


def chip(e):
    return f"<span class='chip' style='--c:{COL_ESC[e]}'>{e}</span>"


TEC_NOMBRE = {a["id"]: a["nombre"] for a in A_}
TEC_CORTO = {"ace_bof": "acero BF-BOF", "ace_eaf": "acero EAF (chatarra)", "ace_h2": "acero DRI-H₂",
             "alu_p": "Al primario", "alu_s": "Al reciclado", "ele_t": "electricidad térmica", "ele_r": "electricidad renovable",
             "hor_c": "hormigón Portland", "hor_lc3": "hormigón LC3", "bat_nmc": "batería NMC", "bat_lfp": "batería LFP",
             "biw_a": "carrocería de acero", "biw_m": "carrocería multimaterial", "bus_a": "estructura de acero",
             "bus_al": "estructura de aluminio", "tram_a": "caja de acero", "tram_al": "caja de aluminio",
             "via_l": "vía en losa", "via_b": "vía en balasto", "via_c": "vía en césped", "mar_a": "marquesina acero-vidrio",
             "mar_m": "marquesina de madera"}


def mezcla_html(mz):
    out = []
    for g, partes in mz:
        out.append(" + ".join(f"{pct(w, 0)} {TEC_CORTO.get(t, t)}" if w < 0.999 else TEC_CORTO.get(t, t) for t, w in partes))
    return "<br>".join(out)


H = []   # trozos del HTML

# =============================================================================
# CABECERA Y ESTILO
# =============================================================================
H.append(r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Plan integral de producción: coche, autobús y tranvía autónomos — Leontief, Kantorovich y método del taller</title>
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
h1{font-size:34px;line-height:1.2;margin:0 0 10px}
h2{font-size:27px;margin:72px 0 12px;padding-top:14px;border-top:3px solid var(--ink)}
h3{font-size:21px;margin:44px 0 8px;padding-top:8px;border-top:1px solid var(--line)}
h4{font-size:16.5px;margin:28px 0 6px;color:#292524}
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
.paso{background:#fff;border:1px dashed #d6d3d1;border-radius:8px;padding:10px 16px;margin:10px 0}
.paso b.n{display:inline-block;background:var(--ink);color:#fff;border-radius:50%;width:22px;height:22px;text-align:center;line-height:22px;font-size:12px;margin-right:6px}
table{border-collapse:collapse;width:100%;font-size:12.8px;font-variant-numeric:tabular-nums}
th,td{padding:5px 7px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);font-weight:600}
th mjx-container{font-size:135%!important}
td.n{text-align:right;white-space:nowrap}td.w{width:18%;min-width:90px}.mut{color:var(--mut)}
tr.hl td{background:#eef2ff}tr.rec td{background:#f0fdf4}tr.sep td{background:#fafaf9;font-weight:600;color:var(--mut);font-size:11.5px;text-transform:uppercase;letter-spacing:.04em}
.bar{height:11px;background:#f5f5f4;border-radius:3px;overflow:hidden;margin-top:4px}.bar span{display:block;height:100%;border-radius:3px}
.stack{display:flex;height:12px;background:#f5f5f4;border-radius:3px;overflow:hidden;margin-top:5px;min-width:90px}.stack span{display:block;height:100%}
.chip{display:inline-block;font-size:10.5px;padding:0 7px;border-radius:999px;border:1px solid var(--c);color:var(--c);white-space:nowrap}
.ok{color:var(--ok);font-weight:600}.no{color:var(--red);font-weight:600}.warn{color:var(--warn);font-weight:600}
.leg{font-size:12.5px;color:var(--mut);margin-top:6px}.leg span{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 4px 0 12px;vertical-align:middle}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}@media (max-width:1100px){.two{grid-template-columns:1fr}}
.ficha-cab{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:12px 0}
.ficha-cab div{background:#f5f5f4;border-radius:8px;padding:8px 12px;font-size:13px}.ficha-cab b{display:block;font-size:19px}
code{font-family:ui-monospace,Menlo,monospace;font-size:13px;background:#f5f5f4;padding:1px 5px;border-radius:4px}
.gantt .row{display:flex;align-items:center;gap:8px;font-size:12.5px;margin:4px 0}.gantt .lab{width:340px;flex-shrink:0}
.gantt .track{flex:1;position:relative;height:20px;background:#f5f5f4;border:1px solid var(--line);border-radius:4px}
.gantt .b{position:absolute;top:2px;bottom:2px;border-radius:3px;color:#fff;font-size:11px;display:flex;align-items:center;justify-content:center}
.gantt .crit{background:var(--red)}.gantt .nc{background:#78716c}
svg.chart{width:100%;height:auto}svg .grid{stroke:#e7e5e4}svg .tk{font-size:11px;fill:#78716c}svg .ax{font-size:12px;fill:#57534e}
svg .front{fill:none;stroke:#4338ca;stroke-width:2}svg .pf{fill:#4338ca}svg .dom{fill:#be123c}svg .cp{fill:#15803d;stroke:#fff;stroke-width:2}svg .lb{font-size:12px;fill:#1c1917}
</style></head><body>
""")

# =============================================================================
# NAVEGACIÓN
# =============================================================================
nav = ["<nav><b>Índice</b>", "<a href='#resumen'>Resumen del plan</a>", "<a href='#guia'>Cómo está organizado</a>",
       "<a href='#metodos'>1. Los tres métodos, paso a paso</a>", "<a class='sub' href='#m-leontief'>1.1 Leontief</a>",
       "<a class='sub' href='#m-kantorovich'>1.2 Kantorovich</a>", "<a class='sub' href='#m-taller'>1.3 Método del taller</a>",
       "<a href='#catalogo'>2. Catálogo de técnicas</a>", "<a class='sub' href='#cat-tecnicas'>2.1 Todas las actividades</a>",
       "<a class='sub' href='#cat-merito'>2.2 Qué técnica es mejor</a>", "<a href='#fichas'>3. Producción de cada producto</a>"]
for g in M.PRODUCTOS:
    nav.append(f"<a class='sub' href='#f-{g}'>{NOMBRE[g].split('(')[0]}</a>")
nav += ["<a href='#procesos'>3 bis. Procesos de fabricación</a>", "<a href='#agregado'>4. Plan de producción agregado</a>", "<a href='#ciudad'>5. Movilidad de la ciudad</a>",
        "<a class='sub' href='#c-eficiencia'>5.1 Eficiencia de cada modo</a>", "<a class='sub' href='#c-escenarios'>5.2 Escenarios y óptimos</a>",
        "<a class='sub' href='#c-pareto'>5.3 Frontera de Pareto</a>", "<a class='sub' href='#c-flota'>5.4 Parque y horas</a>",
        "<a href='#fabrica'>6. Máximo de coches por fábrica</a>", "<a href='#supuestos'>7. Supuestos y límites</a></nav>"]
H.append("\n".join(nav))
H.append("<main>")

# =============================================================================
# RESUMEN
# =============================================================================
ref, comp = M.I["ref"], M.I["comp"]
H.append(T(r"""
<h1>Plan integral de producción para la movilidad de una ciudad: coche, autobús autónomo y tranvía autónomo</h1>
<p class="lead">Ciudad de <b>[[HAB]] habitantes</b> en <b>[[SUP]] km²</b>. Para cada producto (coche de combustión, coche eléctrico, autobús eléctrico autónomo, tranvía autónomo, vía, parada, marquesina y cargador) se calcula <b>qué hay que producir y con qué insumos</b> (Leontief), <b>qué método de producción es mejor</b> (Kantorovich) y <b>cómo se organiza su fabricación</b> (método del taller). Después se agrega todo en un plan de producción único y se elige la combinación de modos que mueve a la ciudad con menos trabajo y menos CO₂.</p>
<section id="resumen">
<div class="kpis">
<div class="kpi"><div class="v">−[[RED_H]]</div><div class="l">horas de trabajo/año del plan recomendado frente al modelo coche-céntrico ([[H_C]] M frente a [[H_R]] M)</div></div>
<div class="kpi"><div class="v">−[[RED_C]]</div><div class="l">CO₂/año ([[C_C]] t frente a [[C_R]] t)</div></div>
<div class="kpi"><div class="v">×[[MULT]]</div><div class="l">movilidad producible con las mismas horas y el mismo CO₂ que hoy</div></div>
<div class="kpi"><div class="v">[[FB]] / [[FT]]</div><div class="l">autobuses / tranvías autónomos del parque; [[VIA]] km de vía, [[MAR]] marquesinas</div></div>
<div class="kpi"><div class="v">+[[GAN_FAB]]</div><div class="l">coches más con las mismas horas eligiendo bien las técnicas, y −[[RED_FAB]] de CO₂</div></div>
<div class="kpi"><div class="v">[[ETA_BUS]] vs [[ETA_CAR]]</div><div class="l">rendimiento útil autobús frente a coche: parte de la energía que mueve personas</div></div>
</div>
<div class="res"><b>Conclusiones principales.</b>
<ol>
<li><b>El cambio de modo pesa mucho más que el cambio de técnica.</b> Pasar de coche a autobús y tranvía autónomos reduce el trabajo social un [[RED_H]] y el CO₂ un [[RED_C]]. Electrificar los mismos coches solo reduce el CO₂ un [[RED_BEV]].</li>
<li><b>Producir más con lo mismo pasa por reciclar.</b> El acero de horno eléctrico con chatarra y el aluminio reciclado ahorran horas y CO₂ a la vez; solo los limita la chatarra disponible. Son siempre la primera decisión del plan.</li>
<li><b>El método recomendado para cada producto</b> minimiza el coste social: horas + μ·CO₂, con μ = [[MU]] h/t. Este valor equivale a unos 75 €/t de CO₂ si la hora de trabajo cuesta 25 €. Con ese criterio entran la electricidad renovable, el acero con hidrógeno, el hormigón bajo en clínker y la batería LFP. La caja de aluminio solo compensa en el tranvía, y la marquesina de madera no compensa.</li>
<li><b>El taller depende del volumen.</b> Los coches salen de una línea en cadena con takt de 2 minutos. Los autobuses, de una línea por estaciones con takt de unas 26 horas. Los tranvías y la vía se fabrican y construyen por proyecto, a puesto fijo, con camino crítico.</li>
</ol></div>
</section>
""", HAB=f(M.HAB), SUP=f(M.SUP), RED_H=pct(1 - comp["horas"] / ref["horas"], 0), H_C=f(comp["horas"] / 1e6, 2),
           H_R=f(ref["horas"] / 1e6, 2), RED_C=pct(1 - comp["co2"] / ref["co2"], 0), C_C=f(comp["co2"]), C_R=f(ref["co2"]),
           MULT=f(M.S["max"]["t"] / M.D, 2), FB=f(comp["flota"]["BUS"]), FT=f(comp["flota"]["TRAM"]),
           VIA=f(comp["stock"]["VIA"]), MAR=f(comp["stock"]["MAR"]),
           GAN_FAB=pct(M.FAB["opt"]["N"] / M.FAB["base"]["N"] - 1, 1), RED_FAB=pct(1 - M.FAB["opt"]["co2"] / M.FAB["base"]["co2"], 0),
           ETA_BUS=pct(MODOS["BUS"]["eta_util"], 1), ETA_CAR=pct(MODOS["CICE"]["eta_util"], 1),
           RED_BEV=pct(1 - M.I["bev"]["co2"] / ref["co2"], 0), MU=f(M.MU_CO2, 0)))

H.append(r"""
<h2 id="guia">Cómo está organizado este documento</h2>
<p>El plan se construye de abajo arriba en tres niveles. Cada nivel contesta una pregunta y pasa su respuesta al siguiente:</p>
<div class="box"><table><thead><tr><th>Nivel</th><th>Pregunta</th><th>Herramienta</th><th>Resultado</th><th>Dónde</th></tr></thead><tbody>
<tr><td><b>Macro</b></td><td>¿Qué cantidades de cada cosa hacen falta, contando toda la cadena hasta la mina?</td><td>Leontief: \(\mathbf{x}=(I-A)^{-1}\mathbf{y}\)</td><td>Toneladas, MWh y unidades de cada sector; horas y CO₂ incorporados</td><td>§1.1, cada ficha (b–c), §4</td></tr>
<tr><td><b>Meso</b></td><td>¿Con qué método conviene producir cada cosa? ¿Cuánto se puede producir como máximo?</td><td>Kantorovich: programación lineal y su dual</td><td>Técnica óptima, producción máxima, valoraciones duales (precios sombra)</td><td>§1.2, §2, cada ficha (d), §5, §6</td></tr>
<tr><td><b>Micro</b></td><td>¿Cómo se organiza la fabricación: ritmo, puestos, operarios, calendario?</td><td>Método del taller: takt, balanceo, camino crítico</td><td>Organización de cada taller, operarios, duración de las obras</td><td>§1.3, cada ficha (e)</td></tr>
</tbody></table></div>
<p>La <b>sección 3</b> es el núcleo: tiene una ficha para cada producto con cinco apartados, siempre en el mismo orden. (a) Qué es y cuánto se produce. (b) Su receta de insumos. (c) La cadena completa con Leontief. (d) La comparación de métodos de producción con Kantorovich. (e) La organización del taller.</p>
""")

# =============================================================================
# 1. MÉTODOS CON EJEMPLO
# =============================================================================
# ejemplo de juguete: mineral -> acero -> autobús
q_toy = 133
l_toy = (0.15, 2.5, 1400.0)
a_MA, a_AB = 1.6, 6.0
v_A = l_toy[1] + a_MA * l_toy[0]
v_B = l_toy[2] + a_AB * v_A
x_B, x_A, x_M = q_toy, a_AB * q_toy, a_MA * a_AB * q_toy
# técnicas de acero (valores reales del modelo)
tec_ace = {t["nombre"]: t for t in []}
ct = {}
for k, a in enumerate(A_[:M.N_PROD]):
    if a["bien"] == "ACE":
        ct[a["id"]] = (a["h"] + sum(q * M.v0[IX[g]] for g, q in a["ins"].items()),
                       a["co2"] + sum(q * M.e0[IX[g]] for g, q in a["ins"].items()))
vb, eb = ct["ace_bof"]; ve, ee = ct["ace_eaf"]; vh, eh = ct["ace_h2"]
h_min = 0.6 * vb + 0.4 * ve
H.append(T(r"""
<h2 id="metodos">1. Los tres métodos, paso a paso con un ejemplo pequeño</h2>
<p>Antes de aplicarlos a todo el sistema (37 bienes y 52 actividades), conviene ver cómo funciona cada método en una cadena mínima: <b>mineral de hierro → acero → autobús</b>, para fabricar los [[Q]] autobuses que la ciudad repone cada año.</p>

<h3 id="m-leontief">1.1 Leontief: cuánto hay que producir de cada cosa</h3>
<p><b>Idea.</b> Cada sector necesita productos de otros sectores para producir. Si se pide un autobús, hace falta acero; el acero necesita mineral; y así hacia atrás. Leontief calcula de una vez <i>toda</i> la producción necesaria, directa e indirecta.</p>
<div class="paso"><b class="n">1</b><b>Coeficientes técnicos.</b> \(a_{ij}\) = cantidad del bien \(i\) que hace falta para producir una unidad del bien \(j\). En el ejemplo: 1 autobús necesita \(a_{AB}=6\) t de acero, y 1 t de acero necesita \(a_{MA}=1{,}6\) t de mineral.</div>
<div class="paso"><b class="n">2</b><b>Ecuación de balance.</b> Lo que produce cada sector (\(x_i\)) se reparte entre lo que consumen los demás sectores (\(\sum_j a_{ij}x_j\)) y la demanda final (\(y_i\)):
\[ x_i = \sum_j a_{ij}\,x_j + y_i \quad\Longleftrightarrow\quad \mathbf{x} = A\mathbf{x}+\mathbf{y} \quad\Longrightarrow\quad \mathbf{x} = (I-A)^{-1}\mathbf{y} = L\,\mathbf{y} \]</div>
<div class="paso"><b class="n">3</b><b>Resolución del ejemplo.</b> Con \(\mathbf{y} = (0,\,0,\,[[Q]])\) para (mineral, acero, autobús):
\[ A=\begin{pmatrix}0&1{,}6&0\\0&0&6\\0&0&0\end{pmatrix},\quad
L=(I-A)^{-1}=\begin{pmatrix}1&1{,}6&9{,}6\\0&1&6\\0&0&1\end{pmatrix},\quad
\mathbf{x}=L\mathbf{y}=\begin{pmatrix}[[XM]]\ \text{t mineral}\\ [[XA]]\ \text{t acero}\\ [[Q]]\ \text{autobuses}\end{pmatrix} \]
La última columna de \(L\) es la <b>lista completa de materiales de un autobús</b>: 6 t de acero y 9,6 t de mineral. El 9,6 es el efecto indirecto: \(6\times 1{,}6\).</div>
<div class="paso"><b class="n">4</b><b>Horas incorporadas.</b> Con las horas directas por unidad \(\mathbf{l} = ([[L1]];\ [[L2]];\ [[L3]])\) (minería, acería, ensamblaje del autobús):
\[ \mathbf{v}^{\top} = \mathbf{l}^{\top}L \;\Rightarrow\; v_{\text{acero}} = [[L2]] + 1{,}6\times [[L1]] = [[VA]]\ \text{h/t},\qquad v_{\text{autobús}} = [[L3]] + 6\times[[VA]] = [[VB]]\ \text{h} \]
Se separan así las <b>horas de ensamblaje final</b> (\(l_{\text{autobús}}=[[L3]]\) h) de las <b>horas totales</b> de toda la cadena (\(v = [[VB]]\) h). El CO₂ se calcula igual: \(\boldsymbol\varepsilon^{\top}=\mathbf d^{\top}L\).</div>
<p class="nota">En el modelo completo, \(A\) es una matriz de 37×37 y la inversa se calcula numéricamente. La condición para que el sistema sea viable es que el radio espectral de \(A\) sea menor que 1 (condición de Hawkins–Simon). En el modelo es \(\rho(A)=[[RHO]]\).</p>

<h3 id="m-kantorovich">1.2 Kantorovich: con qué método producir</h3>
<p><b>Idea.</b> Leontief da una única receta por sector. Pero el acero se puede hacer de varias maneras, y cada una gasta horas, CO₂ y recursos distintos. Kantorovich plantea un <b>programa lineal</b>: elegir cuánto se produce con cada técnica para cumplir el plan al menor coste, respetando los recursos escasos.</p>
<div class="paso"><b class="n">1</b><b>Las técnicas del acero</b>, con todos sus insumos valorados en horas y CO₂ incorporados:
<table style="width:auto;margin-top:6px"><thead><tr><th>Técnica</th><th>Horas / t</th><th>t CO₂ / t</th><th>Límite</th></tr></thead><tbody>
<tr><td>Alto horno + convertidor (BF-BOF)</td><td class="n">[[VB_]]</td><td class="n">[[EB_]]</td><td>—</td></tr>
<tr><td>Horno eléctrico con chatarra (EAF)</td><td class="n">[[VE_]]</td><td class="n">[[EE_]]</td><td>chatarra: ≤ 40 % del acero</td></tr>
<tr><td>Reducción directa con hidrógeno (DRI-H₂)</td><td class="n">[[VH_]]</td><td class="n">[[EH_]]</td><td>—</td></tr>
</tbody></table></div>
<div class="paso"><b class="n">2</b><b>Programa lineal</b> para producir \(S\) toneladas de acero:
\[ \min\; [[VB_]]\,z_1 + [[VE_]]\,z_2 + [[VH_]]\,z_3 \quad\text{s.a.}\quad z_1+z_2+z_3 \ge S,\qquad z_2 \le 0{,}4\,(z_1+z_2+z_3),\qquad z\ge 0 \]
Solución: el EAF es el más barato, así que se usa hasta el límite (40 %), y el resto se hace con BF-BOF. Coste: \(0{,}6\times[[VB_]] + 0{,}4\times[[VE_]] = [[HMIN]]\) h/t, frente a [[VB_]] con la técnica única de Leontief.</div>
<div class="paso"><b class="n">3</b><b>El dual: valoraciones objetivamente determinadas.</b> Cada restricción tiene un precio sombra. El de la restricción de chatarra es \([[VB_]]-[[VE_]] = [[DUAL]]\) h: es lo que se ahorraría si se pudiera pasar una tonelada más de acero a EAF, es decir, <b>lo que vale la chatarra</b> en horas de trabajo social. Kantorovich llamó a estos precios <i>valoraciones objetivamente determinadas</i>: no son precios de mercado, son el valor que cada recurso escaso tiene <i>para el plan</i>.</div>
<div class="paso"><b class="n">4</b><b>Varios objetivos a la vez.</b> Si también importa el CO₂, se minimiza el <b>coste social</b>: \(\min\ \mathbf h^{\top}\mathbf z + \mu\,\mathbf c^{\top}\mathbf z\), con \(\mu\) = horas que se está dispuesto a dedicar para evitar 1 t de CO₂. Con \(\mu=[[MU]]\): BF-BOF cuesta \([[VB_]] + [[MU]]\times[[EB_]] = [[SB]]\) y DRI-H₂ \([[VH_]] + [[MU]]\times[[EH_]] = [[SH]]\). El hidrógeno pasa a ser mejor y sustituye al alto horno. Variando \(\mu\) se obtiene la <b>frontera de Pareto</b>: el conjunto de planes en los que no se puede bajar el CO₂ sin subir las horas.</div>
<div class="paso"><b class="n">5</b><b>Producción máxima.</b> El mismo modelo se puede plantear al revés: con unas horas \(\bar H\) dadas, \(\max\ q\) sujeto a \(B\mathbf z \ge q\,\mathbf e_j,\ \mathbf h^{\top}\mathbf z\le \bar H\). Elegir bien las técnicas permite producir más con el mismo trabajo. En cada ficha se indica cuánto más.</div>
<div class="formula k"><div class="tt">Forma general que usa el modelo completo</div>
\[ \min_{\mathbf z\ge 0}\ \mathbf h^{\top}\mathbf z+\mu\,\mathbf c^{\top}\mathbf z\quad\text{s.a.}\quad B\mathbf z\ge\mathbf y\ \ (\text{balance}),\quad z_{\text{EAF}}\le 0{,}4\!\!\sum_{\text{acero}}\!\! z,\ \ z_{\text{Al rec.}}\le 0{,}55\!\!\sum_{\text{alum.}}\!\! z,\ \ z_{\text{balasto}}\le 0{,}3\!\!\sum_{\text{vía}}\!\! z,\quad R\mathbf z\le\mathbf r \]
<p>\(B\) tiene una columna por actividad: +1 en el bien que produce y \(-a_{ik}\) en cada insumo. Si hay una sola técnica por bien, \(B = I - A\) y el problema se reduce a Leontief.</p></div>

<h3 id="m-taller">1.3 Método del taller: cómo se organiza la fabricación</h3>
<p><b>Idea.</b> Leontief y Kantorovich dicen cuánto producir y con qué técnica. El taller decide <i>cómo</i>: a qué ritmo sale cada unidad, cuántos puestos y operarios hacen falta y en qué orden se hacen las tareas. Kantorovich formuló su primer problema (1939) precisamente en un taller: repartir piezas entre máquinas para maximizar los juegos completos. El documento <code>planificacion_turismo.html</code> lo desarrolla para el motor del coche.</p>
<div class="paso"><b class="n">1</b><b>Takt</b>: cada cuánto tiene que salir una unidad.
\[ \text{takt} = \frac{\text{horas de planta al año}}{\text{unidades al año}} = \frac{2\ \text{turnos}\times 7{,}5\ \text{h}\times 230\ \text{días}}{q} = \frac{3.450\ \text{h}}{q} \]
Para [[Q]] autobuses: takt = [[TAKT]] h. Sale un autobús cada 26 horas de planta, casi dos jornadas de dos turnos.</div>
<div class="paso"><b class="n">2</b><b>Puestos y operarios</b>: si el autobús lleva [[L3]] h de ensamblaje y debe salir uno cada [[TAKT]] h, hacen falta \(\lceil [[L3]] / [[TAKT]]\rceil = [[PUESTOS]]\) operarios trabajando a la vez. Organizados en estaciones de 6, son [[EST]] estaciones, y el autobús avanza una estación cada takt.</div>
<div class="paso"><b class="n">3</b><b>Tipo de organización</b> según el takt: menos de 1 h, <b>línea continua</b> (coches); entre 1 y 60 h, <b>línea por estaciones con pulsos</b> (autobuses, marquesinas, cargadores); más de 60 h, <b>puesto fijo / proyecto</b>, donde los equipos van al producto (tranvías, vía, paradas). En este último caso el calendario se calcula con el <b>camino crítico</b> (CPM).</div>
""", Q=q_toy, XM=f(x_M, 1), XA=f(x_A, 0), L1=f(l_toy[0], 2), L2=f(l_toy[1], 1), L3=f(l_toy[2], 0), VA=f(v_A, 2), VB=f(v_B, 2),
           RHO=f(M.RHO, 3), VB_=f(vb, 2), EB_=f(eb, 2), VE_=f(ve, 2), EE_=f(ee, 2), VH_=f(vh, 2), EH_=f(eh, 2), HMIN=f(h_min, 2),
           DUAL=f(vb - ve, 2), MU=f(M.MU_CO2, 0), SB=f(vb + M.MU_CO2 * eb, 2), SH=f(vh + M.MU_CO2 * eh, 2),
           TAKT=f(3450 / q_toy, 1), PUESTOS=math.ceil(1400 / (3450 / q_toy)), EST=math.ceil(math.ceil(1400 / (3450 / q_toy)) / 6)))

# =============================================================================
# 2. CATÁLOGO DE TÉCNICAS
# =============================================================================
H.append("<h2 id='catalogo'>2. Catálogo de técnicas: todas las formas de producir cada cosa</h2>")
H.append("<p>Cada fila es una <b>actividad</b>: produce una unidad de un bien con una receta de insumos, unas horas de trabajo directo y unas emisiones directas. Cuando un bien tiene varias filas, son <b>métodos alternativos</b> entre los que Kantorovich elige. La primera de cada bien es la técnica base que usa Leontief.</p>")
H.append("<h3 id='cat-tecnicas'>2.1 Todas las actividades de producción</h3><div class='box'><table><thead><tr><th>Bien</th><th>Actividad (método)</th><th>Insumos por unidad producida</th><th>Horas directas</th><th>t CO₂ directo</th><th>Límite / nota</th></tr></thead><tbody>")
ult = None
for k, a in enumerate(A_[:M.N_PROD]):
    e = ESC[a["bien"]]
    if e != ult:
        H.append(f"<tr class='sep'><td colspan='6'>{e}</td></tr>"); ult = e
    alt = sum(1 for b in A_[:M.N_PROD] if b["bien"] == a["bien"]) > 1
    ins = ", ".join(f"{fa(q)} {UNIDAD[g]} {NOMBRE[g].lower()}" for g, q in a["ins"].items()) or "—"
    lim = next((c[3] for c in M.CUOTAS_TEC if c[0] == a["id"]), "")
    nota = "; ".join(x for x in [lim, a["nota"]] if x)
    marca = "" if not alt else (" <span class='mut'>(base)</span>" if M.BASE[a["bien"]] == k else " <span class='warn'>(alternativa)</span>")
    H.append(f"<tr><td><b>{a['bien']}</b> <span class='mut'>{UNIDAD[a['bien']]}</span></td><td>{a['nombre']}{marca}</td><td>{ins}</td>"
             f"<td class='n'>{fa(a['h'])}</td><td class='n'>{fa(a['co2'])}</td><td class='mut'>{nota}</td></tr>")
H.append("</tbody></table></div>")

# 2.2 orden de mérito
H.append(r"""<h3 id='cat-merito'>2.2 Qué técnica es mejor: comparación una a una</h3>
<p>Cada técnica alternativa se compara con la base del mismo bien, valorando sus insumos con las horas (\(v\)) y el CO₂ (\(\varepsilon\)) incorporados de Leontief:</p>
<div class="formula k">\[ v_k = h_k + \sum_i v_i\,a_{ik},\qquad \varepsilon_k = c_k + \sum_i \varepsilon_i\,a_{ik},\qquad \alpha_k = \frac{v_k - v_{\text{base}}}{\varepsilon_{\text{base}} - \varepsilon_k}\ \ \text{(horas por t CO}_2\text{ evitada)} \]
<p>Hay tres casos. <span class="ok">Dominante</span>: menos horas y menos CO₂; se usa siempre, hasta donde lo permitan los recursos. <span class="no">Dominada</span>: más horas y más CO₂; no se usa nunca. <span class="warn">Intercambio</span>: reduce CO₂ a cambio de horas; se usa si \(\alpha_k \le \mu = 3\) h/t.</p></div>
<div class="box"><table><thead><tr><th>Bien</th><th>Técnica</th><th>\(v_k\) horas/ud</th><th>\(\varepsilon_k\) t CO₂/ud</th><th>Δ horas</th><th>Δ CO₂</th><th>\(\alpha_k\) h/t</th><th>Veredicto (con μ = 3)</th></tr></thead><tbody>""")
merito = []
for g in sorted(set(a["bien"] for a in A_[:M.N_PROD])):
    ks = [k for k, a in enumerate(A_[:M.N_PROD]) if a["bien"] == g]
    if len(ks) < 2:
        continue
    vals = {k: (A_[k]["h"] + sum(q * M.v0[IX[i]] for i, q in A_[k]["ins"].items()),
                A_[k]["co2"] + sum(q * M.e0[IX[i]] for i, q in A_[k]["ins"].items())) for k in ks}
    b = M.BASE[g]
    for k in ks:
        v, e = vals[k]
        if k == b:
            ver, al = "<span class='mut'>base</span>", "—"
        else:
            dv, de = v - vals[b][0], e - vals[b][1]
            if dv <= 0 and de <= 0:
                ver, al = "<span class='ok'>dominante</span>", f(dv / -de, 2) if de < 0 else "—"
            elif dv >= 0 and de >= 0:
                ver, al = "<span class='no'>dominada</span>", "—"
            else:
                a_ = dv / -de
                ver = "<span class='ok'>intercambio, compensa</span>" if a_ <= M.MU_CO2 else "<span class='warn'>intercambio, no compensa</span>"
                al = f(a_, 2)
                merito.append((a_, A_[k]["nombre"]))
        dv_s = "—" if k == b else ("+" if v - vals[b][0] > 0 else "") + fa(v - vals[b][0])
        de_s = "—" if k == b else ("+" if e - vals[b][1] > 0 else "") + fa(e - vals[b][1])
        H.append(f"<tr><td><b>{g}</b></td><td>{A_[k]['nombre']}</td><td class='n'>{fa(v)}</td><td class='n'>{fa(e)}</td>"
                 f"<td class='n'>{dv_s}</td><td class='n'>{de_s}</td><td class='n'><b>{al}</b></td><td>{ver}</td></tr>")
H.append("</tbody></table></div>")
merito.sort()
H.append("<div class='res'><b>Orden de mérito para reducir CO₂</b> (técnicas de intercambio, de la más barata a la más cara en horas por tonelada evitada): "
         + "; ".join(f"{n.split('(')[0].strip()} ({f(a, 2)} h/t)" for a, n in merito)
         + ". Con μ = 3 h/t se adoptan todas las de α ≤ 3. El reciclaje (EAF, aluminio secundario) es dominante y va siempre primero, hasta agotar la chatarra.</div>")

# =============================================================================
# 3. FICHAS
# =============================================================================
DESC = {
    "CICE": "Turismo medio del segmento C, de unos 1.350 kg, con motor de gasolina. Se fabrica en una planta de 100.000 unidades al año: estampación, soldadura de carrocería, pintura, montaje del grupo motopropulsor y montaje final. El plan recomendado para la ciudad ya no repone coches de combustión; la ficha sirve de referencia y para la fábrica (§6).",
    "CBEV": "Turismo eléctrico de unos 1.650 kg con batería de 60 kWh y motor de 110 kW. Comparte carrocería, chasis, interior y cristales con el de combustión; cambia el motor y la caja por batería, motor eléctrico e inversor. La ciudad necesita reponer unos [[QCITY]] al año (el 8 % de los viajes que siguen en coche), que salen de la misma planta de 100.000.",
    "BUS": "Autobús urbano de 12 m, 80 plazas, unos 13 t en vacío, con batería de 420 kWh, 300 kW de tracción y kit de conducción autónoma (lidar, radar, cámaras y cómputo redundante). Vida útil de 12 años y 60.000 km al año.",
    "TRAM": "Tranvía articulado de 32 m, 220 plazas y unos 42 t, con 720 kW de tracción, una pequeña batería para tramos sin catenaria y kit autónomo doble (una cabina en cada extremo). Vida útil de 30 años y 70.000 km al año.",
    "VIA": "Un kilómetro de línea de tranvía de vía doble: carril, plataforma, catenaria, la parte proporcional de subestación de tracción y la señalización. Vida útil de 40 años. Capacidad de unos 10 millones de pkm al año por km.",
    "PAR": "Parada de tranvía con dos andenes, pérgola, validadoras, información en tiempo real y accesibilidad. 1,8 paradas por km de línea.",
    "MAR": "Marquesina de autobús con cimentación, cubierta, cerramiento de vidrio, banco y panel de información. Una por cada 180.000 pkm al año de autobús. Vida útil de 20 años.",
    "CRG": "Cargador de 150 kW para depósito de autobuses, con su electrónica de potencia, armario y cimentación. Uno por cada dos autobuses. Vida útil de 12 años.",
}
NOTAS = {
    "CICE": "El coche de combustión gasta casi todas sus horas en <b>componentes</b>: motor, transmisión y cableado son intensivos en mecanizado y montaje. El ensamblaje final solo supone un 24 % del total. Con el método recomendado su CO₂ de fabricación cae un 85 % con las mismas horas, pero el uso (27 t de CO₂ en su vida) sigue pesando unas siete veces y media más que la fabricación.",
    "CBEV": "La batería es el componente decisivo. Pasar de NMC a <b>LFP</b> reduce minerales críticos, energía y horas. Por eso Kantorovich la elige en todos los métodos que no son el base.",
    "BUS": "La <b>estructura de aluminio no compensa</b> en fabricación: ahorra 40 kWh de batería y 3,2 t de acero, pero añade 1,7 t de aluminio y 80 h de montaje. Solo compensaría si se valorase la energía ahorrada durante el uso, que es pequeña en un autobús urbano. El método recomendado es estructura de acero, batería LFP, acero con chatarra e hidrógeno y electricidad renovable.",
    "TRAM": "La <b>caja de aluminio sí compensa</b> en el tranvía: los perfiles extruidos largos se sueldan con robot y ahorran 400 h de calderería por vehículo, más que el trabajo extra del aluminio. Es un caso donde la técnica cambia <i>en el ensamblaje final</i>, no solo en los materiales.",
    "VIA": "La vía es casi toda <b>obra</b>: el 90 % de sus horas está en la construcción in situ. El balasto es la técnica que más horas ahorra, pero solo se puede usar en tramos segregados (máx. 30 %). Con μ = 3 el resto se hace en losa con hormigón LC3, que reduce el CO₂ del hormigón un tercio. La vía en césped emite menos, pero cuesta 4.000 h/km más: tiene sentido por razones urbanas (drenaje, calor), no por CO₂.",
    "PAR": "La parada es casi todo montaje en obra (95 % de las horas). Lo único que mejora el método es el CO₂ de su hormigón y su acero.",
    "MAR": "La <b>marquesina de madera</b> es la de menor CO₂, pero cuesta 15 h más por unidad. Su coste de abatimiento (unas 64 h/t) supera con mucho μ = 3, así que el plan mantiene acero y vidrio, fabricados con acero de chatarra e hidrógeno y electricidad renovable.",
    "CRG": "Casi todo su trabajo está en el armario de potencia y el montaje. El método solo cambia el origen de los materiales.",
}
CREW = {"CICE": 1, "CBEV": 1, "BUS": 6, "TRAM": 8, "VIA": 30, "PAR": 6, "MAR": 2, "CRG": 2}

H.append(r"""<h2 id="fichas">3. Producción de cada producto</h2>
<p>Cada ficha sigue el mismo esquema: <b>(a)</b> qué es y cuánto se produce; <b>(b)</b> la receta directa de cada método, con lo que aporta cada insumo en horas y CO₂; <b>(c)</b> la cadena completa con Leontief, es decir, todo lo que hay que extraer y fabricar por unidad y para el plan anual; <b>(d)</b> la comparación de métodos con Kantorovich: cuál produce más con las mismas horas, cuál emite menos y cuál se recomienda; <b>(e)</b> la organización del taller.</p>
<div class="formula"><div class="tt">Fórmulas que se usan en cada ficha</div>
\[ \text{(b)}\ \ h_{ij} = a_{ij}\,v_i,\ \ c_{ij} = a_{ij}\,\varepsilon_i \qquad
\text{(c)}\ \ \mathbf r_j = L_{\cdot j},\ \ \text{plan} = q_j\,L_{\cdot j},\ \ H^{\text{escalón}}_j = \sum_{i\in\text{esc.}} l_i\,\ell_{ij} \]
\[ \text{(d)}\ \ \min\ \mathbf h^{\top}\mathbf z\ \ |\ \ \min\ \mathbf c^{\top}\mathbf z\ \ |\ \ \min\ \mathbf h^{\top}\mathbf z+\mu\,\mathbf c^{\top}\mathbf z\quad \text{s.a.}\ B\mathbf z\ge q_j\mathbf e_j\ \text{y cuotas},\qquad q^{\max}_m = q_j\cdot\frac{h^{\text{base}}}{h^{m}} \]
\[ \text{(e)}\ \ \text{takt}=\frac{3.450\ \text{h}}{q_j},\qquad \text{operarios simultáneos}=\left\lceil\frac{l_j}{\text{takt}}\right\rceil,\qquad \text{operarios/año}=\frac{l_j\,q_j}{1.650\ \text{h}} \]</div>""")

for g in M.PRODUCTOS:
    fi = M.FICHAS[g]
    j = IX[g]
    q = fi["q"]
    mets = fi["metodos"]
    mb, mr = mets["base"], mets["comp"]
    H.append(f"<h3 id='f-{g}'>3.{M.PRODUCTOS.index(g) + 1} {NOMBRE[g]}</h3>")
    # (a)
    vida = M.VIDA.get(g)
    stock = M.PLAN["stock"].get(g, 0)
    H.append("<h4>(a) Qué es y cuánto se produce</h4><p>" + T(DESC[g], QCITY=f(M.Q_PLAN["CBEV"])) + "</p>")
    H.append(f"<div class='ficha-cab'><div>Producción anual de la ficha<b>{fa(q)} {UNIDAD[g]}</b></div>"
             f"<div>Parque del plan recomendado<b>{f(stock) if g not in ('CICE',) else '0'} {UNIDAD[g]}</b></div>"
             f"<div>Vida útil<b>{vida} años</b></div>"
             f"<div>Horas de ensamblaje final<b>{fa(mr['ens'])} h/{UNIDAD[g]}</b></div>"
             f"<div>Horas totales (recomendado)<b>{fa(mr['h_ud'])} h/{UNIDAD[g]}</b></div>"
             f"<div>CO₂ (base → recomendado)<b>{fa(mb['c_ud'])} → {fa(mr['c_ud'])} t</b></div></div>")
    # (b) receta
    H.append("<h4>(b) Receta directa de cada método</h4><p>Insumos por unidad. Las horas y el CO₂ de cada insumo son los incorporados en toda su cadena (\\(a_{ij}v_i\\) y \\(a_{ij}\\varepsilon_i\\)), con técnica base.</p>")
    cols = []
    for a, filas in fi["receta"]:
        tb = [f"<div class='box'><b>{a['nombre']}</b>{' <span class=mut>(base)</span>' if M.BASE[g] == M.ID[a['id']] else ''}"
              f"<table><thead><tr><th>Insumo</th><th>Cantidad</th><th>Horas incorporadas</th><th>t CO₂ incorporado</th><th></th></tr></thead><tbody>"]
        hmax = max([x[2] for x in filas] + [a["h"]])
        for gi, qq, hh, cc in sorted(filas, key=lambda x: -x[2]):
            tb.append(f"<tr><td>{chip(ESC[gi])} {NOMBRE[gi]}</td><td class='n'>{fa(qq)} {UNIDAD[gi]}</td><td class='n'>{fa(hh)}</td>"
                      f"<td class='n'>{fa(cc)}</td><td class='w'>{bar(hh, hmax, COL_ESC[ESC[gi]])}</td></tr>")
        tot_h = a["h"] + sum(x[2] for x in filas); tot_c = a["co2"] + sum(x[3] for x in filas)
        tb.append(f"<tr><td><b>Ensamblaje final (trabajo directo)</b></td><td></td><td class='n'><b>{fa(a['h'])}</b></td><td class='n'>{fa(a['co2'])}</td>"
                  f"<td class='w'>{bar(a['h'], hmax, '#be123c')}</td></tr>")
        tb.append(f"<tr class='hl'><td><b>Total por unidad</b></td><td></td><td class='n'><b>{fa(tot_h)}</b></td><td class='n'><b>{fa(tot_c)}</b></td><td></td></tr></tbody></table></div>")
        cols.append("".join(tb))
    H.append("<div class='two'>" + "".join(cols) + "</div>" if len(cols) > 1 else cols[0])
    # (c) Leontief cadena completa
    H.append("<h4>(c) Cadena completa con Leontief: todo lo que hay que producir</h4>")
    H.append(f"<p>Columna \\(L_{{\\cdot,{g}}}\\) de la inversa de Leontief: cantidad de cada bien que hace falta, directa o indirectamente, por cada {UNIDAD[g]} de {NOMBRE[g].lower()}. Multiplicada por {fa(q)} {UNIDAD[g]} da la producción de toda la cadena para el plan anual. Las dos últimas columnas usan la mezcla de técnicas del método recomendado.</p>")
    rows = ["<div class='box'><table><thead><tr><th>Bien</th><th>Por unidad (base)</th><th>Plan anual (base)</th><th>Por unidad (recomendado)</th><th>Plan anual (recomendado)</th></tr></thead><tbody>"]
    ult = None
    for i in sorted(range(M.NB), key=lambda i: (M.ESCALONES.index(ESC[COD]) if (COD := M.COD[i]) and ESC[COD] in M.ESCALONES else 9, i)):
        c_ = M.COD[i]
        if c_ in ("PKM",) or (fi["req"][i] < 1e-7 and fi["req_opt"][i] < 1e-7) or c_ == g:
            continue
        if ESC[c_] != ult:
            rows.append(f"<tr class='sep'><td colspan='5'>{ESC[c_]}</td></tr>"); ult = ESC[c_]
        rows.append(f"<tr><td>{NOMBRE[c_]} <span class='mut'>({UNIDAD[c_]})</span></td><td class='n'>{fa(fi['req'][i])}</td><td class='n'>{fa(fi['req'][i] * q)}</td>"
                    f"<td class='n'>{fa(fi['req_opt'][i])}</td><td class='n'>{fa(fi['req_opt'][i] * q)}</td></tr>")
    rows.append("</tbody></table></div>")
    H.append("".join(rows))
    # escalones
    tot_b = sum(fi["esc_h"].values()); tot_o = sum(fi["esc_h_opt"].values())
    mx = max(tot_b, tot_o)
    ctot_b = sum(fi["esc_c"].values()); ctot_o = sum(fi["esc_c_opt"].values()); cmx = max(ctot_b, ctot_o, 1e-9)
    H.append("<div class='box'><b>Horas y CO₂ por escalón de la cadena</b> (por unidad)<table><thead><tr><th>Escalón</th><th>Horas base</th><th>Horas recomendado</th><th>t CO₂ base</th><th>t CO₂ recomendado</th></tr></thead><tbody>"
             + "".join(f"<tr><td>{chip(e)}</td><td class='n'>{fa(fi['esc_h'][e])}</td><td class='n'>{fa(fi['esc_h_opt'][e])}</td>"
                       f"<td class='n'>{fa(fi['esc_c'][e])}</td><td class='n'>{fa(fi['esc_c_opt'][e])}</td></tr>" for e in M.ESCALONES)
             + f"<tr class='hl'><td><b>Total</b></td><td class='n'><b>{fa(tot_b)}</b></td><td class='n'><b>{fa(tot_o)}</b></td><td class='n'><b>{fa(ctot_b)}</b></td><td class='n'><b>{fa(ctot_o)}</b></td></tr></tbody></table>"
             + "<div class='two' style='margin-top:8px'><div>Horas: base / recomendado"
             + stack([(fi['esc_h'][e], COL_ESC[e], e) for e in M.ESCALONES], mx) + stack([(fi['esc_h_opt'][e], COL_ESC[e], e) for e in M.ESCALONES], mx)
             + "</div><div>CO₂: base / recomendado" + stack([(fi['esc_c'][e], COL_ESC[e], e) for e in M.ESCALONES], cmx)
             + stack([(fi['esc_c_opt'][e], COL_ESC[e], e) for e in M.ESCALONES], cmx) + "</div></div>"
             + "<div class='leg'>" + "".join(f"<span style='background:{COL_ESC[e]}'></span>{e}" for e in M.ESCALONES) + "</div></div>")
    # (d) Kantorovich
    H.append("<h4>(d) Métodos de producción comparados con Kantorovich</h4>")
    H.append("<p>Cada fila es la solución de un programa lineal distinto sobre <i>todas</i> las técnicas de la cadena del producto. <b>Producción con las mismas horas</b>: cuántas unidades saldrían con las horas que gasta el método base. <b>Con las mismas horas y el mismo CO₂</b>: el mínimo de las dos razones, es decir, cuántas unidades se pueden hacer sin gastar más horas <i>ni</i> emitir más que el método base.</p>")
    rows = ["<div class='box'><table><thead><tr><th>Método</th><th>Técnicas elegidas</th><th>Horas/ud</th><th>Ensamblaje/ud</th><th>t CO₂/ud</th><th>Coste social h + 3·CO₂</th><th>Producción con las mismas horas</th><th>Con las mismas horas y el mismo CO₂</th></tr></thead><tbody>"]
    for key, m in mets.items():
        ratio_h = mb["h_ud"] / m["h_ud"]
        ratio_hc = min(ratio_h, mb["c_ud"] / m["c_ud"] if m["c_ud"] > 0 else 9)
        cls = " class='rec'" if key == "comp" else ""
        rows.append(f"<tr{cls}><td><b>{m['nombre']}</b></td><td>{mezcla_html(m['mezcla'])}</td><td class='n'>{fa(m['h_ud'])}</td>"
                    f"<td class='n'>{fa(m['ens'])}</td><td class='n'>{fa(m['c_ud'])}</td><td class='n'>{fa(m['h_ud'] + M.MU_CO2 * m['c_ud'])}</td>"
                    f"<td class='n'>{fa(q * ratio_h)} <span class='mut'>({'+' if ratio_h >= 1 else ''}{pct(ratio_h - 1, 1)})</span></td>"
                    f"<td class='n'>{fa(q * ratio_hc)} <span class='mut'>({'+' if ratio_hc >= 1 else ''}{pct(ratio_hc - 1, 1)})</span></td></tr>")
    rows.append("</tbody></table></div>")
    H.append("".join(rows))
    mh, mc = mets["h"], mets["c"]
    du = mh["cuotas"]
    H.append(T("""<div class="res"><b>Qué método optimiza mejor la producción.</b>
<ul>
<li><b>Para producir más con el mismo trabajo</b>, el mejor es el de <b>mínimo trabajo</b>: [[HH]] h/ud frente a [[HB]] del base. Con las mismas horas salen <b>[[QH]] unidades en vez de [[Q]]</b> ([[GH]]).</li>
<li><b>Para emitir lo mínimo</b>, el de <b>mínimo CO₂</b>: [[CC]] t/ud frente a [[CB]] (−[[RC]]), a cambio de [[DHC]] h/ud respecto al de mínimo trabajo.</li>
<li><b>Recomendado (coste social mínimo)</b>: [[HR]] h/ud y [[CR]] t/ud. Recoge casi toda la reducción de CO₂ y mantiene [[GR]] de producción con las mismas horas.</li>
<li><b>Valor de los recursos escasos</b> (duales del método de mínimo trabajo): [[DUALES]].</li>
</ul></div>""", HH=fa(mh["h_ud"]), HB=fa(mb["h_ud"]), QH=fa(q * mb["h_ud"] / mh["h_ud"]), Q=fa(q),
               GH=("+" + pct(mb["h_ud"] / mh["h_ud"] - 1, 1)), CC=fa(mc["c_ud"]), CB=fa(mb["c_ud"]), RC=pct(1 - mc["c_ud"] / mb["c_ud"], 0),
               DHC=("+" if mc["h_ud"] >= mh["h_ud"] else "") + fa(mc["h_ud"] - mh["h_ud"]), HR=fa(mr["h_ud"]), CR=fa(mr["c_ud"]),
               GR=("+" if mb["h_ud"] / mr["h_ud"] >= 1 else "") + pct(mb["h_ud"] / mr["h_ud"] - 1, 1),
               DUALES="; ".join(f"{dict(ace_eaf='cada t de acero que se pudiera pasar a EAF ahorraría', alu_s='cada t de aluminio que se pudiera reciclar ahorraría', via_b='cada km más que se pudiera hacer en balasto ahorraría')[k]} <b>{fa(v / (fi['q'] if False else 1))} h</b>"
                                for k, v in du.items() if v > 1e-6) or "ningún recurso escaso limita este producto"))
    H.append(f"<p>{NOTAS[g]}</p>")
    # frontera del producto
    fr = fi["frontera"]
    if fr:
        H.append("<div class='box'><b>Frontera horas–CO₂ del producto</b> (ε-restricción: mínimo de horas para cada techo de CO₂ por unidad). μ es el precio sombra: horas por cada t de CO₂ que se recorta.<table><thead><tr><th>Techo t CO₂/ud</th><th>Horas/ud mínimas</th><th>μ (h/t)</th></tr></thead><tbody>"
                 + "".join(f"<tr><td class='n'>{fa(p['c'])}</td><td class='n'>{fa(p['h'])}</td><td class='n'>{fa(p['mu'])}</td></tr>" for p in fr)
                 + "</tbody></table></div>")
    # (e) taller
    H.append("<h4>(e) Organización del taller</h4>")
    takt = fi["takt_h"]
    crew = CREW[g]
    if g in ("CICE", "CBEV"):
        txt = T("""<p>Producción de la planta: [[Q]] coches al año. <b>Takt = 3.450 h / [[Q]] = [[TK]] min</b>. Ensamblaje final de [[L]] h por coche → \\(\\lceil [[L]]\\cdot 60 / [[TK]]\\rceil\\) = <b>[[P]] puestos de operario simultáneos por turno</b>, en una <b>línea continua</b>. El tramo de 14 tareas de la línea, balanceado por pesos posicionales, y el taller de motores, resuelto como problema de juegos completos, están en <code>planificacion_turismo.html</code>. La ciudad absorbe [[QC]] coches al año de esta planta (un [[SH]] de su producción).</p>""",
                Q=f(q), TK=f(takt * 60, 2), L=fa(fi["l_ens"]), P=f(fi["puestos"]), QC=f(M.Q_PLAN["CBEV"]),
                SH=pct(M.Q_PLAN["CBEV"] / q, 1))
    elif takt < 60:
        est = math.ceil(fi["puestos"] / crew)
        txt = T("""<p>Producción: [[Q]] al año. <b>Takt = 3.450 / [[Q]] = [[TK]] h</b>: [[ORG]]. Ensamblaje de [[L]] h por unidad → <b>[[P]] operarios trabajando a la vez</b>, organizados en <b>[[E]] estaciones de [[C]] operarios</b>. Cada takt, todas las unidades avanzan una estación. Plantilla de ensamblaje: [[OP]] operarios-año (a 1.650 h por operario).</p>""",
                Q=fa(q), TK=f(takt, 1), ORG=fi["org"].lower(), L=fa(fi["l_ens"]), P=f(fi["puestos"]), E=est, C=crew,
                OP=f(fi["operarios"], 1))
    else:
        txt = T("""<p>Producción: [[Q]] al año. <b>Takt = [[TK]] h</b>: con tan pocas unidades no tiene sentido una línea. La organización es [[ORG]]. Con [[L]] h por unidad y equipos de [[C]] personas, cada unidad ocupa a un equipo unas [[SEM]] semanas. Hacen falta [[OP]] operarios-año para la producción anual.</p>""",
                Q=fa(q), TK=f(takt, 0), ORG=fi["org"].lower(), L=fa(fi["l_ens"]), C=crew, SEM=f(fi["l_ens"] / crew / 37.5, 0),
                OP=f(fi["operarios"], 1))
    H.append(txt)
    if g == "VIA":
        TT = M.T_VIA
        rows = ["<div class='box'><b>Camino crítico de la construcción de 1 km de vía</b><div class='gantt'>"]
        for a in M.CPM_VIA:
            k = a[0]; crit = M.HOLG[k] == 0
            rows.append(f"<div class='row'><div class='lab'><b>{k}</b> {a[1]}</div><div class='track'>"
                        f"<span class='b {'crit' if crit else 'nc'}' style='left:{100 * M.ES[k] / TT:.2f}%;width:{100 * a[2] / TT:.2f}%'>{a[2]} d</span></div></div>")
        rows.append("</div><table style='margin-top:10px'><thead><tr><th></th><th>Actividad</th><th>Días</th><th>Precede</th><th>Inicio</th><th>Fin</th><th>Holgura</th></tr></thead><tbody>")
        for a in M.CPM_VIA:
            k = a[0]
            rows.append(f"<tr{' class=hl' if M.HOLG[k] == 0 else ''}><td><b>{k}</b></td><td>{a[1]}</td><td class='n'>{a[2]}</td><td>{', '.join(a[3]) or '—'}</td>"
                        f"<td class='n'>{M.ES[k]}</td><td class='n'>{M.EF[k]}</td><td class='n'>{M.HOLG[k]}</td></tr>")
        crit = " → ".join(a[0] for a in M.CPM_VIA if M.HOLG[a[0]] == 0)
        rows.append(f"</tbody></table><p><b>Duración: {TT} días por tramo de 1 km. Ruta crítica: {crit}</b>: la subestación, por sus plazos de equipos. Fórmulas: \\(ES_j=\\max_{{i\\in\\text{{pred}}}}EF_i\\), \\(EF_j=ES_j+d_j\\), \\(H_j=LS_j-ES_j\\). Para construir los {f(M.PLAN['stock']['VIA'])} km del plan en unos 5 años hay que trabajar en unos {math.ceil(M.PLAN['stock']['VIA'] / 5 * TT / 230)} tramos a la vez.</p></div>")
        H.append("".join(rows))

# =============================================================================
# 3 bis. PROCESOS DE FABRICACIÓN (juegos completos)
# =============================================================================
H.append(r"""<h2 id="procesos">3 bis. Procesos de fabricación: qué proceso maximiza la producción</h2>
<p>Aquí <b>método de producción</b> significa <b>proceso de fabricación</b>: cómo se hace físicamente cada pieza. Por ejemplo, estampar y soldar frente a fundir de una pieza (gigacasting), soldar a mano frente a soldar por fricción con robot, u hormigonar in situ frente a prefabricar. Cada producto es un <b>juego completo</b> de piezas, y cada pieza se puede hacer con varios procesos que usan recursos distintos de la planta. Es exactamente el primer problema que resolvió Kantorovich en 1939.</p>
<div class="formula k"><div class="tt">Problema de los juegos completos de Kantorovich</div>
\[ \max\ \lambda\quad\text{s.a.}\quad \sum_{p\,\in\,k} x_p \;\ge\; n_k\,\lambda\ \ \ \forall\,\text{pieza }k,\qquad \sum_p u_{rp}\,x_p \;\le\; R_r\ \ \ \forall\,\text{recurso }r,\qquad x_p\ge 0 \]
<p>\(x_p\): piezas al año hechas con el proceso \(p\). \(n_k\): piezas \(k\) por producto. \(u_{rp}\): horas de operario, horas de máquina, toneladas de material o días de calle cortada por pieza. \(R_r\): capacidad anual de la planta. \(\lambda\): productos completos al año. Los duales \(\pi_r\), que Kantorovich llamó <b>multiplicadores resolutorios</b>, dicen cuántos productos más saldrían por cada unidad extra del recurso \(r\): señalan el cuello de botella.</p></div>
<p>Para cada producto se resuelven tres casos: <b>todo con el proceso tradicional</b>, <b>todo con el proceso nuevo</b> y la <b>mezcla óptima de Kantorovich</b>. Casi siempre gana la mezcla: cada proceso se usa hasta que satura su máquina y el resto se hace con el otro.</p>""")
for key, pl in PR.PLANTAS.items():
    r = PR.RES[key]
    o, t, nw = r["opt"], r["trad"], r["nuevo"]
    recs = pl["recursos"]
    H.append(f"<h3>{pl['nombre']}</h3>")
    H.append("<div class='box'><table><thead><tr><th>Pieza</th><th>Proceso</th><th>Datos físicos</th>"
             + "".join(f"<th>{recs[rr][0].split('(')[0]} ({recs[rr][1]}/pieza)</th>" for rr in recs)
             + "<th>Piezas/año en el óptimo</th></tr></thead><tbody>")
    for p, pr in enumerate(pl["procesos"]):
        x = o["x"][p]
        cls = " class='rec'" if x > 1e-6 else ""
        H.append(f"<tr{cls}><td><b>{next(n for k, n, _ in pl['piezas'] if k == pr[0])}</b></td><td>{pr[1]}</td><td class='mut'>{pr[3]}</td>"
                 + "".join(f"<td class='n'>{fa(pr[2][rr]) if rr in pr[2] else '—'}</td>" for rr in recs)
                 + f"<td class='n'><b>{fa(x) if x > 1e-6 else '0'}</b></td></tr>")
    H.append("</tbody></table></div>")
    H.append("<div class='two'><div class='box'><b>Producción máxima (productos completos al año)</b><table><tbody>"
             f"<tr><td>Todo con el proceso tradicional</td><td class='n'>{fa(t['lam'])}</td></tr>"
             f"<tr><td>Todo con el proceso nuevo</td><td class='n'>{fa(nw['lam'])}</td></tr>"
             f"<tr class='rec'><td><b>Mezcla óptima de Kantorovich</b></td><td class='n'><b>{fa(o['lam'])}</b> "
             f"<span class='mut'>(+{pct(o['lam'] / max(t['lam'], nw['lam']) - 1, 0)} sobre el mejor proceso único)</span></td></tr></tbody></table></div>"
             "<div class='box'><b>Uso de recursos y multiplicadores resolutorios</b><table><thead><tr><th>Recurso</th><th>Usado / disponible</th><th>π: productos extra por unidad de recurso</th></tr></thead><tbody>"
             + "".join(f"<tr><td>{recs[rr][0]}</td><td class='n'>{f(o['uso'][rr])} / {f(recs[rr][2])} {recs[rr][1]}</td>"
                       f"<td class='n'>{('<b>' + fa(o['dual_rec'][rr]) + '</b> (cuello de botella)') if o['dual_rec'][rr] > 1e-9 else '0 (sobra)'}</td></tr>" for rr in recs)
             + "</tbody></table></div></div>")
H.append("""<div class="res"><b>Resumen: qué proceso maximiza la producción.</b>
<ul>
<li><b>Coche</b>: carrocería mitad estampada y soldada, mitad con gigacasting (el aluminio y los robots de soldadura son el límite). Bloque motor mixto: hierro fundido y aluminio inyectado. Cigüeñal de fundición nodular, que gana siempre a la forja.</li>
<li><b>Autobús</b>: estructura sobre todo en kit de aluminio atornillado, hasta saturar el CNC, y el resto soldada en acero. Paneles de chapa de acero, porque el composite gasta más horas. Batería cell-to-pack con robot.</li>
<li><b>Tranvía</b>: caja sobre todo de aluminio soldado por fricción, hasta saturar la máquina FSW. Bogies mitad soldados, mitad fundidos y mecanizados.</li>
<li><b>Vía</b>: plataforma mixta, prefabricada hasta saturar la planta y el resto in situ. Carril en barras largas soldadas en taller. El cuello de botella es la <b>calle cortada</b>, no las horas.</li>
<li><b>Parada</b>: sobre todo modular prefabricada. <b>Marquesina</b>: siempre kit cortado por láser y atornillado. <b>Cargador</b>: mezcla de módulos en rack y cableado a mano, porque el banco de pruebas limita.</li>
</ul></div>""")

# =============================================================================
# 4. PLAN AGREGADO
# =============================================================================
z = M.S["comp"]["z"]
H.append(r"""<h2 id="agregado">4. Plan de producción agregado (plan recomendado, un año)</h2>
<p>Es la solución completa de Kantorovich para la ciudad: cuánto produce cada sector en un año y con qué técnica. Equivale a la ecuación de Leontief \(\mathbf x = A^*\mathbf x + \mathbf y\), con la matriz \(A^*\) de las técnicas elegidas. Incluye la reposición anual de vehículos e infraestructura y toda la energía de operación. Los coches eléctricos salen de la planta de 100.000 (§6); aquí solo cuenta la parte que corresponde a la ciudad.</p>""")
rows = ["<div class='box'><table><thead><tr><th>Bien</th><th>Producción anual</th><th>Técnicas (reparto)</th><th>Horas directas</th><th>t CO₂ directo</th></tr></thead><tbody>"]
ult = None
for g in M.COD:
    if g == "PKM":
        continue
    ks = [k for k, a in enumerate(A_[:M.N_PROD]) if a["bien"] == g]
    tot = z[ks].sum()
    if tot < 1e-6:
        continue
    if ESC[g] != ult:
        rows.append(f"<tr class='sep'><td colspan='5'>{ESC[g]}</td></tr>"); ult = ESC[g]
    rep = " + ".join(f"{pct(z[k] / tot, 0)} {TEC_CORTO.get(A_[k]['id'], A_[k]['nombre'])}" for k in ks if z[k] / tot > 1e-3) if len(ks) > 1 else A_[ks[0]]["nombre"]
    rows.append(f"<tr><td><b>{NOMBRE[g]}</b></td><td class='n'>{fa(tot)} {UNIDAD[g]}</td><td>{rep}</td><td class='n'>{f(sum(z[k] * A_[k]['h'] for k in ks))}</td>"
                f"<td class='n'>{f(sum(z[k] * A_[k]['co2'] for k in ks))}</td></tr>")
hop = sum(z[k] * A_[k]["h"] for k in M.PK); cop = sum(z[k] * A_[k]["co2"] for k in M.PK)
rows.append(f"<tr class='sep'><td colspan='5'>Operación del servicio</td></tr><tr><td><b>Movilidad</b></td><td class='n'>{f(M.D)} mil pkm</td><td>"
            + " + ".join(f"{pct(z[M.ACT_MODO[m]] / M.D, 1)} {MODOS[m]['nombre'].lower()}" for m in MODOS if z[M.ACT_MODO[m]] > 1)
            + f"</td><td class='n'>{f(hop)}</td><td class='n'>{f(cop)}</td></tr>")
rows.append(f"<tr class='hl'><td><b>Total</b></td><td></td><td></td><td class='n'><b>{f(M.S['comp']['horas'])}</b></td><td class='n'><b>{f(M.S['comp']['co2'])}</b></td></tr></tbody></table></div>")
H.append("".join(rows))
gr = comp["grupos"]
H.append("<div class='box'><b>Horas del plan por escalón</b><table><thead><tr><th>Escalón</th><th>Horas/año plan recomendado</th><th>Horas/año coche-céntrico</th><th></th></tr></thead><tbody>"
         + "".join(f"<tr><td>{k}</td><td class='n'>{f(gr.get(k, 0))}</td><td class='n'>{f(ref['grupos'].get(k, 0))}</td><td class='w'>{bar(gr.get(k, 0), max(ref['grupos'].values()), '#4338ca')}</td></tr>"
                   for k in list(M.ESCALONES) + ["Operación y mantenimiento"])
         + "</tbody></table></div>")

# =============================================================================
# 5. CIUDAD
# =============================================================================
H.append(T(r"""<h2 id="ciudad">5. Movilidad de la ciudad: qué combinación de modos producir</h2>
<div class="formula"><div class="tt">Demanda</div>
\[ D = [[HAB]]\ \text{hab}\times 2{,}6\ \tfrac{\text{viajes}}{\text{día}}\times 0{,}62\ \text{(motorizados)}\times 6{,}8\ \text{km}\times 365 = [[D]]\ \text{millones de pkm/año} \]
<p>No todo el mundo conduce: como máximo el 58 % de los pkm puede ir en coche (personas con carné y coche, ocupación 1). Al menos un 8 % va en coche por falta de alternativa (pedanías, noche, puerta a puerta). El tranvía solo cabe en corredores densos (≤ 45 % y ≤ 60 km de línea) y el autobús cubre al menos el 10 % del territorio disperso de los [[SUP]] km².</p></div>
<h3 id="c-eficiencia">5.1 Eficiencia de cada modo</h3>
<div class="formula">\[ \eta_e=\frac{\text{energía en rueda}}{\text{energía final}},\quad \eta_o=\frac{n}{\text{plazas}},\quad \eta_m=\frac{100\,n}{M+100\,n},\quad \eta_{\text{útil}}=\eta_e\,\eta_m,\quad e_{\text{pkm}}=\frac{e_{\text{vkm}}}{n} \]
<p>\(\eta_m\) aplica tu fórmula 100/(p+100) a cualquier ocupación \(n\). Como la ocupación ya entra en \(\eta_m\), el producto \(\eta_e\eta_o\eta_m\) la cuenta dos veces: lo muestro como índice, pero el rendimiento físico es \(\eta_{\text{útil}}\).</p></div>""",
           HAB=f(M.HAB), D=f(M.D / 1000, 0), SUP=f(M.SUP)))
rows = ["<div class='box'><table><thead><tr><th>Modo</th><th>Masa</th><th>n / plazas</th><th>\\(\\eta_e\\)</th><th>\\(\\eta_o\\)</th><th>\\(\\eta_m\\)</th><th>\\(\\eta_{\\text{útil}}\\)</th><th>\\(\\eta_e\\eta_o\\eta_m\\)</th><th>Wh/pkm</th><th>Horas/mil pkm</th><th>g CO₂/pkm</th></tr></thead><tbody>"]
for k, m in MODOS.items():
    rows.append(f"<tr><td><b>{m['nombre']}</b></td><td class='n'>{f(m['masa'])} kg</td><td class='n'>{f(m['ocup'])}/{m['plazas']}</td><td class='n'>{pct(m['eta_e'], 0)}</td>"
                f"<td class='n'>{pct(m['eta_o'], 1)}</td><td class='n'>{pct(m['eta_m'], 2)}</td><td class='n'><b>{pct(m['eta_util'], 2)}</b></td><td class='n'>{pct(m['eta_triple'], 3)}</td>"
                f"<td class='n'>{f(m['kwh_pkm'] * 1000)}</td><td class='n'>{f(m['h_tot'], 2)}</td><td class='n'>{f(m['c_tot'] * 1000, 1)}</td></tr>")
rows.append("</tbody></table></div>")
H.append("".join(rows))
H.append("<h3 id='c-escenarios'>5.2 Escenarios y óptimos de Kantorovich</h3><div class='box'><table><thead><tr><th>Escenario</th><th>% coche comb.</th><th>% coche eléc.</th><th>% bus</th><th>% tranvía</th><th>M horas/año</th><th>t CO₂/año</th><th>MWh energía</th></tr></thead><tbody>")
for k, nom in M.ESCENARIOS:
    ii = M.I[k]
    H.append(f"<tr{' class=rec' if k == 'comp' else ''}><td><b>{nom}</b>{stack([(ii['pkm'][m], MODOS[m]['color'], m) for m in MODOS], ii['tot'])}</td>"
             + "".join(f"<td class='n'>{f(100 * ii['pkm'][m] / ii['tot'], 1)}</td>" for m in MODOS)
             + f"<td class='n'>{f(ii['horas'] / 1e6, 2)}</td><td class='n'>{f(ii['co2'])}</td><td class='n'>{f(ii['energia'])}</td></tr>")
H.append("</tbody></table><div class='leg'>" + "".join(f"<span style='background:{m['color']}'></span>{m['nombre']}" for m in MODOS.values()) + "</div></div>")
H.append(T("<p>Con las mismas horas y el mismo CO₂ que el escenario coche-céntrico, el programa de <b>máxima movilidad</b> (\\(\\max t\\) s.a. \\(B\\mathbf z\\ge t\\,\\mathbf e_{\\text{PKM}}\\)) produce <b>×[[M]]</b> los pkm actuales.</p>", M=f(M.S["max"]["t"] / M.D, 2)))
# Pareto
pts = M.PARETO
W, Hh, pad = 760, 330, 64
xs = [p["co2"] for p in pts] + [M.I[k]["co2"] for k in ("ref", "bev", "bus")]
ys = [p["horas"] for p in pts] + [M.I[k]["horas"] for k in ("ref", "bev", "bus")]
lx0, lx1 = math.log10(min(xs) * 0.8), math.log10(max(xs) * 1.3)
y1 = max(ys) * 1.08
X = lambda c: pad + (math.log10(c) - lx0) / (lx1 - lx0) * (W - pad - 20)
Y = lambda h: Hh - 40 - h / y1 * (Hh - 60)
svg = [f'<svg viewBox="0 0 {W} {Hh}" class="chart">']
for t in [5e3, 1e4, 2e4, 5e4, 1e5, 2e5, 4e5]:
    if lx0 <= math.log10(t) <= lx1:
        svg.append(f'<line x1="{X(t):.1f}" y1="20" x2="{X(t):.1f}" y2="{Hh - 40}" class="grid"/><text x="{X(t):.1f}" y="{Hh - 24}" class="tk" text-anchor="middle">{f(t / 1000)} kt</text>')
for t in np.arange(0, y1, 1e6):
    svg.append(f'<line x1="{pad}" y1="{Y(t):.1f}" x2="{W - 20}" y2="{Y(t):.1f}" class="grid"/><text x="{pad - 6}" y="{Y(t) + 4:.1f}" class="tk" text-anchor="end">{f(t / 1e6)} M h</text>')
svg.append('<path class="front" d="' + " ".join(f"{'M' if i == 0 else 'L'}{X(p['co2']):.1f},{Y(p['horas']):.1f}" for i, p in enumerate(pts)) + '"/>')
svg += [f'<circle cx="{X(p["co2"]):.1f}" cy="{Y(p["horas"]):.1f}" r="3.5" class="pf"/>' for p in pts]
for k, lab in [("ref", "Coche-céntrico"), ("bev", "Coche eléctrico"), ("bus", "Autobús + coche mín.")]:
    ii = M.I[k]
    svg.append(f'<circle cx="{X(ii["co2"]):.1f}" cy="{Y(ii["horas"]):.1f}" r="5" class="dom"/><text x="{X(ii["co2"]) - 8:.1f}" y="{Y(ii["horas"]) - 9:.1f}" class="lb" text-anchor="end">{lab}</text>')
svg.append(f'<circle cx="{X(comp["co2"]):.1f}" cy="{Y(comp["horas"]):.1f}" r="6" class="cp"/><text x="{X(comp["co2"]) + 9:.1f}" y="{Y(comp["horas"]) + 20:.1f}" class="lb">Recomendado</text>')
svg.append(f'<text x="{W / 2}" y="{Hh - 4}" class="ax" text-anchor="middle">t CO₂/año (escala logarítmica)</text></svg>')
H.append("<h3 id='c-pareto'>5.3 Frontera de Pareto horas–CO₂</h3><div class='formula k'>\\[ \\min\\ \\mathbf h^{\\top}\\mathbf z\\ \\ \\text{s.a.}\\ \\ \\mathbf c^{\\top}\\mathbf z\\le\\varepsilon,\\ \\text{resto del modelo};\\qquad \\mu(\\varepsilon)=-\\partial(\\mathbf h^{\\top}\\mathbf z^*)/\\partial\\varepsilon \\]</div>"
         f"<div class='box'>{''.join(svg)}<p class='leg'>Azul: planes eficientes. Rojo: escenarios dominados (peores en horas <i>y</i> en CO₂). Verde: recomendado.</p>"
         "<table><thead><tr><th>t CO₂</th><th>Horas</th><th>μ h/t</th>" + "".join(f"<th>% {x}</th>" for x in ["coche comb.", "coche eléc.", "bus", "tranvía"]) + "</tr></thead><tbody>"
         + "".join(f"<tr><td class='n'>{f(p['co2'])}</td><td class='n'>{f(p['horas'])}</td><td class='n'>{fa(p['mu'])}</td>" + "".join(f"<td class='n'>{f(100 * p['pkm'][m] / M.D, 1)}</td>" for m in MODOS) + "</tr>" for p in pts)
         + "</tbody></table></div>")
# flota
H.append("<h3 id='c-flota'>5.4 Parque, reposición anual y horas de cada producto</h3><div class='box'><table><thead><tr><th>Producto</th><th>Parque coche-céntrico</th><th>Parque recomendado</th><th>Vida</th><th>Reposición anual</th><th>Horas ensamblaje / año</th><th>Horas totales / año</th><th>Horas para construir el parque</th></tr></thead><tbody>")
tot = [0, 0, 0]
for g in M.PRODUCTOS:
    if g == "CICE" and comp["stock"]["CICE"] < 1:
        st_c = 0
    st_c = comp["stock"].get(g, 0)
    qa = comp["prod"][g]
    mr = M.FICHAS[g]["metodos"]["comp"]
    he, ht, hi = qa * mr["ens"], qa * mr["h_ud"], st_c * mr["h_ud"]
    tot = [tot[0] + he, tot[1] + ht, tot[2] + hi]
    H.append(f"<tr><td><b>{NOMBRE[g]}</b></td><td class='n'>{f(ref['stock'].get(g, 0))}</td><td class='n'><b>{f(st_c)}</b></td><td class='n'>{M.VIDA[g]}</td>"
             f"<td class='n'>{fa(qa)}</td><td class='n'>{f(he)}</td><td class='n'>{f(ht)}</td><td class='n'>{f(hi)}</td></tr>")
H.append(f"<tr class='hl'><td><b>Total</b></td><td></td><td></td><td></td><td></td><td class='n'><b>{f(tot[0])}</b></td><td class='n'><b>{f(tot[1])}</b></td><td class='n'><b>{f(tot[2])}</b></td></tr></tbody></table></div>")

# =============================================================================
# 6. FÁBRICA
# =============================================================================
fb = M.FAB
H.append(T(r"""<h2 id="fabrica">6. Máximo de coches que puede producir la fábrica</h2>
<p>Con las horas de toda la cadena fijadas en las que necesita el plan base de 100.000 coches de combustión (\(\bar H\) = [[HF]] h), ¿cuántos coches se pueden producir eligiendo bien los métodos?</p>
<div class="formula k">\[ \max\ N = z_{\text{CICE}}+z_{\text{CBEV}}\quad\text{s.a.}\quad B\mathbf z\ge 0,\ \ \mathbf h^{\top}\mathbf z\le\bar H,\ \ \text{cuotas de chatarra},\ \ \text{celdas}\le 6\ \text{GWh},\ \ (\mathbf c^{\top}\mathbf z\le\bar C) \]</div>
<div class="box"><table><thead><tr><th>Plan</th><th>Coches</th><th>t CO₂ fabricación</th><th>t CO₂/coche</th></tr></thead><tbody>
<tr><td>Leontief, técnica base, combustión</td><td class="n">[[NB]]</td><td class="n">[[CB]]</td><td class="n">[[CBU]]</td></tr>
<tr class="rec"><td>Kantorovich, combustión (mejor método)</td><td class="n"><b>[[NO]]</b></td><td class="n">[[CO]]</td><td class="n">[[COU]]</td></tr>
<tr><td>Kantorovich, eléctrico</td><td class="n">[[NE]]</td><td class="n">[[CE]]</td><td class="n">[[CEU]]</td></tr>
</tbody></table></div>""", HF=f(M.H_FAB), NB=f(fb["base"]["N"]), CB=f(fb["base"]["co2"]), CBU=f(fb["base"]["co2"] / fb["base"]["N"], 2),
           NO=f(fb["opt"]["N"]), CO=f(fb["opt"]["co2"]), COU=f(fb["opt"]["co2"] / fb["opt"]["N"], 2),
           NE=f(fb["bev"]["N"]), CE=f(fb["bev"]["co2"]), CEU=f(fb["bev"]["co2"] / fb["bev"]["N"], 2)))
H.append("<div class='two'><div class='box'><b>Máximo de coches con techo de CO₂ de fabricación</b><table><thead><tr><th>Techo</th><th>Coches</th><th>Técnicas activas</th></tr></thead><tbody>"
         + "".join(f"<tr><td class='n'>{pct(fr_, 0)}</td><td class='n'>{f(r['N']) if r else '—'}</td><td>{', '.join(TEC_CORTO[t] for t in ['ace_bof', 'ace_eaf', 'ace_h2', 'alu_p', 'alu_s', 'ele_t', 'ele_r', 'bat_lfp'] if r and r['tec'].get(t, 0) > 1e-6)}</td></tr>" for fr_, r in M.FAB_SENS)
         + "</tbody></table></div><div class='box'><b>Con techo de CO₂ de ciclo de vida</b> (fabricación + 180.000 km de uso)<table><thead><tr><th>Techo</th><th>Combustión</th><th>Eléctricos</th><th>Total</th></tr></thead><tbody>"
         + "".join(f"<tr><td class='n'>{pct(fr_, 0)}</td><td class='n'>{f(r['n']['CICE'])}</td><td class='n'>{f(r['n']['CBEV'])}</td><td class='n'><b>{f(r['N'])}</b></td></tr>" for fr_, r in M.FAB_VIDA if r)
         + "</tbody></table></div></div>")
H.append(T("<div class='res'>Elegir bien los métodos da <b>[[G]] más coches</b> con las mismas horas y <b>[[R]] menos CO₂</b> de fabricación. Se puede recortar un 65 % el CO₂ de fabricación sin perder producción. En cambio, si se limita el CO₂ de toda la vida del coche, la fábrica tiene que pasarse al eléctrico y produce menos coches. <b>Maximizar coches y minimizar CO₂ están en conflicto. Lo que deshace el conflicto es el cambio de modo (§5).</b></div>",
           G=pct(fb["opt"]["N"] / fb["base"]["N"] - 1, 1), R=pct(1 - fb["opt"]["co2"] / fb["base"]["co2"], 0)))

# =============================================================================
# 7. SUPUESTOS
# =============================================================================
H.append(r"""<h2 id="supuestos">7. Supuestos y límites</h2><ul>
<li><b>Coeficientes ilustrativos</b>, con órdenes de magnitud realistas, pero no son datos de ningún fabricante ni de ninguna ciudad concreta. Están todos en <code>modelo_plan.py</code> y el documento se regenera con <code>python build_plan.py</code>.</li>
<li><b>Linealidad</b>: rendimientos constantes y ocupaciones medias fijas (coche 1, autobús 22, tranvía 66). No se modelan economías de red, congestión ni costes fijos de línea.</li>
<li><b>Valoración del CO₂</b>: μ = 3 h/t (≈ 75 €/t a 25 €/h). Con otro μ cambia el método recomendado; las tablas de frontera de cada ficha muestran hasta dónde.</li>
<li><b>Fuera del modelo</b>: viario y aparcamiento del coche (que lo empeorarían), tiempo de viaje de los usuarios, capital fijo de las fábricas (moldes, prensas, robots) y la energía ahorrada en uso por los vehículos más ligeros.</li>
<li><b>Autonomía</b>: 1 supervisor remoto por cada 10 vehículos en servicio. Con conductor, autobús y tranvía suman las horas de conducción, y aun así siguen por delante del coche.</li>
</ul><p class="nota">Solver: HiGHS (<code>scipy.optimize.linprog</code>). Documento complementario: <code>planificacion_turismo.html</code> (balanceo de línea, juegos completos y camino crítico del turismo).</p>
</main></body></html>""")

html = "\n".join(H)
with open("planificacion_integral.html", "w", encoding="utf-8") as fh:
    fh.write(html)
print("OK", len(html))
