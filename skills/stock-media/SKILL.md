---
name: stock-media
description: Search Pexels and Pixabay together for stock photos and stock video, and Pixabay for illustrations, vector art and animations, pick the best match, then download and optimize it for where it will be used (WebP for web pages, JPEG or PNG for PowerPoint, Keynote, Google Slides and Word documents, compressed MP4 plus poster for video). Use for hero images, background videos, card thumbnails, illustrations, slide photos, report covers, or any stock media a page, deck or document needs.
---

# Stock media sourcing (Pexels + Pixabay)

Find stock images and video for web pages, decks and documents, and save them
in the format and size that suits where they will be used. Photo searches
run against both Pexels and Pixabay, so you compare two pools of candidates and
pick the best one from either. Illustration and vector searches go to Pixabay
alone. Video searches query both and save a compressed MP4 with a WebP
poster frame. Pairs well with a frontend design skill.

## Limits to know before searching

These apply to the free API keys that Pexels and Pixabay hand out on signup.
Tested 2026-10-15.

- Pixabay images download at 1280px wide at most (`largeImageURL`). Full
  resolution needs Pixabay's approved full API access, which free keys lack.
  For anything that has to render wider than 1280px (a full-bleed hero, a
  1920px banner), use Pexels results only.
- Pixabay vectors download as a 1280px raster PNG, usually with a transparent
  background. The SVG source is not available with a free key. If the user
  needs a true scalable SVG, give them the result's `page_url` so they can
  download it from Pixabay by hand, and say why.
- Pexels has photos and live-footage video only. Illustration, vector and
  animation searches go to Pixabay alone.
- Pexels video goes up to 4K. Pixabay video usually tops out at 1920x1080 and
  only sometimes has 4K. Pixabay video search has no orientation filter, so the
  skill filters on width and height after the search.
- Video needs ffmpeg on the PATH for compression and the poster frame.
- Pixabay returns at most 500 results per query and allows 100 requests per
  60 seconds. Pexels allows 200 requests per hour and 20,000 per month.
- Pixabay `largeImageURL` links expire after about 24 hours and must not be
  hotlinked. Always download the file into the project.
- The Pixabay key goes in the URL query string. Never print or log a Pixabay
  search URL.

Tell the user when one of these limits shaped the pick, for example "this
Pixabay image is 1280px, so it'll look soft as a full-width hero."

## Print UTF-8 or the script dies on a photographer's name

Every Python script here prints photographer and uploader names, and Python on
Windows writes stdout as cp1252. Names are worldwide: the first `ş`, `ü`, `ż` or
`ñ` raises `UnicodeEncodeError: 'charmap' codec can't encode character` part way
through the output, so the search half-succeeds and then crashes.

Set the encoding as the first thing any script does, before the imports that
print:

```python
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
```

Running the script from Bash instead? Put `PYTHONIOENCODING=utf-8` in front of
the command. Either works; doing neither fails the moment a name is not English.

## API keys

