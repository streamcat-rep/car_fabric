"""Genera planificacion_movilidad.html a partir de modelo_movilidad.py"""
import math
import numpy as np
import modelo_movilidad as M

IX, A_, MODOS = M.IX, M.A_, M.MODOS
D = M.D


def f(x, d=0):
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(x, d=1):
    return f(100 * x, d) + " %"


def bar(val, vmax, color="var(--acc)"):
    w = 0 if vmax <= 0 else max(0.6, 100 * val / vmax)
    return f'<div class="bar"><span style="width:{w:.1f}%;background:{color}"></span></div>'


def stack(parts, total_max):
    """parts: [(valor, color, etiqueta)]"""
    segs = "".join(
        f'<span title="{lab}: {f(v, 3)}" style="width:{100 * v / total_max:.2f}%;background:{c}"></span>'
        for v, c, lab in parts if v > 0)
    return f'<div class="stack">{segs}</div>'


COL = {k: m["color"] for k, m in MODOS.items()}
P = {}  # placeholders

# ---------------------------------------------------------------- 1. demanda
P.update(HAB=f(M.HAB), SUP=f(M.SUP), DENS=f(M.HAB / M.SUP), VIAJES=f(M.VIAJES_DIA, 1),
         CUOTA_MOTOR=f(100 * M.CUOTA_MOTOR), DIST=f(M.DIST_MEDIA, 1), D=f(D), D_MILL=f(D / 1e6, 2),
         PKM_HAB=f(D * 1000 / M.HAB), CUOTA_COND=f(100 * M.CUOTA_CONDUCTORES), COCHE_MIN=f(100 * M.CUOTA_COCHE_MIN),
         TRAM_MAX=f(100 * M.CUOTA_TRAM_MAX), VIA_MAX=f(M.VIA_MAX_KM), BUS_MIN=f(100 * M.CUOTA_BUS_MIN),
         KAPPA=f(M.KAPPA_VIA * 1000 / 1e6), KPKM_MAR=f(M.KPKM_POR_MAR))

# ---------------------------------------------------------------- 2. eficiencia por modo
filas = []
for k, m in MODOS.items():
    filas.append(
        f"<tr><td><span class='dot' style='background:{m['color']}'></span><b>{m['nombre']}</b></td>"
        f"<td class='n'>{f(m['masa'])} kg</td><td class='n'>{f(m['ocup'], 0)} / {m['plazas']}</td>"
        f"<td class='n'>{pct(m['eta_e'], 0)}</td><td class='n'>{pct(m['eta_o'], 1)}</td>"
        f"<td class='n'>{pct(m['eta_m'], 2)}</td><td class='n'><b>{pct(m['eta_util'], 2)}</b></td>"
        f"<td class='n'>{pct(m['eta_triple'], 3)}</td><td class='w'>{bar(m['eta_util'], 0.13, m['color'])}</td></tr>")
P["TABLA_ETA"] = "".join(filas)
car = MODOS["CICE"]
P.update(ETA_CAR_M=pct(car["eta_m"], 2), ETA_CAR_U=pct(car["eta_util"], 2), ETA_CAR_T=pct(car["eta_triple"], 3),
         ETA_BUS_U=pct(MODOS["BUS"]["eta_util"], 2), ETA_TRAM_U=pct(MODOS["TRAM"]["eta_util"], 2),
         RATIO_BUS=f(MODOS["BUS"]["eta_util"] / car["eta_util"], 1),
         RATIO_TRAM=f(MODOS["TRAM"]["eta_util"] / car["eta_util"], 1))

