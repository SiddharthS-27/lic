# Test Suite for lic CLI

This directory contains comprehensive test cases for the lic CLI tool.

## Test Coverage

### 1. **TestGetGitName** (3 tests)
- ✅ Successful git name retrieval
- ✅ Failure when git is not configured
- ✅ Exception handling when git is not found

### 2. **TestFetchLicenses** (3 tests)
- ✅ Successful license fetching from GitHub API
- ✅ Handling empty license list
- ✅ HTTP error handling

### 3. **TestGetLicense** (2 tests)
- ✅ Successful license content retrieval
- ✅ Handling missing license body

### 4. **TestRenderLicense** (8 tests)
- ✅ [year] placeholder replacement
- ✅ [fullname] placeholder replacement
- ✅ [yyyy] placeholder replacement
- ✅ [name of copyright owner] placeholder replacement
- ✅ [NAME OF COPYRIGHT OWNER] placeholder replacement
- ✅ Multiple placeholders in single content
- ✅ Content without placeholders
- ✅ Special characters in author names

### 5. **TestGetLicenseKeyInteractive** (2 tests)
- ✅ Successful interactive license selection
- ✅ Handling user cancellation

### 6. **TestGetAuthorInput** (3 tests)
- ✅ Author from command-line arguments
- ✅ Interactive author input with git name
- ✅ Interactive author input without git name

### 7. **TestGetYearInput** (3 tests)
- ✅ Year from command-line arguments
- ✅ Interactive year input with current year default
- ✅ Custom year input

### 8. **TestSaveLicense** (3 tests)
- ✅ License file creation
- ✅ Overwriting existing license file
- ✅ Unicode content handling

### 9. **TestMainFunction** (6 tests)
- ✅ Main with all command-line arguments
- ✅ Main in interactive mode (no arguments)
- ✅ Main with only license argument (fast path)
- ✅ Keyboard interrupt handling
- ✅ Invalid license error handling
- ✅ Full integration workflow

### 10. **TestCommandLineArgumentParsing** (3 tests)
- ✅ Help argument parsing
- ✅ Long-form arguments (--license, --author, --year)
- ✅ Short-form arguments (-l, -a, -y)

### 11. **TestEdgeCases** (7 tests)
- ✅ Empty license content
- ✅ Empty author name
- ✅ Empty year
- ✅ Very long author names
- ✅ Duplicate placeholders
- ✅ Network timeout handling
- ✅ Single license selection

## Running Tests

### Install test dependencies:
```bash
uv pip install -e ".[dev]"
# or
pip install -e ".[dev]"
```

### Run all tests:
```bash
pytest tests/
```

### Run with verbose output:
```bash
pytest tests/ -v
```

### Run with coverage report:
```bash
pytest tests/ --cov=src/lic_cli --cov-report=html
```

### Run specific test class:
```bash
pytest tests/test_cli.py::TestRenderLicense -v
```

### Run specific test:
```bash
pytest tests/test_cli.py::TestRenderLicense::test_render_license_year_placeholder -v
```

## Test Statistics

- **Total Test Cases**: 44
- **Test Categories**: 11
- **Coverage Areas**:
  - Unit tests for individual functions
  - Integration tests for main workflow
  - Command-line argument parsing
  - Error handling and edge cases
  - Mock tests for external API calls
  - File I/O operations
  - Unicode and special character handling

## Key Testing Strategies

1. **Mocking External Dependencies**: All HTTP calls and subprocess calls are mocked to avoid external dependencies
2. **Parameterized Tests**: Tests cover both happy paths and error conditions
3. **Edge Case Coverage**: Tests include empty inputs, long strings, special characters, and timeouts
4. **Integration Testing**: Main function tests verify the complete workflow
5. **File System Testing**: Tests use temporary directories to avoid polluting the actual filesystem

## Example Test Scenarios

### Scenario 1: Full Command-Line Usage (Fast Path)
```bash
lic -l mit -a "John Doe" -y 2026
```
- Skips API call to fetch all licenses
- Uses provided arguments directly
- Generates license immediately

### Scenario 2: Interactive Mode
```bash
lic
```
- Fetches all licenses from GitHub
- Prompts for license selection
- Prompts for author (with git name as default)
- Prompts for year (with current year as default)
- Generates license

### Scenario 3: Partial Arguments
```bash
lic -l mit -a "John Doe"
```
- Skips API call
- Uses license and author from arguments
- Prompts only for year

## Mocking Strategy

The tests use `unittest.mock` to mock:
- `httpx.get()` - GitHub API calls
- `subprocess.run()` - Git config calls
- `questionary` - Interactive prompts
- `console` - Rich console output
- `Path.write_text()` - File writing operations

This ensures tests are:
- ✅ Fast (no network calls)
- ✅ Reliable (no external dependencies)
- ✅ Isolated (no side effects)
- ✅ Deterministic (no randomness)
