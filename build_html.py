"""Genera planificacion_turismo.html a partir de los resultados de modelo.py"""
import numpy as np
import modelo as M

S = M.SECTORES
IDX = M.IDX
N = M.N_COCHES
LE, KA, TA, BA, JO, CP = M.leontief, M.kantorovich, M.taller, M.balanceo, M.johnson, M.cpm


def f(x, d=0):
    """formato español: 1.234.567,89"""
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def bar(val, vmax, color="var(--acc)"):
    w = 0 if vmax == 0 else max(0.5, 100 * val / vmax)
    return f'<div class="bar"><span style="width:{w:.1f}%;background:{color}"></span></div>'


NIVEL_COLOR = {"Extracción": "#a16207", "Energía": "#b45309", "Materiales": "#0e7490",
               "Componentes": "#4338ca", "Producto final": "#be123c"}


def chip(nivel):
    return f'<span class="chip" style="--c:{NIVEL_COLOR[nivel]}">{nivel}</span>'


# ---------------------------------------------------------------- tablas Leontief
x, v, e, L, A = LE["x"], LE["v"], LE["e"], LE["L"], LE["A"]
j_tur = IDX["TUR"]

# matriz A en mapa de calor
cab = "".join(f"<th title='{s[1]}'>{s[0]}</th>" for s in S)
filas = []
for i, si in enumerate(S):
    celdas = []
    for j in range(len(S)):
        a = A[i, j]
        if a == 0:
            celdas.append("<td class='z'>·</td>")
        else:
            alpha = min(1, 0.15 + 0.85 * np.log10(1 + a * 10) / np.log10(151))
            txt = f(a, 3) if a < 1 else f(a, 2)
            celdas.append(f"<td style='background:rgba(67,56,202,{alpha:.2f});color:{'#fff' if alpha > .5 else '#111'}' "
                          f"title='{si[1]} por unidad de {S[j][1]}'>{txt}</td>")
    filas.append(f"<tr><th title='{si[1]}'>{si[0]}</th>{''.join(celdas)}</tr>")
tabla_A = f"<table class='mat'><thead><tr><th></th>{cab}</tr></thead><tbody>{''.join(filas)}</tbody></table>"

# leyenda de códigos
leyenda = "".join(f"<tr><td><b>{s[0]}</b></td><td>{s[1]}</td><td>{s[2]}</td><td>{chip(s[3])}</td></tr>" for s in S)

# producción bruta
xmax_por_coche = max(L[:, j_tur])
filas_x = []
for i, s in enumerate(S):
    filas_x.append(
        f"<tr><td>{chip(s[3])}</td><td><b>{s[0]}</b> {s[1]}</td><td class='n'>{f(L[i, j_tur], 4)}</td>"
        f"<td>{s[2]}</td><td class='n'>{f(x[i])}</td><td class='n'>{f(v[i], 2)}</td><td class='n'>{f(e[i], 3)}</td></tr>")
tabla_x = "".join(filas_x)

# trabajo por sector (contribución al coche)
contrib_l = M.l * L[:, j_tur]
contrib_e = M.d * L[:, j_tur]
orden_l = np.argsort(-contrib_l)
filas_l = "".join(
    f"<tr><td><b>{S[i][0]}</b> {S[i][1]}</td><td class='n'>{f(contrib_l[i], 2)} h</td>"
    f"<td class='w'>{bar(contrib_l[i], contrib_l.max(), NIVEL_COLOR[S[i][3]])}</td>"
    f"<td class='n'>{f(100 * contrib_l[i] / contrib_l.sum(), 1)} %</td></tr>"
    for i in orden_l if contrib_l[i] > 0.005)
orden_e = np.argsort(-contrib_e)
filas_e = "".join(
    f"<tr><td><b>{S[i][0]}</b> {S[i][1]}</td><td class='n'>{f(contrib_e[i] * 1000, 0)} kg</td>"
    f"<td class='w'>{bar(contrib_e[i], contrib_e.max(), '#be123c')}</td>"
    f"<td class='n'>{f(100 * contrib_e[i] / contrib_e.sum(), 1)} %</td></tr>"
    for i in orden_e if contrib_e[i] > 0.0005)

# rondas de Neumann (trabajo)
y = M.y
rondas = []
acc = 0
Ak_y = y.copy()
for k in range(7):
    trab = M.l @ Ak_y / N
    acc += trab
    rondas.append((k, trab, acc, (Ak_y[IDX['ACE']]) / N, (Ak_y[IDX['ELE']]) / N))
    Ak_y = A @ Ak_y
