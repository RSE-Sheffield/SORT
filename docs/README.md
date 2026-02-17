# SORT Developer Documentation

This directory contains detailed technical documentation for developers working on SORT (Self-Assessment of Organisational Readiness Tool).

## Getting Started Guide

### 👋 New to SORT?

Follow this recommended reading order:

1. **[architecture.md](architecture.md)** - Understand the system architecture with visual diagrams
2. **[data-model.md](data-model.md)** - Learn the database structure and entity relationships
3. **[testing.md](testing.md)** - Set up your test environment and run tests

### 🔧 Ready to Contribute?

Once you've read the above, check out:

- **[../CONTRIBUTING.md](../CONTRIBUTING.md)** - Contribution guidelines and PR process
- **[../RELEASING.md](../RELEASING.md)** - Semantic versioning and automated release process

### 🚀 Deploying to Production?

Required reading for deployment:

1. **[deployment.md](deployment.md)** - Server configuration, systemd setup, and production settings
2. **[troubleshooting.md](troubleshooting.md)** - Common issues and recovery procedures

## Complete Documentation Index

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [architecture.md](architecture.md) | System architecture diagrams, design patterns, request flow, and technology stack | Understanding system design, planning new features, onboarding |
| [data-model.md](data-model.md) | Database schema, entity relationships, JSONField structures, and model properties | Working with models, writing migrations, querying data |
| [testing.md](testing.md) | Frontend/backend testing frameworks, factory patterns, and writing tests | Writing new tests, debugging test failures, CI/CD setup |
| [deployment.md](deployment.md) | Production deployment, server architecture, systemd configuration, and environment setup | Initial deployment, infrastructure changes, server maintenance |
| [troubleshooting.md](troubleshooting.md) | Debugging techniques, log analysis, common issues, and recovery procedures | Investigating bugs, production incidents, error diagnosis |
| [data-management.md](data-management.md) | Data export commands, CSV generation, and database management utilities | Exporting survey data, generating reports, data migrations |
| [invitations.md](invitations.md) | Token-based invitation system, email workflows, and invitation management | Implementing invitation features, debugging invite issues |
| [templates.md](templates.md) | Icon system, template resources, and UI component guidelines | Adding icons, updating templates, UI consistency |

## Documentation by Task

### 🏗️ Architecture & Design

