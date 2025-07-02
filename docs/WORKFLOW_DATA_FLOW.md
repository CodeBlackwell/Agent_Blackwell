# Workflow Data Flow Documentation

This document provides detailed information about data flow between agents in different workflows.

## TDD Workflow

**Description:** Test-Driven Development workflow (planner → designer → test_writer → coder → reviewer)

![TDD Workflow Visualization](workflow_visualizations/tdd_workflow.png)

### Data Flow Details

#### input → planner

**Schema:**

```
requirements: str
workflow: WorkflowStep
team_members: list
```

**Description:** Input schema for the coding team tool

---

#### planner → designer

**Schema:**

```
team_member: TeamMember
output: str
```

**Description:** Result from a single team member

---

#### designer → test_writer

**Schema:**

```
team_member: TeamMember
output: str
```

**Description:** Result from a single team member

---

#### test_writer → coder

**Schema:**

```
team_member: TeamMember
output: str
```

**Description:** Result from a single team member

---

#### coder → reviewer

**Schema:**

```
team_member: TeamMember
output: str
```

**Description:** Result from a single team member

---

## Full Workflow

**Description:** Full development workflow (planner → designer → coder → reviewer)

![Full Workflow Visualization](workflow_visualizations/full_workflow.png)

### Data Flow Details

#### input → planner

**Schema:**

```
requirements: str
workflow: WorkflowStep
team_members: list
```

**Description:** Input schema for the coding team tool

---

#### planner → designer

**Schema:**

```
team_member: TeamMember
output: str
```

**Description:** Result from a single team member

---

#### designer → coder

**Schema:**

```
team_member: TeamMember
output: str
```

**Description:** Result from a single team member

---

#### coder → reviewer

**Schema:**

```
team_member: TeamMember
output: str
```

**Description:** Result from a single team member

---

## Individual Workflow

**Description:** Individual workflow step execution (single agent)

![Individual Workflow Visualization](workflow_visualizations/individual_workflow.png)

### Data Flow Details

## Complete Workflow System Overview

This diagram shows the entire workflow system architecture and all possible agent interactions:

![Workflow System Overview](workflow_visualizations/workflow_overview.png)