filas_neu = "".join(
    f"<tr><td class='n'>{k}</td><td class='n'>{f(t, 3)} h</td><td class='n'>{f(a, 2)} h</td>"
    f"<td class='n'>{f(100 * a / v[j_tur], 2)} %</td><td class='n'>{f(ac * 1000, 1)} kg</td><td class='n'>{f(el * 1000, 1)} kWh</td></tr>"
    for k, t, a, ac, el in rondas)

# composición física del coche (materiales directos + indirectos al nivel de componente)
masa = {c: L[IDX[c], j_tur] for c in ["ACE", "ALU", "COB", "POL", "CAU", "VID"]}

# ---------------------------------------------------------------- Kantorovich
ACT, z, zl, B = KA["ACT"], KA["z"], KA["z_libre"], KA["B"]
cr = KA["coste_red"]
pr = KA["precios"]
alt_idx = list(range(len(S), len(ACT)))
alternativas = {"ACE": [IDX["ACE"], alt_idx[0]], "ALU": [IDX["ALU"], alt_idx[1]],
                "ELE": [IDX["ELE"], alt_idx[2]], "BIW": [IDX["BIW"], alt_idx[3]]}


def ins_txt(ins, rec):
    partes = [f"{f(val, 3)} {k}" for k, val in ins.items()]
    partes += [f"{f(val, 2)} {k.replace('CHA_ACE', 'chatarra Fe').replace('CHA_ALU', 'chatarra Al').replace('RENOV', 'cap. renovable')}" for k, val in rec.items()]
    return ", ".join(partes) if partes else "—"


filas_tec = []
for bien, ks in alternativas.items():
    for k in ks:
        a = ACT[k]
        estado = "<span class='ok'>activa</span>" if z[k] > 1e-6 else "<span class='no'>descartada</span>"
        filas_tec.append(
            f"<tr><td><b>{bien}</b></td><td>{a[0]}</td><td>{ins_txt(a[2], a[5])}</td>"
            f"<td class='n'>{f(a[3], 2)}</td><td class='n'>{f(a[4], 3)}</td>"
            f"<td class='n'>{f(zl[k])}</td><td class='n'>{f(z[k])}</td><td class='n'>{f(cr[k], 3)}</td><td>{estado}</td></tr>")
tabla_tec = "".join(filas_tec)

filas_pr = "".join(
    f"<tr><td><b>{s[0]}</b> {s[1]}</td><td>{s[2]}</td><td class='n'>{f(v[i], 3)}</td><td class='n'>{f(pr[i], 3)}</td>"
    f"<td class='n'>{'+' if pr[i] - v[i] >= 0 else ''}{f(100 * (pr[i] - v[i]) / v[i], 1)} %</td></tr>"
    for i, s in enumerate(S))

rec_nombre = {k: v_ for k, v_ in M.RECURSOS.items()}
filas_rec = "".join(
    f"<tr><td>{rec_nombre[k][0]}</td><td class='n'>{f(rec_nombre[k][2])} {rec_nombre[k][1]}</td>"
    f"<td class='n'>{f(KA['uso'][k])}</td><td class='n'>{f(100 * KA['uso'][k] / rec_nombre[k][2], 1)} %</td>"
    f"<td class='n'><b>{f(KA['duales'][k], 3)}</b> h/{rec_nombre[k][1].replace('t CO2', 't CO₂')}</td>"
    f"<td>{'saturado → valoración positiva' if KA['duales'][k] > 1e-6 else 'con holgura → valoración nula'}</td></tr>"
    for k in ["CHA_ACE", "CHA_ALU", "RENOV", "CO2"])

co2_k = KA["uso"]["CO2"]
smax = max(s_[2] for s_ in M.sens if s_[2])
smin = min(s_[2] for s_ in M.sens if s_[2])
filas_sens = "".join(
    f"<tr><td class='n'>{f(100 * fr, 0)} %</td><td class='n'>{f(t)}</td>"
    + (f"<td class='n'>{f(ob)}</td><td class='n'>{f(ob / N, 2)}</td><td class='n'>{f(du, 3)}</td>"
       f"<td class='w'>{bar(ob - smin + (smax - smin) * 0.05, (smax - smin) * 1.05, '#0e7490')}</td>"
       if ob else "<td colspan='4' class='no'>infactible: ninguna combinación de técnicas cumple el techo</td>")
    + "</tr>"
    for fr, t, ob, du in M.sens)

# ---------------------------------------------------------------- Taller
P, MQ, PR, T = TA["PIEZAS"], TA["MAQ"], TA["PROD"], TA["T"]
cab_p = "".join(f"<th>{p[0]}<br><small>×{p[1]}/motor</small></th>" for p in P)
filas_prod = "".join(
    f"<tr><td><b>{m[0]}</b><br><small>{m[1]} máq. × {f(m[2])} h = {f(m[1] * m[2])} h</small></td>"
    + "".join(f"<td class='n'>{f(PR[i, k], 1) if PR[i, k] else '—'}</td>" for k in range(len(P))) + "</tr>"
    for i, m in enumerate(MQ))
