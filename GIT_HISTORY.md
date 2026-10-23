# Git history note

The intended incremental commit sequence is:

1. `chore: scaffold CT-200 traceability service`
2. `feat: reconstruct numbered manual hierarchy`
3. `feat: add versioned browse selection and generation APIs`
4. `docs: explain validation and decision log`

The execution environment used to prepare this submission did not include the `git` executable, so these commits could not be materialized here. Run the following in the repository before submission:

```bash
git init
git add . && git commit -m "chore: scaffold CT-200 traceability service"
# make the parser/tests commit next, then API commit, then docs commit
```
