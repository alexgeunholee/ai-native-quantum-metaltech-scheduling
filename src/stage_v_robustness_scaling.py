# ERP Quantum Hackathon 2026 — Experiment 3: robustness, scaling and QAOA depth
# Run in a Google Colab cell after: %pip -q install "qiskit>=1.1,<3" "qiskit-aer>=0.14,<1" "dimod>=0.12,<1" "dwave-neal>=0.6,<1" "ortools>=9.9,<11" numpy scipy matplotlib
# Self-contained synthetic data and executable experiments. No paid/hardware API.
from __future__ import annotations
import json, hashlib, time, math, platform, sys, zipfile, traceback
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
from itertools import combinations
import importlib.metadata as metadata
import numpy as np
import dimod, neal
from ortools.sat.python import cp_model
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt

STAMP = datetime.now(timezone.utc).isoformat()
RUN_ID = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
BASE = Path('/content') if Path('/content').exists() else Path.cwd()
ROOT = BASE / ('ERP_EXPERIMENT3_EVIDENCE_' + RUN_ID)
ROOT.mkdir(parents=True, exist_ok=False)
for sub in ['inputs','models','runs','verification','figures','quantum']:(ROOT/sub).mkdir(exist_ok=True)
SEEDS = [101, 202, 303, 404, 505]
PENALTIES = [5, 25, 100]
READS = {3:120, 4:150, 5:170}
SWEEPS = {3:800, 4:1000, 5:1200}
CP_LIMIT_S = 40
PERIOD = 8
POWER = {'T':8,'F':12,'S':6}
OUTAGE = ('F',3,5)
COST_UNIT = 5000  # cents/5000 = 0.02 * electricity cost in USD
DURATION = {'Z1':(2,1,2),'Z2':(1,2,1),'Z3':(2,2,1),
            'Z4':(1,2,2),'Z5':(2,1,1)}  # Z4,Z5 synthetic, not official
DUES = {'Z1':7,'Z2':5,'Z3':10,'Z4':12,'Z5':14}  # synthetic
WEIGHTS = {'Z1':1,'Z2':3,'Z3':1,'Z4':2,'Z5':1}
MACHINES = ('T','F','S')

# F = makespan + 2 * weighted tardiness + 0.02 * tariff-based electricity USD.
# For fixed-minimum-makespan QUBO, the makespan is constant, so QUBO
# minimizes the remaining terms. FULL weighted optimum is separately checked.
def save(rel, obj):
    p=ROOT/rel; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+'\n',encoding='utf8')
    return p

def cost_cents(machine,start,duration):
    # Peak in hours [2,6), [10,14), ...; matches original 3-job case at H=9.
    peak=sum(1 for h in range(start,start+duration) if 2 <= h%PERIOD < 6)
    return POWER[machine]*(peak*27+(duration-peak)*11)

def selected_jobs(n):return {j:DURATION[j] for j in list(DURATION)[:n]}

def audit(jobs, schedule, horizon=None):
    expected={(j,m):d for j,dd in jobs.items() for m,d in zip(MACHINES,dd)}
    seen={}; errors=[]
    for item in schedule:
        j,m,s,e=item['job'],item['machine'],item['start'],item['end'];k=(j,m)
        if k not in expected or k in seen:errors.append('duplicate/unknown '+str(k));continue
        if not isinstance(s,int) or not isinstance(e,int) or s<0 or e-s!=expected[k]:errors.append('invalid time '+str(k))
        if m==OUTAGE[0] and s<OUTAGE[2] and e>OUTAGE[1]:errors.append('maintenance '+str(k))
        if horizon is not None and e>horizon:errors.append('horizon '+str(k))
        seen[k]=(s,e)
    if set(seen)!=set(expected):errors.append('missing operations')
    for j in jobs:
        for a,b in zip(MACHINES,MACHINES[1:]):
            if (j,a) in seen and (j,b) in seen and seen[j,a][1]>seen[j,b][0]:errors.append('precedence '+j)
    for m in MACHINES:
        ints=sorted((s,e) for (j,m1),(s,e) in seen.items() if m1==m)
        for a,b in zip(ints,ints[1:]):
            if a[1]>b[0]:errors.append('machine collision '+m)
    if errors:return {'valid':False,'errors':errors}
    makespan=max(e for s,e in seen.values())
    tard=sum(WEIGHTS[j]*max(0,seen[j,'S'][1]-DUES[j]) for j in jobs)
    cents=sum(cost_cents(m,s,e-s) for (j,m),(s,e) in seen.items())
    return {'valid':True,'makespan':makespan,'weighted_tardiness':tard,
            'electricity_usd':cents/100,'electricity_cents':cents,
            'objective':round(makespan+2*tard+cents/COST_UNIT,8)}

