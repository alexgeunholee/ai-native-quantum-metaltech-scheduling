"""QPoland ERP Hackathon Experiment 4: certified adaptive-horizon QUBO.

Self-contained extended/synthetic ERP cases. Execute on Google Colab after the notebook's
pip-install cell; requires no physical QPU, secrets, or external input files.

The fixed-H QUBO adds an explicit exact-makespan anchor. Searching multiple feasible
horizons, rather than constraining H=minimum-makespan, is the original contribution
being TESTED. Numerical performance claims require actual executions.
"""
from __future__ import annotations

import sys, json, time, math, hashlib, zipfile, traceback
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from itertools import combinations
import importlib.metadata as packages
import numpy as np
import dimod, neal
from ortools.sat.python import cp_model
import matplotlib.pyplot as plt

UTC_NOW = datetime.now(timezone.utc)
RUNID = UTC_NOW.strftime('%Y%m%dT%H%M%S%fZ')
ROOT = (Path('/content') if Path('/content').exists() else Path.cwd()) / ('ERP_EXPERIMENT4_'+RUNID)
for sub in ('inputs','models','runs','verification','figures','summaries'):
    (ROOT/sub).mkdir(parents=True,exist_ok=True)

DURATION = {'Z1':(2,1,2),'Z2':(1,2,1),'Z3':(2,2,1),
            'Z4':(1,2,2),'Z5':(2,1,1)}
DUE = {'Z1':7,'Z2':5,'Z3':10,'Z4':12,'Z5':14}
WEIGHT = {'Z1':1,'Z2':3,'Z3':1,'Z4':2,'Z5':1}
MACHINES = ('T','F','S')
OUTAGE = ('F',3,5)
POWER = {'T':8,'F':12,'S':6}
TARIFF_PERIOD = 8
ELECTRICITY_DENOMINATOR = 5000  # electricity cost cents/5000 = 0.02 * USD
PENALTIES = (25,100)
SEEDS = (101,202,303,404,505)
READS = {3:150,4:200,5:240}
SWEEPS = {3:1000,4:1200,5:1500}
CP_TIME_LIMIT_SECONDS = 35
# 3 jobs: baseline control. 4/5 jobs: exactly min-makespan and min+1.
# Each additional horizon requires its OWN separately verified QUBO and CP-SAT model.
JOB_HORIZON_OFFSETS = {3:(0,),4:(0,1),5:(0,1)}


def record(relative_path,obj):
    p=ROOT/relative_path
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8')
    return p


def selected(n):
    return {j:DURATION[j] for j in list(DURATION)[:n]}


def operation_cost_cents(machine,start,duration):
    peak=sum(2<=h%TARIFF_PERIOD<6 for h in range(start,start+duration))
    return POWER[machine]*(27*peak+11*(duration-peak))


def independent_schedule_audit(jobs,schedule,exact_horizon=None):
    expected={(j,m):d for j,ds in jobs.items() for m,d in zip(MACHINES,ds)}
    found={};violations=[]
    for op in schedule:
        j,m,s,e=(op[k] for k in ('job','machine','start','end'))
        key=(j,m)
        if key not in expected or key in found:
            violations.append('unknown/duplicate '+str(key));continue
        if type(s) is not int or type(e) is not int or s<0 or e-s!=expected[key]:
            violations.append('duration/time '+str(key))
        if m==OUTAGE[0] and s<OUTAGE[2] and e>OUTAGE[1]:
            violations.append('maintenance '+str(key))
        if exact_horizon is not None and e>exact_horizon:
            violations.append('beyond H '+str(key))
        found[key]=(s,e)
    if set(expected)!=set(found):violations.append('missing operation')
    for j in jobs:
        if all((j,m) in found for m in MACHINES):
            if found[j,'T'][1]>found[j,'F'][0] or found[j,'F'][1]>found[j,'S'][0]:
                violations.append('precedence '+j)
    for m in MACHINES:
        intervals=sorted((s,e) for (j,k),(s,e) in found.items() if k==m)
        if any(a[1]>b[0] for a,b in zip(intervals,intervals[1:])):
            violations.append('machine overlap '+m)
    if violations:return {'valid':False,'violations':violations}
    makespan=max(e for s,e in found.values())
    if exact_horizon is not None and makespan!=exact_horizon:
        return {'valid':False,'violations':['actual makespan differs from exact-H target']}
    weighted_tardiness=sum(WEIGHT[j]*max(0,found[j,'S'][1]-DUE[j]) for j in jobs)
    electricity_cents=sum(operation_cost_cents(m,s,e-s) for (_,m),(s,e) in found.items())
    total=makespan+2*weighted_tardiness+electricity_cents/ELECTRICITY_DENOMINATOR
    return {'valid':True,'makespan_hours':makespan,'weighted_tardiness':weighted_tardiness,
            'electricity_usd':electricity_cents/100,'electricity_cents':electricity_cents,
            'objective':round(total,8)}


