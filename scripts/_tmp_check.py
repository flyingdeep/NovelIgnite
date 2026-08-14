import json
import urllib.request

sid = '6e353c67-a8e4-497e-9a35-4f8eed3ca94c'  # 寒冬归途
r = json.load(urllib.request.urlopen(f'http://127.0.0.1:8000/api/v1/stories/{sid}/read', timeout=5))
print('=== READER PAYLOAD ===')
for ch in r['chapters']:
    scene_summary = []
    for s in ch['scenes']:
        scene_summary.append(f"{s['title']}(beats={len(s['beats'])})")
    print(f"ch{ch['ordinal']} [{ch['access_status']}] {ch['title']}: {scene_summary}")
