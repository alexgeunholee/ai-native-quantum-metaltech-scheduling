# Full experiment source from the one-click Colab notebook.
# Install in Colab: %pip install veloxq-sdk dimod numpy pandas matplotlib

# STEP 2 — Noninteractive experiment settings (no user edits required)
TEAM_NAME = "AI-Native Quantum"
# Fixed, limited benchmark campaign: four archived QUBOs, one job per QUBO.
BENCHMARKS = [
    "official_3jobs_H8",        # 39 variables — official challenge baseline
    "energy_3jobs_H9_P25",     # 40 variables — synthetic industrial extension
    "energy_4jobs_H12_P25",    # 88 variables — adaptive horizon
    "energy_5jobs_H13_P25",    # 128 variables — adaptive horizon
]
NUM_REP = 256                 # Low-cost benchmark configuration, not SDK defaults
NUM_STEPS = 1500
MAX_RECORDS_ARCHIVED = 10000
print("Team:", TEAM_NAME)
print("One remote VeloxQ run is planned for each of", len(BENCHMARKS), "QUBOs.")
print("Solver settings: num_rep=",NUM_REP," num_steps=",NUM_STEPS)
print("All four frozen QUBOs will be presented and compared in this Colab notebook.")

# STEP 3 — Load the four frozen QUBO models (complete replacement cell)
# Identical archived JSON, re-compressed losslessly with LZMA for a shorter cell.
# No optimization runs and no API calls occur here.
import base64, lzma, json, hashlib, pathlib, os, time, math, statistics, zipfile, datetime
import numpy as np
import dimod
from IPython.display import display, Markdown