def cp_reference(jobs,mode,exact_horizon=None):
    max_h=sum(sum(ds) for ds in jobs.values())+OUTAGE[2]+4
    mod=cp_model.CpModel();starts={};ends={};intervals={m:[] for m in MACHINES}
    for j,ds in jobs.items():
        for m,d in zip(MACHINES,ds):
            s=mod.NewIntVar(0,max_h-d,f's_{j}_{m}')
            e=mod.NewIntVar(0,max_h,f'e_{j}_{m}')
            starts[j,m]=s;ends[j,m]=e
            intervals[m].append(mod.NewIntervalVar(s,d,e,f'iv_{j}_{m}'))
        mod.Add(starts[j,'F']>=ends[j,'T'])
        mod.Add(starts[j,'S']>=ends[j,'F'])
    intervals[OUTAGE[0]].append(mod.NewIntervalVar(OUTAGE[1],OUTAGE[2]-OUTAGE[1],OUTAGE[2],'outage'))
    for m in MACHINES:mod.AddNoOverlap(intervals[m])
    cm=mod.NewIntVar(0,max_h,'Cmax')
    mod.AddMaxEquality(cm,[ends[j,'S'] for j in jobs])
    if exact_horizon is not None:mod.Add(cm==exact_horizon)
    if mode=='makespan':mod.Minimize(cm)
    else:
        weighted_tard=[];energy=[]
        for j,ds in jobs.items():
            late=mod.NewIntVar(0,max_h,f'late_{j}')
            mod.Add(late>=ends[j,'S']-DUE[j])
            weighted_tard.append(WEIGHT[j]*late)
            for m,d in zip(MACHINES,ds):
                costs=[operation_cost_cents(m,s,d) for s in range(max_h-d+1)]
                c=mod.NewIntVar(min(costs),max(costs),f'energy_{j}_{m}')
                mod.AddElement(starts[j,m],costs,c)
                energy.append(c)
        mod.Minimize(ELECTRICITY_DENOMINATOR*cm +
                     2*ELECTRICITY_DENOMINATOR*sum(weighted_tard)+sum(energy))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=CP_TIME_LIMIT_SECONDS
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=13
    t=time.perf_counter();s=solver.Solve(mod)
    result={'status':solver.StatusName(s),'certified':s==cp_model.OPTIMAL,
            'seconds':round(time.perf_counter()-t,4),'requested_exact_horizon':exact_horizon}
    if s in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        schedule=sorted(({'job':j,'machine':m,'start':solver.Value(starts[j,m]),
                          'end':solver.Value(ends[j,m])} for j in jobs for m in MACHINES),
                        key=lambda x:(x['start'],x['machine'],x['job']))
        audit=independent_schedule_audit(jobs,schedule,exact_horizon)
        if not audit['valid']:raise AssertionError('Independent audit rejected CP-SAT schedule')
        value=float(solver.ObjectiveValue())/(1 if mode=='makespan' else ELECTRICITY_DENOMINATOR)
        if abs(value-(audit['makespan_hours'] if mode=='makespan' else audit['objective']))>1e-6:
            raise AssertionError('CP-SAT objective scale mismatch')
        result.update(schedule=schedule,metrics=audit,objective=value,
                      best_bound=float(solver.BestObjectiveBound()))
    return result


