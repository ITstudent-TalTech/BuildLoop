# Test Fixtures — source_ingestion

## sample_ehr.pdf

A minimal valid PDF 1.0 file (~321 bytes) with one empty page.
Generated programmatically — not a real EHR document.

Used as the mock HTTP response body in `test_ehr_fetcher.py` and
`test_service.py` wherever the EHR endpoint returns 200 OK.

Re-generate with:

```python
import os

pdf = b'%PDF-1.0\n'
pdf += b'1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n'
pdf += b'2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n'
pdf += b'3 0 obj\n<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]>>\nendobj\n'
xref_offset = len(pdf)
pdf += b'xref\n0 4\n'
pdf += b'0000000000 65535 f\r\n0000000009 00000 n\r\n'
pdf += b'0000000058 00000 n\r\n0000000115 00000 n\r\n'
pdf += ('trailer\n<</Size 4 /Root 1 0 R>>\nstartxref\n%d\n' % xref_offset).encode()
pdf += b'%%EOF\n'

with open('sample_ehr.pdf', 'wb') as f:
    f.write(pdf)
```
