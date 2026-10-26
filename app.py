import os, re, secrets
from collections import Counter
from urllib.parse import urlparse, parse_qs
import requests
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

app = FastAPI(docs_url=None, redoc_url=None)
security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    username = os.getenv("APP_USER", "admin")
    password = os.getenv("APP_PASSWORD", "")
    if not password or not (secrets.compare_digest(credentials.username, username) and secrets.compare_digest(credentials.password, password)):
        raise HTTPException(status_code=401, detail="Invalid login", headers={"WWW-Authenticate": "Basic"})

class RequestBody(BaseModel):
    url: str
    api_key: str | None = None

def extract_video_id(raw: str):
    raw = raw.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", raw):
        return raw
    u = urlparse(raw)
    host = (u.hostname or "").lower()
    if host in ("youtu.be", "www.youtu.be"):
        candidate = u.path.strip("/").split("/")[0]
    elif host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        if u.path == "/watch":
            candidate = parse_qs(u.query).get("v", [""])[0]
        elif u.path.startswith(("/shorts/", "/live/", "/embed/")):
            candidate = u.path.split("/")[2]
        else:
            candidate = ""
    else:
        candidate = ""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        raise HTTPException(400, "Enter a valid YouTube video URL")
    return candidate

def youtube(endpoint, key, **params):
    try:
        response = requests.get("https://www.googleapis.com/youtube/v3/" + endpoint,
                                params={"key": key, **params}, timeout=20)
    except requests.RequestException:
        raise HTTPException(502, "YouTube request failed")
    if not response.ok:
        try:
            error = response.json().get("error", {})
            reason = ((error.get("errors") or [{}])[0]).get("reason", "")
            message = error.get("message", "YouTube API error")
        except (ValueError, TypeError, AttributeError, IndexError):
            reason, message = "", "YouTube API error"
        raise HTTPException(response.status_code, {"message": message[:250], "reason": reason})
    return response.json()

@app.get("/")
def home(_: str = Depends(authenticate)):
    return FileResponse("index.html")

@app.post("/api/analyze")
def analyze(body: RequestBody, _: str = Depends(authenticate)):
    key = (body.api_key or os.getenv("YOUTUBE_API_KEY", "")).strip()
    if not key:
        raise HTTPException(400, "Please enter your YouTube API key")
    video = extract_video_id(body.url)
    commenters, seen, page_token = [], set(), None
    while len(commenters) < 100:
        args = dict(part="snippet", videoId=video, maxResults=100, order="time", textFormat="plainText")
        if page_token:
            args["pageToken"] = page_token
        page = youtube("commentThreads", key, **args)
        for thread in page.get("items", []):
            snippet = thread.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
            channel_id = snippet.get("authorChannelId", {}).get("value")
            if not channel_id or channel_id in seen:
                continue
            seen.add(channel_id)
            commenters.append({"name": snippet.get("authorDisplayName", "Unknown"),
                               "channel_id": channel_id,
                               "url": "https://www.youtube.com/channel/" + channel_id,
                               "status": "pending", "subscriptions": []})
            if len(commenters) == 100:
                break
        page_token = page.get("nextPageToken")
        if not page_token:
            break

    totals = {}
    for person in commenters:
        subscriptions, visited, token = [], set(), None
        try:
            while True:
                args = dict(part="snippet", channelId=person["channel_id"], maxResults=50)
                if token:
                    args["pageToken"] = token
                page = youtube("subscriptions", key, **args)
                for item in page.get("items", []):
                    snippet = item.get("snippet", {})
                    target = snippet.get("resourceId", {}).get("channelId")
                    if not target or target in visited:
                        continue
                    visited.add(target)
                    subscriptions.append({"title": snippet.get("title", "Untitled channel"),
                                          "channel_id": target, "url": "https://www.youtube.com/channel/" + target})
                token = page.get("nextPageToken")
                if not token:
                    break
        except HTTPException as exc:
            error = exc.detail if isinstance(exc.detail, dict) else {}
            reason = error.get("reason", "")
            if exc.status_code == 403 and reason in ("subscriptionForbidden", "forbidden"):
                person["status"] = "unavailable"
                continue
            if exc.status_code == 404:
                person["status"] = "unavailable"
                continue
            raise
        person["subscriptions"] = subscriptions
        person["status"] = "public" if subscriptions else "no_public_results"
        for channel in subscriptions:
            if channel["channel_id"] not in totals:
                totals[channel["channel_id"]] = dict(channel, commenters=0)
            totals[channel["channel_id"]]["commenters"] += 1
    channels = sorted(totals.values(), key=lambda item: (-item["commenters"], item["title"].lower()))
    return {"video_id": video, "commenters": commenters, "channels": channels,
            "count": len(commenters), "public_count": sum(c["status"] == "public" for c in commenters)}
