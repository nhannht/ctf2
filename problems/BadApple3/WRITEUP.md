# Bad Apple 3

Status: in progress

## Challenge

Description:

```text
iykyk

https://www.youtube.com/watch?v=6p9iiLJX59w

Flag format: HCMUS-CTF\{[a-z0-9_]{46}\}
```

## Current Analysis

- there is no local distribution archive in the repo
- the YouTube link is the only published artifact
- direct anonymous YouTube extraction from the normal YouTube endpoints was
  blocked by bot protection
- Invidious API access works and was enough to recover:
  - metadata
  - storyboard sheets
  - working proxied media URLs via `latest_version?...&local=true`

## Verified Facts

- title: `Bad Apple 3`
- author: `Trịnh Minh Huy`
- author id: `UCnok566UPS9XBZ1-ZDYOdsQ`
- length: about `326` seconds
- the video has no description and no captions
- comments are mostly jokes and do not contain a solve hint
- the channel is tiny and does not expose obvious `Bad Apple 1` / `Bad Apple 2`
  uploads through the public Invidious API

## Acquisition

- saved metadata to `video_api.json`
- saved storyboard sheets under `storyboards/`
- split the storyboard sheets into 66 frame tiles under `tiles/`
- eventually recovered the actual video files locally:
  - `video_360p.mp4`
  - `video_1080p60.mp4`

The working media path was not the raw GoogleVideo URL from the API. Those
URLs were signed to the Invidious server IP and returned `403` directly. The
working route was the Invidious proxy endpoint:

- `https://inv.thepixora.com/latest_version?id=6p9iiLJX59w&itag=<itag>&local=true`

Verified working downloads:

- `itag=18` -> `360p` muxed MP4
- `itag=298` -> `720p60` video-only MP4
- `itag=299` -> `1080p60` video-only MP4

## Storyboard Analysis

- the storyboard sheets do not look like normal thumbnails
- raw storyboard tiles looked blue-gray and noisy
- `blue - red` channel differences on storyboard tiles exposed structure, but
  this turned out to be a storyboard / JPEG artifact rather than a property of
  the real video
- QR detection on raw and transformed storyboard tiles returned no hits

## Real Video Analysis

### Direct checks

- the real video frames are grayscale, not blue-tinted
- `360p` file metadata:
  - `640x360`
  - `30 fps`
  - `9750` video frames
  - AAC audio track present
- `1080p60` file size is `200827295` bytes and completed successfully

### Dead ends already checked

- raw QR detection on storyboard thumbnails: no hits
- QR detection on real extracted frames: no hits
- OCR on sampled `360p` and `1080p` frames: only gibberish, no flag string
- MP4 metadata / strings scan: no useful embedded text
- simple blur / downscale / threshold passes on still frames did not produce an
  obvious visible flag

### Structural measurements

- on real `360p` frames, horizontal and vertical autocorrelation show a strong
  periodicity at `5 px`
- on real `1080p` frames, autocorrelation shows a strong periodicity at
  `15 px`, with additional substructure at `5 px`
- this means the `1080p` encode is not just a trivial upscale of the `360p`
  file; it contains a meaningful `15x15` cell structure
- splitting one `1080p` frame into `15x15` macrocells and then into `3x3`
  `5x5` phase blocks shows that different sub-block phases behave differently,
  which is another sign of a structured encoder rather than random noise
- PCA / per-tile template analysis confirms there is a strong fixed tile
  template mixed with weaker signal

## Current Best Lead

The strongest clue is no longer the recursive-video guess.

A previous HCMUS-CTF misc challenge, `Is This Bad Apple?`, was solved by
recognizing the video as an `Infinite Storage Glitch` encoding and using the
`Dislodge` workflow from the `Infinite-Storage-Glitch` tool. That old writeup
is highly relevant here because:

- the challenge naming is clearly in the same family
- the current video also looks like dense black/white data rather than a normal
  rendered scene
- the title hint `iykyk` fits “know the previous `Bad Apple` / ISG trick”
  better than a generic stego puzzle

So the current solve direction is:

- treat `Bad Apple 3` as a likely `Infinite Storage Glitch` or related
  video-as-data container
- reproduce or reimplement the `Dislodge` path locally against the downloaded
  `video_1080p60.mp4`
- only fall back to more custom visual decoding if the ISG hypothesis is proven
  false

## Tooling Progress

- public GitHub access for the original `Infinite-Storage-Glitch` repo is
  awkward in this environment:
  - direct `git clone` over HTTPS failed
  - guessed GitHub archive and release URLs returned `404`
- despite that, the older writeup gives enough evidence that the ISG path is
  worth pursuing before more ad hoc computer-vision work

## Artifacts

- `video_api.json`
- `storyboards/`
- `tiles/`
- `video_360p.mp4`
- `video_1080p60.mp4`
- `video_frames_360/`
- derived storyboard analysis images:
  - `tiles_contact.png`
  - `brdiff_contact.png`
  - `maskblur_contact.png`
  - `temporal_resid_contact.png`

## Next Steps

- obtain a working copy of the `Infinite-Storage-Glitch` dislodger or recreate
  the required decode steps from documentation / mirrors
- run the decoder against `video_1080p60.mp4`
- if that fails, continue with cell-structure based reverse engineering on the
  `15x15` macrocell format