# kWh, horas y CO2 por pkm
hmax = max(m["h_tot"] for m in MODOS.values())
cmax = max(m["c_tot"] for m in MODOS.values())
filas_h, filas_c, filas_k = [], [], []
for k, m in MODOS.items():
    filas_h.append(
        f"<tr><td><b>{m['nombre']}</b></td><td class='n'>{f(m['h_veh'], 3)}</td><td class='n'>{f(m['h_inf'], 3)}</td>"
        f"<td class='n'>{f(m['h_ene'], 3)}</td><td class='n'>{f(m['h_oper'], 3)}</td><td class='n'><b>{f(m['h_tot'], 2)}</b></td>"
        f"<td class='w'>{stack([(m['h_veh'], '#4338ca', 'vehículo'), (m['h_inf'], '#0e7490', 'infraestructura'), (m['h_ene'], '#b45309', 'energía'), (m['h_oper'], '#a8a29e', 'operación')], hmax)}</td>"
        f"<td class='n mut'>{f(m['h_conduccion'], 1)}</td></tr>")
    filas_c.append(
        f"<tr><td><b>{m['nombre']}</b></td><td class='n'>{f(m['c_veh'] * 1000, 1)}</td><td class='n'>{f(m['c_inf'] * 1000, 1)}</td>"
        f"<td class='n'>{f(m['c_ene'] * 1000, 1)}</td><td class='n'><b>{f(m['c_tot'] * 1000, 1)}</b></td>"
        f"<td class='n'>{f((m['c_veh'] + m['c_inf'] + m['c_ene_ren']) * 1000, 1)}</td>"
        f"<td class='w'>{stack([(m['c_veh'], '#4338ca', 'vehículo'), (m['c_inf'], '#0e7490', 'infraestructura'), (m['c_ene'], '#be123c', 'energía')], cmax)}</td></tr>")
    filas_k.append(
        f"<tr><td><b>{m['nombre']}</b></td><td class='n'>{f(m['kwh_vkm'], 2)}</td><td class='n'>{f(m['ocup'], 0)}</td>"
        f"<td class='n'><b>{f(m['kwh_pkm'] * 1000, 0)}</b></td><td class='n'>{f(m['kwh_pkm'] * m['eta_e'] * 1000, 0)}</td>"
        f"<td class='w'>{bar(m['kwh_pkm'], car['kwh_pkm'], m['color'])}</td><td class='n'>{f(car['kwh_pkm'] / m['kwh_pkm'], 1)}×</td></tr>")
P.update(TABLA_HPKM="".join(filas_h), TABLA_CPKM="".join(filas_c), TABLA_KWH="".join(filas_k))

# ---------------------------------------------------------------- 3. horas por producto
PRODUCTOS = ["CICE", "CBEV", "BUS", "TRAM", "VIA", "PAR", "MAR", "CRG", "AUT", "BAT", "MEL", "BIW", "MOT", "ACE", "ALU", "HOR", "ELE"]
filas = []
for g in PRODUCTOS:
    i = IX[g]
    b = M.BIENES[i]
    filas.append(
        f"<tr><td><b>{g}</b> {b[1]}</td><td>{b[2]}</td><td class='n'><b>{f(M.l0[i], 2)}</b></td>"
        f"<td class='n'>{f(M.v0[i] - M.l0[i], 2)}</td><td class='n'><b>{f(M.v0[i], 2)}</b></td>"
        f"<td class='n'>{pct(M.l0[i] / M.v0[i], 0)}</td><td class='n'>{f(M.v1[i], 2)}</td>"
        f"<td class='n'>{f(M.e0[i], 3)}</td><td class='n'>{f(M.e1[i], 3)}</td></tr>")
