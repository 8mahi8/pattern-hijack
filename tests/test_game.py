"""PATTERN HIJACK browser regression test.

Execute: python tests/test_game.py
This harness injects test helpers into a local in-memory HTML copy.
The publicly deployed index.html contains no cheat/test API.
"""
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT/'index.html').read_text(encoding='utf-8')
BRIDGE = r'''
window.__PATTERN_TEST__ = {
 state: () => ({
  waveIndex, running, dead, won, pausedUpgrade, clearingWave,
  bullets:bullets.length, hp:P.hp, alive:aliveEmitters().length,
  bossMode, bossBreak, bossHP:bossCore.hp, breaks, wavesCleared
 }),
 clearWave: () => { for(const e of [...aliveEmitters()]) killEmitter(e); },
 forceCapture: pid => {
  hostile(300,220,0,0,5,pid,8);
  lastFlowPid=pid;
  hijack();
 },
 damageCore: damage => applyDamageToBossCore(damage),
 injectBullets: n => {for(let i=0;i<n;i++)hostile(100+(i%20)*2,180+(i%5)*2,0,0,5,0,8)},
 forceCollisionKill: () => {
  // Simulate a real projectile collision that destroys the final emitter during update().
  for(const e of emitters){e.alive=false;e.hp=0}
  const e=emitters[0];e.alive=true;e.hp=.01;
  bullets.push({x:e.x,y:e.y,vx:0,vy:0,r:3,friendly:true,auto:false,damage:2,life:1});
 },
 forceGameOver: () => {P.hp=0;dead=true;running=false;showResult(false)},
 tick: dt => update(dt),
};
'''
insert='reset(false);requestAnimationFrame(frame);'
assert HTML.count(insert)==1, 'Game bootstrapping changed: update harness'
TEST_HTML=HTML.replace(insert,BRIDGE+'\n'+insert,1)

def check(condition,desc):
 if not condition: raise AssertionError(desc)
 print('PASS:',desc)

with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path=shutil.which('chromium') or None,args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':1300,'height':870})
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(TEST_HTML,wait_until='load')
 check(page.locator('#startBtn').is_visible(),'Start screen opens')
 page.locator('#startBtn').click()
 page.wait_for_timeout(250)
 state=lambda:page.evaluate('window.__PATTERN_TEST__.state()')
 check(state()['running'] and state()['waveIndex']==0,'Wave 1 starts')
 check(page.locator('canvas').evaluate('(e)=>e.width')==960,'Canvas available')

 # Exercise real game update for a few seconds in browser.
 page.wait_for_timeout(1700)
 check(len(errors)==0,'No JavaScript exceptions during normal play')

 # Advance all four waves, including the notoriously fragile last-emitter handoff.
 for wave in range(4):
  check(state()['waveIndex']==wave,f'Correct wave {wave+1}')
  page.evaluate('window.__PATTERN_TEST__.clearWave()')
  check(state()['clearingWave'],f'Wave {wave+1} enters safe transition')
  page.wait_for_timeout(660)
  check(page.locator('#upgrade').evaluate('(e)=>e.classList.contains("show")'),f'Upgrade opens after wave {wave+1}')
  page.locator('#cards .card').first.click()
  page.wait_for_timeout(60)

 check(state()['bossMode'] and state()['waveIndex']==4,'Reached Boss after four upgrades')
 check(state()['bossHP']==720,'Boss starts with full core health')
 page.evaluate('window.__PATTERN_TEST__.damageCore(200)')
 check(state()['bossHP']==720,'Boss cannot be damaged before CORE BREAK')

 for pid in [0,2,3]:
  page.evaluate('(pid)=>window.__PATTERN_TEST__.forceCapture(pid)',pid)
 check(state()['bossBreak']>0 and state()['breaks']>=1,'Three-color HIJACK triggers CORE BREAK')
 page.evaluate('window.__PATTERN_TEST__.damageCore(10000)')
 page.wait_for_timeout(350)
 check(page.locator('#result').evaluate('(e)=>e.classList.contains("show")'), 'Clear screen appears after defeating Boss')
 check('CLEAR' in page.locator('#resultTitle').inner_text(), 'Victory is reported accurately')

 # Recovery from run state including old key state / stale callbacks.
 page.locator('#resultRestart').click()
 check(page.locator('#startBtn').is_visible() and not state()['running'],'Restart returns to clean menu')
 page.locator('#startBtn').click()
 page.evaluate('window.__PATTERN_TEST__.injectBullets(950)')
 page.evaluate('window.__PATTERN_TEST__.tick(.016)')
 check(state()['bullets']<=620,'High load respects bullet cap')
 check(len(errors)==0,'No JS exceptions across clear/restart/stress cycle')
 page.evaluate('window.__PATTERN_TEST__.forceCollisionKill()')
 page.evaluate('window.__PATTERN_TEST__.tick(.016)')
 check(state()['clearingWave'],'Projectile collision with final emitter triggers safe transition')
 page.locator('#restart').click()
 page.wait_for_timeout(700)
 check(not state()['running'] and not page.locator('#upgrade').is_visible(), 'Restart during transition cannot open stale upgrade')
 check(len(errors)==0,'No JS exceptions after restart-during-transition')
 # Mobile regression: stage is very short on phones; overlays must escape it.
 # Emulate portrait, landscape, and compact touch screens and use actual taps.
 for width,height in [(390,844),(844,390),(320,568)]:
  mobile=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=3,is_mobile=True,has_touch=True)
  mobile_errors=[]
  mobile.on('pageerror',lambda e: mobile_errors.append(str(e)))
  mobile.set_content(TEST_HTML,wait_until='load')
  prefix=f'Mobile {width}x{height}'
  mobile.locator('#startBtn').tap(timeout=5000)
  check(mobile.evaluate('window.__PATTERN_TEST__.state().running'),prefix+' START tap works')
  mobile.locator('#restart').tap(timeout=5000)
  check(mobile.locator('#startBtn').is_visible(),prefix+' header RESTART tap works')
  mobile.locator('#startBtn').tap(timeout=5000)
  mobile.evaluate('window.__PATTERN_TEST__.clearWave()')
  mobile.wait_for_timeout(650)
  check(mobile.locator('#upgrade').is_visible(),prefix+' upgrade overlay is displayed')
  mobile.locator('#cards .card').last.tap(timeout=5000)
  check(mobile.evaluate('window.__PATTERN_TEST__.state().waveIndex')==1,prefix+' upgrade card tap works')
  mobile.evaluate('window.__PATTERN_TEST__.forceGameOver()')
  check(mobile.locator('#resultRestart').is_visible(),prefix+' game over overlay appears')
  mobile.locator('#resultRestart').tap(timeout=5000)
  check(mobile.locator('#startBtn').is_visible() and not mobile.evaluate('window.__PATTERN_TEST__.state().running'),prefix+' PLAY AGAIN tap works')
  check(not mobile_errors,prefix+' no JavaScript exceptions')
  mobile.close()
 browser.close()

print('ALL BROWSER TESTS PASS')
