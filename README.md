# stock-media skill

A Claude Code skill that finds free stock photos and video for a web project, then saves them in web-ready formats. Photo and video searches run against Pexels and Pixabay together, so the agent compares two pools of candidates and picks the best one from either. Searches for illustrations, vectors or animations go to Pixabay alone, since Pexels has photos and live footage only.

Images are resized and saved as WebP. Videos are trimmed, re-encoded to H.264 MP4 with the audio stripped, and saved with a WebP poster frame, ready for a muted background loop.

The skill also tells the agent the limits of the free API tiers before it searches. Pixabay images top out at 1280px wide, Pixabay vectors download as PNG rather than SVG, and both services have rate limits. With that in front of it, the agent won't put a 1280px image in a full-width hero, and it says so when a limit shaped its pick.

To install it, copy the `stock-media` folder into your Claude Code skills directory:

```bash
git clone https://github.com/dtsoden/stock-media-skill.git
cp -r stock-media-skill/stock-media ~/.claude/skills/
```

On Windows, the skills directory is `%USERPROFILE%\.claude\skills`. To use the skill in one project only, put the folder in that project's `.claude/skills/` instead.

You need Python 3 with Pillow (`pip install Pillow`), plus ffmpeg on your PATH if you want video. You also need two free API keys, one from https://www.pexels.com/api/ and one from https://pixabay.com/api/docs/ (shown after you log in). Set them as environment variables:

```bash
export PEXELS_API_KEY=...
export PIXABAY_API_KEY=...
```

If you keep secrets in a vault or a secret manager, inject them at run time instead of exporting them. The skill shows how. It never prints the keys or writes them into your project.

Then ask Claude Code for what you need, for example "find a hero image for this landing page" or "get a 10-second background video of ocean waves". You can also call the skill directly with `/stock-media`.

Both services allow free commercial use without attribution, under the [Pexels license](https://www.pexels.com/license/) and the [Pixabay content license](https://pixabay.com/service/license-summary/). Check those terms yourself for anything unusual, such as using an image in a logo or trademark.

The skill itself is MIT licensed. See `LICENSE`.