filas_T = "".join(
    f"<tr><td><b>{m[0]}</b></td>"
    + "".join(f"<td class='n'>{f(T[i, k]) if T[i, k] > 0.5 else '·'}</td>" for k in range(len(P)))
    + f"<td class='n'>{f(T[i].sum())} / {f(TA['cap_h'][i])}</td><td class='n'><b>{f(TA['mult_maq'][i], 3)}</b></td></tr>"
    for i, m in enumerate(MQ))
fila_piezas = "".join(f"<td class='n'>{f(TA['piezas_opt'][k])}</td>" for k in range(len(P)))
fila_piezas_n = "".join(f"<td class='n'>{f(TA['piezas_naive'][k])}</td>" for k in range(len(P)))
fila_mult = "".join(f"<td class='n'>{f(TA['mult_piezas'][k], 3)}</td>" for k in range(len(P)))
mult_rel = TA['mult_piezas'] / TA['mult_piezas'].min()

# balanceo
tid = {t[0]: t for t in BA["TAREAS"]}
filas_tareas = "".join(
    f"<tr><td><b>{t[0]}</b></td><td>{t[1]}</td><td class='n'>{f(t[2], 1)}</td><td>{', '.join(t[3]) or '—'}</td>"
    f"<td class='n'>{f(BA['PW'][t[0]], 1)}</td></tr>"
    for t in sorted(BA["TAREAS"], key=lambda t: -BA["PW"][t[0]]))
est_html = []
for n_, (tareas, carga) in enumerate(BA["estaciones"], 1):
    segs = "".join(
        f"<span class='seg' style='width:{100 * tid[t][2] / BA['TAKT']:.2f}%' title='{tid[t][1]} ({f(tid[t][2], 1)} min)'>{t}</span>"
        for t in tareas)
    est_html.append(f"<div class='estrow'><div class='estlab'>E{n_}</div><div class='esttrack'>{segs}"
                    f"<span class='idle' style='width:{100 * (BA['TAKT'] - carga) / BA['TAKT']:.2f}%'></span></div>"
                    f"<div class='estval'>{f(carga, 2)} / {f(BA['TAKT'], 2)} min</div></div>")
est_html = "".join(est_html)
contenido_montaje_min = M.l[j_tur] * 60
puestos_planta = int(np.ceil(contenido_montaje_min / BA["TAKT"]))

# Johnson
CM = JO["Cmax"]
gj = []
for nom, s1, f1, s2, f2 in JO["gantt"]:
    gj.append(f"<div class='grow'><div class='glab'>{nom}</div><div class='gtrack'>"
              f"<span class='gb m1' style='left:{100 * s1 / CM:.2f}%;width:{100 * (f1 - s1) / CM:.2f}%'>E</span>"
              f"<span class='gb m2' style='left:{100 * s2 / CM:.2f}%;width:{100 * (f2 - s2) / CM:.2f}%'>S</span></div></div>")
gantt_j = "".join(gj)
filas_lotes = "".join(
    f"<tr><td>{j[0]}</td><td class='n'>{f(j[1], 1)}</td><td class='n'>{f(j[2], 1)}</td>"
    f"<td>{'Grupo 1 (p₁ ≤ p₂) → al principio, p₁ creciente' if j[1] <= j[2] else 'Grupo 2 (p₁ > p₂) → al final, p₂ decreciente'}</td></tr>"
    for j in JO["LOTES"])

# CPM
TT = CP["T"]
gc = []
filas_cpm = []
for a in CP["ACTIV"]:
    k = a[0]
    crit = CP["holg"][k] == 0
    gc.append(f"<div class='grow'><div class='glab'><b>{k}</b> {a[1]}</div><div class='gtrack'>"
              f"<span class='gb {'crit' if crit else 'nc'}' style='left:{100 * CP['ES'][k] / TT:.2f}%;width:{100 * a[2] / TT:.2f}%'>{a[2]} d</span>"
              + (f"<span class='slack' style='left:{100 * CP['EF'][k] / TT:.2f}%;width:{100 * CP['holg'][k] / TT:.2f}%'></span>" if not crit else "")
              + "</div></div>")
    filas_cpm.append(f"<tr class='{'critrow' if crit else ''}'><td><b>{k}</b></td><td>{a[1]}</td><td class='n'>{a[2]}</td><td>{', '.join(a[3]) or '—'}</td>"
                     f"<td class='n'>{CP['ES'][k]}</td><td class='n'>{CP['EF'][k]}</td><td class='n'>{CP['LS'][k]}</td>"
                     f"<td class='n'>{CP['LF'][k]}</td><td class='n'>{CP['holg'][k]}</td></tr>")
