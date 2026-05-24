# HCMUS-CTF 2026 Quals Write-up Announcement

Saved from the Discord announcement on `2026-05-24 22:33:01 +0700`.

## Original announcement

Chào các bạn `@2026 Participant`,

Chỉ còn vài tiếng nữa là vòng loại HCMUS-CTF 2026 sẽ chính thức khép lại.
Các đội đạt thứ hạng cao sẽ có thời gian đến `23:59` ngày hôm nay
(`May 24, 2026 at 11:59 PM`) để submit write-up.

Đội không nộp write-up sẽ không được vào chung kết. Trong trường hợp các đội
phía trên không đủ điều kiện tham gia chung kết, BTC sẽ tiếp tục xét đến các
đội tiếp theo.

## Forms

- Write-up form short link: <https://forms.gle/CHYTuC8ScAcH8bu9A>
- Write-up form resolved URL:
  <https://docs.google.com/forms/d/e/1FAIpQLSdy_WToyNiIy7VmJcoXUEjLz7NSzS8P0TtG9SB5fOuLFZn20A/viewform>
- Write-up form title: `HCMUS-CTF 2026 QUALS WRITE-UP SUBMISSION`

- Feedback form short link: <https://forms.gle/XjJ6VrpDTbAR9j2H7>
- Feedback form resolved URL:
  <https://docs.google.com/forms/d/e/1FAIpQLSczPfwdJvGagiGghoGmNetVirqb-QRB9_hTxnak18XgtWmSCw/viewform>
- Feedback form title: `HCMUS-CTF 2026 QUALS FEEDBACK`

## Challenges requiring write-ups if solved

- Crypto: `Crypto101`, `Rust In Peace`, `funny helicopher morphology - 2`
- Forensics: `Memeory`
- Misc: `Nyanko Daisensou`, `Bad Apple 3`
- Pwn: `xv6`, `xv6_revenge`, `notebook`, `simple file manager`
- Reverse: `Hide and Seek 2`
- Web: `Pink Black Vault Heist`, `The Real TARget`, `Core Issues`, `Fun PHP`

## Submission format

Write-up must be submitted as `PDF`. If written in Notion, HackMD, or similar,
export or print to PDF first.

## AI transcript policy

BTC accepts AI-agent transcripts as write-up support if the team used AI during
the solve. Accepted approaches:

- share the conversation link directly
- include the conversation link in the PDF
- export Codex / Claude Code transcript to HTML, upload it to a secret Gist,
  and link the `https://gisthost.github.io/` view inside the PDF

Referenced tools:

- <https://github.com/simonw/claude-code-transcripts>
- <https://github.com/masonc15/codex-transcript-viewer>

Example one-liners from the announcement:

```bash
find ~/.codex/sessions -type f -name '*.jsonl' -newermt '2026-05-23 08:00:00 +07:00' -exec grep -l -- 'HCMUS-CTF{' {} + | xargs -n1 uvx --from=https://github.com/masonc15/codex-transcript-viewer.git codex-transcript-viewer

find ~/.claude/projects -type f -name '*.jsonl' -newermt '2026-05-23 08:00:00 +07:00' -exec grep -l -- 'HCMUS-CTF{' {} + | xargs -n1 uvx claude-code-transcripts json --output-auto
```

## Restrictions

- Do not publish write-ups before the submission deadline ends.
- Do not discuss challenge solutions publicly before the deadline ends.

## Feedback

BTC also requests anonymous feedback:

- Feedback form short link: <https://forms.gle/XjJ6VrpDTbAR9j2H7>
- Feedback form resolved URL:
  <https://docs.google.com/forms/d/e/1FAIpQLSczPfwdJvGagiGghoGmNetVirqb-QRB9_hTxnak18XgtWmSCw/viewform>
