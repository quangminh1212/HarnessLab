# Example: multi-AI PR review council

```powershell
cd C:\Dev\HarnessLab
python -m harnesslab council init pr-review-demo `
  --topic "Review approach for feature X" `
  --root examples\council-pr-review `
  --rounds 2

# With a real PR:
# python -m harnesslab council init pr-review-demo --ref owner/repo/pull/12 --root examples\council-pr-review

python -m harnesslab council next pr-review-demo --root examples\council-pr-review
python -m harnesslab council turn pr-review-demo --root examples\council-pr-review `
  --role proposer --content "CLAIM: approve with nits | EVIDENCE: … | ASK: add test for edge Y"
python -m harnesslab council decide pr-review-demo --root examples\council-pr-review
```

Artifacts appear under `examples/council-pr-review/councils/pr-review-demo/`.