PAYLOAD_B64 = (
    "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"
    "AAAABFla"
)
PAYLOAD_SHA256 = "67733301ecbc18da83bb5151984487857b0ee96f2f70797f91121290b68d5955"
_payload_raw = lzma.decompress(base64.b64decode(PAYLOAD_B64))
DATA = json.loads(_payload_raw)
assert hashlib.sha256(json.dumps(DATA, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == PAYLOAD_SHA256, "Archived QUBO fingerprint mismatch"
MODELS = DATA["models"]
INPUTS = DATA["inputs"]
REFS = DATA["references"]

def build_bqm(model):
    quadratic = {(d["u"], d["v"]): float(d["bias"]) for d in model["quadratic"]}
    return dimod.BinaryQuadraticModel(
        {k: float(v) for k, v in model["linear"].items()},
        quadratic, float(model["offset"]), dimod.BINARY
    )

BQM = {bid: build_bqm(model) for bid, model in MODELS.items()}
EXPECTED_QUBO_SPECS = {
    "official_3jobs_H8": (39, 181, 45.0),
    "energy_3jobs_H9_P25": (40, 180, 250.0),
    "energy_4jobs_H12_P25": (88, 698, 325.0),
    "energy_5jobs_H13_P25": (128, 1256, 400.0),
}
assert set(BQM) == set(EXPECTED_QUBO_SPECS), "Missing or unexpected QUBO models"
print("Archived model SHA-256:", PAYLOAD_SHA256)
for bid, (n_expected, edges_expected, offset_expected) in EXPECTED_QUBO_SPECS.items():
    bqm = BQM[bid]
    actual = (len(bqm.variables), len(bqm.quadratic), float(bqm.offset))
    expected = (n_expected, edges_expected, offset_expected)
    print(f"{bid}: {actual[0]} binary variables, {actual[1]} interactions, offset={actual[2]}")
    assert actual == expected, f"{bid}: expected {expected}, received {actual}"
print("PASS: All four archived QUBOs match their individual model specifications.")


MACHINES = ("T", "F", "S")

def validate_sample(bid, sample):
    """Independent application-level validation; never infer feasibility solely from energy."""
    cfg = INPUTS[bid]
    processing = cfg["processing_hours"]
    H = int(REFS[bid]["target_makespan"])
    selected = {}
    issues = []
    for job, durations in processing.items():
        for machine in MACHINES:
            prefix = f"{job}_{machine}_"
            active = [key for key,value in sample.items() if key.startswith(prefix) and int(value)==1]
            if len(active)!=1:
                issues.append(f"{job}-{machine} has {len(active)} starts, expected one")
                continue
            t = int(active[0].rsplit("_",1)[-1]); d = int(durations[MACHINES.index(machine)])
            selected[(job,machine)] = (t,t+d)
            if t<0 or t+d>H:
                issues.append(f"{job}-{machine} outside horizon")
            if machine=='F' and not cfg.get('official',False):
                _, lo, hi = cfg['outage']
                if t < hi and t+d > lo:
                    issues.append(f"{job} milling overlaps outage")
    for job in processing:
        if (job,'T') in selected and (job,'F') in selected:
            if selected[job,'T'][1] > selected[job,'F'][0]:issues.append(f"{job} T/F precedence")
        if (job,'F') in selected and (job,'S') in selected:
            if selected[job,'F'][1] > selected[job,'S'][0]:issues.append(f"{job} F/S precedence")
    for machine in MACHINES:
        intervals=sorted([(a,b,j) for (j,m),(a,b) in selected.items() if m==machine])
        for (a,b,j),(c,d,k) in zip(intervals,intervals[1:]):
            if b>c:issues.append(f"{machine} overlap {j}/{k}")
    Cmax = max((e for (j,m),(s,e) in selected.items()),default=0)
    if Cmax!=H:issues.append(f"makespan {Cmax} vs required {H}")
    schedule = [dict(job=j,machine=m,start=s,end=e) for (j,m),(s,e) in selected.items()]
    schedule.sort(key=lambda r:(r['start'],r['machine'],r['job']))
    if issues:return {'feasible':False,'issues':issues,'schedule':schedule,'makespan':Cmax}
    if cfg.get('official',False):
        return {'feasible':True,'issues':[],'schedule':schedule,'makespan':Cmax,'business_objective':Cmax,
                'weighted_tardiness':None,'electricity_usd':None}
    weighted_tardiness=0
    for job in processing:
        completion=selected[job,'S'][1]
        weighted_tardiness += int(cfg['priority_weights'][job])*max(0,completion-int(cfg['due_hours'][job]))
    cost=0.0
    peak_kwh=0.0
    for (job,machine),(s,e) in selected.items():
        power=float(cfg['power_kw'][machine])
        for h in range(s,e):
            peak=(h%8) in (2,3,4,5)
            cost += power*(0.27 if peak else 0.11)
            if peak: peak_kwh += power
    objective=Cmax+2*weighted_tardiness+0.02*cost
    return {'feasible':True,'issues':[],'schedule':schedule,'makespan':Cmax,
            'business_objective':round(objective,8),'weighted_tardiness':weighted_tardiness,
            'electricity_usd':round(cost,8),'peak_kwh':peak_kwh}


def normalize_sample(sample,bqm,result_variables):
    # VeloxQ SDK documentation: SampleSet columns follow input BQM variable order.
    orig={str(k):int(v) for k,v in dict(sample).items()}
    labels=set(map(str,bqm.variables))
    if set(orig)==labels:return orig
    indices=list(result_variables)
    expected=list(map(str,bqm.variables))
    assert len(indices)==len(expected),"Unexpected result-variable count"
    if set(orig) != set(map(str,indices)):
        raise ValueError("Unexpected returned variable labels; refusing to guess the bit mapping")
    mapped={expected[i]:orig[str(indices[i])] for i in range(len(indices))}
    return mapped

print("Independent decoder ready; no VeloxQ solver jobs submitted.")


# STEP 5 — Secure, hidden-input API key prompt. Do not edit this cell.
# Your key is not written into notebook source, visible output, ZIP, or GitHub.
import getpass
import os
from IPython.display import display, Markdown

print("VeloxQ remote execution requires your own API key.")
print("Paste your *replacement* API key into the masked field below and press Enter.")
print("The characters you enter should not appear in the notebook output.")
print("You can submit an empty value to skip remote jobs and still export a preflight ZIP.")

# Avoid echoing the token and avoid creating an enduring notebook code literal.
try:
    _key_entry = getpass.getpass("VeloxQ API key (hidden input): ").strip()
except (EOFError, KeyboardInterrupt):
    _key_entry = ""

AUTH_READY = bool(_key_entry)
if AUTH_READY:
    os.environ["VELOX_TOKEN"] = _key_entry
    print("PASS: API key received privately in this Colab runtime (not displayed).")
else:
    os.environ.pop("VELOX_TOKEN", None)
    print("No API key entered. VeloxQ will NOT run; a preflight ZIP will still be produced.")
_key_entry = None  # Remove extra reference. Process environment is ephemeral.

# STEP 6 — Run VeloxQ for all four models and compare with archived references.
# A remote error is recorded without revealing sensitive exception text.
# The final ZIP step runs even if any remote benchmark fails.
import math, time, json
import dimod
from IPython.display import display, Markdown

RESULTS = {}

if not AUTH_READY:
    print("Remote runs skipped because no API key was provided.")
    for bid in BENCHMARKS:
        RESULTS[bid] = {"status": "NOT_EXECUTED", "reason": "No key supplied"}
else:
    try:
        from veloxq_sdk import VeloxQSolver
        SDK_AVAILABLE = True
    except Exception as exc:
        SDK_AVAILABLE = False
        print("SDK import failed:", type(exc).__name__, "(error details withheld for safety)")
        for bid in BENCHMARKS:
            RESULTS[bid] = {"status": "SDK_IMPORT_ERROR", "error_type": type(exc).__name__}

    if SDK_AVAILABLE:
        for run_index, bid in enumerate(BENCHMARKS, start=1):
            display(Markdown(f"### VeloxQ run {run_index}/{len(BENCHMARKS)} — `{bid}`"))
            bqm = BQM[bid]
            t0 = time.perf_counter()
            try:
                solver = VeloxQSolver()
                solver.parameters.num_rep = int(NUM_REP)
                solver.parameters.num_steps = int(NUM_STEPS)
                sampled = solver.sample(bqm)  # Actual, remote VeloxQ submission
                wall_sec = time.perf_counter() - t0

                if sampled.vartype != dimod.BINARY:
                    raise ValueError("Unexpected variable domain")

                records = []
                samples_total = 0
                samples_feasible = 0
                for datum in sampled.data(['sample', 'energy', 'num_occurrences'], sorted_by=None):
                    bit_dict = normalize_sample(datum.sample, bqm, sampled.variables)
                    if len(bit_dict) != len(bqm.variables) or any(v not in (0,1) for v in bit_dict.values()):
                        raise ValueError("Invalid or incomplete binary sample")
                    recomputed_energy = float(bqm.energy(bit_dict))
                    solver_energy = float(datum.energy)
                    if not math.isclose(recomputed_energy, solver_energy, rel_tol=1e-6, abs_tol=5e-4):
                        raise ValueError("VeloxQ energy and archived QUBO energy disagree")
                    decoded = validate_sample(bid, bit_dict)
                    occ = int(datum.num_occurrences)
                    if occ < 1:
                        raise ValueError("Invalid sample occurrence count")
                    samples_total += occ
                    samples_feasible += occ if decoded['feasible'] else 0
                    records.append({
                        'sample':bit_dict, 'provider_energy': solver_energy,
                        'qubo_energy':recomputed_energy, 'occurrences':occ, **decoded
                    })

                if not samples_total:
                    raise ValueError("VeloxQ returned no samples")
                feasible = sorted((r for r in records if r['feasible']),
                                  key=lambda r:(r['business_objective'],r['qubo_energy']))
                best = feasible[0] if feasible else None
                target = REFS[bid].get('target_objective')
                reference_match = bool(best and (
                    math.isclose(float(best['business_objective']), float(target), abs_tol=1e-5)
                    if target is not None else best['makespan'] == REFS[bid]['target_makespan']
                ))
                # For a feasible QUBO solution, objective = horizon + QUBO energy.
                # Check it without rerunning any CP-SAT optimization.
                if best:
                    expected_energy = (float(best['business_objective']) - REFS[bid]['target_makespan']) \
                        if target is not None else 0.0
                    if not math.isclose(best['qubo_energy'], expected_energy,
                                        rel_tol=1e-6, abs_tol=5e-4):
                        raise ValueError('Feasible solution objective does not match frozen QUBO')

                # Provider metadata may be useful; scrub any token before archival.
                metadata = str(getattr(sampled, 'info', {}))
                for sensitive in filter(None, [os.environ.get('VELOX_TOKEN', '')]):
                    metadata = metadata.replace(sensitive, '[REDACTED]')
                RESULTS[bid] = {
                    'status':'SUCCESS',
                    'backend':'VeloxQ quantum-inspired GPU optimizer; no physical QPU',
                    'wall_seconds':round(wall_sec,3),
                    'num_rep':NUM_REP,'num_steps':NUM_STEPS,
                    'total_samples_weighted':samples_total,
                    'feasible_samples_weighted':samples_feasible,
                    'feasible_fraction':round(samples_feasible/samples_total, 7),
                    'optimal_reference_match':reference_match,
                    'best_feasible':best,
                    'top_feasible':[{k:v for k,v in r.items() if k!='sample'} for r in feasible[:10]],
                    'samples':records[:MAX_RECORDS_ARCHIVED],
                    'result_info':metadata[:2000],
                }
                print(f"COMPLETED: {samples_total} samples; {samples_feasible} valid; "
                      f"feasible fraction = {samples_feasible/samples_total:.1%}")
                if best:
                    print("Best feasible manufacturing makespan:",best['makespan'])
                    print("Best feasible business objective:",best['business_objective'])
                    print("Reference optimum matched:",reference_match)
                else:
                    print("No valid production schedule found in returned samples.")
            except Exception as exc:
                # Never print raw error messages; HTTP errors can include auth details.
                RESULTS[bid] = {
                    'status':'REMOTE_OR_RESULT_ERROR',
                    'error_type':type(exc).__name__,
                    'wall_seconds':round(time.perf_counter()-t0,3),
                    'note':'Exception message withheld to protect API credential'
                }
                print('This benchmark did not finish successfully:',type(exc).__name__)
                print('No solver result will be claimed for this benchmark.')
                # To avoid repeated unintended API charges on auth/network faults,
                # do not continue submitting more models after a remote exception.
                for remaining in BENCHMARKS[run_index:]:
                    RESULTS[remaining] = {'status':'NOT_EXECUTED',
                                          'reason':'Stopped after prior remote/error response'}
                break

# Clear the copied process environment token before exporting any evidence.
os.environ.pop("VELOX_TOKEN", None)
print('Remote phase finished. Credentials cleared from environment before ZIP creation.')

# STEP 7 — Display all results and automatically download evidence ZIP.
# This cell executes after success, nonfeasible runs, errors, or no-key preflight.
import json, zipfile, hashlib
from pathlib import Path
from datetime import datetime, timezone
from IPython.display import display, Markdown
import pandas as pd
import matplotlib.pyplot as plt

stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
root = Path('/content') if Path('/content').exists() else Path.cwd()
out = root / f'AI_Native_Quantum_VeloxQ_Evidence_{stamp}'
out.mkdir(parents=True, exist_ok=True)
zip_path = root / (out.name + '.zip')

def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str), encoding='utf-8')

