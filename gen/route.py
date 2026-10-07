"""GND stubs -> Specctra DSN (everything but GND) -> Freerouting -> SES -> routed.pkl"""
import os, pickle, subprocess, sys, time
import design as D
import pcbio as P
import stitch as ST

FR = '/opt/kicad/freerouting.jar'
WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'route_work')
os.makedirs(WORK, exist_ok=True)


def stubs():
    t, v, fails = ST.stitch([], [], ST.gnd_pads())
    print('GND stubs', len(v), 'fails', fails)
    return t, v


def dsn(t, v, path):
    nets = [n for n in D.all_nets() if n != 'GND']
    P.write_dsn(path, t, v, only=set(nets), obstacle_nets=['GND'])


if __name__ == '__main__':
    passes = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    t, v = stubs()
    pickle.dump((t, v), open(f'{WORK}/stubs.pkl', 'wb'))
    dsn(t, v, f'{WORK}/in.dsn')
    t0 = time.time()
    r = subprocess.run(['java', '-jar', FR, '-de', f'{WORK}/in.dsn', '-do', f'{WORK}/out.ses', '-mp', str(passes),
                        '-mt', '1', '--gui.enabled=false'], capture_output=True, text=True, timeout=5400)
    open(f'{WORK}/fr.log', 'w').write(r.stdout + r.stderr)
    print('freerouting done', round(time.time() - t0), 's')
    rt, rv = P.read_ses(f'{WORK}/out.ses')
    keep_t = [x for x in rt if x[6] != 'GND']
    keep_v = [x for x in rv if x[2] != 'GND']
    pickle.dump((t + keep_t, v + keep_v), open('routed.pkl', 'wb'))
    print('routed tracks', len(keep_t), 'vias', len(keep_v))
