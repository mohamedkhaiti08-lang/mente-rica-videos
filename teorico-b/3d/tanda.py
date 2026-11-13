import os, subprocess, sys, json
out, n = sys.argv[1], int(sys.argv[2])
NF = int(json.load(open(f'{out}/spec.json'))['dur'] * 30)
fr = [i for i in range(NF) if not os.path.exists(f'{out}/frames/{i:04d}.png')][:2 * n]
print('faltan', len([i for i in range(NF) if not os.path.exists(f'{out}/frames/{i:04d}.png')]), 'esta tanda', len(fr), flush=True)
if fr:
    ps = [subprocess.Popen([sys.executable, 'teorico-b/3d/motor3d.py', f'{out}/spec.json', f'{out}/frames', '--sueltos', *map(str, fr[k::2])], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for k in (0, 1)]
    for p in ps: p.wait()
print('quedan', len([i for i in range(NF) if not os.path.exists(f'{out}/frames/{i:04d}.png')]))