**Understanding the system:**
- [architecture.md](architecture.md) - Overall system architecture with Mermaid diagrams
- [data-model.md](data-model.md) - Database design and relationships
- [../CLAUDE.md#code-architecture](../CLAUDE.md#code-architecture) - Service layer pattern and app structure

**Key concepts:**
- **Service Layer Pattern**: All business logic in service classes with automatic permission checking
- **Multi-Tenancy**: Organisation-based isolation with RBAC (ADMIN vs PROJECT_MANAGER roles)
- **Configuration-Driven Surveys**: JSON-defined survey structures stored in `survey_config` field
- **Hybrid Rendering**: Django templates + embedded Svelte components via Vite

### 💻 Development Workflow

**Setting up your environment:**
1. Follow setup instructions in [../CLAUDE.md#development-setup](../CLAUDE.md#development-setup)
2. Read [testing.md](testing.md) to configure test environment
3. Review [../CLAUDE.md#accessibility-compliance](../CLAUDE.md#accessibility-compliance) for WCAG requirements

**Making changes:**
1. Create a feature branch from `main`
2. Write code following patterns in [architecture.md](architecture.md)
3. Write tests using patterns from [testing.md](testing.md)
4. Run `make check` and `make test` before committing
5. Create PR and ensure accessibility checklist is complete
6. Use conventional commits for automated versioning (see [../RELEASING.md](../RELEASING.md))

**Common development tasks:**
- **Adding a new model**: Review [data-model.md](data-model.md) for naming conventions and patterns
- **Creating a service method**: Follow service layer pattern in [architecture.md](architecture.md#key-design-patterns)
- **Building UI components**: Check accessibility requirements in [../CLAUDE.md#accessibility-compliance](../CLAUDE.md#accessibility-compliance)
- **Writing tests**: Use factories and base classes documented in [testing.md](testing.md)

### 🧪 Testing & Quality

**Running tests:**
```bash
make test              # Run all tests
make lint              # Check code quality
make check             # Django system checks + migration verification
```

**Writing tests:**
- [testing.md](testing.md) - Comprehensive testing guide with examples
- [../CLAUDE.md#testing-utilities](../CLAUDE.md#testing-utilities) - Test base classes and factories

**Debugging:**
- [troubleshooting.md](troubleshooting.md) - Common issues and solutions
- [../CLAUDE.md#useful-management-commands](../CLAUDE.md#useful-management-commands) - Debug commands

### 🚀 Deployment & Operations

**Initial deployment:**
1. [deployment.md](deployment.md) - Complete deployment guide
2. [../CLAUDE.md#environment-variables](../CLAUDE.md#environment-variables) - Required configuration
3. [data-management.md](data-management.md) - Loading initial data

**Ongoing operations:**
- **Monitoring logs**: See [troubleshooting.md](troubleshooting.md#log-analysis)
- **Exporting data**: Use commands in [data-management.md](data-management.md)
- **Managing invitations**: Follow workflows in [invitations.md](invitations.md)
- **Troubleshooting issues**: Start with [troubleshooting.md](troubleshooting.md)

**Release process:**
- [../RELEASING.md](../RELEASING.md) - Automated semantic versioning
- Merges to `main` with `feat:` or `fix:` commits trigger releases automatically
- No manual version bumping needed!

### 📋 Feature-Specific Documentation

**Survey System:**
- Survey architecture: [architecture.md](architecture.md#data-model-architecture)
- Survey models: [data-model.md](data-model.md#survey-app-models)
- Survey config structure: [../CLAUDE.md#model-architecture](../CLAUDE.md#model-architecture)

**Permission System:**
- Permission flow: [architecture.md](architecture.md#permission-architecture)
- Service layer permissions: [../CLAUDE.md#service-layer-pattern](../CLAUDE.md#service-layer-pattern)
- Role definitions: [data-model.md](data-model.md#organisationmembership)

**File Uploads:**
- Evidence files: [data-model.md](data-model.md#surveyevidencesection)
- File management: [data-management.md](data-management.md)
- Upload locations: [../CLAUDE.md#important-notes](../CLAUDE.md#important-notes)

**Invitation System:**
- Complete guide: [invitations.md](invitations.md)
- Token generation: [data-model.md](data-model.md#invitation)
- Email workflows: [invitations.md](invitations.md#email-workflows)

### ♿ Accessibility Standards

**Mandatory reading for all contributors:**
- [../CLAUDE.md#accessibility-compliance](../CLAUDE.md#accessibility-compliance) - Complete WCAG 2.1 AA guide

**Key requirements:**
- Semantic HTML (use `<button>`, not `<div onclick>`)
- Keyboard navigation (all features accessible without mouse)
- Form accessibility (labels, error messages, ARIA attributes)
- Color contrast (4.5:1 for normal text, 3:1 for large text)
- Screen reader testing (NVDA, VoiceOver, or TalkBack)

**Before submitting PR:**
- Run automated accessibility checks (GitHub Actions)
- Complete manual accessibility checklist in PR description
- Test with keyboard navigation and screen reader

## Quick Reference

### Project Structure
```
SORT/
├── home/              # Authentication, organisations, projects
│   ├── models.py      # User, Organisation, OrganisationMembership, Project
│   ├── services/      # OrganisationService, ProjectService
│   └── views.py
├── survey/            # Surveys, responses, evidence, invitations
│   ├── models.py      # Survey, SurveyResponse, Invitation, Evidence
│   ├── services/      # SurveyService
│   └── views.py
├── ui_components/     # Svelte components
│   └── src/
├── data/              # JSON survey configurations
│   └── readiness_descriptions/
├── docs/              # You are here!
├── SORT/test/         # Test utilities (factories, base classes)
└── static/            # Built frontend assets
```

### Key Concepts

| Concept | Description | Documentation |
|---------|-------------|---------------|
| Service Layer | Business logic in service classes with automatic permission checking | [architecture.md](architecture.md#key-design-patterns) |
| RBAC | Role-based access control (ADMIN vs PROJECT_MANAGER) | [architecture.md](architecture.md#permission-architecture) |
| Multi-Tenancy | Organisation-based data isolation | [data-model.md](data-model.md) |
| Hybrid Rendering | Django templates + Svelte components | [architecture.md](architecture.md#frontend-architecture) |
| Config-Driven Surveys | JSON survey definitions in `survey_config` field | [../CLAUDE.md#model-architecture](../CLAUDE.md#model-architecture) |
| Token Invitations | Unique tokens for anonymous survey responses | [invitations.md](invitations.md) |

### External Resources

- **Main README**: [../README.md](../README.md) - Project overview and quick start
- **Contributing Guide**: [../CONTRIBUTING.md](../CONTRIBUTING.md) - PR workflow and standards
- **Release Guide**: [../RELEASING.md](../RELEASING.md) - Semantic versioning with semantic-release
- **Project Instructions**: [../CLAUDE.md](../CLAUDE.md) - Comprehensive development guide

## Need Help?

### Documentation Issues
- Documentation unclear or outdated? Open an issue on GitHub
- Missing documentation? Submit a PR adding the missing content

### Development Questions
1. Check [troubleshooting.md](troubleshooting.md) for common issues
2. Review relevant documentation above
3. Ask the team on Slack: #sort-dev
4. Open a GitHub issue if it's a bug or feature request

### Production Issues
1. Check logs (see [troubleshooting.md](troubleshooting.md#log-analysis))
2. Review [deployment.md](deployment.md) for configuration issues
3. Follow incident response procedures in [troubleshooting.md](troubleshooting.md#recovery-procedures)
4. Escalate to infrastructure team if needed

---

**Last Updated**: 2026-02-17

**Maintainers**: See [../CONTRIBUTING.md](../CONTRIBUTING.md) for current maintainers
