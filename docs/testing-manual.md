# Manual testing checklist

This document contains a systematic guide to testing all the functionality in the app.

Please **document any bugs** found with details, screenshots and reproduction steps.

## Authentication & User Management

### Registration
- [ ] Navigate to registration page
- [ ] Submit empty form → validation errors appear
- [ ] Submit invalid email → validation error shown
- [ ] Submit mismatched passwords → validation error shown
- [ ] Register with valid details → success, user logged in
- [ ] Verify confirmation email sent (check console in dev mode)
- [ ] Attempt to register with existing email → error shown

### Login
- [ ] Navigate to login page
- [ ] Submit empty form → validation errors appear
- [ ] Submit incorrect credentials → error message shown
- [ ] Submit correct credentials → logged in, redirected to dashboard
- [ ] Verify "Remember me" checkbox persists session
- [ ] Test logout → redirected to home/login page

### Password Reset
- [ ] Click "Forgot password" link
- [ ] Submit invalid email → error or no indication (security)
- [ ] Submit valid email → reset email sent (check console)
- [ ] Click reset link in email → redirected to password reset form
- [ ] Submit new password → success message, can log in with new password
- [ ] Try to reuse same reset link → expired/invalid link message

## Organisation Management

### Creating Organisation (as new user)
- [ ] Navigate to "Create Organisation" page
- [ ] Submit empty form → validation errors
- [ ] Create organisation with valid name → success, redirected
- [ ] Verify user is assigned ADMIN role for the organisation
- [ ] Check organisation appears in "My Organisation" section

### Managing Organisation Members (as ADMIN)
- [ ] Navigate to organisation member management page
- [ ] Invite new member with email address
- [ ] Verify invitation email sent (check console)
- [ ] Invite existing user email → check behaviour
- [ ] Change member role from PROJECT_MANAGER to ADMIN
- [ ] Change member role from ADMIN to PROJECT_MANAGER
- [ ] Remove member from organisation
- [ ] Verify removed member loses access

### Organisation Permissions (as PROJECT_MANAGER)
- [ ] Log in as user with PROJECT_MANAGER role
- [ ] Attempt to access organisation settings → denied/hidden
- [ ] Attempt to invite members → denied/hidden
- [ ] Attempt to remove members → denied/hidden
- [ ] Verify can still view organisation name/details

## Project Management

### Creating Projects (as ADMIN)
- [ ] Navigate to "Create Project" page
- [ ] Submit empty form → validation errors
- [ ] Create project with valid name and description → success
- [ ] Verify project appears in projects list
- [ ] Create multiple projects → all appear in list
- [ ] Verify project reference numbers are sequential

### Editing Projects (as ADMIN)
- [ ] Navigate to project details page
- [ ] Click "Edit" button
- [ ] Update project name and description → changes saved
- [ ] Clear required fields → validation errors
- [ ] Cancel editing → no changes saved

### Deleting Projects (as ADMIN)
- [ ] Navigate to project details page
- [ ] Click "Delete" button
- [ ] Confirmation dialog appears
- [ ] Cancel deletion → project remains
- [ ] Confirm deletion → project removed from list
- [ ] Verify associated surveys are also deleted/handled

### Project Permissions (as PROJECT_MANAGER)
- [ ] Log in as PROJECT_MANAGER assigned to specific project
- [ ] Verify can view assigned project details
- [ ] Verify can edit assigned project
- [ ] Verify can create surveys within assigned project
- [ ] Attempt to view unassigned project → denied
- [ ] Attempt to edit unassigned project → denied

## Survey Configuration

### Creating Surveys
- [ ] Navigate to project → "Create Survey" button
- [ ] Submit empty form → validation errors
- [ ] Create survey with valid title → success
- [ ] Verify survey reference number generated (SURVEY-000001)
- [ ] Verify survey appears in project's survey list
- [ ] Verify survey status is "Draft" initially

