import argparse, json, hashlib, shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('job')
args=parser.parse_args()
job=json.loads(Path(args.job).read_text(encoding='utf-8-sig'))
target=ROOT/job['file']
target.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(job['source'],target)
im=Image.open(target)
record={
 'file':job['file'], 'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
 'generatedAt':job['startedAt'], 'registeredAt':datetime.now(ZoneInfo('America/New_York')).isoformat(),
 'timestampMeaning':'generatedAt为已记录的本次工具调用开始时间；宿主未披露精确渲染完成时间。',
 'width':im.width,'height':im.height,'format':im.format,'mode':im.mode,
 'tool':'image_gen.imagegen','route':'builtin',
 'configSnapshot':json.loads((ROOT/'records/image-config.snapshot.json').read_text(encoding='utf-8-sig')),
 'submittedParameters':{'model':None,'quality':None,'transparent_background':job['transparent_background'],'referenced_image_paths':job['references']},
 'actualModel':None,'actualQuality':None,
 'unverifiedReason':'宿主管理，工具没有型号/质量选择器；本次返回仅含image_url及output_hint，未披露可核实型号/质量。',
 'evidence':{'toolResult':job['receipt'],'returnedFields':['image_url','output_hint'],'nativeOutput':job['source'],'pngMetadataKeys':list(im.info.keys())},
 'prompt':job['prompt'],'references':[{'file':r,'purpose':'首要风格参考，实际附图'} for r in job['references']],
 'reviewStatus':'pending_visual_review', 'operation':'native_model_generation_no_resampling'
}
(Path(str(target)+'.generation.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'file':str(target),'size':im.size,'mode':im.mode,'alphaExtrema':im.getchannel('A').getextrema() if im.mode=='RGBA' else None},ensure_ascii=False))
