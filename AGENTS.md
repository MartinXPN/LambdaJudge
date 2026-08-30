# Guidelines
We use Python 3.14 for all the code, making sure to use the latest Python standards:
- Don't use `from __future__ import annotations` as it's no longer necessary.
- Use ` | None` instead of `Optional[]` for optional types (`str | None` instead of `Optional[str]`).
- Use built-in collection types instead of importing from `typing` (e.g., use `list` instead of `List`, `dict` instead of `Dict`, etc.).
- Don't edit the `__init__.py` files - they should be empty.
- Don't use `__all__` exports. Instead, import modules and functions directly where they are needed.
- Keep the files small and focused on a single responsibility. If a file grows too large (300+ lines), consider breaking it down into smaller modules.
- Use f-strings instead of `%` formatting or `str.format()`.


## Error Handling
- Avoid using excessive try-except blocks.
- Do not use error handling for environment variables. Assume they are present and valid.


## Coding Style
- Avoid creating redundant helper functions if the logic can be implemented clearly within the current function.
- Avoid over-engineered solutions, deep nesting, or unnecessary abstraction layers.
- Write simple, clear, and concise code.
- Make sure your code is elegant and Pythonic.
- Don't be afraid to have a second pass on your code to simplify and improve it after writing the initial version.
- Use `dedent()` for multi-line strings (that don't contain multi-line f-string variables).
- Don't add types to variables inside functions / methods unless it significantly improves the code.
- Run `pre-commit run --all-files` to format code and check for linting issues.


## Testing with `pytest`
- Only create tests that are necessary to ensure the correctness of the code.
- Avoid writing tests for trivial code or code that is already well-covered by existing tests.
