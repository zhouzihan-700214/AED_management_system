# AED Operations Control Center — Design Upgrade

## Product decision

The home page is no longer a module directory called **AED Management Hub**. It is now **AED Operations Control Center**, a working management surface for priority, progress, responsibility, exceptions, and direct action.

## What was removed

- oversized decorative Hero;
- background grid and floating orb;
- six large module-navigation cards;
- static Operating Model explanation;
- generic `SYSTEM ONLINE` label;
- top-level KPIs such as total AED count and map-ready percentage that did not indicate immediate action.

## What replaced it

### 1. Compact control header

A dark, restrained header shows:

- page purpose;
- latest source update;
- source warnings;
- direct `Report issue` and `Start PM` actions.

### 2. Management toolbar

The user can change:

- management view;
- month;
- assignee;
- search term.

Views:

```text
Overview | PM | Issues | Asset readiness
```

### 3. Context-sensitive KPIs

Metrics now change with the selected view. Examples include overdue PM, due-soon PM, open Issues, pending verification, unassigned work, expiring consumables, and incomplete master data.

### 4. Priority Work Queue

PM tasks, Issues, pending verification, consumable readiness, and data exceptions use one consistent queue model:

```text
Category | Priority | Item | Location | Due / Age | Owner | Status | Next Action
```

The queue is sorted by operational importance rather than source-file order.

### 5. Selected Item panel

Selecting a queue row updates the right-hand decision panel. It shows the relevant AED or Issue context and offers direct actions such as:

- Start PM checklist;
- Open PM planning;
- Open AED Master Data;
- Report Issue;
- Open Issue workflow.

### 6. Management summaries

The lower page shows:

- monthly PM completion;
- Issue pipeline;
- consumable and data readiness;
- recent operational activity;
- data-source health.

## Visual principles

```text
Dark control frame + light operational workspace
```

- Navy establishes system navigation and management context.
- Light surfaces support long-duration reading, tables and forms.
- Borders and surface depth replace excessive shadows.
- Status always uses words as well as colour.
- Spacing follows a consistent 4px / 8px scale.
- Large decorative motion is removed and reduced-motion preferences are supported.

## Business-rule correction

The previous project used two competing PM cycles:

- PM Planning: completion date + 6 months;
- PM checklist submission: service date + 12 months.

The new system uses `Next PM Date` as the shared operational source. Checklist submission calculates it from:

```text
Service Date + PM Interval Months
```

The default interval is 12 months and can be configured per AED.

## Main implementation files

Added:

- `services/dashboard_service.py`
- `ui/dashboard_components.py`
- `tests/test_dashboard_service.py`

Reworked:

- `views/dashboard.py`
- `services/pm_service.py`
- `services/aed_service.py`
- `services/issue_service.py`
- `views/pm_planning.py`
- `views/aed_management.py`
- `views/issues.py`
- `views/registry.py`
- `ui/styles.py`
- `ui/navigation.py`
- `app.py`

## Acceptance target

Within ten seconds of opening the application, the user should be able to identify:

- overdue AED maintenance;
- Issues that require follow-up;
- resolutions waiting for verification;
- unassigned work;
- consumables approaching expiry;
- incomplete or implausible data;
- the next available action for the selected item.
