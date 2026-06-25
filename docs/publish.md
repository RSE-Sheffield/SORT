# Publishing a Release

This guide covers the end-to-end flow for releasing SORT and archiving it to [ORDA](https://orda.shef.ac.uk) — the University of Sheffield's institutional research data repository — so each release receives a citable DataCite DOI.

## Release pipeline overview

```
Merge to main
     │
     ▼
release.yaml (semantic-release)
  • bumps version
  • builds frontend
  • creates GitHub Release with artifacts
     │
     ▼
release-to-orda.yml (triggered by GitHub Release)
  • downloads release zip + tarball
  • uploads to ORDA article via Figshare API
     │
     ▼
ORDA mints / updates DOI
```

---

## One-time ORDA setup

These steps must be completed by a project maintainer before the automated archival will run. They only need to be done once.

### 1. Create a Software item in ORDA

1. Go to <https://orda.shef.ac.uk> and sign in with your University of Sheffield credentials.
2. Click **My data → Create a new item**.
3. Set **Item type** to **Software**.
4. Fill in the metadata:
   - **Title**: Self-Assessment of Organisational Readiness Tool (SORT)
   - **Authors**: match the authors in `CITATION.cff`
   - **Description**: copy the abstract from `CITATION.cff`
   - **Keywords**: healthcare, surveys, nursing
   - **License**: MIT
   - **Categories**: choose an appropriate research category (e.g. *Medical Informatics*)
5. **Save** the item (do not publish yet — files will be uploaded automatically).
6. Note the **article ID** from the URL:
   `https://orda.shef.ac.uk/articles/software/.../<ARTICLE_ID>`

### 2. Generate a Figshare personal access token

1. In ORDA, go to **Account → Applications → Personal tokens**.
2. Click **Create new token**, give it a descriptive name (e.g. `SORT GitHub Actions`), and copy the token value immediately — it is shown only once.

### 3. Add the secret and variable to the GitHub repository

In the `RSE-Sheffield/SORT` repository settings:

| Type | Name | Value |
|------|------|-------|
| **Secret** | `FIGSHARE_TOKEN` | The personal access token from step 2 |
| **Variable** | `FIGSHARE_ARTICLE_ID` | The article ID from step 1 |

Path: **Settings → Secrets and variables → Actions**

The `release-to-orda.yml` workflow is gated on `vars.FIGSHARE_ARTICLE_ID != ''`, so it stays dormant until this variable is set. No workflow failures will occur on repositories that have not yet completed this setup.

---

## Automated release flow

Once the one-time setup is complete, every merge to `main` that triggers a release follows this path automatically:

1. A `feat:` or `fix:` commit is merged to `main`.
2. The **Create Release** workflow (`release.yaml`) runs:
   - Builds the frontend (`npm run build`)
   - Runs `npx semantic-release` to determine the version, generate a changelog, and create a GitHub Release with source and frontend archives attached
3. GitHub fires the `release: [published]` event, triggering **Release to ORDA** (`release-to-orda.yml`):
   - Downloads the release `.zip` and `.tar.gz` from GitHub
   - Uploads both files to the ORDA article via the Figshare API
4. ORDA updates the article and mints or increments the DOI.

---

## Adding the DOI badge to README.md

After the first release is archived and ORDA has assigned a DOI:

1. Open the ORDA article page and copy the DOI (e.g. `10.15131/shef.data.NNNNNNN`).
2. Add the badge to the top of `README.md`, alongside the existing CI badge:

```markdown
[![DOI](https://img.shields.io/badge/DOI-10.15131%2Fshef.data.NNNNNNN-blue)](https://doi.org/10.15131/shef.data.NNNNNNN)
```

3. Add the DOI to `CITATION.cff` under an `identifiers` block:

```yaml
identifiers:
  - type: doi
    value: 10.15131/shef.data.NNNNNNN
    description: The concept DOI for all versions of SORT
```

---

## Verifying an upload

After a release:

1. Open the repository **Actions** tab and check the **Release to ORDA** workflow run for the relevant release tag.
2. Open the ORDA article at <https://orda.shef.ac.uk> and confirm the new files appear under **Files**.
3. The DOI link (e.g. `https://doi.org/10.15131/shef.data.NNNNNNN`) should resolve to the updated article.

---

## Further reading

- [semantic-release guide](semantic-release-guide.md) — commit conventions and version automation
- [figshare/github-upload-action](https://github.com/figshare/github-upload-action) — the action used for uploads
- [RSE-Sheffield/release_to_ORDA](https://github.com/RSE-Sheffield/release_to_ORDA) — template repository for this pattern