def cpsat(jobs, mode, horizon=None):
    upper=sum(sum(ds) for ds in jobs.values()) + (OUTAGE[2]-OUTAGE[1])+6
    model=cp_model.CpModel(); starts={};ends={};intervals=defaultdict(list)
    for j,durations in jobs.items():
        for m,d in zip(MACHINES,durations):
            s=model.NewIntVar(0,upper-d,f's_{j}_{m}')
            e=model.NewIntVar(0,upper,f'e_{j}_{m}')
            intervals[m].append(model.NewIntervalVar(s,d,e,f'i_{j}_{m}'))
            starts[j,m]=s;ends[j,m]=e
        model.Add(starts[j,'F']>=ends[j,'T'])
        model.Add(starts[j,'S']>=ends[j,'F'])
    ms,lo,hi=OUTAGE
    intervals[ms].append(model.NewIntervalVar(lo,hi-lo,hi,'maintenance'))
    for items in intervals.values():model.AddNoOverlap(items)
    cmax=model.NewIntVar(0,upper,'cmax')
    model.AddMaxEquality(cmax,[ends[j,'S'] for j in jobs])
    if horizon is not None:model.Add(cmax<=horizon)
    if mode=='makespan':model.Minimize(cmax)
    else:
        tard=[];energy=[]
        for j in jobs:
            t=model.NewIntVar(0,upper,'tard_'+j)
            model.Add(t>=ends[j,'S']-DUES[j])
            tard.append(WEIGHTS[j]*t)
            for m,d in zip(MACHINES,jobs[j]):
                table=[cost_cents(m,s,d) for s in range(upper-d+1)]
                ec=model.NewIntVar(min(table),max(table),f'c_{j}_{m}')
                model.AddElement(starts[j,m],table,ec)
                energy.append(ec)
        model.Minimize(COST_UNIT*cmax+2*COST_UNIT*sum(tard)+sum(energy))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=CP_LIMIT_S
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=13
    ts=time.perf_counter();stat=solver.Solve(model);elapsed=time.perf_counter()-ts
    out={'status':solver.StatusName(stat),'proved_optimal':stat==cp_model.OPTIMAL,
         'runtime_s':round(elapsed,4),'best_bound':float(solver.BestObjectiveBound()) if stat in (cp_model.OPTIMAL,cp_model.FEASIBLE) else None}
    if stat in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        sched=sorted([dict(job=j,machine=m,start=int(solver.Value(starts[j,m])),end=int(solver.Value(ends[j,m])))
                      for j in jobs for m in MACHINES],key=lambda op:(op['start'],op['machine'],op['job']))
        a=audit(jobs,sched,horizon)
        if not a['valid']:raise AssertionError('Independent audit rejected CP-SAT output')
        obj=float(solver.ObjectiveValue())/(1 if mode=='makespan' else COST_UNIT)
        if abs(obj-(a['makespan'] if mode=='makespan' else a['objective']))>1e-6:
            raise AssertionError('CP-SAT objective differs from independent auditor')
        out.update(schedule=sched,metrics=a,objective=obj)
    return out