def make_exact_h_qubo(jobs,H,P):
    # Core one-hot scheduling, capacity and precedence plus an exact-makespan anchor:
    # P*(1 - sum_j x[j,S,H-duration[j,S]])^2. Since S is a single machine,
    # no two operations can finish at H in a FEASIBLE schedule.
    linear=defaultdict(float);quadratic=defaultdict(float);offset=0.0
    byop={};lookup={}
    for j,ds in jobs.items():
        for idx,(m,d) in enumerate(zip(MACHINES,ds)):
            start_lo=sum(ds[:idx]);start_hi=H-sum(ds[idx:]);available=[]
            for s in range(start_lo,start_hi+1):
                if m==OUTAGE[0] and s<OUTAGE[2] and s+d>OUTAGE[1]:continue
                v=f'{j}_{m}_{s}'
                lookup[v]={'job':j,'machine':m,'start':s,'end':s+d}
                available.append((s,v))
                linear[v]-=P
                linear[v]+=operation_cost_cents(m,s,d)/ELECTRICITY_DENOMINATOR
                if m=='S':linear[v]+=2*WEIGHT[j]*max(0,s+d-DUE[j])
            if not available:raise ValueError(f'No valid candidate starts for {j} {m} at H={H}')
            byop[j,m]=available
            offset+=P
            for (_,v),(_,w) in combinations(available,2):quadratic[tuple(sorted((v,w)))]+=2*P
    for m in MACHINES:
        for j1,j2 in combinations(jobs,2):
            d1=jobs[j1][MACHINES.index(m)];d2=jobs[j2][MACHINES.index(m)]
            for t1,v in byop[j1,m]:
                for t2,w in byop[j2,m]:
                    if t1<t2+d2 and t2<t1+d1:quadratic[tuple(sorted((v,w)))]+=P
    for j,ds in jobs.items():
        for before,after,d in [('T','F',ds[0]),('F','S',ds[1])]:
            for t1,v in byop[j,before]:
                for t2,w in byop[j,after]:
                    if t2<t1+d:quadratic[tuple(sorted((v,w)))]+=P
    anchors=[v for j in jobs for s,v in byop[j,'S'] if s+jobs[j][2]==H]
    if not anchors:raise ValueError('No candidate can finish at H: exact horizon infeasible')
    offset+=P
    for v in anchors:linear[v]-=P
    for v,w in combinations(anchors,2):quadratic[tuple(sorted((v,w)))]+=2*P
    bqm=dimod.BinaryQuadraticModel(dict(linear),dict(quadratic),offset,dimod.BINARY)
    metadata={'jobs':len(jobs),'exact_horizon':H,'penalty':P,
              'binary_variables':len(bqm.variables),'quadratic_interactions':len(bqm.quadratic),
              'anchor_candidates':len(anchors),'qubo_energy_relation':'E(x)=F(x)-H for valid exact-H schedules'}
    return bqm,lookup,metadata


def run_annealer(jobs,H,P,seed):
    bqm,lookup,meta=make_exact_h_qubo(jobs,H,P)
    t0=time.perf_counter()
    samples=neal.SimulatedAnnealingSampler().sample(bqm,num_reads=READS[len(jobs)],
             num_sweeps=SWEEPS[len(jobs)],seed=seed)
    elapsed=time.perf_counter()-t0
    hits=0;best=None;min_raw=float('inf');seen=0
    for row in samples.data(['sample','energy','num_occurrences']):
        occ=int(row.num_occurrences);seen+=occ
        bits=dict(row.sample);e=float(row.energy)
        if abs(bqm.energy(bits)-e)>1e-5:raise AssertionError('Reported annealer energy differs from independent BQM')
        min_raw=min(min_raw,e)
        schedule=sorted((dict(info) for v,info in lookup.items() if bits.get(v,0)),
                        key=lambda x:(x['start'],x['machine'],x['job']))
        audit=independent_schedule_audit(jobs,schedule,exact_horizon=H)
        if audit['valid']:
            if abs(e-(audit['objective']-H))>1e-5:
                raise AssertionError('Actual QUBO energy fails analytical objective check')
            hits+=occ
            if best is None or audit['objective']<best['objective']-1e-9:
                best={'objective':audit['objective'],'metrics':audit,'schedule':schedule,'energy':e}
    if seen!=READS[len(jobs)]:raise AssertionError('Invalid total annealer read count')
    return {'seed':seed,'penalty':P,'n_jobs':len(jobs),'H':H,'reads':seen,
            'sweeps':SWEEPS[len(jobs)],'feasible_reads':hits,
            'feasible_sample_fraction':hits/seen,'runtime_s':round(elapsed,4),
            'raw_lowest_energy':min_raw,'best':best,'model':meta}


