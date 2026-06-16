# Writing Guide — All Three Papers

A single shared style and pipeline so paper 1, paper 2 and paper 3 look like
they belong to the same submission. Read once before drafting any of the three
report markdown files; the actual Word document is generated mechanically from
markdown via pandoc.

`paper2.docx` is the worked example — open it, then come back here.

---

## TL;DR

1. Write your draft in `paperN-…/report/paperN.md`.
2. Use the **front matter template** in §3 verbatim, swap in your own name.
3. Use the **section list for your paper** in §5.
4. Embed figures, tables, citations using the conventions in §6.
5. Build appendices per §7 — codes, raw runs, screenshots all in.
6. Regenerate the `.docx` with the **single pandoc command in §8**. Done.

---

## 1. What we're targeting

Two source documents pinned this down (full analysis in
`/Users/endribaku/.claude/plans/goofy-petting-sun.md` if you want the trail):

- **`FINAL PROJECT-CEN-SWE-2025-2026.pdf`** — the grading rubric. Hard rules:
  10 pt, one-column, single-spaced; **10–15 body pages**;
  **5,000–8,000 body words**; appendices contain codes + screenshots + raw runs.
- **`oss-sample-paper for the CEN 308 project.pdf`** — Peng/Li/Mili sample.
  Sets the typographic style: UPPERCASE byline, italic affiliation,
  `SUMMARY`/`KEY WORDS:`, bracketed numbered citations, etc.

Where they conflict the rubric wins; where the rubric is silent the sample
wins. The agreed conventions are baked into the rest of this document.

---

## 2. Format constants (don't override)

| Property | Value |
|---|---|
| Body font | Times New Roman, 10 pt, all black |
| Code font | Courier New, 10 pt, all black (no syntax colouring) |
| Layout | one column, single-spaced, **fully justified** |
| Page margins | 0.6 inch all sides |
| Body length | 10–15 pages, 5,000–8,000 words *(appendices don't count)* |
| Title page / TOC | none |

These all live in `config/reference-10pt.docx`. Don't touch it; the pandoc
command in §8 reads it automatically.

---

## 3. Front matter template

Replace `YOUR NAME` with your own name in CAPS. Everything else is fixed.

```markdown
# Your Paper Title Here (mixed case, no all-caps)

YOUR NAME

*Epoka University, Faculty of Architecture and Engineering, Tirana, Albania*
*(email: yourusername@epoka.edu.al)*

::: {custom-style="Summary Heading"}
SUMMARY
:::

A single ~200-word paragraph. State the problem, what you built, the headline
result with one or two specific numbers, and the one-line takeaway. No
citations in the summary. No bullet points.

**KEY WORDS:** five to eight comma-separated terms, lowercase, ending without
a full stop
```

Notes:
- The `::: {custom-style="Summary Heading"} SUMMARY :::` block uses a custom
  paragraph style that's already defined in `config/reference-10pt.docx`. It
  centers just SUMMARY; the regular section headings stay left-aligned.
- Don't add a "Date", "Course", "Author:" label, or reproducibility line in
  the front matter. The sample paper doesn't have them.

---

## 4. Body anatomy

Sections are numbered, bold, left-aligned. Pandoc maps markdown headings to
Word styles automatically:

| Markdown | Renders as |
|---|---|
| `# Title` | Word "Title" style (centered) |
| `## 1. Section name` | "Heading 2" (bold, left, large) |
| `### 1.1 Subsection` | "Heading 3" (bold, left, medium) |
| `#### 1.1.1 Sub-subsection` | "Heading 4" (bold, left, small) |

Don't go deeper than four levels. Don't use `*italic*` or `**bold**` to fake
a heading — use a real heading.

---

## 5. Section list, by paper

The PDF prescribes which sections must appear. Use **these exact numbered
sections**, in this order. Content within each is up to you; the section
heading is fixed.

### Paper 1 — Shell Scripts

1. Introduction
2. Experimental Setup
3. Script Analysis (your 10 scripts; one subsection per script with the 7 dimensions)
4. Comparative Optimization Study
5. Design Patterns in Shell Scripts
6. Case Study: Script Refactoring (the CRT subject)
7. New Script Design (your novel tool)
8. Results & Discussion
9. Conclusion

### Paper 2 — Concurrency (worked example, already done)

1. Introduction
2. Related Work
3. Methodology
4. Experimental Design
5. Performance Evaluation
6. Scalability Study
7. Comparative Analysis
8. Optimization Proposal
9. Discussion
10. Conclusion

### Paper 3 — Scheduling & Queuing

1. Introduction
2. System Model
3. MLFQ Simulation
4. Metrics
5. Simulation Framework
6. Optimization Study
7. Visualization
8. Queuing Theory Extension
9. Randomness Study
10. Results
11. Conclusion

---

## 6. Body conventions

### Citations

Inline numbered citations in brackets, no spaces:
- Single: `Dijkstra introduced the problem [1].`
- Multiple: `…the classical synchronization problems [1,2,7].`

The References list goes at the end of the body (before appendices) as a
numbered list:

```markdown
## References

1. E. W. Dijkstra. *Cooperating Sequential Processes.* Technical Report
   EWD-123, Technological University Eindhoven, 1965.
2. C. A. R. Hoare. "Monitors: An Operating System Structuring Concept."
   *Communications of the ACM*, 17(10):549–557, 1974.
3. ...
```

Every reference must be cited at least once in the body. Conversely, every
inline `[N]` must resolve to a real entry.

### Tables

```markdown
**Table 1**: One-line caption describing the table. Period at end.

| Header A | Header B |
|---|---|
| value | value |
```

The `**Table N**:` prefix is bold; the caption sentence is non-bold. Put the
caption *above* the table.

### Figures

Embed images with a Markdown image syntax. Caption goes in the alt-text;
pandoc renders it as a normal figure caption underneath the image:

```markdown
![**Figure 1**: One-line caption.](../figures/your-folder/your-figure.png){width=3.3in}
```

`{width=3.3in}` is important — it stops figures from filling the page and
blowing the 15-page budget. Use that exact width for all body figures so
they look uniform.

### Cross-references

Plain English, no markdown magic: write "See Figure 4", "Table 7 shows…",
"§5.3". Don't use pandoc's `\ref{}` syntax — Word doesn't render it.

---

## 7. Appendices (required by the PDF)

The PDF explicitly demands codes, raw runs, and screenshots in appendices,
**per paper** (i.e., each paper has its own appendices). The appendices do
NOT count toward the 15-page body limit.

Use this fixed structure:

```markdown
## Appendices *(not counted toward the page/word limit)*

### Appendix A — Source code
(Embed every source file as a fenced code block. For paper 1: all 10
shell scripts. For paper 2: the C and Java files. For paper 3: the Python
modules.)

### Appendix B — Drivers / scripts / harness
(Anything that orchestrates runs but isn't core source.)

### Appendix C — Raw runs (samples)
(First 20–30 lines of the relevant CSV / log files.)

### Appendix D — Full-resolution plots
(Pointer to figures/ folders; figures already embedded in the body.)

### Appendix E — Sample simulation screenshots
(Terminal screenshots from actual runs — the PDF emphasises these twice.
Drop PNGs in paperN-…/screenshots/ and embed them here.)
```

Paper 2's appendix is the worked example —
`paper2-concurrency/report/paper2.md` lines 770–end.

---

## 8. Build command (the only one you need)

Once your `paperN.md` is ready, regenerate the `.docx` from the repo root:

```bash
cd paperN-…/report
pandoc paperN.md -o paperN.docx --resource-path=.:.. \
       --reference-doc=../../config/reference-10pt.docx \
       --syntax-highlighting=none
```

That's it. The reference doc handles every formatting decision (fonts,
margins, justification, summary centering). The `--syntax-highlighting=none`
flag keeps code blocks plain black.