P["TABLA_HORAS"] = "".join(filas)
P.update(V_CICE=f(M.v0[IX['CICE']], 1), V_CBEV=f(M.v0[IX['CBEV']], 1), V_BUS=f(M.v0[IX['BUS']]),
         V_TRAM=f(M.v0[IX['TRAM']]), V_VIA=f(M.v0[IX['VIA']]), L_BUS=f(M.l0[IX['BUS']]), L_TRAM=f(M.l0[IX['TRAM']]),
         E_CICE=f(M.e0[IX['CICE']], 2), E_CBEV=f(M.e0[IX['CBEV']], 2),
         PLAZAS_CICE=f(M.v0[IX['CICE']] / 5, 1), PLAZAS_BUS=f(M.v0[IX['BUS']] / 80, 1),
         PLAZAS_TRAM=f(M.v0[IX['TRAM']] / 220, 1),
         PKM_VIDA_CICE=f(MODOS['CICE']['km_anio'] * MODOS['CICE']['vida'] * MODOS['CICE']['ocup']),
         PKM_VIDA_BUS=f(MODOS['BUS']['km_anio'] * MODOS['BUS']['vida'] * MODOS['BUS']['ocup']),
         PKM_VIDA_TRAM=f(MODOS['TRAM']['km_anio'] * MODOS['TRAM']['vida'] * MODOS['TRAM']['ocup']),
         H_PKM_CICE=f(M.v0[IX['CICE']] / (MODOS['CICE']['km_anio'] * MODOS['CICE']['vida'] * MODOS['CICE']['ocup']) * 1000, 3),
         H_PKM_BUS=f(M.v0[IX['BUS']] / (MODOS['BUS']['km_anio'] * MODOS['BUS']['vida'] * MODOS['BUS']['ocup']) * 1000, 3),
         H_PKM_TRAM=f(M.v0[IX['TRAM']] / (MODOS['TRAM']['km_anio'] * MODOS['TRAM']['vida'] * MODOS['TRAM']['ocup']) * 1000, 3))

# ---------------------------------------------------------------- 4. comparación de técnicas
por_bien = {}
for t in M.comp_tec:
    por_bien.setdefault(t["bien"], []).append(t)
filas = []
for g, ts in por_bien.items():
    base = ts[0]
    for t in ts:
        dv, de = t["v"] - base["v"], t["e"] - base["e"]
        if t is base:
            veredicto, coste = "<span class='mut'>técnica base</span>", "—"
        elif dv <= 0 and de <= 0:
            veredicto, coste = "<span class='ok'>dominante: ahorra horas y CO₂</span>", f(dv / -de, 2) if de < 0 else "—"
        elif dv >= 0 and de >= 0:
            veredicto, coste = "<span class='no'>dominada: más horas y más CO₂</span>", "—"
        else:
            veredicto, coste = "<span class='warn'>intercambio: menos CO₂ a cambio de horas</span>", f(dv / -de, 2)
        lim = ", ".join({"CHA_FE": "chatarra de acero", "CHA_AL": "chatarra de Al", "RENOV": "capacidad renovable",
                         "CELDAS": "celdas"}[r] for r in t["rec"]) or "—"
        filas.append(f"<tr><td><b>{g}</b></td><td>{t['nombre']}</td><td class='n'>{f(t['v'], 3)}</td><td class='n'>{f(t['e'], 3)}</td>"
                     f"<td class='n'>{('+' if dv > 0 else '') + f(dv, 3) if t is not base else '—'}</td>"
                     f"<td class='n'>{('+' if de > 0 else '') + f(de, 3) if t is not base else '—'}</td>"
                     f"<td class='n'><b>{coste}</b></td><td>{veredicto}</td><td>{lim}</td></tr>")
P["TABLA_TEC"] = "".join(filas)

