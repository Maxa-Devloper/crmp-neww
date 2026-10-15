#!/usr/bin/env python3
"""Fabric manifest -> NeoForge 1.21.1 manifest (CurseForge API orqali).
Ishlatish:  CF_API_KEY=xxxx python convert_manifest.py Tensura_Beyond_Worlds.zip
Natija: manifest.json (NeoForge) + report.txt (qo'lda tekshirish kerak bo'lganlar)."""
import json, os, re, sys, zipfile, urllib.request, urllib.parse

KEY = os.environ.get("CF_API_KEY") or sys.exit("CF_API_KEY kerak (console.curseforge.com)")
API = "https://api.curseforge.com/v1"
NEOFORGE = 6

def call(path, data=None):
    req = urllib.request.Request(API + path, headers={"x-api-key": KEY, "Accept": "application/json", "User-Agent": "Mozilla/5.0 (tensura-neoforge-convert)",
                                                       "Content-Type": "application/json"},
                                 data=json.dumps(data).encode() if data else None)
    return json.load(urllib.request.urlopen(req))

# slug -> ("SAME") | ("ALT", yangi_slug) | ("DROP", sabab) | ("CHECK",)
ALT = {
 "iceberg-fabric": "iceberg", "equipment-compare-fabric": "equipment-compare",
 "sophisticated-core-unofficial-fabric-port": "sophisticated-core",
 "sophisticated-storage-unofficial-fabric-port": "sophisticated-storage",
 "sophisticated-backpacks-unofficial-fabric-port": "sophisticated-backpacks",
 "yungs-api-fabric": "yungs-api", "terrablender-fabric": "terrablender",
 "lootr-fabric": "lootr", "ferritecore-fabric": "ferritecore",
 "fabric-language-kotlin": "kotlin-for-forge", "trinkets": "curios",
}
DROP = {
 "fabric-api": "Fabric-only", "forge-config-api-port": "NeoForge'da kerak emas",
 "toffys-hooks": "Fabric-only", "structure-pool-api": "Fabric-only (NeoForge'da kerak emas)",
 "geckoanimfix": "Fabric compat fix", "cinderscapes": "NeoForge versiyasi yo'q",
 "cardinal-components-api": "Fabric-only; bog'liq modlar o'zi olib keladi",
 "nameless-trinkets": "Fabric-only (Trinkets uchun)",
}
CHECK = {  # NeoForge 1.21.1 build bormi — avval shu projectda qidiriladi, topilmasa report'ga tushadi
 "continuity","krypton","connectiblechains","decocraft","decocraft-nature","better-archeology",
 "towns-and-towers","iceandfire-ce","uranus","jupiter","chatanimation","resourcepackcached",
 "ydms-weapon-master","fancy-toasts","templates-2","customnpcs-unofficial","cnpc-gecko-addon",
 "unofficial-cmdcam-fabric","cnpc-xaero-compat","beyond-adventures","tensura-better-subordinates",
 "tensura-barriers","tensuravisibleores","anime-icons-xaeros","tr-ancient-artifacts",
 "tensura-unique-monsters","tensura-slimethrone-extras","tensura-compat-ice-fire",
}
SHADER_OR_PACK = {"complementary-reimagined","complementary-unbound","bsl-shaders","sildurs-vibrant-shaders","anime-icons-xaeros"}

def newest(mod_id):
    r = call(f"/mods/{mod_id}/files?gameVersion=1.21.1&modLoaderType={NEOFORGE}&pageSize=50")["data"]
    r = [f for f in r if "1.21.1" in f["gameVersions"] and "NeoForge" in f["gameVersions"]]
    if not r: return None
    r.sort(key=lambda f: (f["releaseType"] == 1, f["fileDate"]), reverse=True)  # release > beta > alpha, keyin yangiligi
    return r[0]

def by_slug(slug):
    for q in (f"slug={urllib.parse.quote(slug)}", f"searchFilter={urllib.parse.quote(slug.replace('-', ' '))}"):
        try:
            r = call(f"/mods/search?gameId=432&classId=6&{q}")["data"]
        except Exception:
            continue
        m = next((m for m in r if m["slug"] == slug), None)
        if m: return m
    return None

src = zipfile.ZipFile(sys.argv[1]); man = json.loads(src.read("manifest.json"))
ids = [f["projectID"] for f in man["files"]]
mods = {m["id"]: m for m in call("/mods", {"modIds": ids})["data"]}
old_files = {f["projectID"]: f for f in man["files"]}

# NeoForge 1.21.1 oxirgi barqaror versiyasi
meta = urllib.request.urlopen("https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml").read().decode()
vers = [v for v in re.findall(r"<version>(21\.1\.\d+)</version>", meta)]
nf = max(vers, key=lambda v: int(v.split(".")[2]))

files, report = [], []
def add(pid, fid, req): files.append({"projectID": pid, "fileID": fid, "required": req, "isLocked": False})

def handle(pid):
    m = mods.get(pid); slug = m["slug"] if m else str(pid); req = old_files[pid].get("required", True)
    if slug in SHADER_OR_PACK:  # shader/resource pack loaderga bog'liq emas
        add(pid, old_files[pid]["fileID"], req); return
    if slug in DROP: report.append(f"DROP   {slug}: {DROP[slug]}"); return
    target = pid
    if slug in ALT:
        t = by_slug(ALT[slug])
        if not t: report.append(f"YOQ    {slug} -> {ALT[slug]} topilmadi (qo'lda qo'shing)"); return
        target = t["id"]
    f = newest(target)
    if f: add(target, f["id"], req)
    else:
        tag = "CHECK " if slug in CHECK else "YOQ   "
        report.append(f"{tag} {slug}: NeoForge 1.21.1 fayl topilmadi - almashtirish/olib tashlash kerak")

for pid in ids:
    try:
        handle(pid)
    except Exception as e:
        report.append(f"XATO   {mods[pid]['slug'] if pid in mods else pid}: {e}")

out = {"minecraft": {"version": "1.21.1", "modLoaders": [{"id": f"neoforge-{nf}", "primary": True}]},
       "manifestType": "minecraftModpack", "manifestVersion": 1, "name": man.get("name", "Tensura Beyond Worlds") + " (NeoForge)",
       "version": "1.0", "author": man.get("author", ""), "files": files, "overrides": "overrides"}
json.dump(out, open("manifest.json", "w"), indent=2)
open("report.txt", "w").write("\n".join(report) + "\n")
print(f"NeoForge {nf}: {len(files)}/{len(ids)} mod; report.txt: {len(report)} ta muammo")
