"""Print createScheduledPost args (date + info JSON) for posts FIRST..LAST, media pinned to SHA."""
import json, sys
from pathlib import Path
REPO = str(Path(__file__).resolve().parent.parent)
a, b, sha = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
base = f"https://raw.githubusercontent.com/yourpracticehacks-oss/Practice-hacks-posts/{sha}/reels"
for n in range(a, b + 1):
    t = json.load(open(f"{REPO}/tips/post-{n}.json"))
    info = {"autoPublish": True, "draft": False, "descendants": [], "firstCommentText": "", "hasNotReadNotes": False,
            "media": [f"{base}/post-{n}.mp4"], "videoThumbnailUrl": f"{base}/post-{n}-cover.png",
            "mediaAltText": [f'{t["hook"]} {t["statement"]}'],
            "providers": [{"network": "facebook"}, {"network": "instagram"}],
            "publicationDate": {"dateTime": t["publish"][:19], "timezone": "America/New_York"},
            "shortener": False, "smartLinkData": {"ids": []}, "text": t["caption"],
            "facebookData": {"type": "REEL"}, "instagramData": {"type": "REEL", "showReelOnFeed": True}}
    print(f"### {n} date={t['publish']}")
    print(json.dumps(info, ensure_ascii=False))