# modos como técnicas de movilidad: coste de abatimiento frente al coche de combustión
filas = []
for k, m in MODOS.items():
    dv, de = m["h_tot"] - car["h_tot"], m["c_tot"] - car["c_tot"]
    if k == "CICE":
        ver, coste = "<span class='mut'>referencia</span>", "—"
    elif dv <= 0 and de <= 0:
        ver, coste = "<span class='ok'>dominante</span>", "&lt; 0 (ahorra ambas)"
    elif dv >= 0 and de >= 0:
        ver, coste = "<span class='no'>dominada</span>", "—"
    else:
        ver, coste = "<span class='warn'>intercambio</span>", f(dv / -de / 1000, 2)
    filas.append(f"<tr><td><b>{m['nombre']}</b></td><td class='n'>{f(m['h_tot'], 3)}</td><td class='n'>{f(m['c_tot'] * 1000, 1)}</td>"
                 f"<td class='n'>{f(m['kwh_pkm'] * 1000, 0)}</td><td class='n'>{('+' if dv > 0 else '') + f(dv, 3) if k != 'CICE' else '—'}</td>"
                 f"<td class='n'>{('+' if de > 0 else '') + f(de * 1000, 1) if k != 'CICE' else '—'}</td><td class='n'>{coste}</td><td>{ver}</td></tr>")
P["TABLA_TEC_MODOS"] = "".join(filas)

# ---------------------------------------------------------------- 5. fábrica
fb = M.fab
TEC_LAB = [('ace_bof', 'BF-BOF'), ('ace_eaf', 'EAF'), ('ace_h2', 'DRI-H₂'), ('alu_p', 'Al primario'), ('alu_s', 'Al reciclado'), ('ele_t', 'térmica'), ('ele_r', 'renovable'), ('biw_m', 'BIW multimaterial')]
filas = []
nombres = {"base_ice": "Leontief puro (técnica base, sólo combustión)",
           "opt_ice": "Kantorovich, sólo combustión (elige técnicas)",
           "opt_bev": "Kantorovich, sólo eléctrico",
           "opt_mix": "Kantorovich, mezcla libre combustión/eléctrico"}
for key, nom in nombres.items():
    r = fb[key]
    filas.append(f"<tr><td>{nom}</td><td class='n'><b>{f(r['N'])}</b></td><td class='n'>{f(r['n']['CICE'])}</td>"
                 f"<td class='n'>{f(r['n']['CBEV'])}</td><td class='n'>{f(r['co2'])}</td><td class='n'>{f(r['co2'] / r['N'], 2)}</td>"
                 f"<td class='n'>{f(r['co2_vida'] / r['N'], 1)}</td><td class='n'>{f(1 / r['dual']['HORAS'], 1) if r['dual']['HORAS'] > 1e-9 else '—'}</td></tr>")
P["TABLA_FAB"] = "".join(filas)
filas = []
for fr, c, r in M.fab_sens:
    filas.append(f"<tr><td class='n'>{pct(fr, 0)}</td><td class='n'>{f(c)}</td>"
                 + (f"<td class='n'><b>{f(r['N'])}</b></td><td class='n'>{pct(r['N'] / fb['base_ice']['N'] - 1, 2)}</td>"
                    f"<td class='n'>{f(r['dual'].get('CO2', 0) * 1000, 2)}</td>"
                    f"<td>{', '.join(lab for t, lab in TEC_LAB if r['tec'].get(t, 0) > 1e-6)}</td>"
                    if r else "<td colspan='4' class='no'>infactible</td>") + "</tr>")
P["TABLA_FAB_SENS"] = "".join(filas)
filas = []
for fr, c, r in M.fab_vida:
    filas.append(f"<tr><td class='n'>{pct(fr, 0)}</td><td class='n'>{f(c / 1e6, 2)} Mt</td>"
                 + (f"<td class='n'><b>{f(r['N'])}</b></td><td class='n'>{f(r['n']['CICE'])}</td><td class='n'>{f(r['n']['CBEV'])}</td>"
                    f"<td class='w'>{stack([(r['n']['CICE'], COL['CICE'], 'combustión'), (r['n']['CBEV'], COL['CBEV'], 'eléctrico')], 102000)}</td>"
                    if r else "<td colspan='4' class='no'>infactible</td>") + "</tr>")