summary = [
    'TEAM AI-NATIVE QUANTUM — VELOXQ MANUFACTURING BENCHMARK',
    'Date UTC: '+stamp,
    'Archived coefficient-model SHA-256: '+PAYLOAD_SHA256,
    'VeloxQ backend: quantum-inspired GPU solver; not a physical quantum QPU',
    'External industrial extension and scaling data are synthetic',
    'Only status=SUCCESS means an actual VeloxQ result was returned',
    'Solver parameters: num_rep='+str(NUM_REP)+' num_steps='+str(NUM_STEPS),
    ''
]
rows = []
for bid in BENCHMARKS:
    bqm = BQM[bid]
    ref = REFS[bid]
    run = RESULTS.get(bid, {'status':'NOT_EXECUTED'})
    status = run.get('status','NOT_EXECUTED')
    best = run.get('best_feasible') or {}
    label = ('MATCH' if run.get('optimal_reference_match') else 'NOT_MATCHED') if status == 'SUCCESS' else 'NO_NEW_RESULT'
    rows.append({
        'benchmark':bid,
        'binary_variables':len(bqm.variables),
        'quadratic_interactions':len(bqm.quadratic),
        'run_status':status,
        'reference_makespan':ref['target_makespan'],
        'reference_business_objective':ref.get('target_objective', ref['target_makespan']),
        'veloxq_feasible_fraction':run.get('feasible_fraction'),
        'veloxq_best_makespan':best.get('makespan'),
        'veloxq_best_business_objective':best.get('business_objective'),
        'veloxq_optimum_match':run.get('optimal_reference_match'),
        'veloxq_wall_seconds':run.get('wall_seconds'),
    })
    summary += [
        bid+': '+status,
        '  QUBO variables: '+str(len(bqm.variables))+'; interactions: '+str(len(bqm.quadratic))+
            '; offset: '+str(float(bqm.offset)),
        '  Prior independent reference: '+json.dumps(ref,sort_keys=True),
        '  VeloxQ outcome: '+label,
        '  Feasible samples (weighted): '+str(run.get('feasible_samples_weighted'))+
           ' / '+str(run.get('total_samples_weighted')),
        '  VeloxQ best business objective: '+str(best.get('business_objective')),
        '  Remote wall time (seconds): '+str(run.get('wall_seconds')),
        ''
    ]
    write_json(out / (bid+'_model.json'), MODELS[bid])
    write_json(out / (bid+'_input.json'), INPUTS[bid])
    write_json(out / (bid+'_reference.json'), REFS[bid])
    write_json(out / (bid+'_veloxq_result.json'), run)

    if status == 'SUCCESS' and best.get('schedule'):
        display(Markdown('### Best feasible VeloxQ schedule — '+bid))
        sched_df = pd.DataFrame(best['schedule'])
        display(sched_df)
        sched_df.to_csv(out/(bid+'_schedule.csv'), index=False)
        fig, ax = plt.subplots(figsize=(10,3.6))
        for op in best['schedule']:
            y = {'T':0,'F':1,'S':2}[op['machine']]
            ax.barh(y, op['end']-op['start'], left=op['start'],
                    edgecolor='black', alpha=0.75)
            ax.text(op['start']+0.07,y,op['job'],va='center')
        ax.set_yticks([0,1,2],['Turning (T)','Milling (F)','Welding (S)'])
        ax.set_xlabel('Time (hours)')
        ax.set_xlim(0,ref['target_makespan']+.4)
        ax.invert_yaxis()
        ax.grid(axis='x',alpha=0.25)
        ax.set_title(bid+' — Actual VeloxQ result')
        plt.tight_layout()
        fig.savefig(out/(bid+'_Gantt.png'), dpi=150)
        plt.show()
        plt.close(fig)

