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
npm run test:watch     # Watch mode
npm run test:coverage  # With coverage report
make e2e     # Playwright browser tests in e2e/ (needs: playwright install chromium)
```

### Code Quality
```bash
# Linting
npm run lint
npm run lint:fix
make lint  # Python linting with flake8 and black

# Type checking (TypeScript/Svelte)
npm run lint:check
```

### Building for Production
```bash
# Build JavaScript components
npm run build

# Collect static files
python manage.py collectstatic
```

### Useful Management Commands
```bash
# Clear orphaned uploaded files
python manage.py clear_orphaned_files

# Export survey usage report
python manage.py usage

# Generate survey CSV export
python manage.py csv
```

## Code Architecture

### Django App Structure

The project consists of two main Django apps with distinct responsibilities:

**Home App** (`/home/`)
- User authentication and management (custom User model with email as username)
- Organisation and OrganisationMembership models for multi-tenancy
- Project management within organisations
- Role-based access control (ADMIN, PROJECT_MANAGER)

**Survey App** (`/survey/`)
- Survey creation, configuration, and lifecycle management
- Response collection and storage (JSON-based answers)
- Evidence gathering and improvement planning sections
- File uploads and attachments
- CSV/Excel export functionality
- Invitation system with unique tokens

### Service Layer Pattern

All business logic is abstracted into service classes located in `services/` directories within each app. Services enforce permission checking using a decorator pattern:

- **BasePermissionService**: Abstract base class with `can_view()`, `can_edit()`, `can_delete()`, `can_create()` methods
- **@requires_permission** decorator: Enforces permission checks before executing service methods
- Services are singletons accessed via module-level instances (e.g., `organisation_service`, `project_service`, `survey_service`)

Key service classes:
- `OrganisationService`: Organisation lifecycle and member management
- `ProjectService`: Project CRUD with inherited organisation permissions
- `SurveyService`: Survey operations, response handling, exports, evidence/improvement sections

**Important**: Always use service layer methods for business logic rather than direct model manipulation. Services handle permission checking automatically.

### Model Architecture

**Key Models and Relationships**:
```
User (custom auth model)
  └─> OrganisationMembership (role: ADMIN or PROJECT_MANAGER)
       └─> Organisation
            └─> Project
                 └─> Survey (has survey_config JSONField)
                      ├─> SurveyResponse (answers JSONField)
                      ├─> Invitation (token-based)
                      ├─> SurveyEvidenceSection (section_id indexed)
                      │    └─> SurveyEvidenceFile
                      └─> SurveyImprovementPlanSection (section_id indexed)