### Configuring Survey Settings
- [ ] Navigate to survey configuration page
- [ ] Enable/disable consent section → changes saved
- [ ] Enable/disable demography section → changes saved
- [ ] Add custom demographic questions → saved correctly
- [ ] Configure maturity rating scales → changes saved
- [ ] Preview survey → configuration reflected correctly

### Survey Lifecycle
- [ ] Publish survey (Draft → Active) → status changes
- [ ] Verify public response link becomes available
- [ ] Verify QR code generated for survey
- [ ] Archive survey (Active → Archived) → status changes
- [ ] Verify archived survey cannot accept new responses
- [ ] Attempt to edit active survey → warning/restriction shown

## Survey Responses (Public Token-Based)

### Accessing Survey
- [ ] Copy public survey response link (with token)
- [ ] Open link in private/incognito browser (not logged in)
- [ ] Verify survey loads without authentication
- [ ] Verify survey title and description shown
- [ ] Attempt invalid token URL → error page shown

### Completing Survey - Consent Section
- [ ] Verify consent checkbox present
- [ ] Attempt to proceed without consent → validation error
- [ ] Check consent box → can proceed to next section

### Completing Survey - Demography Section
- [ ] Fill in demographic questions
- [ ] Submit with missing required fields → validation errors
- [ ] Submit with invalid data → validation errors
- [ ] Submit valid data → proceed to main survey

### Completing Survey - Main Questions
- [ ] Answer Likert scale questions → selections saved
- [ ] Answer text input questions → text saved
- [ ] Answer multiple choice questions → selections saved
- [ ] Test navigation: Next/Previous buttons work correctly
- [ ] Leave questions blank → validation on submit (if required)
- [ ] Verify progress indicator updates correctly

### Survey Submission
- [ ] Submit incomplete survey → validation errors shown
- [ ] Submit complete survey → success message displayed
- [ ] Verify response saved in database (check via admin)
- [ ] Attempt to access same token again → show "already submitted" or allow viewing
- [ ] Verify response appears in survey response list (for survey owner)

## Evidence and Improvement Plan Sections

### Evidence Section
- [ ] Navigate to survey → Evidence section
- [ ] Add evidence for a specific survey section
- [ ] Upload file as evidence → file saved correctly
- [ ] Add text description to evidence → saved correctly
- [ ] Edit existing evidence entry → changes saved
- [ ] Delete evidence entry → confirmation, then removed
- [ ] Verify evidence indexed by section_id correctly

### Improvement Plan Section
- [ ] Navigate to survey → Improvement Plan section
- [ ] Add improvement plan for a specific section
- [ ] Enter text content → saved correctly
- [ ] Upload supporting files → files saved correctly
- [ ] Edit existing improvement plan → changes saved
- [ ] Delete improvement plan → confirmation, then removed

### File Uploads
- [ ] Upload valid file types (PDF, DOCX, images) → success
- [ ] Attempt to upload invalid file type → error shown
- [ ] Attempt to upload oversized file → error shown
- [ ] Verify uploaded files appear in file list
- [ ] Download uploaded file → file downloads correctly
- [ ] Delete uploaded file → confirmation, then removed
- [ ] Verify orphaned files cleaned up (use management command)

## Survey Results and Exports

### Viewing Results
- [ ] Navigate to survey results page
- [ ] Verify response count shown correctly
- [ ] View individual response details
- [ ] Verify all submitted answers displayed correctly
- [ ] Check Likert scale answers expanded correctly
- [ ] Verify demography data shown (if collected)

### CSV Export
- [ ] Click "Export to CSV" button
- [ ] Verify CSV file downloads
- [ ] Open CSV in spreadsheet software
- [ ] Verify headers correct
- [ ] Verify all responses included
- [ ] Verify nested Likert answers flattened correctly
- [ ] Check special characters handled correctly (commas, quotes)

### Excel Export (if implemented)
- [ ] Click "Export to Excel" button
- [ ] Verify .xlsx file downloads
- [ ] Open file in Excel/LibreOffice
- [ ] Verify formatting preserved
- [ ] Verify charts/visualizations included (if applicable)

### Usage Report
- [ ] Run `python manage.py usage` command
- [ ] Verify report generates correctly
- [ ] Check survey usage statistics accurate