def make_qubo(jobs,horizon,penalty):
    # Fixed horizon H is independently determined by CP-SAT min-makespan.
    # Every feasible fixed-H schedule then has Cmax=H, a constant.
    linear=defaultdict(float);pairs=defaultdict(float);windows={};lookup={};offset=0.
    for j,durations in jobs.items():
        for k,(m,d) in enumerate(zip(MACHINES,durations)):
            earliest=sum(durations[:k]);latest=horizon-sum(durations[k:]);arr=[]
            for s in range(earliest,latest+1):
                if m==OUTAGE[0] and s<OUTAGE[2] and s+d>OUTAGE[1]:continue
                name=f'{j}_{m}_{s}'
                arr.append((s,name));lookup[name]={'job':j,'machine':m,'start':s,'end':s+d}
                linear[name]+=-penalty
                linear[name]+=cost_cents(m,s,d)/COST_UNIT
                if m=='S':linear[name]+=2*WEIGHTS[j]*max(0,s+d-DUES[j])
            if not arr:raise ValueError(f'no starts for {j} {m} at H={horizon}')
            windows[j,m]=arr;offset+=penalty
            for (sa,a),(sb,b) in combinations(arr,2):pairs[tuple(sorted((a,b)))]+=2*penalty
    for m in MACHINES:
        for ja,jb in combinations(jobs,2):
            da=jobs[ja][MACHINES.index(m)];db=jobs[jb][MACHINES.index(m)]
            for sa,a in windows[ja,m]:
                for sb,b in windows[jb,m]:
                    if sa<sb+db and sb<sa+da:pairs[tuple(sorted((a,b)))]+=penalty
    for j,ds in jobs.items():
        for ma,mb,da in [('T','F',ds[0]),('F','S',ds[1])]:
            for sa,a in windows[j,ma]:
                for sb,b in windows[j,mb]:
                    if sb<sa+da:pairs[tuple(sorted((a,b)))]+=penalty
    bqm=dimod.BinaryQuadraticModel(dict(linear),dict(pairs),offset,dimod.BINARY)
    meta={'vars':len(linear),'couplers':len(pairs),'penalty':penalty,'horizon':horizon,'offset':offset}
    return bqm,lookup,meta

def decode(sample,lookup):
    return sorted([dict(v) for name,v in lookup.items() if sample.get(name,0)],
                  key=lambda op:(op['start'],op['machine'],op['job']))

def sampler_trial(jobs,H,penalty,seed,reads,sweeps):
    bqm,lookup,meta=make_qubo(jobs,H,penalty)
    t0=time.perf_counter()
    rows=neal.SimulatedAnnealingSampler().sample(bqm,num_reads=reads,num_sweeps=sweeps,seed=seed)
    runtime=time.perf_counter()-t0
    hits=0;best=None;min_energy=math.inf;sample_count=0
    for row in rows.data(['sample','energy','num_occurrences']):
        n=int(row.num_occurrences);sample_count+=n
        energy=float(row.energy);min_energy=min(min_energy,energy)
        sample=dict(row.sample)
        if abs(float(bqm.energy(sample))-energy)>1e-5:raise AssertionError('Solver/BQM energy mismatch')
        sched=decode(sample,lookup);a=audit(jobs,sched,H)
        if a['valid']:
            if abs(energy-(a['objective']-H))>1e-5:raise AssertionError('QUBO feasible energy/objective mismatch')
            hits+=n
            if best is None or a['objective']<best['objective']-1e-8:
                best={'objective':a['objective'],'schedule':sched,'metrics':a,'energy':energy}
    assert sample_count==reads,(sample_count,reads)
    return {'n_jobs':len(jobs),'seed':seed,'penalty':penalty,'reads':reads,'sweeps':sweeps,
            'runtime_s':round(runtime,4),'valid_shots':hits,'valid_fraction':hits/reads,
            'lowest_raw_energy':min_energy,'best':best,'model':meta}