```

**Configuration-Driven Surveys**: Survey structure is loaded from JSON configuration files in `data/readiness_descriptions/`. The `survey_config` JSONField on Survey model stores the complete question structure, field types, and validation rules.

**Custom Properties**: Models use property methods for computed values:
- `Survey.reference_number`: Formatted identifier (SURVEY-000001)
- `Survey.sections`: Returns question section groups from config
- `Survey.fields`: All question field names
- `SurveyResponse.answers_values`: Flattened answer values (expands nested Likert structures)

### Vite Integration with Django

The project uses custom Django template tags for Vite integration (`home/templatetags/vite_integration.py`):

- **{% vite_client %}**: Includes Vite HMR client in DEBUG mode
- **{% vite_asset 'path/to/asset.ts' %}**: Resolves assets differently based on environment:
  - DEBUG: Links to Vite dev server (http://localhost:5173)
  - Production: Resolves from manifest.json in static files

JavaScript/TypeScript components live in `ui_components/src/` and are built with Vite to `static/ui-components/`. Always run `npm run build` before deploying.

### Testing Utilities

Custom test base classes in `SORT/test/test_case/`:

- **SORTTestCase**: Extends Django TestCase with standard user setup
- **ServiceTestCase**: For testing service layer methods
- **ViewTestCase**: Provides `login()`, `get()`, `post()` helper methods with automatic status code checking

Model factories using factory_boy in `SORT/test/model_factory/`:
- UserFactory, SuperUserFactory, OrganisationFactory, ProjectFactory, SurveyFactory, InvitationFactory
- All test users have predictable emails (user0@sort.com, user1@sort.com, etc.)

### URL Patterns

URLs follow a hierarchical structure:
- `/` - Home and authentication
- `/myorganisation/` - Organisation management
- `/projects/<project_id>/` - Project views
- `/survey/<pk>/` - Survey management and configuration
- `/survey_response/<token>` - Public survey response form (no authentication required)

### Role-Based Access Control

- **ADMIN**: Full control over organisation, all projects, and all surveys
- **PROJECT_MANAGER**: Can manage specific projects and their surveys
- Permissions cascade: organisation role → project access → survey access
- All service methods enforce permissions via `@requires_permission` decorator

### Frontend Components (Svelte)

Interactive UI components in `ui_components/src/`:
- SurveyConfigConsentDemographyApp: Survey configuration interface
- SurveyResponseApp: Dynamic survey response form
- FileBrowser: File upload and management

Components use Bootstrap 5 for styling and Chart.js for visualizations.

## Development Workflow

### Branching Strategy

- **main branch**: Primary branch for all development and production
- **Branch naming**: Must follow [conventional branch naming](https://conventional-branch.github.io/) with these prefixes:
  - `feat/` - New features
  - `fix/` - Bug fixes
  - `docs/` - Documentation changes
  - `style/` - Code style changes (formatting, whitespace)
  - `refactor/` - Code refactoring without changing behavior
  - `perf/` - Performance improvements
  - `test/` - Test additions or changes
  - `build/` - Build system or dependency changes
  - `ci/` - CI/CD configuration changes
  - `chore/` - Maintenance tasks
  - `revert/` - Revert previous commits
- **Enforcement**: GitHub rulesets enforce conventional branch naming for all branches (except `main`, `develop`, `staging`, `production`)

### Making Changes

1. Create an issue describing the problem or requirement
2. Create a branch associated with that issue
3. Make changes and create a draft PR
4. Mark PR "Ready for review" when complete
5. Merge to `main` branch after review and approval

### Releases

SORT uses **semantic versioning** (MAJOR.MINOR.PATCH) with automatic releases:

- **Automatic releases**: Every merge to `main` triggers a release workflow that auto-increments the patch version
- **Version tracking**: Version is stored in the `VERSION` file and `package.json`
- **Release artifacts**: Each release includes built frontend assets and source archives
- **Release notes**: Auto-generated from commit messages between releases

**For patch releases** (bug fixes):
- Simply merge to main - version auto-increments (e.g., 0.1.0 → 0.1.1)

**For minor/major releases** (new features/breaking changes):
```bash
# Bump version before merging to main
./scripts/bump-version.sh minor  # or 'major'
git add VERSION package.json package-lock.json
git commit -m "chore: bump version to $(cat VERSION)"
```

See [RELEASING.md](RELEASING.md) for complete release documentation.

### Environment Variables

Required `.env` file (development only):
```bash
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1 localhost
DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DJANGO_LOG_LEVEL=DEBUG
```

## Key Technologies

- **Backend**: Django 5.1, Python 3.12
- **Frontend**: Svelte 5, TypeScript, Vite 6, Bootstrap 5
- **Testing**: Django TestCase, Vitest, Testing Library
- **Database**: SQLite (dev), PostgreSQL (production)
- **Third-party Django apps**: django-allauth, django-invitations, crispy-forms, qr-code

## Further Documentation

Detailed technical documentation is available in the [docs/](docs/) directory:

- [docs/data-model.md](docs/data-model.md) - Database schema and entity relationships
- [docs/deployment.md](docs/deployment.md) - Production deployment and server configuration
- [docs/testing.md](docs/testing.md) - Testing frameworks and writing tests

See [docs/README.md](docs/README.md) for a complete documentation index.

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

Use [Conventional Commits](https://www.conventionalcommits.org/). Pushes to `main` update an open release-please PR (version bump + changelog); merging that PR cuts the actual release. See `RELEASING.md`.

```
feat: ...   → minor release
fix: ...    → patch release
chore: ...  → no release
```