P["TABLA_FAB_VIDA"] = "".join(filas)
P.update(N_BASE=f(fb['base_ice']['N']), N_OPT=f(fb['opt_ice']['N']), N_BEV=f(fb['opt_bev']['N']),
         GAN_OPT=pct(fb['opt_ice']['N'] / fb['base_ice']['N'] - 1, 2), H_FAB=f(M.H_FAB),
         CO2_RED_FAB=pct(1 - fb['opt_ice']['co2'] / fb['base_ice']['co2'], 0),
         USO_CICE=f(M.CO2_USO['CICE'], 1), USO_CBEV=f(M.CO2_USO['CBEV'], 1),
         VIDA_CICE=f(M.e0[IX['CICE']] + M.CO2_USO['CICE'], 1), VIDA_CBEV=f(M.e0[IX['CBEV']] + M.CO2_USO['CBEV'], 1),
         N30=f(M.fab_sens[5][2]['N']), CELDAS_FAB=f(M.CAP_FAB['CELDAS'] / 1e6, 0))

# ---------------------------------------------------------------- 6. escenarios ciudad
IND = M.IND
ref = IND["ref"]
filas = []
for key, nom, s in M.ESCENARIOS:
    ii = IND[key]
    sh = stack([(ii["pkm"][k], COL[k], MODOS[k]["nombre"]) for k in MODOS], ii["tot"])
    clase = " class='hl'" if key == "comp" else ""
    filas.append(f"<tr{clase}><td><b>{nom}</b>{sh}</td>"
                 + "".join(f"<td class='n'>{f(100 * ii['pkm'][k] / ii['tot'], 1)}</td>" for k in MODOS)
                 + f"<td class='n'>{f(ii['horas'] / 1e6, 2)}</td><td class='n'>{pct(ii['horas'] / ref['horas'] - 1, 0)}</td>"
                   f"<td class='n'>{f(ii['co2'])}</td><td class='n'>{pct(ii['co2'] / ref['co2'] - 1, 0)}</td>"
                   f"<td class='n'>{f(ii['energia'])}</td><td class='n'>{pct(ii['energia'] / ref['energia'] - 1, 0)}</td></tr>")
P["TABLA_ESC"] = "".join(filas)
comp = IND["comp"]
P.update(H_REF=f(ref['horas'] / 1e6, 2), H_COMP=f(comp['horas'] / 1e6, 2), RED_H=pct(1 - comp['horas'] / ref['horas'], 0),
         C_REF=f(ref['co2']), C_COMP=f(comp['co2']), RED_C=pct(1 - comp['co2'] / ref['co2'], 1),
         E_REF=f(ref['energia']), E_COMP=f(comp['energia']), RED_E=pct(1 - comp['energia'] / ref['energia'], 0),
         MULT_MOV=f(M.sol_max['t'] / D, 2),
         SH_BUS=f(100 * comp['pkm']['BUS'] / comp['tot'], 1), SH_TRAM=f(100 * comp['pkm']['TRAM'] / comp['tot'], 1),
         SH_CBEV=f(100 * comp['pkm']['CBEV'] / comp['tot'], 1),
         FLOTA_BUS=f(comp['flota']['BUS']), FLOTA_TRAM=f(comp['flota']['TRAM']), FLOTA_CBEV=f(comp['flota']['CBEV']),
         FLOTA_CICE_REF=f(ref['flota']['CICE']), VIA_KM=f(comp['infra']['VIA'], 0), MAR_N=f(comp['infra']['MAR']),
         PAR_N=f(comp['infra']['PAR']), CRG_N=f(comp['infra']['CRG']),
         ELE_REN=pct(comp['elec_ren'] / comp['elec_tot'], 0),
         HI_REF=f(ref['h_inicial'] / 1e6, 1), HI_COMP=f(comp['h_inicial'] / 1e6, 1),
         CI_REF=f(ref['co2_inicial']), CI_COMP=f(comp['co2_inicial']),
         HCOND_REF=f(ref['h_cond'] / 1e6, 1), HCOND_COMP=f(comp['h_cond'] / 1e6, 1))