gantt_c = "".join(gc)
filas_cpm = "".join(filas_cpm)
ruta_crit = " → ".join(a[0] for a in CP["ACTIV"] if CP["holg"][a[0]] == 0)

# --------------------------------------------------------------- valores clave
kp = dict(
    N=f(N), horas=f(v[j_tur], 1), co2=f(e[j_tur], 2), co2k=f(co2_k / N, 2),
    horask=f(KA["obj"] / N, 2), horas_libre=f(KA["obj_libre"] / N, 2),
    rho=f(LE["rho"], 4), lam=f(TA["lam"]), lam_n=f(TA["lam_naive"]),
    ganancia=f(100 * (TA["lam"] / TA["lam_naive"] - 1), 1), T=TT, takt=f(BA["TAKT"], 2),
    takt_s=f(BA["TAKT"] * 60, 0), ef=f(100 * BA["eficiencia"], 1), nest=len(BA["estaciones"]),
    nmin=BA["N_min"], sumt=f(BA["sum_t"], 1), cm=f(JO["Cmax"], 1), cm0=f(JO["Cmax_orig"], 1),
    trab_tot=f(LE["trabajo_total"]), co2_tot=f(LE["co2_total"]), techo=f(KA["techo"]),
    co2_libre=f(KA["co2_libre"]), elec=f(L[IDX['ELE'], j_tur], 2), pTUR=f(pr[j_tur], 2),
    du_fe=f(KA["duales"]["CHA_ACE"], 3), du_al=f(KA["duales"]["CHA_ALU"], 3),
    du_co2=f(KA["duales"]["CO2"], 3), cr_multi=f(cr[alt_idx[3]], 3),
    min_anio=f(BA["min_anio"]), puestos=f(puestos_planta), montaje_min=f(contenido_montaje_min),
    util_taller=f(100 * N / TA["lam"], 1), seq=" → ".join(j[0] for j in JO["seq"]),
    acero_coche=f(masa["ACE"] * 1000), alu=f(masa["ALU"] * 1000), cob=f(masa["COB"] * 1000),
    pol=f(masa["POL"] * 1000), cau=f(masa["CAU"] * 1000), vid=f(masa["VID"] * 1000),
    fe=f(L[IDX['FE'], j_tur] * 1000), bau=f(L[IDX['BAU'], j_tur] * 1000), car=f(L[IDX['CAR'], j_tur] * 1000),
    cru=f(L[IDX['CRU'], j_tur] * 1000), cuc=f(L[IDX['CUC'], j_tur] * 1000),
    red_co2=f(100 * (1 - co2_k / LE["co2_total"]), 1),
    sobre=f(100 * (1 - KA["obj"] / LE["trabajo_total"]), 2),
    z_eaf=f(z[alt_idx[0]]), z_alsec=f(z[alt_idx[1]]), z_ren=f(z[alt_idx[2]]),
    z_bof=f(z[IDX['ACE']]), z_alp=f(z[IDX['ALU']]), z_term=f(z[IDX['ELE']]),
    renov_cap=f(M.RECURSOS["RENOV"][2]), vELE=f(v[IDX["ELE"]], 2), renov_uso=f(KA["uso"]["RENOV"]),
)

with open("plantillas/plantilla_turismo.html", encoding="utf-8") as fh:
    html = fh.read()

reemplazos = dict(TABLA_A=tabla_A, LEYENDA=leyenda, TABLA_X=tabla_x, FILAS_L=filas_l, FILAS_E=filas_e,
                  FILAS_NEU=filas_neu, TABLA_TEC=tabla_tec, FILAS_PR=filas_pr, FILAS_REC=filas_rec,
                  FILAS_SENS=filas_sens, CAB_P=cab_p, FILAS_PROD=filas_prod, FILAS_T=filas_T,
                  FILA_PIEZAS=fila_piezas, FILA_PIEZAS_N=fila_piezas_n, FILA_MULT=fila_mult,
                  FILAS_TAREAS=filas_tareas, EST_HTML=est_html, GANTT_J=gantt_j, FILAS_LOTES=filas_lotes,
                  GANTT_C=gantt_c, FILAS_CPM=filas_cpm, RUTA_CRIT=ruta_crit)
for k, val in reemplazos.items():
    html = html.replace("{{" + k + "}}", val)
for k, val in kp.items():
    html = html.replace("{{" + k + "}}", str(val))
assert "{{" not in html, html[html.index("{{"):html.index("{{") + 40]
with open("planificacion_turismo.html", "w", encoding="utf-8") as fh:
    fh.write(html)
print("OK planificacion_turismo.html", len(html), "bytes")
