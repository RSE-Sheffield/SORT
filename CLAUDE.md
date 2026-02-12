# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SORT (Self-Assessment of Organisational Readiness Tool) is a Django-based web application that enables organizations to evaluate and strengthen their research capabilities within nursing and health care practices. The application uses Django 5.1 with a Svelte/Vite frontend integration for interactive components.

## Common Commands

### Development Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows
source .venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
npm install

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Load test data
python manage.py loaddata ./data/*.json
```

### Running the Application
```bash
# Start Django development server (terminal 1)
python manage.py runserver

# Start Vite dev server for JavaScript components (terminal 2)
npm run dev
```

### Testing
```bash
# Backend tests (Django)
python manage.py test home/tests --parallel=auto --failfast
python manage.py test survey/tests --parallel=auto --failfast

# Run all tests
make test

# Frontend tests (Vitest)
npm test
npm run test:watch     # Watch mode
npm run test:coverage  # With coverage report
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

## Important Notes

- Always use the service layer for business logic operations
- Test both Django and JavaScript changes with respective test suites
- Run `npm run build` before deploying to ensure static assets are built
- Survey structure is JSON-driven; modify configs in `data/readiness_descriptions/`
- File uploads go to `MEDIA_ROOT/survey/{survey_id}/` and `MEDIA_ROOT/survey_evidence/{section_id}/`
- Test user passwords match their role name in lowercase (from test data fixtures)

## Accessibility Compliance

The SORT-online platform serves healthcare professionals (nurses, midwives, allied health professionals) across diverse NHS organisations. Accessibility is not optional—it's a legal requirement under the Public Sector Bodies Accessibility Regulations 2018 and essential to our mission of supporting research capacity development.

### WCAG 2.1 Level AA Compliance

All code contributions must adhere to **WCAG 2.1 Level AA** standards. This is enforced through automated GitHub Actions checks and manual code review.

### Core Accessibility Principles

#### 1. Semantic HTML First

- Use semantic HTML elements (`<button>`, `<form>`, `<nav>`, `<main>`, `<section>`, `<article>`) instead of generic divs
- Never use `<div>` or `<span>` for clickable/interactive elements
- Use `<label>` elements with `for` attributes that match input `id` values
- Use `<fieldset>` and `<legend>` for grouped form inputs (e.g., maturity rating scales)

**Example - DO:**

```html
<form method="post">
  <fieldset>
    <legend>Maturity Level Assessment</legend>
    <div class="form-group">
      <label for="maturity_0">Not yet planned</label>
      <input type="radio" id="maturity_0" name="maturity" value="0">
    </div>
  </fieldset>
</form>
```

**Example - DON'T:**

```html
<div onclick="submitForm()">
  <span>Not yet planned</span>
  <input type="radio" name="maturity" value="0">
</div>
```

#### 2. Keyboard Navigation

- All interactive elements must be keyboard accessible without requiring a mouse
- Ensure Tab order is logical and follows visual flow (left-to-right, top-to-bottom)
- Use `tabindex` only when necessary and never with positive values (`tabindex="0"` or `tabindex="-1"` only)
- Provide visible focus indicators with minimum 3:1 contrast ratio

**Example - Django template:**

```html
<button type="submit" class="btn btn-primary">
  Submit SORT Assessment
</button>

<!-- Focus indicator in CSS -->
button:focus-visible {
  outline: 3px solid #003d7a; /* NHS dark blue */
  outline-offset: 2px;
}
```

#### 3. Form Accessibility

All forms must include:

- Associated labels for every input (use `for` and `id` attributes)
- Required field indicators with both visual and text-based markers
- Error messages linked to form fields via `aria-describedby`
- Help text associated with inputs via `aria-describedby`
- Clear form validation feedback with `role="alert"`

**Example - Django form template:**

```html
<form method="post" novalidate>
  {% csrf_token %}
  
  {% for field in form %}
    <div class="form-group">
      <label for="{{ field.id_for_label }}" class="form-label">
        {{ field.label }}
        {% if field.field.required %}
          <span class="required-indicator" aria-label="required">*</span>
        {% endif %}
      </label>
      
      {{ field }}
      
      {% if field.help_text %}
        <small class="form-text" id="{{ field.id_for_label }}_help">
          {{ field.help_text|safe }}
        </small>
      {% endif %}
      
      {% if field.errors %}
        <div class="invalid-feedback" role="alert" 
             aria-describedby="{{ field.id_for_label }}">
          {{ field.errors.0 }}
        </div>
      {% endif %}
    </div>
  {% endfor %}
  
  <button type="submit" class="btn btn-primary">Submit</button>
