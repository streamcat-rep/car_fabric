"""Genera planificacion_viviendas_balance.html: necesidades del plan óptimo frente a la producción nacional 2025 (INE)."""
import balance_viviendas as BV
import modelo_viviendas as M

CORTO_MET = {"trad": "Tradicional", "pref": "Prefabricado 2D", "mod": "Modular 3D", "lsf": "Acero ligero (LSF)", "clt": "Madera CLT", "imp": "Impresión 3D"}
COL_MET = {"trad": "#78716c", "pref": "#0e7490", "mod": "#4338ca", "lsf": "#d97706", "clt": "#15803d", "imp": "#be123c"}


def f(x, d=0):
    s = f"{x:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return "0" if s.lstrip("-").strip("0,") == "" else s


def fa(x):
    ax = abs(x)
    if ax >= 1000: return f(x, 0)
    if ax >= 100: return f(x, 1)
    if ax >= 1: return f(x, 2)
    if ax >= 0.01: return f(x, 3)
    return f(x, 4) if ax > 0 else "0"


def pct(x, d=1):
    return f(100 * x, d) + " %"


INE = BV.INE
H = [r"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Balance de materiales: 1.000.000 de viviendas frente a la producción industrial nacional 2025</title>
<style>
:root{--bg:#fafaf9;--panel:#fff;--ink:#1c1917;--mut:#57534e;--line:#e7e5e4;--acc:#4338ca;--ok:#15803d;--red:#be123c;--warn:#b45309}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif}
.top{position:sticky;top:0;z-index:5;background:#1c1917;color:#fff;display:flex;gap:4px;padding:0 24px;align-items:center;flex-wrap:wrap}
.top a{color:#d6d3d1;text-decoration:none;padding:12px 14px;font-size:14px;border-bottom:3px solid transparent}
.top a.on{color:#fff;border-bottom-color:#fbbf24;font-weight:600}.top a:hover{color:#fff}
main{max-width:1400px;margin:0 auto;padding:32px 24px 120px}
h1{font-size:31px;line-height:1.2;margin:0 0 10px}h2{font-size:24px;margin:44px 0 10px}p,li{max-width:92ch}.lead{font-size:17px;color:var(--mut)}
.tabs{display:flex;gap:8px;margin:24px 0 8px}.tabs button{font:inherit;font-size:15px;padding:9px 18px;border-radius:8px;border:1px solid var(--line);background:#fff;cursor:pointer}
.tabs button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.panel{display:none}.panel.on{display:block}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:18px 0}
.kpi{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px 14px}.kpi .v{font-size:23px;font-weight:700}.kpi .l{font-size:13px;color:var(--mut)}
.box{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:14px 0;overflow-x:auto}
.res{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:12px 16px;margin:14px 0}
.alerta{background:#fff1f2;border:1px solid #fecdd3;border-radius:8px;padding:12px 16px;margin:14px 0}
.nota{font-size:14px;color:var(--mut);border-left:3px solid var(--line);padding-left:12px}
table{border-collapse:collapse;width:100%;font-size:12.8px;font-variant-numeric:tabular-nums}
th,td{padding:6px 7px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);font-weight:600;background:#fff}
td.n{text-align:right;white-space:nowrap}td:first-child{min-width:230px}.mut{color:var(--mut);font-size:12px}
tr.def td{background:#fff1f2}tr.just td{background:#fffbeb}tr.sep td{background:#fafaf9;font-weight:600;color:var(--mut);font-size:11.5px;text-transform:uppercase}
.pos{color:var(--ok);font-weight:600}.neg{color:var(--red);font-weight:700}
.meter{position:relative;height:12px;background:#f5f5f4;border-radius:3px;min-width:70px}
.meter span{position:absolute;left:0;top:0;bottom:0;border-radius:3px}.meter i{position:absolute;top:-3px;bottom:-3px;width:2px;background:#1c1917;left:50%}
.stack{display:flex;height:14px;border-radius:3px;overflow:hidden;margin:6px 0}.stack span{display:block;height:100%}
.leg span{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 4px 0 12px;vertical-align:middle}.leg{font-size:12.5px;color:var(--mut)}
code{font-family:ui-monospace,Menlo,monospace;font-size:12px;background:#f5f5f4;padding:1px 4px;border-radius:4px}
</style></head><body>
<div class="top"><a href="planificacion_viviendas.html">Plan de viviendas y comedores</a><a class="on" href="planificacion_viviendas_balance.html">Balance con la producción nacional 2025</a></div>
<main>"""]

H.append(f"""<h1>¿Tenemos lo que hace falta? Necesidades del plan óptimo frente a la producción industrial de España en 2025</h1>
<p class="lead">Para cada producto industrial que necesita el programa de 1.000.000 de viviendas, se compara <b>lo que hace falta</b> (plan de máxima producción de Kantorovich, con la mezcla de métodos constructivos) con <b>lo que ya se fabrica en España</b> según la Encuesta Industrial Anual de Productos de 2025. Balance = <b>tenemos − necesitamos</b>.</p>
<div class="box"><b>Cómo se calcula</b>
<ul>
<li><b>Necesidad</b>: se parte del plan de máxima producción del documento principal (§4.1). Es la mezcla óptima de métodos y, en una segunda etapa, el mínimo CO₂ para esa producción. Los materiales básicos (cemento, hormigón, aluminio, cobre, lana mineral) salen de la columna de la inversa de Leontief de la vivienda, con toda la cadena incluida. Los productos que dependen del método (tipo de acero, ladrillo, placa o yeso, madera para CLT) se calculan con los m² de cada método de la mezcla. Los productos por unidad (ventanas, sanitarios, electrodomésticos, ascensores) se calculan con dotaciones estándar por vivienda. En el caso B se suma su parte de comedor ({f(BV.PLZ_VIV, 3)} plazas por vivienda).</li>
<li><b>Necesidad anual</b> = necesidad por vivienda × ritmo máximo del plan (viviendas/año). <b>Balance anual</b> = producción nacional 2025 − necesidad anual.</li>
<li><b>Producción nacional 2025</b>: {INE['fuente']}, tomada de <a href="{INE['pagina']}">Producción industrial de España, producto a producto</a> (datos generados el {INE['generado'][:10]}). Cada fila indica los códigos de producto del INE que se suman.</li>
</ul>
<p class="nota">El balance compara con <b>toda</b> la producción nacional, que hoy ya se usa en la construcción actual, la rehabilitación y la exportación, y no tiene en cuenta las importaciones. Un balance positivo significa que la industria española fabrica más de lo que pide el programa, no que ese excedente esté libre. La columna «% de la producción nacional» es la mejor medida de la presión que el programa añade a cada sector.</p></div>
<div class="tabs"><button class="on" data-t="A">Caso A · viviendas de 70 m² con cocina</button><button data-t="B">Caso B · viviendas de 62 m² sin cocina + comedores</button></div>""")

for c, r in BV.CASOS.items():
    filas = r["filas"]
    deficit = [fl for fl in filas if fl["balance"] is not None and fl["balance"] < 0]
    justos = [fl for fl in filas if fl["cuota"] is not None and 0.5 <= fl["cuota"] <= 1]
    sindato = [fl for fl in filas if fl["prod"] is None]
    mix = r["mix"]
    H.append(f"<section class='panel{' on' if c == 'A' else ''}' id='p{c}'>")
    H.append(f"""<div class="kpis">
<div class="kpi"><div class="v">{f(r['tasa'])}</div><div class="l">viviendas al año en el plan de máxima producción → 1.000.000 en {f(r['anios'], 1)} años</div></div>
<div class="kpi"><div class="v">{len(filas)}</div><div class="l">productos industriales comparados</div></div>
<div class="kpi"><div class="v" style="color:var(--red)">{len(deficit)}</div><div class="l">con déficit: la producción nacional de 2025 no llega</div></div>
<div class="kpi"><div class="v" style="color:var(--warn)">{len(justos)}</div><div class="l">muy justos: el programa necesita entre el 50 % y el 100 % de lo que se fabrica</div></div>
<div class="kpi"><div class="v">{len(sindato)}</div><div class="l">sin dato publicado en 2025 (secreto estadístico)</div></div>
</div>
<div class="box"><b>Mezcla de métodos del plan</b>
<div class="stack">{''.join(f'<span style="width:{100 * w:.2f}%;background:{COL_MET[m]}" title="{CORTO_MET[m]}"></span>' for m, w in sorted(mix.items(), key=lambda kv: -kv[1]))}</div>
<div class="leg">{''.join(f'<span style="background:{COL_MET[m]}"></span>{CORTO_MET[m]} {pct(w, 1)}' for m, w in sorted(mix.items(), key=lambda kv: -kv[1]))}</div>
{('<p class="mut">Comedores: ' + ' + '.join(f'{pct(w, 0)} {CORTO_MET[m].lower()}' for m, w in r['plz_mix'].items() if w > 1e-3) + '</p>') if r['plz_mix'] else ''}</div>""")
    if deficit:
        H.append("<div class='alerta'><b>Productos con déficit.</b> España fabrica menos de lo que pide el programa al ritmo máximo: "
                 + "; ".join(f"<b>{fl['nombre'].lower()}</b> (faltan {f(-fl['balance'])} {fl['u']} al año; el programa pide el {pct(fl['cuota'], 0)} de lo que se fabrica)" for fl in deficit)
                 + ". Hay tres salidas: importar, ampliar la capacidad de producción o bajar el ritmo. A 200.000 viviendas al año, el balance de esos productos sería: "
                 + "; ".join(f"{fl['nombre'].lower()}: {'+' if fl['prod'] - fl['nec_200k'] >= 0 else ''}{f(fl['prod'] - fl['nec_200k'])} {fl['u']}" for fl in deficit) + ".</div>")
    H.append("<div class='box'><table><thead><tr><th>Producto</th><th>Unidad</th><th>Necesidad por vivienda</th><th>Necesidad total (1.000.000)</th>"
             f"<th>Necesidad anual (ritmo máx. {f(r['tasa'])}/año)</th><th>Producción nacional 2025 (INE)</th><th>Balance anual: tenemos − necesitamos</th>"
             "<th>% de la producción nacional</th><th></th><th>Balance a 200.000/año</th></tr></thead><tbody>")
    for fl in filas:
        cls = ""
        if fl["balance"] is not None and fl["balance"] < 0:
            cls = " class='def'"
        elif fl["cuota"] is not None and fl["cuota"] >= 0.5:
            cls = " class='just'"
        cods = ", ".join(f"<code>{k}</code>" for k in fl["codigos"])
        if fl["prod"] is None:
            prod = "<span class='mut'>sin dato (secreto estadístico)</span>"
            bal = cuo = medidor = b200 = "—"
        else:
            prod = f(fl["prod"]) + (" <span class='mut'>(parcial)</span>" if fl["parcial"] else "")
            bal = f"<span class='{'pos' if fl['balance'] >= 0 else 'neg'}'>{'+' if fl['balance'] >= 0 else ''}{f(fl['balance'])}</span>"
            cuo = pct(fl["cuota"], 1)
            w = min(fl["cuota"], 2) / 2 * 100
            col = "#be123c" if fl["cuota"] > 1 else ("#d97706" if fl["cuota"] >= 0.5 else "#15803d")
            medidor = f"<div class='meter' title='la raya marca el 100 %'><span style='width:{w:.1f}%;background:{col}'></span><i></i></div>"
            b2 = fl["prod"] - fl["nec_200k"]
            b200 = f"<span class='{'pos' if b2 >= 0 else 'neg'}'>{'+' if b2 >= 0 else ''}{f(b2)}</span>"
        H.append(f"<tr{cls}><td><b>{fl['nombre']}</b><div class='mut'>{fl['como']}<br>INE: {cods}</div></td><td>{fl['u']}</td><td class='n'>{fa(fl['nec_viv'])}</td>"
                 f"<td class='n'>{f(fl['nec_total'])}</td><td class='n'><b>{f(fl['nec_anual'])}</b></td><td class='n'>{prod}</td><td class='n'>{bal}</td>"
                 f"<td class='n'>{cuo}</td><td>{medidor}</td><td class='n'>{b200}</td></tr>")
    H.append("</tbody></table><p class='leg'><span style='background:#15803d'></span>menos del 50 % de la producción nacional<span style='background:#d97706'></span>entre el 50 % y el 100 %<span style='background:#be123c'></span>más del 100 %: déficit. La raya negra marca el 100 %.</p></div>")
    # productos INE usados
    H.append("<details class='box'><summary><b>Productos del INE utilizados (nombre completo, unidad, cantidad 2025 y 2024, valor 2025)</b></summary><table><thead><tr><th>Código</th><th>Producto (INE)</th><th>Unidad</th><th>Cantidad 2025</th><th>Cantidad 2024</th><th>Valor 2025 (miles €)</th></tr></thead><tbody>")
    vistos = []
    for fl in filas:
        for k in fl["codigos"]:
            if k in vistos:
                continue
            vistos.append(k)
            p = INE["productos"][k]
            q25 = "sin dato" if p["q2025"] is None else f(p["q2025"])
            q24 = "sin dato" if p["q2024"] is None else f(p["q2024"])
            v25 = "—" if p["v2025"] is None else f(p["v2025"])
            H.append(f"<tr><td><code>{k}</code></td><td>{p['nombre']}</td><td>{p['unidad']}</td><td class='n'>{q25}</td><td class='n'>{q24}</td><td class='n'>{v25}</td></tr>")
    H.append("</tbody></table></details></section>")

rA, rB = BV.CASOS["A"], BV.CASOS["B"]


def fila(r, i):
    return next(fl for fl in r["filas"] if fl["id"] == i)


H.append(f"""<h2>Lectura</h2>
<div class="res"><ul>
<li><b>Los materiales pesados sobran.</b> Al ritmo máximo, el programa necesita alrededor del {pct(fila(rA, 'cem')['cuota'], 0)} del cemento, el {pct(fila(rA, 'hor')['cuota'], 0)} del hormigón, el {pct(fila(rA, 'red')['cuota'], 0)} del redondo para hormigón y el {pct(fila(rA, 'baldosa')['cuota'], 0)} de las baldosas que fabrica España. La industria de base tiene tamaño suficiente.</li>
<li><b>Los cuellos de botella están en productos de equipamiento.</b> La <b>lana mineral</b> ({pct(fila(rA, 'lana')['cuota'], 0)} de la producción) y los <b>aparatos sanitarios de porcelana</b> ({pct(fila(rA, 'san')['cuota'], 0)}) no llegan. En el caso A, también <b>frigoríficos</b> ({pct(fila(rA, 'fri')['cuota'], 0)}) y <b>lavavajillas</b> ({pct(fila(rA, 'lav')['cuota'], 0)}), cuya producción nacional es muy pequeña.</li>
<li><b>Productos muy justos</b>: la chapa galvanizada para el acero ligero (cerca del {pct(fila(rA, 'gal')['cuota'], 0)}), la placa de yeso (≈{pct(fila(rA, 'placa')['cuota'], 0)}), el vidrio aislante (≈{pct(fila(rA, 'vid')['cuota'], 0)}) y los hornos de empotrar ({pct(fila(rA, 'hor2')['cuota'], 0)}). Como la industria ya los destina a la construcción actual, en la práctica podrían quedarse cortos.</li>
<li><b>El caso B elimina los déficits de electrodomésticos</b>: sin cocinas no hacen falta frigoríficos, lavavajillas, placas, hornos, campanas ni muebles de cocina, porque el equipamiento se concentra en los {f(M.COM_PROV.sum())} comedores. Mantiene los de lana mineral y sanitarios.</li>
<li><b>Para cerrar los déficits</b> hay tres palancas: ampliar las plantas de lana mineral, de sanitarios y de chapa galvanizada (que el modelo de Kantorovich puede incluir como nuevas actividades con su coste en horas), cambiar el aislamiento por otros materiales (fibra de madera, celulosa o EPS, que no tienen el mismo cuello de botella) o importar.</li>
</ul></div>
<p class="nota">Reproducible con <code>python build_viviendas_balance.py</code>. Los productos del INE están guardados en <code>datos/ine_2025_construccion.json</code> y la conversión de necesidades está en <code>balance_viviendas.py</code>. El modelo del plan (<code>modelo_viviendas.py</code>) no se ha modificado.</p>
</main>
<script>
document.querySelectorAll('.tabs button').forEach(b=>b.addEventListener('click',()=>{{
  document.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x===b));
  document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('on',p.id==='p'+b.dataset.t));
}}));
</script></body></html>""")

html = "\n".join(H)
with open("planificacion_viviendas_balance.html", "w", encoding="utf-8") as fh:
    fh.write(html)
print("OK", len(html))