# payoff
ideal, nadir = M.PAYOFF["ideal"], M.PAYOFF["nadir"]
P.update(ID_H=f(ideal[0]), ID_C=f(ideal[1]), ID_E=f(ideal[2]), NA_H=f(nadir[0]), NA_C=f(nadir[1]), NA_E=f(nadir[2]))
filas = []
for key, nom in [("h", "min horas"), ("c", "min CO₂"), ("e", "min energía"), ("comp", "compromiso")]:
    ii = IND[key]
    filas.append(f"<tr><td><b>{nom}</b></td><td class='n'>{f(ii['horas'])}</td><td class='n'>{f(ii['co2'])}</td><td class='n'>{f(ii['energia'])}</td>"
                 f"<td class='n'>{f((ii['horas'] - ideal[0]) / (nadir[0] - ideal[0]), 4)}</td><td class='n'>{f((ii['co2'] - ideal[1]) / (nadir[1] - ideal[1]), 4)}</td>"
                 f"<td class='n'>{f((ii['energia'] - ideal[2]) / (nadir[2] - ideal[2]), 4)}</td></tr>")
P["TABLA_PAYOFF"] = "".join(filas)

# máxima movilidad
mx = M.IND_MAX
P["TABLA_MAX"] = "".join(
    f"<tr><td><b>{MODOS[k]['nombre']}</b></td><td class='n'>{f(ref['pkm'][k])}</td><td class='n'>{f(mx['pkm'][k])}</td></tr>" for k in MODOS) + \
    f"<tr class='hl'><td><b>Total</b></td><td class='n'><b>{f(ref['tot'])}</b></td><td class='n'><b>{f(mx['tot'])}</b></td></tr>" + \
    f"<tr><td>Horas de trabajo</td><td class='n'>{f(ref['horas'])}</td><td class='n'>{f(mx['horas'])}</td></tr>" + \
    f"<tr><td>CO₂ (t)</td><td class='n'>{f(ref['co2'])}</td><td class='n'>{f(mx['co2'])}</td></tr>"

# Pareto SVG (eje x logarítmico)
pts = M.pareto
W, Hh, pad = 760, 340, 60
xs_all = [p["co2"] for p in pts] + [IND[k]["co2"] for k in ("ref", "bev", "bus")]
ys_all = [p["horas"] for p in pts] + [IND[k]["horas"] for k in ("ref", "bev", "bus")]
lx0, lx1 = math.log10(min(xs_all) * 0.8), math.log10(max(xs_all) * 1.25)
y0, y1 = 0, max(ys_all) * 1.08


def X(c):
    return pad + (math.log10(c) - lx0) / (lx1 - lx0) * (W - pad - 20)


def Y(h):
    return Hh - 40 - (h - y0) / (y1 - y0) * (Hh - 60)


svg = [f'<svg viewBox="0 0 {W} {Hh}" class="chart" role="img" aria-label="Frontera de Pareto horas frente a CO2">']
for tick in [5e3, 1e4, 2e4, 5e4, 1e5, 2e5, 4e5]:
    if lx0 <= math.log10(tick) <= lx1:
        svg.append(f'<line x1="{X(tick):.1f}" y1="20" x2="{X(tick):.1f}" y2="{Hh - 40}" class="grid"/>'
                   f'<text x="{X(tick):.1f}" y="{Hh - 22}" class="tk" text-anchor="middle">{f(tick / 1000)} kt</text>')
for tick in np.arange(0, y1, 1e6):
    svg.append(f'<line x1="{pad}" y1="{Y(tick):.1f}" x2="{W - 20}" y2="{Y(tick):.1f}" class="grid"/>'
               f'<text x="{pad - 8}" y="{Y(tick) + 4:.1f}" class="tk" text-anchor="end">{f(tick / 1e6)} M</text>')