</form>
```

#### 4. Color Contrast

All text and interactive elements must meet WCAG AA contrast ratios:

- **Normal text**: minimum 4.5:1 contrast ratio (white text on dark backgrounds, or dark text on light)
- **Large text** (18pt+ or 14pt+ bold): minimum 3:1 contrast ratio
- **UI components**: minimum 3:1 contrast ratio for borders and visual indicators

Before merge, verify contrast using:

- WAVE browser extension (manual check)
- Axe DevTools browser extension (automated check)
- GitHub Actions axe-core output (pre-commit check)

**Example - CSS compliant with NHS palette:**

```css
/* Good: NHS Dark Blue (003d7a) on white */
.btn-primary {
  background-color: #003d7a; /* Contrast: 8.3:1 */
  color: #ffffff;
}

/* Good: Body text (333333) on white */
body {
  color: #333333;
  background-color: #ffffff;
  /* Contrast: 12.6:1 */
}

/* Bad: Grey text (999999) on light grey background */
.disabled-text {
  color: #999999;
  background-color: #eeeeee;
  /* Contrast: 2.1:1 - FAILS */
}
```

#### 5. Images and Icons

- **All images** require descriptive `alt` text that conveys meaning/purpose
- **Icon-only buttons** require `aria-label` or hidden text via `.sr-only` class
- **Decorative images** use `alt=""` and `aria-hidden="true"`
- **Complex images** (charts, diagrams) require detailed description via `aria-describedby`

**Example - Icon button:**

```html
<!-- Good -->
<button class="btn-close" aria-label="Close navigation menu">
  <svg aria-hidden="true"><!-- close icon --></svg>
</button>

<!-- Also good -->
<button class="btn btn-secondary">
  <svg aria-hidden="true"><!-- download icon --></svg>
  <span class="sr-only">Download</span> Results
</button>
```

**Example - Chart/diagram:**

```html
<figure>
  <img src="maturity-chart.png" alt="Maturity assessment results" 
       aria-describedby="chart-description">
  <figcaption id="chart-description">
    The chart shows substantial progress in Releasing Potential (score 3.2) 
    and Embedding Research (score 2.8), with lower scores in Digitally 
    Enabled Research (score 1.5).
  </figcaption>
</figure>
```

#### 6. ARIA Attributes (Use Carefully)

ARIA should enhance, not replace, semantic HTML. Follow the rule: **ARIA is a last resort**.

**When to use ARIA:**

- Adding descriptions to icons or complex components
- Indicating dynamic content changes (`aria-live`)
- Marking required fields or error states
- Defining custom component roles only when semantic HTML won't work

**When NOT to use ARIA:**

- Don't use `role="button"` on divs—use `<button>`
- Don't use `aria-label` instead of visible labels—use `<label>`
- Don't use `role="link"` on buttons—use `<a>` or keep as button
- Don't overuse `aria-describedby`—use visible help text first

**Example - Correct ARIA usage:**

```html
<!-- Good: Semantic + ARIA enhancement -->
<form>
  <div class="maturity-scale" role="group" aria-labelledby="scale-legend">
    <legend id="scale-legend">Select maturity level:</legend>
    <label>
      <input type="radio" name="maturity" value="0" required>
      Not yet planned
    </label>
  </div>
</form>

<!-- Good: Live region for dynamic updates -->
<div role="status" aria-live="polite" aria-atomic="true">
  <!-- JavaScript will update this with form save messages -->
</div>

<!-- Bad: Unnecessary ARIA -->
<div role="button" tabindex="0" aria-label="Submit">
  Click me
</div>
```

#### 7. Svelte Component Accessibility

When writing Svelte components:

**Avoid:**

```svelte
<!-- DON'T: Non-semantic, onclick-driven -->
<div on:click={handleSubmit} class="button">
  Submit
</div>
```

**Do:**

```svelte
<!-- DO: Semantic button with proper event handling -->
<button on:click={handleSubmit} class="btn btn-primary">
  Submit
</button>

<!-- DO: Icon button with aria-label -->
<button aria-label="Close form" on:click={closeForm}>
  <CloseIcon />
</button>