Setup (`SETUP.md` in https://github.com/dtsoden/stock-media-skill) stores the
two keys and records where in `~/.config/stock-media/config.json`. If that
file is missing and `scripts/check_keys.py` fails, the skill has not been set
up: point the user to that setup and stop.

Never print a key, never write one into the project, never read a key file,
and never ask the user to paste a key into the chat. Load keys with the helper
in this skill's `scripts/` folder, which checks environment variables first and
then the OS credential store. Write each search script to a scratch or temp
directory (not the project) and start it like this, with `SKILL_DIR` set to
the absolute path of the folder that holds this SKILL.md:

```python
import os, sys
SKILL_DIR = '/absolute/path/to/stock-media'  # the folder holding this SKILL.md
sys.path.insert(0, os.path.join(SKILL_DIR, 'scripts'))
from stock_media_keys import get_key
PEXELS_KEY = get_key('pexels')
PIXABAY_KEY = get_key('pixabay')
```

How to run the script depends on the `store` value in the config file:

- `keyring` or `env`: run it normally, `python search.py`.
- `aihsm`: inject the keys with the vault names from `aihsm_names`:
  `aihsm run --set PEXELS_API_KEY=<pexels name> --set PIXABAY_API_KEY=<pixabay name> -- python search.py`.
  Run python directly as the injected command. Wrapping it in `bash -c '...'`
  loses the variables.

`python scripts/check_keys.py` (through aihsm if that is the store) confirms
both keys work without printing them. If your sandbox blocks network access
or the OS credential store, ask the user to allow it for these scripts.

The Pixabay key travels in the query string, so never print or log a Pixabay
search URL. Image and video URLs from either service are safe to print.

## CRITICAL: send a browser User-Agent

The Pexels API and CDN sit behind Cloudflare, which blocks the default
`Python-urllib` and bot user agents with **HTTP 403, `error code: 1010`**. Send a
real browser User-Agent on every request to both services, for searches and
image downloads alike:

```python
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
```

## Arguments
The request describes what images are needed and how they'll be used. This can be:
- A natural language description of images needed (e.g. "hero background for a fintech app", "team photos for about page", "product showcase images")
- A specific search query
- A design context where you determine what images would enhance the UI/UX

## Workflow

### 1. Understand the design context
- Read the target component/page files to understand the visual design language, color palette, layout, and purpose
- Determine what role the image(s) will play: hero, background, illustration, card thumbnail, avatar, texture, etc.
- Work out the dimensions needed (full-bleed, card, icon, etc.). This decides whether Pixabay can be used at all, see the size limit below.

### 2. Search both services
One function queries both and returns results in a common shape, so candidates
from each can be compared side by side:

```python
import sys, os, json, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
SKILL_DIR = '/absolute/path/to/stock-media'  # the folder holding this SKILL.md
sys.path.insert(0, os.path.join(SKILL_DIR, 'scripts'))
from stock_media_keys import get_key
PEXELS_KEY = get_key('pexels')
PIXABAY_KEY = get_key('pixabay')

def _get(url, headers=None):
    req = urllib.request.Request(url, headers={'User-Agent': UA, **(headers or {})})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def search_pexels(query, orientation='landscape', per_page=15, color=None):
    """orientation: landscape | portrait | square
    color: red | orange | yellow | green | turquoise | blue | violet | pink |
           brown | black | gray | white, or a hex code like 'ffffff'"""
    params = {'query': query, 'per_page': per_page, 'orientation': orientation}
    if color:
        params['color'] = color
    data = _get('https://api.pexels.com/v1/search?' + urllib.parse.urlencode(params),
                {'Authorization': PEXELS_KEY})
    return [{
        'source': 'pexels',
        'type': 'photo',
        'id': p['id'],
        'width': p['width'], 'height': p['height'],
        'max_download_width': p['width'],
        'description': p.get('alt') or '',
        'author': p['photographer'],
        'page_url': p['url'],
        'preview_url': p['src']['medium'],
        'download_url': p['src']['original'],
        'avg_color': p.get('avg_color'),
        'popularity': None,
    } for p in data['photos']]

PIXABAY_ORIENTATION = {'landscape': 'horizontal', 'portrait': 'vertical', 'square': 'all'}

def search_pixabay(query, orientation='landscape', per_page=15, color=None, min_width=0,
                   image_type='photo'):
    """image_type: photo | illustration | vector | all
    color: grayscale | transparent | red | orange | yellow | green |
           turquoise | blue | lilac | pink | white | gray | black | brown
    Query is limited to 100 characters."""
    params = {'key': PIXABAY_KEY, 'q': query[:100], 'image_type': image_type,
              'orientation': PIXABAY_ORIENTATION[orientation],
              'per_page': max(3, per_page), 'safesearch': 'true'}
    if color:
        params['colors'] = color
    if min_width:
        params['min_width'] = min_width
    data = _get('https://pixabay.com/api/?' + urllib.parse.urlencode(params))
    hits = [h for h in data['hits']
            if not h.get('isAiGenerated') and not h.get('isLowQuality')]
    return [{
        'source': 'pixabay',
        'type': h['type'],
        'id': h['id'],
        'width': h['imageWidth'], 'height': h['imageHeight'],
        'max_download_width': min(1280, h['imageWidth']),
        'description': h['tags'],
        'author': h['user'],
        'page_url': h['pageURL'],
        'preview_url': h['webformatURL'],
        'download_url': h['largeImageURL'],
        'avg_color': None,
        'popularity': {'likes': h['likes'], 'downloads': h['downloads']},
    } for h in hits]

def search_all(query, orientation='landscape', per_page=15, color=None, image_type='photo'):
    """image_type 'photo' searches both services. 'illustration' or 'vector'
    searches Pixabay only, because Pexels has photos and nothing else."""
    results = []
    calls = [lambda: search_pixabay(query, orientation, per_page, color, image_type=image_type)]
    if image_type in ('photo', 'all'):
        calls.insert(0, lambda: search_pexels(query, orientation, per_page, color))
    for call in calls:
        try:
            results += call()
        except Exception as e:
            # One service failing should not sink the search.
            print(f'search failed: {type(e).__name__} {getattr(e, "code", "")}')
    return results
```

### Illustrations and vectors
Pixabay also has illustrations and vector art, so `search_all(...,
image_type='illustration')` covers spot illustrations, empty-state art, and
icons-with-character that a photo would not suit. An illustration search also
returns vector items (`type` comes back as `vector/svg`).

This key does not get the SVG source. Vectors download as a 1280px PNG,
often with a transparent background. `download_and_optimize` keeps the
transparency in the WebP. If the user needs a true scalable SVG, say so and
link the `page_url` so they can download it from Pixabay by hand.

The `color` values differ between the services. Pass one both accept (red,
orange, yellow, green, turquoise, blue, pink, white, gray, black, brown) or
call each function separately.

Run several searches with varied queries. Evaluate candidates from both
services together:
- **Size**: `max_download_width` must cover the use case. Pixabay tops out at
  1280px, so for a 1920px hero, only Pexels results qualify.
- **Color**: Pexels gives `avg_color`. For Pixabay, look at the preview.
- **Subject**: Pexels `description` is alt text, Pixabay's is a tag list.
- **Popularity**: Pixabay likes and downloads are a rough quality signal. A
  heavily downloaded image is also more likely to show up on other sites.
- **Look at them**: download the `preview_url` of the shortlisted candidates
  to the scratchpad and view them before choosing. Text metadata alone picks
  poorly.

`search_pixabay` already drops results flagged `isAiGenerated` or
`isLowQuality`.

### 3. Download & optimize
Download the selected image and save it in the format that suits where it is
going: WebP for web pages, JPEG or PNG for decks and documents (see
"Decks and documents" below). The same function handles either source:

```python
from PIL import Image
from io import BytesIO

def download_and_optimize(photo, output_name, output_dir, max_width=1920, quality=75, fmt='webp'):
    """
    photo: one result dict from search_all / search_pexels / search_pixabay
    output_name: filename without extension
    output_dir: where to save (e.g. public/images/)
    max_width: resize to this max width (keeps aspect ratio)
    quality: WebP or JPEG quality 1-100 (ignored for PNG). Guidelines:
        - Hero/showcase images: 75-85
        - Card thumbnails: 65-75
        - Background/texture images: 40-55
        - Decorative/barely-visible: 30-45
    fmt: 'webp' for web pages, 'jpeg' for photos in decks and documents,
         'png' for illustrations that need transparency in a deck or document
    """
    os.makedirs(output_dir, exist_ok=True)

    url = photo['download_url']
    if photo['source'] == 'pexels':
        url += f'?auto=compress&cs=tinysrgb&w={max_width}'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req) as resp:
        img_data = resp.read()

    img = Image.open(BytesIO(img_data))
    if img.width < max_width:
        print(f'  note: source is only {img.width}px wide, asked for {max_width}px')
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)

    ext = {'webp': 'webp', 'jpeg': 'jpg', 'png': 'png'}[fmt]
    out_path = os.path.join(output_dir, f'{output_name}.{ext}')
    if fmt == 'webp':
        img.save(out_path, 'WEBP', quality=quality, method=6)
    elif fmt == 'jpeg':
        if img.mode in ('RGBA', 'LA', 'P'):
            # JPEG has no transparency: flatten onto white
            img = img.convert('RGBA')
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.getchannel('A'))
            img = bg
        img.convert('RGB').save(out_path, 'JPEG', quality=quality, optimize=True, progressive=True)
    else:
        img.save(out_path, 'PNG', optimize=True)

    orig_size = len(img_data)
    new_size = os.path.getsize(out_path)
    print(f'{output_name}.{ext}: {img.width}x{img.height}, {new_size:,} bytes ({(1-new_size/orig_size)*100:.0f}% smaller)')
    print(f'  Source: {photo["source"]} {photo["page_url"]}')
    print(f'  By: {photo["author"]}')
    return out_path
```

Pixabay's `largeImageURL` links expire after about 24 hours and must not be
hotlinked, so always download and serve the file from the project.

### 4. Integrate
- Save images to the project's images directory (detect from project structure, typically `public/images/`, `static/`, `assets/`, `src/assets/`, etc.)
- Reference images in the code using the correct path for the framework
- Make sure `Pillow` is installed (`pip install Pillow`) before processing
- Tell the user which service and page each chosen image came from

## Video

Both services have stock video, and video searches always query both. Use it
for hero background loops and short product or mood clips.
Every file from either service is MP4. Pixabay splits its videos into `film`
(live footage) and `animation` (motion graphics, abstract loops).

Sizes seen when tested on 2026-10-15: Pexels offers several files per video
from 640px up to 4K (`uhd`). Pixabay offers `large` (usually 1920x1080,
sometimes 3840x2160), `medium` (1280x720), `small` (960x540) and `tiny`
(640x360). Pixabay sometimes leaves a size's URL empty, and the code below
skips those.

Stock clips are big: one 40-second Pixabay clip was 38 MB at 1920px.
Never drop a raw download into a page. Re-encode it with ffmpeg and trim it.
If ffmpeg is missing, tell the user to install it (`winget install ffmpeg`,
`brew install ffmpeg`, or `apt install ffmpeg`).

### Search

Uses `_get`, `UA` and the keys from the image search block above.

```python
def search_pexels_videos(query, orientation='landscape', per_page=15):
    params = {'query': query, 'per_page': per_page, 'orientation': orientation}
    data = _get('https://api.pexels.com/videos/search?' + urllib.parse.urlencode(params),
                {'Authorization': PEXELS_KEY})
    out = []
    for v in data['videos']:
        files = [{'width': f['width'], 'height': f['height'], 'url': f['link']}
                 for f in v['video_files']
                 if f.get('file_type') == 'video/mp4' and f.get('width')]
        out.append({
            'source': 'pexels', 'type': 'film', 'id': v['id'],
            'width': v['width'], 'height': v['height'], 'duration': v['duration'],
            'description': ', '.join(v.get('tags') or []),
            'author': v['user']['name'], 'page_url': v['url'],
            'thumbnail_url': v['image'], 'files': files, 'popularity': None,
        })
    return out

def search_pixabay_videos(query, video_type='all', per_page=15):
    """video_type: all | film | animation. Pixabay has no orientation filter
    for video, so check width and height on the results."""
    params = {'key': PIXABAY_KEY, 'q': query[:100], 'video_type': video_type,
              'per_page': max(3, per_page), 'safesearch': 'true'}
    data = _get('https://pixabay.com/api/videos/?' + urllib.parse.urlencode(params))
    out = []
    for h in data['hits']:
        if h.get('isAiGenerated') or h.get('isLowQuality'):
            continue
        files = [{'width': f['width'], 'height': f['height'], 'url': f['url']}
                 for f in h['videos'].values() if f.get('url')]
        if not files:
            continue
        biggest = max(files, key=lambda f: f['width'])
        thumb = next((f['thumbnail'] for f in h['videos'].values() if f.get('thumbnail')), None)
        out.append({
            'source': 'pixabay', 'type': h['type'], 'id': h['id'],
            'width': biggest['width'], 'height': biggest['height'],
            'duration': h['duration'], 'description': h['tags'],
            'author': h['user'], 'page_url': h['pageURL'],
            'thumbnail_url': thumb,
            'files': files,
            'popularity': {'likes': h['likes'], 'downloads': h['downloads']},
        })
    return out

def search_videos_all(query, orientation='landscape', per_page=15, video_type='all'):
    """video_type 'animation' searches Pixabay only. Pexels has live footage only."""
    results = []
    calls = [lambda: search_pixabay_videos(query, video_type, per_page)]
    if video_type in ('all', 'film'):
        calls.insert(0, lambda: search_pexels_videos(query, orientation, per_page))
    for call in calls:
        try:
            results += call()
        except Exception as e:
            print(f'video search failed: {type(e).__name__} {getattr(e, "code", "")}')
    if orientation == 'landscape':
        results = [r for r in results if r['width'] > r['height']]
    elif orientation == 'portrait':
        results = [r for r in results if r['height'] > r['width']]
    return results
```

Judge candidates on `duration` (shorter loops are smaller and loop better),
the largest file width, and the `thumbnail_url`. Download the thumbnails of
shortlisted clips to the scratchpad and look at them before choosing.

### Download & optimize

```python
import subprocess, tempfile

def pick_video_file(video, target_width):
    """Smallest file at least target_width wide, else the largest there is."""
    files = sorted(video['files'], key=lambda f: f['width'])
    for f in files:
        if f['width'] >= target_width:
            return f
    return files[-1]

def download_and_optimize_video(video, output_name, output_dir, max_width=1920,
                                 crf=26, max_seconds=None, keep_audio=False):
    """
    Writes <name>.mp4 (H.264, faststart, web-safe) and <name>-poster.webp.
    crf: 18 = near lossless, 23 = high quality, 26-28 = background loops,
         30+ = heavy compression behind overlays
    max_seconds: trim to this length. 8-15s is plenty for a background loop.
    keep_audio: background videos should be silent; leave this False.
    """
    os.makedirs(output_dir, exist_ok=True)
    f = pick_video_file(video, max_width)
    if f['width'] < max_width:
        print(f'  note: largest file is {f["width"]}px wide, asked for {max_width}px')

    tmp = os.path.join(tempfile.mkdtemp(), 'src.mp4')
    req = urllib.request.Request(f['url'], headers={'User-Agent': UA})
    with urllib.request.urlopen(req) as resp, open(tmp, 'wb') as out:
        out.write(resp.read())

    mp4 = os.path.join(output_dir, f'{output_name}.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp]
    if max_seconds:
        cmd += ['-t', str(max_seconds)]
    cmd += ['-vf', f"scale='min({max_width},iw)':-2", '-c:v', 'libx264',
            '-preset', 'slow', '-crf', str(crf), '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart']
    cmd += ['-c:a', 'aac', '-b:a', '128k'] if keep_audio else ['-an']
    subprocess.run(cmd + [mp4], check=True)

    poster = os.path.join(output_dir, f'{output_name}-poster.webp')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp4,
                    '-frames:v', '1', '-q:v', '75', poster], check=True)

    print(f'{output_name}.mp4: {os.path.getsize(tmp):,} -> {os.path.getsize(mp4):,} bytes')
    print(f'  Source: {video["source"]} {video["page_url"]}')
    print(f'  By: {video["author"]}')
    os.remove(tmp)
    return mp4, poster
```

For a background video, use the poster and keep it muted, or browsers will
refuse to autoplay it:

```html
<video autoplay muted loop playsinline preload="metadata" poster="/images/hero-poster.webp">
  <source src="/videos/hero.mp4" type="video/mp4">
</video>
```

Respect `prefers-reduced-motion` by pausing or hiding the video for users who
set it.

## Optimization guidelines by use case

| Use case | Max width | WebP quality | Notes |
|----------|-----------|-------------|-------|
| Hero / full-bleed | 1920px | 75-85 | Largest, highest quality. Pexels only. |
| Section background | 1920px | 40-55 | Behind overlays, can be aggressive. Pixabay at 1280 can work under a heavy overlay. |
| Card / thumbnail | 800px | 65-75 | Moderate quality, small file |
| Avatar / icon | 400px | 70-80 | Small dimensions, keep sharp |
| Texture / pattern | 1200px | 50-65 | Repeating patterns stay crisp |
| Product / showcase | 1200px | 80-90 | Quality matters, user inspects closely |
| Decorative / accent | 600px | 50-60 | Small flourishes, low priority |

## Decks and documents

Slides and documents need different settings from web pages. Work out where
the file is going from the request and the project (a `.pptx`, `.key` or
`.docx` file, a deck build script, a report template) and pick settings from
the table below. These are starting points, not rules. Adjust them to the
real size the image fills on the slide or page, and say what you chose.

Use JPEG for photos and PNG for illustrations that need a transparent
background. WebP is safe on the web but not everywhere else: older versions of
PowerPoint and Word can't insert it, and Keynote and Google Slides handling
varies, so don't hand a deck or document a WebP file.

Size each image for the space it fills, not for the biggest screen. A deck
with twenty full-size photos gets heavy fast, so the aim is a sharp image on a
projector or a 4K screen without carrying pixels nobody sees.

| Use case | Max width | Format and quality | Notes |
|----------|-----------|--------------------|-------|
| Full-bleed slide photo | 1920px | JPEG 80-85 | Covers a 16:9 slide on a 1080p projector. Use 2560px only if the deck is shown on 4K screens. Pexels only. |
| Half-slide photo | 1280px | JPEG 80 | Image beside text. Pixabay is fine here. |
| Slide thumbnail or icon-sized photo | 640px | JPEG 75-80 | Grids of small photos, team slides |
| Section-divider background | 1920px | JPEG 65-75 | Behind a dark overlay or large title, so compression won't show |
| Illustration on a slide | 1280px | PNG | Keeps transparency. Pixabay vectors come as PNG anyway. |
| Document cover or full-page image | 2000-2550px | JPEG 85 | About 300 ppi on a US Letter or A4 page if it will be printed. 1700px is enough if it is only read on screen. Pexels only. |
| Image inside document text | 1400-1900px | JPEG 80-85 | Fits a 6.5 inch column at 200-300 ppi |
| Diagram-style illustration in a document | 1600px | PNG | Sharp edges and flat color survive better as PNG |

For a deck, keep every photo on the same aspect ratio as its frame and crop
before you save. A photo cropped inside PowerPoint can keep its hidden pixels
in the file. Run
one search per deck where you can and pick images with the same light and
palette, so the slides look like a set.

Video in a deck: PowerPoint and Keynote both play the MP4 that
`download_and_optimize_video` writes. Keep clips short (10-20 seconds) and use
`max_width=1280` and `crf=28` unless the clip fills the whole slide, since an
embedded video is usually the biggest thing in the file. Keep the sound only if
the presenter will play it. The WebP poster is for web pages, so skip it for
decks.

## API reference

**Pexels**
- Search: `GET https://api.pexels.com/v1/search?query=...`, key in the `Authorization` header
- Curated: `GET https://api.pexels.com/v1/curated?per_page=15`
- Photo by ID: `GET https://api.pexels.com/v1/photos/{id}`
- `photo.src` sizes: `original` (full resolution), `large2x` (1880px wide), `large` (940px wide), `medium` (350px tall), `small` (130px tall), `portrait` (800x1200 crop), `landscape` (1200x627 crop)
- Filters: `orientation`, `size`, `color`, `locale`, `page`, `per_page` (max 80)
- Video search: `GET https://api.pexels.com/videos/search?query=...` (filters `orientation`, `size`, `locale`, `page`, `per_page`). Each video has `video_files` with `quality` (sd | hd | uhd), `width`, `height`, `fps` and `link`, plus `image` for a thumbnail.
- Rate limit: 200 requests/hour, 20,000/month, shared between photo and video

**Pixabay**
- Search: `GET https://pixabay.com/api/?key=...&q=...`, key in the query string
- Photo by ID: `GET https://pixabay.com/api/?key=...&id={id}`
- Image URLs: `previewURL` (150px), `webformatURL` (640px), `largeImageURL` (1280px). Full resolution needs approved full API access, which free keys do not have.
- Filters: `image_type`, `orientation` (all | horizontal | vertical), `category`, `colors`, `min_width`, `min_height`, `editors_choice`, `safesearch`, `order` (popular | latest), `page`, `per_page` (3-200)
- Video search: `GET https://pixabay.com/api/videos/?key=...&q=...` (filters `video_type` (all | film | animation), `category`, `min_width`, `min_height`, `editors_choice`, `safesearch`, `order`, `page`, `per_page`). Each hit has `videos` with `large`, `medium`, `small` and `tiny`, each holding `url`, `width`, `height`, `size` and `thumbnail`.
- At most 500 results per query (`totalHits`)
- Rate limit: 100 requests per 60 seconds. Responses carry `X-RateLimit-Remaining`.

## Notes
- Both licenses allow free commercial use with no attribution required. Credit is appreciated.
- Pixabay's API terms ask that search results be cached for 24 hours rather than re-requested.
- When sourcing several images for one page, keep them visually consistent (similar tone, lighting, style). Mixing services is fine if the images match.
- Prefer `loading="lazy"` for any image not in the initial viewport
