# Submission Email

**Subject:** Tri9T AI Internship Assignment — CT-200 QA Traceability API

Hi Tri9T AI team,

Please find my submission for the CT-200 AI Engineering Internship Assignment:

- GitHub repository: `<ADD_GITHUB_REPOSITORY_URL>`
- Approach document: [`APPROACH.md`](./APPROACH.md)
- README and setup instructions: [`README.md`](./README.md)

The repository includes:

- PDF extraction and hierarchy reconstruction
- Versioned SQLite persistence with content hashes
- Version-pinned selections
- Browse, search, comparison, generation, and retrieval APIs
- Retrieval-time staleness and impact reporting
- Pydantic validation at the LLM output boundary
- Explicit parser tests for duplicate headings, out-of-order numbering, and stray body fragments
- A v1 → v2 demo flow

I chose an offline deterministic generation adapter so the project runs without provider credentials. The provider boundary and validation/retry policy are documented in the approach document and can be connected to an LLM provider without changing the persistence contract.

Best,
`<YOUR NAME>`