<!-- DO: Conditional rendering of required indicator -->
{#if isRequired}
  <span class="required-indicator" aria-label="required">*</span>
{/if}
```

**Svelte-specific checks:**

- Ensure `on:keydown` is used alongside `on:click` for non-button elements (rare edge cases only)
- Pass `aria-*` attributes through to DOM elements: `<Component {ariaLabel} />`
- Use reactive statements to keep ARIA values in sync with component state

#### 8. Testing Requirements

Before submitting code for merge:

**Automated (GitHub Actions will run these):**

- [ ] Axe-core accessibility scan passes (zero critical/serious violations)
- [ ] Pa11y tests pass (WCAG2AA standard)
- [ ] Lighthouse accessibility score ≥ 90/100

**Manual checks required in PR description:**

- [ ] All interactive elements tested with keyboard (Tab, Enter, Escape)
- [ ] Tested with at least one screen reader (NVDA, VoiceOver, or TalkBack)
- [ ] Color contrast verified with WAVE or Axe browser extension
- [ ] Form validation messages tested (both visual and screen reader)
- [ ] Mobile testing completed (touch targets 44x44px minimum, zoom to 200%)

**Example PR checklist comment:**

```markdown
## Accessibility Checklist
- [x] Axe-core scan: PASS (no violations)
- [x] Keyboard navigation: PASS (all interactive elements reachable)
- [x] NVDA screen reader: PASS (form labels read correctly)
- [x] Color contrast: PASS (4.8:1 ratio verified with WAVE)
- [x] Mobile zoom: PASS (no overflow at 200%)
- [ ] VoiceOver testing: Not yet (will test on macOS)
```

#### 9. Common Accessibility Mistakes to Avoid

| Mistake                                     | Why It Fails                                 | Solution                                     |
| ------------------------------------------- | -------------------------------------------- | -------------------------------------------- |
| Using `<span>` with `onclick` for actions   | Not keyboard accessible, semantically wrong  | Use `<button>`                               |
| Missing form labels                         | Screen readers can't announce field purpose  | Add `<label for="id">`                       |
| Relying on color alone                      | Red/green colorblind users can't distinguish | Add icons, text, or patterns                 |
| `tabindex="5"` or higher values             | Disrupts keyboard navigation order           | Use `0` or `-1` only                         |
| Alt text: "image", "photo", "picture"       | Doesn't convey meaning                       | Describe purpose: "Chart showing..."         |
| Hiding focus indicator with `outline: none` | Users can't see where they are               | Keep visible or add custom `outline`         |
| Modal without focus trap                    | Tab key escapes modal                        | Trap focus within modal, restore after close |
| Placeholder as label substitute             | Disappears when typing, not associated       | Use `<label>` + `placeholder`                |
| `aria-label` on already-labeled elements    | Creates redundant announcements              | Remove `aria-label`, fix the label instead   |

#### 10. Accessibility in Code Review

When reviewing pull requests, check for:

1. **Semantic HTML**: Are interactive elements using appropriate tags?
2. **Keyboard access**: Can all functionality be used without a mouse?
3. **Form structure**: Are labels, errors, and help text properly associated?
4. **Color use**: Is meaning conveyed beyond color alone?
5. **Images**: Do all images have meaningful alt text?
6. **ARIA sparingly**: Is ARIA used only when HTML can't do the job?
7. **Test evidence**: Has the contributor provided accessibility test screenshots or logs?

Comment template for accessibility issues:

```markdown
### Accessibility Issue

**Problem:** This button uses a div with onclick instead of semantic HTML.

**WCAG Violation:** 2.1.1 Keyboard (Level A)

**Fix:** 
Replace `<div on:click={...}>` with `<button on:click={...}>`

**Reference:** WCAG 2.1 Keyboard - All functionality must be operable via keyboard
```

#### 11. Resources

- **WCAG 2.1 Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/
- **NHS Digital Accessibility Guidance**: https://www.england.nhs.uk/digital/
- **Inclusive Components**: https://inclusive-components.design/
- **The A11Y Project Checklist**: https://www.a11yproject.com/checklist/
- **MDN Accessibility**: https://developer.mozilla.org/en-US/docs/Web/Accessibility
- **WebAIM Screen Reader Testing**: https://webaim.org/articles/screenreader_testing/

#### 12. Questions? Issues?

If you encounter accessibility ambiguities:

1. Check WCAG 2.1 guidelines (link above)
2. Review existing SORT-online code for patterns
3. Consult with the project team on Slack: #accessibility
4. Raise an issue on GitHub tagged `accessibility` for team discussion

------

### Summary

Accessibility is a **shared responsibility**. Every pull request, every component, every line of CSS contributes to whether healthcare professionals can effectively use SORT-online to advance research capacity in their organisations. Write code that works for everyone.