---

## 9. Verification before submission

After regenerating, convert to PDF with LibreOffice and check:

```bash
soffice --headless --convert-to pdf paperN.docx
pdfinfo paperN.pdf | grep Pages
```

Then visually:

- [ ] Author byline is UPPERCASE.
- [ ] Affiliation and email are italic.
- [ ] `SUMMARY` heading is centered; section headings (`1. Introduction`,
  …) are left-aligned.
- [ ] `KEY WORDS:` line is in caps.
- [ ] Body is fully justified (lines reach both margins).
- [ ] Every section heading from §5 is present, numbered in order.
- [ ] Body page count is in **10–15** (Appendices start *after* page 10–15).
- [ ] Body word count is in **5,000–8,000** (Title → Conclusion).
- [ ] Every reference `[N]` is cited at least once; every cite resolves to
  a real reference.
- [ ] All 5 appendices present (A: code, B: drivers, C: raw runs, D: plots,
  E: screenshots).

---

## 10. Existing infrastructure to reuse

Don't reinvent these — paper 2 and paper 3 already use them:

| What | Where |
|---|---|
| Reference docx with all styling | `config/reference-10pt.docx` |
| Benchmark wrapper (GNU time + JSON line parser) | `common/bench.py` |
| Matplotlib helpers (line+errorbars, heatmap, 3D surface, bar) | `common/plots.py` |
| Parameter ranges + seeds | `config/experiments.yaml` |
| Environment description | `ENVIRONMENT.md` |
| Worked example markdown | `paper2-concurrency/report/paper2.md` |

For Paper 1 specifically, the script results go in
`paper1-shell/results/` and figures in `paper1-shell/figures/`, mirroring
the layout of papers 2 and 3.

---

## 11. Pandoc install (one-time)

```bash
# macOS
brew install pandoc
brew install --cask libreoffice  # for the verification step

# Ubuntu (e.g. the VM)
sudo apt install pandoc libreoffice
```

---

## 12. When in doubt

Open `paper2-concurrency/report/paper2.md` and look at how it solves the same
question. Copy that pattern.
