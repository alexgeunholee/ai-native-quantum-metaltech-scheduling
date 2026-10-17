#!/usr/bin/env python3
"""Offline public submission checker: archived evidence only; never runs a solver."""
from pathlib import Path
import json, hashlib, math, sys
ROOT=Path(__file__).resolve().parents[1]
def j(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
checks=[]
def ok(label): checks.append(label); print('PASS:',label)

def manifest_check(folder, manifest_name='manifest.json'):
    base=ROOT/folder
    m=json.loads((base/manifest_name).read_text())
    raw=m.get('files',{})
    assert raw,folder
    for name, meta in raw.items():
        p=base/name
        assert p.exists(),f'Missing {p}'
        b=p.read_bytes()
        digest = meta['sha256'] if isinstance(meta,dict) else meta
        assert hashlib.sha256(b).hexdigest()==digest,p
        if isinstance(meta,dict) and 'bytes' in meta: assert len(b)==meta['bytes'],p
    ok(f'{folder}: {len(raw)} content hashes')

def schedule_check(instance, sched):
    jobs={z['id']:z['operations'] for z in instance['jobs']}
    expectation={(name,o['machine']):o['duration'] for name,ops in jobs.items() for o in ops}
    spans={}
    for row in sched['schedule']:
        k=(row['job'],row['machine'])
        assert k in expectation and k not in spans,('duplicate/unexpected operation',k)
        s,e=row['start'],row['end']
        assert type(s)==type(e)==int and s>=0 and e-s==expectation[k],row
        spans[k]=(s,e)
    assert spans.keys()==expectation.keys(),'Missing operations'
    for name,ops in jobs.items():
        for a,b in zip(ops,ops[1:]):
            assert spans[name,a['machine']][1] <= spans[name,b['machine']][0]
    for m in set(k[1] for k in expectation):
        intervals=sorted(spans[k] for k in spans if k[1]==m)
        assert all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:])),m
    assert max(e for s,e in spans.values())==sched['makespan']
    return spans

def qubo_energy(model,schedule):
    x={k:0 for k in model['linear']}
    for row in schedule['schedule']:
        key=f"{row['job']}_{row['machine']}_{row['start']}"
        assert key in x,key
        x[key]=1
    return model['offset']+sum(float(b)*x[k] for k,b in model['linear'].items())+sum(float(o['bias'])*x[o['u']]*x[o['v']] for o in model['quadratic'])

assert (ROOT/'LICENSE').read_text().startswith('MIT License')
assert (ROOT/'AI_USAGE.md').exists() and (ROOT/'DEVELOPMENT_LOG.md').exists() and (ROOT/'PROJECT_DESIGN.md').exists()
ok('MIT license + required documentation')
manifest_check('evidence/original_baselines')
manifest_check('evidence/robustness_scaling')
# Different evidence generators use different manifest key names.
for folder,fn,key in [('evidence/adaptive_horizon','manifest.json','file_sha256'),
                      ('evidence/veloxq_initial_campaign','SHA256_MANIFEST.json',None)]:
    base=ROOT/folder
    md=json.loads((base/fn).read_text())
    rows=md[key] if key else md
    for name,digest in rows.items():
        p=base/name
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,p
    ok(f'{folder}: {len(rows)} content hashes')
for fname, expected in [('2x2',4),('3x3',8)]:
    sc=j(f'schedule_{fname}.json')
    inst=j(f'evidence/original_baselines/inputs/instance_{fname}.json')
    schedule_check(inst,sc)
    model=j(f'evidence/original_baselines/qubos/instance_{fname}_H{expected}_model.json')
    assert abs(qubo_energy(model,sc))<1e-7
    assert sc['makespan']==expected
    ok(f'official {fname}: valid schedule, zero QUBO energy, makespan {expected}h')
live=j('evidence/live_demo/LIVE_DEMO_RESULTS.json')
assert live['mode']=='live cell-by-cell demonstration'
for name,obj in [('official_3jobs_H8',8.0),('energy_3jobs_H9_P25',11.4456),('energy_4jobs_H12_P25',14.5808),('energy_5jobs_H13_P25',15.7132)]:
    r=live['new_results']['veloxq_'+name]
    assert r['status']=='SUCCESS' and r['best']['feasible'] and r['match_reference']
    assert math.isclose(r['best']['objective'],obj,abs_tol=1e-4),name
    assert 0<r['feasible']<=r['reads']==256,name
    ok(f'live VeloxQ {name}: reported SUCCESS and objective match')
assert live['new_results']['qaoa_A']['optimal_shots']==141
ok('live QAOA: archived 141 / 4096 optimal shots')
for f in ROOT.rglob('*'):
    if f.is_file() and f.suffix in ('.py','.ipynb','.md','.json','.txt','.csv','.env'):
        raw=f.read_text(encoding='utf-8',errors='replace')
        assert not __import__('re').search(r'(?i)(?:VELOX_TOKEN|token|apikey|api_key)\s*[:=]\s*[\"\']?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',raw),f'Credential-looking assignment: {f}'
ok('sensitive original token not present in textual files')
print(f'\nALL CHECKS PASSED: {len(checks)}. No quantum/classical solver executed.\n')
