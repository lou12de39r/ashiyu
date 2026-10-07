"""GND stubs -> Specctra DSN (everything but GND) -> Freerouting -> SES -> routed.pkl"""
import os, pickle, subprocess, sys, time
import design as D
import pcbio as P
import stitch as ST

FR = '/opt/kicad/freerouting.jar'
WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'route_work')
os.makedirs(WORK, exist_ok=True)


def stubs():
    import cleanup as CL
    et, ev = D.escapes()
    t, v, fails = et, ev, []                                   # GND is routed as a normal net (tree), pours on top
    print('GND stubs', len(v), 'fails', fails)
    return t, v


def dsn(t, v, path):
    P.write_dsn(path, t, v)


if __name__ == '__main__':
    passes = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    t, v = stubs()
    pickle.dump((t, v), open(f'{WORK}/stubs.pkl', 'wb'))
    dsn(t, v, f'{WORK}/in.dsn')
    t0 = time.time()
    for attempt in range(4):
      if os.path.exists(f'{WORK}/out.ses'):
          os.remove(f'{WORK}/out.ses')
      r = subprocess.run(['java', '-jar', FR, '-de', f'{WORK}/in.dsn', '-do', f'{WORK}/out.ses', '-mp', str(passes),
                        '-mt', '1', '--gui.enabled=false'], capture_output=True, text=True, timeout=5400)
      open(f'{WORK}/fr.log', 'w').write(r.stdout + r.stderr)
      if os.path.exists(f'{WORK}/out.ses') and os.path.getsize(f'{WORK}/out.ses') > 100:
          break
      print('empty SES, retry', attempt + 1)
    print('freerouting done', round(time.time() - t0), 's')
    rt, rv = P.read_ses(f'{WORK}/out.ses')
    ren = lambda n: 'GND' if n == 'GNDJ3' else n
    keep_t = [x[:6] + (ren(x[6]),) for x in rt if (x[1], x[2]) != (x[3], x[4])]
    keep_v = [x[:2] + (ren(x[2]),) for x in rv]
    # escapes are protected wiring of their own nets and come back in the SES; GND stubs do not
    import cleanup as CL
    rnd = lambda x: tuple(round(e, 3) if isinstance(e, float) else e for e in x)
    allt = list(dict.fromkeys(rnd(x) for x in t + keep_t))
    allv = CL.dedupe_vias([rnd(x) for x in v + keep_v])
    pickle.dump((allt, allv), open('routed.pkl', 'wb'))
    print('routed tracks', len(keep_t), 'vias', len(keep_v))