def qaoa_depth_study():
    # Independent 8-qubit mandatory Instance A, not a scale-model run.
    jobs={'Z1':(2,1),'Z2':(1,2)};names=[];windows={};duration={}
    for j,ds in jobs.items():
        for idx,(m,d) in enumerate(zip(('T','F'),ds)):
            arr=[]
            for s in range(sum(ds[:idx]),4-sum(ds[idx:])+1):
                name=f'{j}_{m}_{s}';names.append(name);arr.append((s,name));duration[name]=(j,m,s,d)
            windows[j,m]=arr
    qlin={n:-1.0 for n in names};qp=defaultdict(float);offset=0.0
    for arr in windows.values():
        offset+=1
        for (_,a),(_,b) in combinations(arr,2):qp[tuple(sorted((a,b)))]+=2
    for m in ('T','F'):
        for ta,a in windows['Z1',m]:
            for tb,b in windows['Z2',m]:
                da=duration[a][3];db=duration[b][3]
                if ta<tb+db and tb<ta+da:qp[tuple(sorted((a,b)))]+=1
    for j,ds in jobs.items():
        for st,a in windows[j,'T']:
            for sf,b in windows[j,'F']:
                if sf<st+ds[0]:qp[tuple(sorted((a,b)))]+=1
    assert len(names)==8
    index={n:i for i,n in enumerate(names)}
    z=np.array([-qlin[n]/2 for n in names],dtype=float)
    zz={}
    for (a,b),coef in qp.items():
        ia,ib=index[a],index[b];z[ia]-=coef/4;z[ib]-=coef/4;zz[ia,ib]=coef/4
    energies=[]
    for n in range(1<<8):
        bits={v:(n>>index[v])&1 for v in names}
        energies.append(offset+sum(qlin[v]*bits[v] for v in names)
                        +sum(coef*bits[a]*bits[b] for (a,b),coef in qp.items()))
    energies=np.array(energies)
    assert min(energies)==0
    results=[];sim=AerSimulator(method='statevector')
    for depth in (1,2,3):
        for trial_seed in (23,67):
            def circuit(par,measure=False):
                qc=QuantumCircuit(8,8 if measure else 0)
                qc.h(range(8))
                for layer in range(depth):
                    g,b=par[2*layer:2*layer+2]
                    for i,coef in enumerate(z):
                        if abs(coef)>1e-10:qc.rz(2*g*coef,i)
                    for (i,j),coef in zz.items():qc.rzz(2*g*coef,i,j)
                    for i in range(8):qc.rx(2*b,i)
                if measure:qc.measure(range(8),range(8))
                return qc
            def mean_energy(par):
                amplitudes=Statevector.from_instruction(circuit(par)).data
                return float(np.dot(abs(amplitudes)**2,energies))
            init=np.random.default_rng(trial_seed+depth*100).uniform(0,math.pi,2*depth)
            t0=time.perf_counter();res=minimize(mean_energy,init,method='COBYLA',options={'maxiter':110,'rhobeg':0.6,'tol':1e-4})
            qc=transpile(circuit(res.x,True),sim,optimization_level=1,seed_transpiler=7)
            counts=sim.run(qc,shots=2048,seed_simulator=trial_seed).result().get_counts()
            opt=sum(v for b,v in counts.items() if energies[int(b.replace(' ',''),2)]<1e-8)
            results.append({'depth':depth,'seed':trial_seed,'fit_success':bool(res.success),
                            'optimizer_message':str(res.message),'iterations_or_evals':int(res.nfev),
                            'fitted_mean_energy':float(res.fun),'optimal_shots':opt,
                            'shots':2048,'optimal_fraction':opt/2048,
                            'seconds':round(time.perf_counter()-t0,3),
                            'optimized_parameters_radians':[float(x) for x in res.x],
                            'aer_counts':dict(counts)})
    save('quantum/qaoa_depth_comparison.json',results)
    return results

# All formal experiments are executed from here; full exceptions are preserved.
RESULTS={'timestamp_utc':STAMP,'design':'fixed-minimum-makespan lexicographic QUBO / independent CP-SAT',
         'official':False,'hardware_qpu_used':False,'cases':[],'qaoa':[],'errors':[]}
