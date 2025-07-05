# Incremental Workflow Unit Tests

This directory contains unit tests for the incremental workflow components.

## Tests

- `test_feature_parser.py` - Tests the feature parser that extracts implementation features from designer output
  - Tests parsing of FEATURE[N] format
  - Tests edge cases (no implementation plan, markdown format)
  - Verifies all features are correctly extracted with proper dependencies

## Running Tests

```bash
# From project root
python tests/unit/incremental/test_feature_parser.py

# Or using pytest
pytest tests/unit/incremental/
```