results={'experiment':'EXP4_ADAPTIVE_EXACT_MAKESPAN_QUBO','start_time_utc':UTC_NOW.isoformat(),
         'physical_qpu':False,'solver_type':'CLASSICAL simulated annealing on a quantum-compatible QUBO',
         'cp_reference':'independent OR-Tools CP-SAT','cases':[],'errors':[]}
try:
    for n,offsets in JOB_HORIZON_OFFSETS.items():
        jobs=selected(n)
        record(f'inputs/{n}jobs.json',{'processing_hours':jobs,'due_hours':{j:DUE[j] for j in jobs},
                 'priority_weights':{j:WEIGHT[j] for j in jobs},'outage':OUTAGE,
                 'tariff':'11 cents/kWh outside hours modulo 8 [2,6); 27 cents/kWh inside',
                 'power_kw':POWER,'synthetic_note':'Only Z1-Z3 processing times are from the official baseline. Z4-Z5 and all industrial extensions are synthetic.'})
        cm_ref=cp_reference(jobs,'makespan')
        full_ref=cp_reference(jobs,'weighted')
        record(f'verification/{n}jobs_minimum_and_unrestricted.json',{'minimum_makespan':cm_ref,'unrestricted_weighted':full_ref})
        if not cm_ref['certified'] or not full_ref['certified']:
            raise RuntimeError(f'{n} jobs: CP-SAT references not proven; abort comparison')
        minH=int(cm_ref['metrics']['makespan_hours'])
        case={'jobs':n,'H_min_certified':minH,'unrestricted_optimum':full_ref['objective'],
              'unrestricted_optimum_H':full_ref['metrics']['makespan_hours'],
              'horizons':[]}
        for add in offsets:
            H=minH+add
            fixed=cp_reference(jobs,'weighted',exact_horizon=H)
            record(f'verification/{n}jobs_exactH{H}.json',fixed)
            if not fixed['certified']:raise RuntimeError(f'CP-SAT exact-H {H}, n={n} not proven; stop')
            hrec={'H':H,'cp_sat_exact_horizon_optimum':fixed['objective'],
                  'reference_certified':True,'trials':[]}
            for P in PENALTIES:
                bqm,lookup,meta=make_exact_h_qubo(jobs,H,P)
                record(f'models/{n}jobs_H{H}_P{P}.json',
                       {'metadata':meta,'offset':bqm.offset,
                        'linear':{str(v):float(bqm.get_linear(v)) for v in bqm.variables},
                        'quadratic':[{'u':str(u),'v':str(v),'bias':float(c)}
                                     for (u,v),c in bqm.quadratic.items()]})
                for seed in SEEDS:
                    trial=run_annealer(jobs,H,P,seed)
                    best=trial['best']
                    trial['matches_certified_exact_H_optimum']=bool(best and abs(best['objective']-fixed['objective'])<1e-6)
                    trial['matches_unrestricted_global_optimum']=bool(best and abs(best['objective']-full_ref['objective'])<1e-6)
                    hrec['trials'].append(trial)
                    record(f'runs/{n}jobs_H{H}.json',hrec)
                    print(f'jobs={n} exact-H={H} penalty={P} seed={seed} feasible={trial["feasible_sample_fraction"]:.1%}'
                          f' best={best["objective"] if best else "NONE"}')
            found=[t['best'] for t in hrec['trials'] if t['best']]
            hrec['best_annealer_objective']=min((t['objective'] for t in found),default=None)
            hrec['exact_H_optimum_matches']=sum(t['matches_certified_exact_H_optimum'] for t in hrec['trials'])
            hrec['unrestricted_global_matches']=sum(t['matches_unrestricted_global_optimum'] for t in hrec['trials'])
            hrec['n_trials']=len(hrec['trials'])
            hrec['model_size']=hrec['trials'][0]['model'] if hrec['trials'] else None
            case['horizons'].append(hrec)
            record(f'runs/{n}jobs_H{H}.json',hrec)
        valid=[t['best'] for h in case['horizons'] for t in h['trials'] if t['best']]
        case['best_adaptive_schedule']=min(valid,key=lambda r:r['objective']) if valid else None
        case['adaptive_global_optimum_match']=bool(valid and abs(case['best_adaptive_schedule']['objective']-full_ref['objective'])<1e-6)
        case['certified_global_reference_gap']=round(case['best_adaptive_schedule']['objective']-full_ref['objective'],8) if valid else None
        results['cases'].append(case)