try:
    for n in (3,4,5):
        jobs=selected_jobs(n)
        save(f'inputs/synthetic_{n}jobs.json',{'jobs':jobs,'due':{j:DUES[j] for j in jobs},
              'weights':{j:WEIGHTS[j] for j in jobs},'outage':OUTAGE,'power_kw':POWER,
              'peak_repeats_every_hours':PERIOD,'peak_hours_modulo':[2,6],
              'prices_cents_per_kwh':[11,27],'provenance':'Z1-Z3 processing times from official 3x3; Z4/Z5 and all extensions synthetic'})
        rmin=cpsat(jobs,'makespan')
        if not rmin['proved_optimal']:
            raise RuntimeError(f'{n} jobs: minimum-makespan optimum NOT certified; fixed-H QUBO comparison halted safely')
        H=int(rmin['metrics']['makespan'])
        rfixed=cpsat(jobs,'weighted',H)
        rglobal=cpsat(jobs,'weighted')
        save(f'verification/{n}jobs_cp_sat.json',{'makespan_reference':rmin,'fixed_horizon_reference':rfixed,'full_weighted_reference':rglobal})
        case={'n_jobs':n,'horizon':H,'makespan_certified':rmin['proved_optimal'],
              'fixed_ref':rfixed['objective'] if 'objective' in rfixed else None,
              'fixed_ref_certified':rfixed['proved_optimal'],
              'full_weighted_reference':rglobal.get('objective'),
              'full_ref_certified':rglobal['proved_optimal'],'trials':[]}
        for penalty in PENALTIES:
            bqm,lookup,meta=make_qubo(jobs,H,penalty)
            save(f'models/{n}jobs_penalty{penalty}_metadata.json',meta)
            save(f'models/{n}jobs_penalty{penalty}_coefficients.json',
                 {'vartype':'BINARY','offset':bqm.offset,
                  'linear':{str(v):float(bqm.get_linear(v)) for v in bqm.variables},
                  'quadratic':[{'u':str(u),'v':str(v),'bias':float(coef)}
                               for (u,v),coef in bqm.quadratic.items()]})
            if penalty==PENALTIES[0]:case['model_size']={'variables':meta['vars'],'quadratic_interactions':meta['couplers']}
            for seed in SEEDS:
                trial=sampler_trial(jobs,H,penalty,seed,READS[n],SWEEPS[n])
                if trial['best'] and rfixed.get('proved_optimal') and rmin.get('proved_optimal'):
                    trial['matches_fixed_horizon_optimum']=abs(trial['best']['objective']-rfixed['objective'])<1e-6
                    trial['fixed_horizon_gap']=round(trial['best']['objective']-rfixed['objective'],8)
                else:
                    trial['matches_fixed_horizon_optimum']=None
                    trial['fixed_horizon_gap']=None
                case['trials'].append(trial)
                save(f'runs/{n}jobs_all_trials.json',case)  # incremental checkpoint
                print(f'JOBS={n} H={H} penalty={penalty} seed={seed} valid={trial["valid_fraction"]:.1%} '
                      f'best={trial["best"]["objective"] if trial["best"] else "NONE"}')
        save(f'runs/{n}jobs_all_trials.json',case)
        RESULTS['cases'].append(case)
    print('Running separate 8-qubit Qiskit Aer QAOA depth study (not scaled BQM QPU)...')
    RESULTS['qaoa']=qaoa_depth_study()
except Exception as error:
    RESULTS['errors'].append({'error':repr(error),'traceback':traceback.format_exc()})
    print('Experiment stopped; partial records preserved:',repr(error))

# Compact summary: copy only this text file to ChatGPT.
lines=['ERP HACKATHON — EXPERIMENT 3 RESULTS','Generated UTC: '+datetime.now(timezone.utc).isoformat(),
       'Solvers: neal CLASSICAL simulated annealing; OR-Tools CP-SAT; optional 8-qubit QAOA on Qiskit Aer.',
       'NO physical QPU, quantum advantage, or VeloxQ run.',
       'Z4/Z5 jobs and all outages/deadlines/tariffs are SYNTHETIC.',
       'IMPORTANT: QUBO uses certified minimum-makespan H when available; comparisons are FIXED-HORIZON,',
       'not automatically the unrestricted globally optimal weighted objective. No CP-SAT warm starts used.']
for c in RESULTS['cases']:
    lines+=['',f"JOBS {c['n_jobs']}; H={c['horizon']}; model={c.get('model_size')}",
           f"Makespan certificate={c['makespan_certified']}; Fixed-H CP-SAT reference={c['fixed_ref']} proven={c['fixed_ref_certified']}",
           f"Unrestricted weighted CP-SAT reference={c['full_weighted_reference']} proven={c['full_ref_certified']}"]
    for p in PENALTIES:
        a=[x for x in c['trials'] if x['penalty']==p]
        feasible=[x for x in a if x['best']]
        wins=sum(x['matches_fixed_horizon_optimum'] is True for x in a)
        mean_rate=sum(x['valid_fraction'] for x in a)/len(a)
        lines.append(f'  penalty {p}: feasible seeds {len(feasible)}/{len(a)}, certified-optimum matches {wins}/{len(a)} '
                     f'(only if references certified); mean feasible shots {mean_rate:.2%}; '
                     f'best F={min((x["best"]["objective"] for x in feasible),default="NONE")}')
