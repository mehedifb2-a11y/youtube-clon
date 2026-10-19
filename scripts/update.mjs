import fs from "fs";

const KEY = process.env.YT_API_KEY;
if (!KEY) throw new Error("YT_API_KEY সেট করা নেই");

const DAY = 864e5;
const KEEP_DAYS = 60;          // ৬০ দিন পর অটো ডিলিট
const MAX_PER_CAT = 4000;      // প্রতি ক্যাটাগরিতে সর্বোচ্চ ভিডিও
const SEARCHES_PER_RUN = 1;    // প্রতি রানে কয়টা সার্চ (১টা = ১০০ কোটা)
const DIR = "site/data";
fs.mkdirSync(DIR, { recursive: true });

// ক্যাটাগরি সেটিংস। channels এ অফিসিয়াল চ্যানেল আইডি (UC...) দিতে পারেন।
// চ্যানেল পোলিং খুব সস্তা (১ কোটা), তাই প্রতি ৩০ মিনিটে সব চ্যানেলের নতুন ভিডিও আসবে।
const CATEGORIES = {
  hindi:   { name: "হিন্দি সিনেমা", minSec: 2400, long: true,
             queries: ["hindi full movie", "bollywood full movie hd"], channels: [] },
  english: { name: "ইংলিশ সিনেমা", minSec: 2400, long: true,
             queries: ["english full movie", "hollywood full movie hd"], channels: [] },
  tamil:   { name: "তামিল সিনেমা", minSec: 2400, long: true,
             queries: ["tamil full movie", "tamil movie hd"], channels: [] },
  bnmovie: { name: "বাংলা সিনেমা", minSec: 2400, long: true,
             queries: ["bangla full movie", "bengali movie hd"], channels: [] },
  natok:   { name: "বাংলা নাটক",   minSec: 600, long: false,
             queries: ["bangla natok", "bangla new natok 2026"], channels: [] },
  song:    { name: "ভিডিও গান",    minSec: 90, long: false,
             queries: ["official video song", "new bangla song"], channels: [] }
};

async function yt(path, params) {
  const u = new URL("https://www.googleapis.com/youtube/v3/" + path);
  for (const [k, v] of Object.entries({ ...params, key: KEY })) u.searchParams.set(k, v);
  const r = await fetch(u);
  const j = await r.json();
  if (j.error) throw new Error(j.error.message);
  return j;
}

const decode = s => s
  .replace(/&amp;/g, "&").replace(/&#39;/g, "'").replace(/&quot;/g, '"')
  .replace(/&lt;/g, "<").replace(/&gt;/g, ">");

const toSec = iso => {
  const m = /PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/.exec(iso || "") || [];
  return (+m[1] || 0) * 3600 + (+m[2] || 0) * 60 + (+m[3] || 0);
};

// ডিউরেশন ও embed করা যায় কিনা চেক (৫০টা ভিডিও = ১ কোটা)
async function details(ids) {
  const out = {};
  for (let i = 0; i < ids.length; i += 50) {
    const j = await yt("videos", {
      part: "contentDetails,status",
      id: ids.slice(i, i + 50).join(","),
      maxResults: 50
    });
    for (const v of j.items) {
      if (v.status?.embeddable) out[v.id] = toSec(v.contentDetails.duration);
    }
  }
  return out;
}

const now = Date.now();
const store = {}, found = {};
for (const k in CATEGORIES) {
  try { store[k] = JSON.parse(fs.readFileSync(`${DIR}/${k}.json`, "utf8")); }
  catch { store[k] = []; }
  found[k] = [];
}

// ১) চ্যানেল থেকে নতুন ভিডিও (সস্তা, প্রতি রানে সব চ্যানেল)
for (const [k, c] of Object.entries(CATEGORIES)) {
  for (const ch of c.channels) {
    try {
      const j = await yt("playlistItems", {
        part: "snippet", playlistId: "UU" + ch.slice(2), maxResults: 50
      });
      for (const it of j.items) {
        const s = it.snippet;
        if (!s.resourceId?.videoId) continue;
        found[k].push({ id: s.resourceId.videoId, t: decode(s.title), c: s.channelTitle, p: s.publishedAt });
      }
    } catch (e) { console.log("চ্যানেল সমস্যা:", ch, e.message); }
  }
}

// ২) সার্চ কোয়েরি ঘুরিয়ে ঘুরিয়ে (কোটা বাঁচাতে প্রতি রানে অল্প কয়েকটা)
const jobs = [];
for (const [k, c] of Object.entries(CATEGORIES)) for (const q of c.queries) jobs.push({ k, q });
const slot = Math.floor(now / 1800000);
for (let n = 0; n < SEARCHES_PER_RUN; n++) {
  const { k, q } = jobs[(slot * SEARCHES_PER_RUN + n) % jobs.length];
  const c = CATEGORIES[k];
  const bootstrap = store[k].length < 300;     // শুরুতে বেশি পেজ আনবে
  let pageToken = "";
  for (let page = 0; page < (bootstrap ? 3 : 1); page++) {
    try {
      const p = {
        part: "snippet", type: "video", q, maxResults: 50,
        order: bootstrap ? "relevance" : "date",
        videoEmbeddable: "true", safeSearch: "moderate"
      };
      if (c.long) p.videoDuration = "long";
      if (pageToken) p.pageToken = pageToken;
      const j = await yt("search", p);
      for (const it of j.items) {
        found[k].push({ id: it.id.videoId, t: decode(it.snippet.title), c: it.snippet.channelTitle, p: it.snippet.publishedAt });
      }
      pageToken = j.nextPageToken;
      if (!pageToken) break;
    } catch (e) { console.log("সার্চ সমস্যা:", q, e.message); break; }
  }
}

// ৩) মার্জ, ৬০ দিনের পুরনো ডিলিট, সেভ
const meta = { updated: now, cats: [] };
for (const [k, c] of Object.entries(CATEGORIES)) {
  const map = new Map(store[k].map(v => [v.id, v]));
  const ids = [...new Set(found[k].map(v => v.id))];
  const det = ids.length ? await details(ids) : {};
  for (const v of found[k]) {
    if (det[v.id] == null || det[v.id] < c.minSec) continue;
    map.set(v.id, { id: v.id, t: v.t, c: v.c, p: v.p, d: det[v.id], f: now }); // f = সর্বশেষ দেখা
  }
  let arr = [...map.values()].filter(v => now - v.f < KEEP_DAYS * DAY);
  arr.sort((a, b) => b.p.localeCompare(a.p));
  arr = arr.slice(0, MAX_PER_CAT);
  fs.writeFileSync(`${DIR}/${k}.json`, JSON.stringify(arr));
  meta.cats.push({ key: k, name: c.name, count: arr.length });
  console.log(k, arr.length, "টা ভিডিও");
}
fs.writeFileSync(`${DIR}/meta.json`, JSON.stringify(meta));