summary_text = '\n'.join(summary)+'\n'
(out/'FINAL_RESULTS_FOR_CHATGPT.txt').write_text(summary_text,encoding='utf-8')
write_json(out/'SUMMARY.json', {'team':TEAM_NAME,'model_sha256':PAYLOAD_SHA256,'results':rows})
pd.DataFrame(rows).to_csv(out/'ALL_BENCHMARKS_COMPARISON.csv',index=False)
display(Markdown('## Complete VeloxQ benchmark comparison'))
display(pd.DataFrame(rows))
display(Markdown('### Evidence summary (also included in ZIP)'))
print(summary_text)
(out/'README.md').write_text(
    'QPoland hackathon evidence — Team AI-Native Quantum.\n'
    'VeloxQ is a GPU-based quantum-inspired optimizer, not a physical QPU.\n'
    'Only benchmark statuses SUCCESS represent real new VeloxQ executions.\n'
    'The synthetic manufacturing extensions are not real plant operating data.\n'
    'The ZIP does not contain API credentials.\n',
    encoding='utf-8'
)
manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(out.iterdir()) if p.is_file()}
write_json(out/'SHA256_MANIFEST.json',manifest)
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(out.iterdir()):
        if p.is_file():z.write(p,arcname='VELOXQ_EVIDENCE/'+p.name)
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None, 'Evidence ZIP failed its integrity test'
print('\nZIP READY:',zip_path.name, '| Size:', f'{zip_path.stat().st_size:,}', 'bytes')

# Trigger download unconditionally: success, error or no-key mode.
try:
    from google.colab import files
    print('Automatic download starting — check your browser Downloads folder.')
    files.download(str(zip_path))
except ImportError:
    print('This run is outside Colab. ZIP saved at:',zip_path)
except Exception as exc:
    print('Browser download could not start:',type(exc).__name__)
    print('In Colab: left sidebar > Files > find',zip_path.name,'> right-click > Download')