## Invitation System

### Creating Invitations
- [ ] Navigate to survey → Invitations section
- [ ] Create invitation with email address
- [ ] Verify unique token generated
- [ ] Verify invitation email sent (check console)
- [ ] Create multiple invitations → unique tokens for each

### Using Invitations
- [ ] Copy invitation link from email
- [ ] Open in browser (not logged in)
- [ ] Verify redirected to survey response form
- [ ] Complete and submit survey
- [ ] Verify invitation marked as "used/completed"

### Managing Invitations
- [ ] View invitation list for survey
- [ ] Check invitation status (Sent, Opened, Completed)
- [ ] Resend invitation → new email sent
- [ ] Revoke invitation → token invalidated
- [ ] Attempt to use revoked invitation → error shown

## Accessibility Testing (WCAG 2.1 AA)

### Keyboard Navigation
- [ ] Use Tab key to navigate through all pages
- [ ] Verify focus indicators visible (3:1 contrast)
- [ ] Verify logical tab order (left-to-right, top-to-bottom)
- [ ] Test form submission using Enter key
- [ ] Test button clicks using Spacebar
- [ ] Test modal/dialog keyboard trapping (Tab stays within)
- [ ] Test Escape key closes modals/dialogs

### Screen Reader Testing (NVDA/VoiceOver)
- [ ] Navigate forms → all labels announced correctly
- [ ] Required fields indicated with "required" announcement
- [ ] Error messages read aloud when form invalid
- [ ] Button purposes announced correctly
- [ ] Landmark regions (nav, main, footer) identified
- [ ] Image alt text announced
- [ ] Link purposes clear from text alone

### Form Accessibility
- [ ] All inputs have associated `<label>` elements
- [ ] Required fields marked with visual indicator + aria-label
- [ ] Error messages linked via `aria-describedby`
- [ ] Help text associated with inputs
- [ ] Fieldsets used for grouped inputs (radio buttons)
- [ ] Form validation provides clear feedback

### Colour Contrast
- [ ] Check all text meets 4.5:1 contrast ratio (normal text)
- [ ] Check large text meets 3:1 contrast ratio
- [ ] Check button/link states have sufficient contrast
- [ ] Verify error messages not indicated by color alone
- [ ] Test with WAVE browser extension → no contrast errors
- [ ] Test with Axe DevTools → no critical violations

### Images and Icons
- [ ] All meaningful images have descriptive alt text
- [ ] Decorative images have `alt=""`
- [ ] Icon-only buttons have `aria-label`
- [ ] Charts have detailed descriptions (`aria-describedby`)

### Mobile Accessibility
- [ ] Test with mobile screen reader (TalkBack/VoiceOver)
- [ ] Touch targets minimum 44x44px
- [ ] Zoom to 200% → no horizontal scrolling, all content visible
- [ ] Test with Android Accessibility Scanner

## Permission and Security Testing

### Role-Based Access Control
- [ ] **ADMIN**: Can access all organisation features
- [ ] **ADMIN**: Can edit all projects in organisation
- [ ] **ADMIN**: Can delete projects and surveys
- [ ] **PROJECT_MANAGER**: Can access assigned projects only
- [ ] **PROJECT_MANAGER**: Cannot access organisation settings
- [ ] **PROJECT_MANAGER**: Cannot delete other managers' projects

### Direct URL Access (Unauthorised)
- [ ] Attempt to access `/projects/<id>/` without permission → 403/404
- [ ] Attempt to access `/survey/<pk>/` without permission → 403/404
- [ ] Attempt to edit organisation URL without ADMIN role → denied
- [ ] Attempt to access other organisation's projects → denied

### Token-Based Access
- [ ] Valid survey token allows response submission
- [ ] Invalid/expired token shows error page
- [ ] Token cannot be used to access admin features
- [ ] Token access does not grant authentication

### CSRF Protection
- [ ] Verify all POST forms include `{% csrf_token %}`
- [ ] Test form submission without CSRF token → 403 error
- [ ] Verify AJAX requests include CSRF token