if RESULTS['qaoa']:
    lines+=['','8-QUBIT QAOA DEPTH TEST (actual Qiskit Aer shots)']
    for depth in (1,2,3):
        items=[r for r in RESULTS['qaoa'] if r['depth']==depth]
        lines.append(f'  p={depth}: success fractions {[round(r["optimal_fraction"],5) for r in items]}; '
                     f'COBYLA success flags {[r["fit_success"] for r in items]}')
lines+=['','ERRORS: '+str(RESULTS['errors']) if RESULTS['errors'] else 'ERRORS: None',
        'Next step: share this file with the Agentic AI PC before making performance claims.']
(ROOT/'FINAL_RESULTS_FOR_CHATGPT.txt').write_text('\n'.join(lines)+'\n',encoding='utf8')
RESULTS['python']=sys.version
RESULTS['packages']={name:metadata.version(name) for name in ('qiskit','qiskit-aer','dimod','dwave-neal','ortools','numpy','scipy')}
save('full_results.json',RESULTS)

# Plot only actual observations, never fabricated or inferred performance numbers.
if RESULTS['cases']:
    fig,ax=plt.subplots(figsize=(8,5))
    for p in PENALTIES:
        xs=[];ys=[]
        for c in RESULTS['cases']:
            vals=[t['valid_fraction'] for t in c['trials'] if t['penalty']==p]
            xs.append(c['n_jobs']);ys.append(float(np.mean(vals)))
        ax.plot(xs,ys,'o-',label=f'Penalty {p}')
    ax.set(xlabel='Number of jobs',ylabel='Mean feasible sample fraction',ylim=(0,1),
           title='Unseeded QUBO annealing: constraint feasibility versus scale')
    ax.legend();fig.tight_layout();fig.savefig(ROOT/'figures/feasibility_vs_scale.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,5));xs=[c['n_jobs'] for c in RESULTS['cases']]
    ax.plot(xs,[c['model_size']['variables'] for c in RESULTS['cases']],'o-',label='Binary variables')
    ax.plot(xs,[c['model_size']['quadratic_interactions'] for c in RESULTS['cases']],'s-',label='Quadratic couplers')
    ax.set(xlabel='Number of jobs',ylabel='Count',title='Fixed-minimum-horizon QUBO model growth')
    ax.legend();fig.tight_layout();fig.savefig(ROOT/'figures/model_growth.png',dpi=160);plt.close(fig)
if RESULTS['qaoa']:
    fig,ax=plt.subplots(figsize=(8,5))
    for r in RESULTS['qaoa']:ax.scatter(r['depth'],r['optimal_fraction'])
    ax.set(xlabel='QAOA depth p',ylabel='Optimal sample fraction',ylim=(0,1),
           title='Actual Qiskit Aer runs, two optimizer seeds per depth')
    fig.tight_layout();fig.savefig(ROOT/'figures/qaoa_depth.png',dpi=160);plt.close(fig)

# Provenance and automatic download, preserving original evidence ZIP separately.
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='manifest.json')
save('manifest.json',{'generated_utc':datetime.now(timezone.utc).isoformat(),
                     'files':{str(p.relative_to(ROOT)):sha(p) for p in files},
                     'initial_utc':STAMP,'physical_qpu_used':False})
zip_path=ROOT.parent/('ERP_Experiment3_Evidence_'+RUN_ID+'.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as zf:
    for p in sorted(ROOT.rglob('*')):
        if p.is_file():zf.write(p,arcname=f'{ROOT.name}/{p.relative_to(ROOT)}')
print('\n'.join(lines));print('\nEvidence ZIP:',zip_path)
try:
    from google.colab import files as colab_files
    colab_files.download(str(zip_path))
except ImportError:
    print('Outside Colab: ZIP saved locally at',zip_path)
except Exception as ex:
    print('Browser download unavailable; ZIP remains at',zip_path,':',ex)
