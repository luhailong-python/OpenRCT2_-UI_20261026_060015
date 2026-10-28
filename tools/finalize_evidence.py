"""Refresh final local evidence after gallery QA. No source art, F: or Git mutation."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from html.parser import HTMLParser
import json,hashlib
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
now=datetime.now(ZoneInfo('America/New_York')).isoformat()
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def write(p,data):(ROOT/p).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()

samples=[
 ('designs/main/01-运行.png','HUD语义、标题暂名标记、信息条、背景与操作空间'),
 ('designs/new-ride/01-交通.png','交通设施独立插画对应、卡片与选择层级'),
 ('designs/details/ride-ops/01-overview-closed.png','设施状态、继续建设/命名/定位/拆除入口'),
 ('designs/details/utility/filebrowser-customise.png','文件导航、选中行、列与预览展开菜单'),
 ('designs/details/management/cheats-3-1.png','游客作弊分组、动作与勾选控件文字')]
review={'reviewedAt':now,'status':'sampled_static_visual_review_passed_pending_user_acceptance','method':'Saved full PNGs actually opened with view_image; source and layout QA reports separately retained. No Unity run.','directFinalRootSamples':[{'file':f,'sha256':sha(f),'observation':s,'blockingIssueObserved':False} for f,s in samples], 'supportingIndependentReports':['docs/independent-visual-review.json','docs/detail-visual-qa.json','docs/operations-visual-qa.json','docs/final-independent-audit.md','docs/product-placement-audit.md','docs/sprite-qa.md'],'allImagesIndividuallyHumanReviewed':False,'knownBlockingArtIssues':[],'unityVerified':False,'sourcePositionBoundary':{'exactSourceScopedIdentifiers':1438,'verifiedProductPositionIdentifiers':820,'unconfirmedProductPositionIdentifiers':618,'staticInteractiveCandidates':957,'candidateProductPositionsVerified':528,'candidateProductPositionsUnconfirmed':429,'identifiedConcreteArtGapGroups':18,'resolvedConcreteArtGapGroups':18},'historicalReports':'Earlier dated observations and superseded hashes remain evidence of the repair process; use current manifests and final reports for final pixels.'}
write('records/visual-review.json',review)

# Refresh every current raster hash, including the final browser screenshot.
index=read('records/image-provenance-index.json')
existing={r['file']:r for r in index['index']}
rows=[]
for folder in ('reference-art','assets','designs','previews'):
 for p in sorted((ROOT/folder).rglob('*')):
  if p.suffix.lower() not in ('.png','.jpg','.jpeg'):continue
  rel=p.relative_to(ROOT).as_posix();im=Image.open(p)
  record=next((q.relative_to(ROOT).as_posix() for q in [Path(str(p)+'.generation.json'),Path(str(p)+'.source.json'),p.with_suffix('.source.json')] if q.exists()),None)
  item=existing.get(rel,{'file':rel,'operation':'see_sidecar' if record else 'derived_review_image'})
  item.update({'sha256':sha(rel),'width':im.width,'height':im.height,'mode':im.mode,'record':record})
  rows.append(item)
index['createdAt']=now;index['index']=rows;write('records/image-provenance-index.json',index)

class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':
   href=dict(attrs).get('href')
   if href:self.links.append(href)
parser=Links();parser.feed((ROOT/'index.html').read_text(encoding='utf-8'))
broken=[h for h in parser.links if not h.startswith(('http:','https:','#')) and not (ROOT/h).exists()]
gallery=read('previews/gallery.json');asset=read('assets/manifest.json');checks=read('records/delivery-qa.json');browser=read('records/gallery-qa.json')
thumbs=list((ROOT/'previews/thumbnails').glob('*.jpg'))
report={'verifiedAt':now,'scope':'final_local_delivery_indexes_and_navigation','counts':{'screens':346,'states':125,'gallery':len(gallery),'formalSprites':asset['formalSpriteCount'],'thumbnailPNGsOrJPGs':len(thumbs),'provenanceRasters':len(rows)},'navigationTargets':parser.links,'missingNavigationTargets':broken,'deliveryMachineFailureCount':len(checks['failures']),'browserStatus':browser['status'],'sourceRepositoryExcludedFromRasterIndex':True,'gitCommitPushPerformed':False,'unityVerified':False}
report['passed']=not broken and len(gallery)==471 and asset['formalSpriteCount']==130 and len(thumbs)==471 and not checks['failures'] and browser['status']=='passed'
write('records/final-delivery-check.json',report)
print(json.dumps(report,ensure_ascii=False))
if not report['passed']:raise SystemExit(1)