path = " ".join(f"{'M' if i == 0 else 'L'}{X(p['co2']):.1f},{Y(p['horas']):.1f}" for i, p in enumerate(pts))
svg.append(f'<path d="{path}" class="front"/>')
for p in pts:
    svg.append(f'<circle cx="{X(p["co2"]):.1f}" cy="{Y(p["horas"]):.1f}" r="3.5" class="pf"><title>CO₂ {f(p["co2"])} t · {f(p["horas"])} h · μ={f(p["mu"], 3)}</title></circle>')
for key, lab in [("ref", "Coche-céntrico"), ("bev", "Coche eléctrico"), ("bus", "Autobús + coche mín.")]:
    ii = IND[key]
    svg.append(f'<circle cx="{X(ii["co2"]):.1f}" cy="{Y(ii["horas"]):.1f}" r="5" class="dom"/>'
               f'<text x="{X(ii["co2"]) - 8:.1f}" y="{Y(ii["horas"]) - 9:.1f}" class="lb" text-anchor="end">{lab}</text>')
cp = IND["comp"]
svg.append(f'<circle cx="{X(cp["co2"]):.1f}" cy="{Y(cp["horas"]):.1f}" r="6" class="cp"/>'
           f'<text x="{X(cp["co2"]) + 10:.1f}" y="{Y(cp["horas"]) + 22:.1f}" class="lb">Compromiso</text>')
svg.append(f'<text x="{W / 2}" y="{Hh - 4}" class="ax" text-anchor="middle">t CO₂/año (escala logarítmica)</text>'
           f'<text x="14" y="{Hh / 2}" class="ax" transform="rotate(-90 14 {Hh / 2})" text-anchor="middle">horas de trabajo/año</text></svg>')
P["SVG_PARETO"] = "".join(svg)
filas = []
for p in pts:
    filas.append(f"<tr><td class='n'>{f(p['co2'])}</td><td class='n'>{f(p['horas'])}</td><td class='n'>{f(p['mu'], 3)}</td>"
                 + "".join(f"<td class='n'>{f(100 * p['pkm'][k] / D, 1)}</td>" for k in MODOS) + "</tr>")
P["TABLA_PARETO"] = "".join(filas)

# duales (solución mínimo trabajo)
sh = M.sol_h
pr = sh["precios"]
ex = sh["extra_dual"]
mu_tipico = [p["mu"] for p in pts if 0.1 < p["mu"] < 10][0]
P.update(P_PKM=f(pr[IX['PKM']], 3), P_ELE=f(pr[IX['ELE']], 3), DU_VIA=f(ex['VIA_MAX'], 3),
         DU_VIA_KM=f(ex['VIA_MAX'] * M.KAPPA_VIA), DU_COCHE=f(ex['COCHE_MIN'], 3), MU_TIP=f(mu_tipico, 3),
         MU_MAX=f(max(p['mu'] for p in pts), 1))
filas = []
for k, m in MODOS.items():
    a = A_[M.ACT_MODO[k]]
    coste_ins = sum(q * pr[IX[g]] for g, q in a["ins"].items())
    total = a["h"] + coste_ins
    filas.append(f"<tr><td><b>{m['nombre']}</b></td><td class='n'>{f(a['h'], 3)}</td><td class='n'>{f(coste_ins, 3)}</td>"
                 f"<td class='n'><b>{f(total, 3)}</b></td><td class='n'>{f(total - pr[IX['PKM']], 3)}</td>"
                 f"<td class='n'>{f(m['c_tot'], 4)}</td><td class='n'><b>{f(total + mu_tipico * m['c_tot'], 3)}</b></td></tr>")
P["TABLA_DUAL_MODOS"] = "".join(filas)

