# Tasks

## 1. Smart Quote Parsing

- [x] 1.1 Extend the shared argument parser to recognize ASCII and paired left/right typographic double-quote delimiters, retaining ASCII-only backslash escaping and existing whitespace/error rules; verify parser tests cover multiword values, numeric-looking string values, ASCII escape compatibility, and unterminated or mismatched smart quotes.
- [x] 1.2 Reuse the parser's quote-opener recognition for non-slash speech dispatch so a leading left typographic double quote routes to `/say`; verify a dispatch-level test distinguishes smart-quote speech from ordinary unquoted speech and emotes.
- [x] 1.3 Verify parser consumers, including the mail-title reparse path, accept smart-quoted arguments without changing their delimiter or free-text semantics; add focused regression coverage for the affected command paths.

## 2. Compatibility Verification

- [x] 2.1 Add an end-to-end action or builder test resolving a smart-quoted multiword item such as `“coffee machine”`, and verify the existing ASCII-quoted equivalent remains passing.
- [x] 2.2 Run the repository test command and `openspec validate support-smart-quoted-input --strict`; verify all tests and change artifacts pass.
