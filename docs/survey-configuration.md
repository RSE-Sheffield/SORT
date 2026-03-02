# Survey Configuration

The SORT surveys have three types of configuration components:

1. **Consent questions** - Welcome message and consent agreement
2. **SORT questions** - Core assessment questions organised into sections A to D with Likert scale responses (0-4)
3. **Demographics questions** - Participant information (age, gender, job title, qualifications, etc.)

All questions are defined in JSON configuration files located in `data/survey_config/`.

## Survey Structure

When a survey is initialised, it combines three configuration files into a single `survey_config` JSON field:

```
survey_config = consent_config + sort_config + demography_config
```

This merged configuration is stored in the `Survey.survey_config` JSONField and contains all sections and questions for that survey.

## Target Audience Types

SORT-online supports multiple target audiences, each with tailored questions:

| Audience Type | Label | Description |
|--------------|-------|-------------|
| `NMAHPs` | Nurses, Midwives and Allied Health Professionals (NMAHPs) | Default option for mixed professional groups |
| `Nurses` | Nurses | Nursing-specific questions and demographics |
| `Midwives` | Midwives | Midwifery-specific questions and demographics |
| `Nurses & Midwives` | Nurses and Midwives | Combined nursing and midwifery focus |
| `AHP` | Allied Health Professionals (AHP) | AHP-specific questions (physiotherapists, occupational therapists, etc.) |
| `Generic` | Generic (Other Professional Groups) | General questions suitable for any professional group in healthcare/research settings |

The target audience is selected when creating a new survey and determines which configuration files are loaded.

## Configuration Files

### Consent Configuration

**File**: `data/survey_config/consent_only_config.json`

The consent configuration is shared across all audience types. It contains:
- Welcome message
- Data sharing agreement
- Consent checkbox

This file is referenced in settings as `CONSENT_TEMPLATE`.

### SORT Questions Configuration

**Files**: `data/survey_config/sort_only_config_<audience>.json`

Examples:
- `sort_only_config_nurses.json`
- `sort_only_config_midwives.json`
- `sort_only_config_nmahps.json`
- `sort_only_config_ahp.json`
- `sort_only_config_generic.json`

These files contain the core SORT assessment questions organised into sections:

- **Section A: Releasing Potential** - Talent spotting, mentorship, research support infrastructure
- **Section B: Embedding Research** - Research culture, PPI involvement, professional development
- **Section C: Digitally Enabled Research** - Digital tools, online platforms, technology infrastructure
- **Section D: Research Infrastructure** - Physical resources, dedicated staff, management support

Each section uses Likert scale questions with options from 0 (Not yet planned) to 4 (Established).

**Generic vs. Profession-Specific Questions:**
- Generic questions use neutral language ("staff", "organisation") suitable for any professional group
- Profession-specific questions reference "nurses", "midwives", etc. and may include profession-specific concepts

### Demographics Configuration

**Files**: `data/survey_config/demography_only_config_<audience>.json`

Examples:
- `demography_only_config_nurses.json`
- `demography_only_config_midwives.json`
- `demography_only_config_nmahps.json`
- `demography_only_config_ahp.json`
- `demography_only_config_generic.json`

Demographics questions collect participant information:

**Common fields** (all audience types):
- Age (integer, 18-100)
- Gender (Male, Female, Non-binary, Prefer not to say)
- Years working in current organisation (integer, 0-100)
- Job title (free text)
- Highest qualification (No qualification, Diploma, Degree, Masters, PhD/Doctorate, Other)
- Years qualified (integer, 0-100)
- Ethnicity (multiple options)

**Profession-specific fields** (varies by audience):
- Current pay band (NHS band structure: Band 2-9)
- Profession/role (e.g., for Nurses: Registered Staff Nurse, Senior Nurse, Specialist Nurse, Advanced Nurse Practitioner)

**Generic demographics:**
- Omits profession-specific fields like NHS pay bands
- Uses generic job title field instead of profession dropdown
- Suitable for non-NHS organisations or mixed professional groups

### Field Configuration Format

Each field in the JSON configuration follows this structure:

```json
{
  "type": "radio|text|textarea|likert|checkbox|select",
  "label": "Question text",
  "description": "Additional context (optional)",
  "required": true|false,
  "sublabels": [],  // For likert type, array of sub-questions
  "options": [],    // For radio/select/likert, array of choice values
  "textType": "PLAIN_TEXT|INTEGER_TEXT|DECIMALS_TEXT|EMAIL_TEXT",  // For text type
  "minNumValue": 0,      // For numeric text types
  "maxNumValue": 100,    // For numeric text types
  "maxNumChar": 500,     // For text/textarea
  "disabled": false,
  "readOnly": true       // Makes field read-only in the UI
}
```

