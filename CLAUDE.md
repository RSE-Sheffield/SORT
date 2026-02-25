# CLAUDE.md

SORT is a Django 5.1 + Svelte/Vite web app for NHS organisations to assess research readiness.

## Commands

```bash
# Run
python manage.py runserver   # terminal 1
npm run dev                  # terminal 2

# Test
make test
python manage.py test home/tests --parallel=auto --failfast
python manage.py test survey/tests --parallel=auto --failfast
npm test

# Quality
make lint
make check   # Django checks + migration verification (run before committing model changes)
```

## Architecture

**Apps**: `home/` (auth, orgs, projects) · `survey/` (surveys, responses, exports)

**Service layer**: All business logic goes through service singletons (`organisation_service`, `project_service`, `survey_service`). Never manipulate models directly — services enforce permissions via `@requires_permission`.

**Model hierarchy**: User → OrganisationMembership (ADMIN|PROJECT_MANAGER) → Organisation → Project → Survey → SurveyResponse/Invitation/Evidence/ImprovementPlan

**Roles**: ADMIN has full org access; PROJECT_MANAGER manages specific projects.

**Survey config**: JSON-driven structure from `data/readiness_descriptions/`; stored in `Survey.survey_config` JSONField.

**Vite integration**: `{% vite_asset %}` template tag serves from dev server (DEBUG) or manifest.json (production). Run `npm run build` before deploying.

**Tests**: Use `ViewTestCase`/`ServiceTestCase` base classes and factories in `SORT/test/`. Test emails follow `user0@sort.com` pattern.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/). Releases are automated via semantic-release on merge to `main`.

```
feat: ...   → minor release
fix: ...    → patch release
chore: ...  → no release
```