except Exception as exc:
    results['errors'].append({'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()})
    print('An error occurred; partial evidence was saved:',exc)

results['runtime_environment']={'python':sys.version,'packages':{n:packages.version(n) for n in ('dimod','dwave-neal','ortools','numpy','matplotlib')}}
record('summaries/full_results.json',results)
lines=['ERP QUANTUM HACKATHON — EXPERIMENT 4 ADAPTIVE HORIZON',
       'Actual executed solver: classical neal simulated annealing on QUBO; CP-SAT exact references.',
       'No physical QPU, VeloxQ, or new Qiskit Aer circuit runs.',
       'H = exact, constrained makespan, not simply upper bound.',
       'All outages, prices and due dates synthetic; 4-5 job expansions synthetic.',
       'Objective F = Cmax + 2*weighted tardiness + 0.02*electricity USD.',
       'Timestamp UTC: '+datetime.now(timezone.utc).isoformat()]
for case in results['cases']:
    lines+=['',f"JOBS={case['jobs']} CP-SAT minimum H={case['H_min_certified']} "
            f"global weighted optimum={case['unrestricted_optimum']} "
            f"(H={case['unrestricted_optimum_H']})"]
    for h in case['horizons']:
        lines.append(f"  exact H={h['H']}: variables={h['model_size']['binary_variables'] if h['model_size'] else 'NA'}, "
                     f"couplers={h['model_size']['quadratic_interactions'] if h['model_size'] else 'NA'}, "
                     f"CP-SAT OPT={h['cp_sat_exact_horizon_optimum']}; "
                     f"QUBO best={h['best_annealer_objective']}; "
                     f"exact-H matches={h['exact_H_optimum_matches']}/{h['n_trials']}; "
                     f"global matches={h['unrestricted_global_matches']}/{h['n_trials']}")
    lines.append(f"  ADAPTIVE BEST={case['best_adaptive_schedule']['objective'] if case['best_adaptive_schedule'] else 'NONE'}; "
                 f"global optimum match={case['adaptive_global_optimum_match']}; "
                 f"global objective gap={case['certified_global_reference_gap']}")
lines.append('ERRORS: '+str(results['errors']) if results['errors'] else 'ERRORS: None')
lines.append('Share this entire summary with the Agentic AI Project Coordinator for scientific review.')
(ROOT/'FINAL_RESULTS_FOR_CHATGPT.txt').write_text('\n'.join(lines)+'\n',encoding='utf8')
if results['cases']:
    fig,ax=plt.subplots(figsize=(8,4))
    for c in results['cases']:
        ax.plot([h['H'] for h in c['horizons']],[h['cp_sat_exact_horizon_optimum'] for h in c['horizons']],
                'o-',label=f"{c['jobs']} jobs certified exact-H")
        if c['best_adaptive_schedule']:
            ax.axhline(c['unrestricted_optimum'],linestyle=':',linewidth=0.9)
    ax.set(xlabel='Exact makespan H (hours)',ylabel='Weighted business objective',
           title='Why minimum makespan is not always minimum business cost')
    ax.legend(fontsize=8);fig.tight_layout()
    fig.savefig(ROOT/'figures/horizon_objective_tradeoff.png',dpi=160);plt.close(fig)

all_files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='manifest.json')
record('manifest.json',{'timestamp_utc':datetime.now(timezone.utc).isoformat(),
       'file_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in all_files},
       'no_physical_qpu':True})
archive=ROOT.parent/('ERP_Experiment4_Adaptive_Horizon_Evidence_'+RUNID+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as zf:
    for p in ROOT.rglob('*'):
        if p.is_file():zf.write(p,arcname=str(ROOT.name+'/'+str(p.relative_to(ROOT))))
print('\n'+'\n'.join(lines)+'\nEVIDENCE ZIP: '+str(archive))
try:
    from google.colab import files
    files.download(str(archive))
except ImportError:
    print('Not in Colab: ZIP saved to',archive)
except Exception as exc:
    print('Browser download could not be started; ZIP remains saved:',exc)