## Settings Configuration

The available audience types and their configuration files are defined in `SORT/settings.py`:

```python
SURVEY_TEMPLATE_DIR = BASE_DIR / "data/survey_config"

SURVEY_TEMPLATES = {
    "Nurses": "sort_only_config_nurses.json",
    "Midwives": "sort_only_config_midwives.json",
    "NMAHPs": "sort_only_config_nmahps.json",
    "Nurses & Midwives": "sort_only_config_nurses_midwives.json",
    "AHP": "sort_only_config_ahp.json",
    "Generic": "sort_only_config_generic.json",
}

DEMOGRAPHY_TEMPLATES = {
    "Nurses": "demography_only_config_nurses.json",
    "Midwives": "demography_only_config_midwives.json",
    "NMAHPs": "demography_only_config_nmahps.json",
    "Nurses & Midwives": "demography_only_config_nurses_midwives.json",
    "AHP": "demography_only_config_ahp.json",
    "Generic": "demography_only_config_generic.json",
}

CONSENT_TEMPLATE = "consent_only_config.json"
```

## Editing Survey Questions

### Modifying Existing Questions

1. Locate the appropriate configuration file in `data/survey_config/`
2. Edit the JSON structure following the field format described above
3. Validate JSON syntax: `python -m json.tool <filename>.json`
4. Test with a new survey to ensure questions render correctly

### Adding a New Audience Type

To add a new target audience:

1. **Create configuration files**:
   - Create `data/survey_config/sort_only_config_<new_audience>.json`
   - Create `data/survey_config/demography_only_config_<new_audience>.json`

2. **Update the model** in `survey/models.py`:
   ```python
   class Profession(models.TextChoices):
       NEW_AUDIENCE = "NewAudience", "Display Label"
   ```

3. **Update settings** in `SORT/settings.py`:
   ```python
   SURVEY_TEMPLATES = {
       ...
       "NewAudience": "sort_only_config_new_audience.json",
   }

   DEMOGRAPHY_TEMPLATES = {
       ...
       "NewAudience": "demography_only_config_new_audience.json",
   }
   ```

4. **Create and apply migration**:
   ```bash
   python manage.py makemigrations survey
   python manage.py migrate
   ```

5. **Test the new configuration**:
   - Create a test survey with the new audience type
   - Verify all questions load correctly
   - Generate mock responses to test data export

## Model Integration

The `Survey` model provides several properties for accessing configuration:

- `survey.survey_body_path` - The selected audience type (e.g., "Generic", "Nurses")
- `survey.template_filename` - SORT questions config filename
- `survey.demography_config_filename` - Demographics config filename
- `survey.sort_config` - Loaded SORT questions configuration
- `survey.demography_config_default` - Default demographics configuration
- `survey.consent_config_default` - Default consent configuration
- `survey.sections` - All merged sections (consent + SORT + demographics)
- `survey.fields` - Flattened list of all field labels

When a survey is initialised via `survey.initialise()`, the three configuration files are merged and stored in `survey.survey_config`.

## Customisation in the UI

Users can customise demographics questions via the survey configuration interface:

1. When creating a survey, the default demographics for the selected audience are loaded
2. Users can modify demographics questions through the survey configuration page
3. SORT questions (sections A-D) are fixed and cannot be modified by users
4. Consent questions are fixed across all surveys

This allows organisations to adapt demographic collection to their specific needs while maintaining consistency in the core SORT assessment questions.

## Validation and Testing

When modifying configuration files:

1. **Validate JSON syntax**:
   ```bash
   python -m json.tool data/survey_config/sort_only_config_<audience>.json
   ```

2. **Run model tests**:
   ```bash
   python manage.py test survey.tests.test_models --failfast
   ```

3. **Test survey initialisation**:
   - Create a new survey via the UI
   - Verify all questions render correctly
   - Test response submission
   - Check CSV/Excel export includes all fields

4. **Generate mock responses**:
   ```python
   survey.generate_mock_responses(num_responses=10)
   ```

   This validates that all field types can accept generated data.

## Best Practices

1. **Maintain consistency**: Keep similar field structures across different audience types
2. **Validate JSON**: Always validate JSON syntax before committing changes
3. **Test thoroughly**: Create test surveys and generate mock responses after changes
4. **Document changes**: Update this documentation when adding new audience types or fields
5. **Use descriptive labels**: Question labels should be clear and concise
6. **Consider accessibility**: Ensure questions are WCAG 2.1 AA compliant when rendered
7. **Preserve data structure**: When modifying existing questions, consider impact on historical survey data