# ---------------------------------------------------------------- 7. plan de flota e infraestructura
VIDAS = {"CICE": 15, "CBEV": 15, "BUS": 12, "TRAM": 30, "VIA": M.VIDA_VIA, "PAR": M.VIDA_VIA, "MAR": M.VIDA_MAR, "CRG": M.VIDA_CRG}
HORAS_OPERARIO = 1650
filas, filas2 = [], []
tot_ens_c = tot_tot_c = 0
for g in ["CICE", "CBEV", "BUS", "TRAM", "VIA", "PAR", "MAR", "CRG"]:
    i = IX[g]
    st_r, st_c = ref["stock"][g], comp["stock"][g]
    an_c = comp["prod"][g]
    h_ens = an_c * M.l0[i]
    h_tot = an_c * M.v0[i]
    tot_ens_c += h_ens
    tot_tot_c += h_tot
    nom = f"<b>{M.BIENES[i][1]}</b> <span class='mut'>({M.BIENES[i][2]})</span>"
    filas.append(f"<tr><td>{nom}</td><td class='n'>{f(st_r)}</td><td class='n'><b>{f(st_c)}</b></td>"
                 f"<td class='n'>{VIDAS[g]}</td><td class='n'><b>{f(an_c, 1)}</b></td></tr>")
    filas2.append(f"<tr><td>{nom}</td><td class='n'>{f(M.l0[i], 1)}</td><td class='n'>{f(h_ens)}</td>"
                  f"<td class='n'>{f(h_ens / HORAS_OPERARIO, 1)}</td><td class='n'>{f(M.v0[i], 1)}</td>"
                  f"<td class='n'>{f(h_tot)}</td><td class='n'>{f(st_c * M.v0[i])}</td></tr>")
filas2.append(f"<tr class='hl'><td><b>Total</b></td><td></td><td class='n'><b>{f(tot_ens_c)}</b></td>"
              f"<td class='n'><b>{f(tot_ens_c / HORAS_OPERARIO, 0)}</b></td><td></td><td class='n'><b>{f(tot_tot_c)}</b></td>"
              f"<td class='n'><b>{f(comp['h_inicial'])}</b></td></tr>")
P["TABLA_FLOTA"] = "".join(filas)
P["TABLA_FLOTA2"] = "".join(filas2)

# horas por bloque y escenario
grupos = list(ref["grupos"].keys())
CORTO = {"Ensamblaje final de vehículos": "Ensamblaje vehículos", "Construcción de infraestructura": "Infraestructura", "Operación y mantenimiento": "Operación y mant."}
cab = "".join(f"<th>{CORTO.get(g, g)}</th>" for g in grupos)
filas = []
for key, nom, s in M.ESCENARIOS:
    ii = IND[key]
    filas.append(f"<tr><td><b>{nom}</b></td>" + "".join(f"<td class='n'>{f(ii['grupos'][g] / 1e3)}</td>" for g in grupos)
                 + f"<td class='n'><b>{f(ii['horas'] / 1e3)}</b></td><td class='n mut'>{f(ii['h_cond'] / 1e3)}</td></tr>")
P["CAB_GRUPOS"] = cab
P["TABLA_GRUPOS"] = "".join(filas)

# ensamblaje final: horas por escenario
filas = []
for key, nom, s in M.ESCENARIOS:
    ii = IND[key]
    filas.append(f"<tr><td><b>{nom}</b></td>" + "".join(f"<td class='n'>{f(ii['h_ens'][g])}</td>" for g in ["CICE", "CBEV", "BUS", "TRAM", "VIA", "PAR", "MAR", "CRG"])
                 + f"<td class='n'><b>{f(sum(ii['h_ens'].values()))}</b></td></tr>")
P["TABLA_ENS"] = "".join(filas)

with open("plantillas/plantilla_movilidad.html", encoding="utf-8") as fh:
    html = fh.read()
for k, v in P.items():
    html = html.replace("{{" + k + "}}", str(v))
assert "{{" not in html, html[html.index("{{"):html.index("{{") + 50]
with open("planificacion_movilidad.html", "w", encoding="utf-8") as fh:
    fh.write(html)
print("OK", len(html))