## Performance and Edge Cases

### Large Data Sets
- [ ] Create 50+ responses for a survey → page loads within 3s
- [ ] Export 100+ responses to CSV → completes without timeout
- [ ] Upload 10+ evidence files → all saved correctly
- [ ] View organisation with 20+ projects → list renders correctly

### Edge Cases
- [ ] Enter extremely long text in text fields → truncated/validated
- [ ] Enter special characters in fields (quotes, commas, unicode)
- [ ] Submit form multiple times rapidly → no duplicates created
- [ ] Delete project with active surveys → handled gracefully
- [ ] Delete user with organisation memberships → handled gracefully

### Error Handling
- [ ] Trigger 404 page (invalid URL) → custom error page shown
- [ ] Trigger 403 page (no permission) → custom error page shown
- [ ] Trigger 500 error (server error) → custom error page shown
- [ ] Test with database down → graceful error handling

## Data Integrity

### Survey Configuration
- [ ] Modify survey config JSON → changes reflected in responses
- [ ] Add new question to config → appears in response form
- [ ] Remove question from config → old responses still viewable
- [ ] Change question type → existing responses validated correctly

### Cascade Deletions
- [ ] Delete organisation → all projects deleted
- [ ] Delete project → all surveys deleted
- [ ] Delete survey → all responses deleted
- [ ] Delete user → organisation memberships removed

### Data Validation
- [ ] Submit invalid JSON in survey answers → rejected
- [ ] Upload file with malicious extension → rejected
- [ ] Enter SQL injection in text fields → sanitized
- [ ] Enter XSS payload in text fields → escaped/sanitized

## Static Files and Assets

### Production Build
- [ ] Run `npm run build` → builds complete without errors
- [ ] Run `python manage.py collectstatic` → collects without errors
- [ ] Verify static files served correctly
- [ ] Verify Vite manifest.json referenced correctly

### Asset Loading
- [ ] Check all images load correctly
- [ ] Check CSS styles applied correctly
- [ ] Check JavaScript components initialize
- [ ] Verify no 404 errors in browser console
- [ ] Test with slow network → assets load progressively

## Email Functionality

### Email Templates
- [ ] Registration confirmation email contains correct link
- [ ] Password reset email contains valid reset link
- [ ] Invitation email contains correct survey link
- [ ] All emails have plain text and HTML versions

### Email Sending (Dev Mode)
- [ ] Emails appear in console (EMAIL_BACKEND=console)
- [ ] Email content formatted correctly
- [ ] Email links work when copied to browser

## Management Commands

### Data Management
- [ ] Run `python manage.py clear_orphaned_files` → orphaned files removed
- [ ] Run `python manage.py usage` → report generated
- [ ] Run `python manage.py csv` → CSV export generated
- [ ] Run `python manage.py migrate` → no errors, applies migrations

### Data Loading
- [ ] Load fixtures: `python manage.py loaddata ./data/*.json`
- [ ] Verify test users created correctly
- [ ] Verify test organisations and projects created
- [ ] Verify test survey configs loaded

## Regression Testing Scenarios

### Common User Flows (End-to-End)
**Flow 1: New User Creates Organisation and Survey**
- [ ] Register new account
- [ ] Create organisation
- [ ] Create project
- [ ] Create survey
- [ ] Configure survey settings
- [ ] Publish survey
- [ ] Copy public link and submit response (incognito)
- [ ] View results and export CSV

**Flow 2: Admin Invites Member to Project**
- [ ] Log in as ADMIN
- [ ] Invite new member with PROJECT_MANAGER role
- [ ] Member accepts invitation (check email)
- [ ] Member logs in and views assigned project
- [ ] Member creates survey in project
- [ ] ADMIN reviews member's survey

**Flow 3: Respondent Completes Full Survey**
- [ ] Click survey invitation link
- [ ] Provide consent
- [ ] Complete demography section
- [ ] Answer all maturity rating questions
- [ ] Provide text comments
- [ ] Submit survey
- [ ] See confirmation message
