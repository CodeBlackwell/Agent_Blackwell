# Execution Report CSV Format

## Overview

The execution report CSV format provides a compressed, tabular view of workflow execution data, achieving **80-99% compression** compared to JSON format while maintaining all critical information.

## CSV File Structure

### 1. **execution_summary_{session_id}.csv**
High-level workflow metrics in a single row:
- `session_id`: Unique workflow identifier
- `start_time`, `end_time`: Workflow timing
- `duration_ms`: Total execution time
- `workflow_type`: Type of workflow executed
- `requirements`: Original user requirements
- `total_events`, `agent_interactions`: Activity metrics
- `commands_executed`, `tests_run`: Execution metrics
- `files_created`, `files_modified`: Output metrics
- `success`, `error`: Final status

### 2. **agent_exchanges_{session_id}.csv**
Detailed agent interaction log:
- `sequence`: Order of execution
- `agent`, `phase`, `iteration`: Agent context
- `timestamp`, `duration_ms`: Timing data
- `task`: Specific task performed
- `success`, `error`: Result status
- `files_created`, `response_type`: Output details

### 3. **execution_report_{session_id}.csv** (Combined)
Comprehensive single-file view combining:
- All agent exchanges in sequence
- Summary metrics in first row
- Complete workflow timeline

### 4. **events_{session_id}.csv**
Workflow event timeline:
- `timestamp`: When event occurred
- `event_type`: Type of event
- `phase`, `agent`: Context
- `description`: Human-readable description
- `data`: Additional event data (JSON)

### 5. **files_{session_id}.csv**
File operation tracking:
- `file_path`: File affected
- `operation`: created/modified/exists
- `agent`, `phase`: Who/when
- `timestamp`: When operated on

### 6. **errors_{session_id}.csv**
Error tracking (if any):
- `error_type`: workflow_error/agent_error
- `agent`, `phase`: Error context
- `error_message`: Error description
- `details`: Additional context

## Benefits

1. **Massive Compression**: 80-99% smaller than JSON
2. **Excel/Sheets Compatible**: Open directly in spreadsheet apps
3. **Query-Friendly**: Easy to filter, sort, and analyze
4. **Time-Series Ready**: Structured for performance analysis
5. **Multiple Views**: Different CSVs for different analysis needs

## Example Usage

```python
from utils.execution_report_csv_converter import convert_execution_report

# Convert JSON report to CSV
csv_files = convert_execution_report("execution_report.json")

# Access specific CSV files
summary_df = pd.read_csv(csv_files['summary'])
exchanges_df = pd.read_csv(csv_files['exchanges'])
```

## Automatic Generation

CSV files are automatically generated alongside JSON reports when workflows complete. Look for them in the same directory as your execution report JSON files.