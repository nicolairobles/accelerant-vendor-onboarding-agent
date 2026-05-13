# Sample Upload Packets

These synthetic packets are for testing the Streamlit `Triage new package` workflow.
Each folder has the loose files a reviewer might upload. The `zips/` folder has
one zip per packet for faster manual testing.

## Strategy

The packets are based on the original prompt and policy docs:

- required intake, quote, contract, questionnaire, and email files
- data-handling risks around personal data, employee data, AI/model training,
  service improvement, subprocessors, and cross-border processing
- finance risks around budget, ACV, TCV, term, and payment terms
- procurement risks around missing setup docs and duplicate vendors
- security/legal risks around SOC 2, DPA, incident response, data retention,
  and approval routing
- guardrail risks from prompt injection, decoy policy files, malformed files,
  and mixed-vendor packages

## Packets

- `valid_low_risk_ops_complete`: Workspace Depot plus tax and vendor setup docs.
- `high_risk_ai_with_support_artifacts`: TalentPulse AI with DPA, SOC 2,
  AI opt-out, incident response, and a more complete questionnaire. It should
  still require human review because it remains high risk and over budget.
- `net_new_supportflow_complete`: net-new SupportFlow Assist customer support
  SaaS package with DPA, SOC 2, subprocessor, and AI training opt-out artifacts.
  It should have no matching sample baseline and should remain review-required
  because it handles customer data and internal integrations.
- `guardrail_prompt_injection_email`: valid required files with a malicious
  vendor email asking the agent to bypass approvals.
- `guardrail_policy_doc_decoy_incomplete`: missing the security questionnaire
  and includes `data_handling_policy.md` as a decoy markdown file.
- `invalid_mixed_vendor_case_prefixes`: mixes `case_001` and `case_003`
  filenames and should be blocked before triage.
- `invalid_bad_quote_schema`: includes a CSV that is not a valid quote schema
  and should be rejected as missing quote.

Regenerate these packets with:

```bash
python3 scripts/build_sample_upload_packets.py
```
