# Piece of Velvet — Grand Opening Advert (Production Script)

**Format:** 9:16 vertical short, ~10 seconds
**Reference:** https://m.youtube.com/shorts/4s0j4XDaSxU (Starbucks holiday cup jump-cut montage)
**Concept:** Recreate the reference beat-for-beat, swapping coffee cups for red velvet cake
variations. Static camera, one centered product, jump cut on every music beat, rapid-fire
finale montage, grand-opening branding.

---

## Reference video breakdown (from Higgsfield video analysis)

- **Camera:** perfectly static medium close-up for the entire video. Never moves.
- **Set:** product centered on a flat light-gray surface; background is a blurred night
  scene with large warm golden-orange bokeh light circles; soft even front lighting.
- **Editing rhythm:** a hard jump cut roughly every 1 second (0:00–0:07) swaps in a new
  product variation. Environment stays pixel-identical between cuts — only the product changes.
- **Finale (0:07–0:10):** extremely rapid jump cuts "blink" through all previous products,
  landing on the hero product on the final music beat with a bright chime.
- **Audio:** upbeat, fast-paced orchestral track with strong percussion; cuts land on beats;
  ends on a sharp bright chime. (Original used holiday music — we swap in celebratory
  grand-opening music.)

## Piece of Velvet shot list (product per second)

| Beat | Time | Product variation |
|------|------|-------------------|
| 1 | 0:00–0:01 | Hero: classic red velvet cake slice, 3 crimson layers, cream cheese frosting swirl on top, red velvet crumbs, on a white gold-rimmed plate with small "Piece of Velvet" script logo |
| 2 | 0:01–0:02 | Red velvet cupcake in a dark-red wrapper, tall cream cheese frosting swirl, tiny heart sprinkle |
| 3 | 0:02–0:03 | Whole mini red velvet cake, fully frosted white with red crumb coating around the base |
| 4 | 0:03–0:04 | Red velvet cake jar (clear glass) — visible alternating red sponge / white cream layers, spoon in jar |
| 5 | 0:04–0:05 | Red velvet milkshake in a tall glass, whipped cream, red velvet crumble rim, striped straw |
| 6 | 0:05–0:06 | Stack of red velvet whoopie pies / sandwich cookies with cream filling |
| 7 | 0:06–0:07 | Red velvet slice in an open branded to-go box ("Piece of Velvet" on the lid) |
| 8 | 0:07–0:10 | Rapid blink-montage of all 7, ending on the hero slice (beat 1) + text card |

**On-screen text:** "PIECE OF VELVET" (elegant serif) with "GRAND OPENING" letter-spaced
beneath it — either persistent at the top of frame, or landing as an end card on the final
chime. Optional final line: "Now Open".

---

## Execution plan (Higgsfield MCP tool calls)

> These calls could not be run in the remote session (generation tools require interactive
> approval). Run them from an interactive Claude session with the Higgsfield connector
> approved, or paste the prompts straight into higgsfield.ai.

### Step 1 — Hero start frame (`generate_image`)

- **model:** `nano_banana_pro` (best for accurate in-image text) — alt: `marketing_studio_image`
- **aspect_ratio:** `9:16`
- **prompt:**

```
Vertical 9:16 product advertisement photo. A single perfect slice of red velvet cake with
cream cheese frosting layers sits centered on a small elegant white dessert plate, on a flat
light gray surface. The plate has a thin gold rim and a small dark red script logo reading
'Piece of Velvet'. The cake slice is deep crimson red with three visible sponge layers,
topped with a swirl of cream cheese frosting and red velvet crumbs. Background is a blurred
night scene with large warm golden-orange bokeh light circles. Soft, even studio front
lighting highlighting the moist cake texture. At the top of the frame, elegant serif text in
cream white reads 'PIECE OF VELVET' with smaller letter-spaced text below it reading
'GRAND OPENING'. Clean, premium bakery ad aesthetic, photorealistic.
```

### Step 2 — The video (`generate_video`)

- **model:** `kling3_0` (multi-shot control + native audio) — alt: `marketing_studio_video`
- **aspect_ratio:** `9:16`, **duration:** `10`
- **medias:** `[{ "role": "start_image", "value": "<job_id from Step 1>" }]`
- **prompt:**

```
Static locked-off camera, medium close-up, never moves for the entire video. A dessert sits
centered on a flat light gray surface against a blurred night background of large warm
golden-orange bokeh light circles, soft even front lighting. Elegant cream-white serif text
at the top of frame reads 'PIECE OF VELVET' above smaller text 'GRAND OPENING' and stays
fixed throughout. Every second, a hard jump cut instantly swaps the dessert for a different
red velvet treat while the plate position, surface, lighting and background stay perfectly
identical: first a classic red velvet cake slice with cream cheese frosting on a gold-rimmed
white plate; then a red velvet cupcake with a tall frosting swirl in a dark red wrapper;
then a whole mini red velvet cake frosted white with red crumbs around the base; then a
red velvet cake jar in clear glass with layered red sponge and white cream; then a red
velvet milkshake with whipped cream and a crumble rim in a tall glass; then a stack of red
velvet sandwich cookies with cream filling; then a red velvet slice in an open branded
bakery to-go box. In the final three seconds, extremely rapid jump cuts blink through all
the desserts in quick succession, landing back on the classic red velvet cake slice exactly
on the final beat. Upbeat celebratory big-band style instrumental music with rhythmic
percussion, each cut landing on a beat, ending with a sharp bright chime on the last cut.
Premium bakery advert, photorealistic, 9:16 vertical.
```

### Step 3 — Polish (optional)

- `upscale_video` to 2K/4K for the final deliverable.
- `reframe` to 1:1 or 16:9 if square/landscape versions are needed for other placements.
- If Kling's baked-in audio isn't right: `generate_audio` — "upbeat celebratory big band
  instrumental, fast tempo, rhythmic percussion accents every beat, finishes with a single
  bright chime, 10 seconds" — and mux it over the video.

### Fallback (if the single-prompt jump cuts come out mushy)

Generate 7 stills (one per shot-list row) with `nano_banana_pro`, using Step 1's output as a
reference image so the set stays identical and only the dessert changes. Animate each with
`kling3_0_turbo` (1s, static camera, subtle steam/sheen), then cut them together on the
beat — 1s each for beats 1–7, then ~0.15s each cycling for the finale, ending on the hero.
