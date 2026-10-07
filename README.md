# GlobalTech HR Data Integration Pipeline

Unified employee dataset for the GlobalTech / AcquiredCo merger. The pipeline loads four HR systems, cleans them onto one schema, resolves duplicate people, and stops delivery when data-quality checks show the extract is not safe for payroll or compliance.

## Business context

HR and Finance need one employee list within 10 business days for Day-1 staffing, benefits eligibility, payroll migration, and headcount-by-jurisdiction reporting.

The source systems were never integrated:

| Source | System | Format | Volume | Risk if left unresolved |
|---|---|---|---|---|
| GlobalTech HRIS | Workday | CSV | ~15,000 | Department codes differ by business unit, so org reports split one function into many |
| AcquiredCo HRIS | BambooHR | JSON | ~3,000 | Employee numbers overlap GlobalTech's range, so a raw join pays or counts the wrong person |
| Payroll | ADP | Excel | ~18,500 | Mixed USD, EUR, and GBP, plus duplicate pay rows |
| Benefits | MedShield | XML | ~12,000 | GlobalTech only, and not every employee is enrolled |

A wrong join shows up as overpayment, a missed enrollment window, or a headcount figure filed with the wrong jurisdiction.

## Design decisions

These choices are the ones HR and Finance asked about. Each one trades a specific error for a specific cost.

### Fuzzy threshold: 88%

`rapidfuzz` token-sort ratio of 88 keeps close variants such as "John Smith" and "Jon Smith" (about 90) and drops pairs that only share a surname. Lowering the cutoff to 80 roughly doubles the review queue on a workforce of this size, because many unrelated people share a last name. We do not auto-merge these pairs. A false positive costs a few minutes of HR review. A silent merge would put the wrong person on payroll. The review file is the control.

### 30-day hire-date block

Two people hired years apart are not the same hire, even when the names are close. Thirty days covers date-entry drift and transfer paperwork. A 90-day window would pull in the next hiring cohort and increase comparisons in proportion to how many people start each month. Blocking on the hire date, rather than comparing all 18,000 payroll rows with all HRIS rows, keeps the pass on the order of a date window instead of hundreds of millions of name comparisons.

### Source priority: HRIS, then Payroll, then Benefits

HRIS is the system of record for identity: name, department, country, and which company the person came from. Payroll is the system of record for pay. Benefits only knows enrollment. If a payroll row overwrote `company_origin`, a compliance extract could file an AcquiredCo employee under GlobalTech or the reverse. Identity fields stay with HRIS. Compensation fields are filled from payroll. Benefits adds enrollment and does not replace either.

### Email match merges; fuzzy match does not

The same email at GlobalTech and AcquiredCo is treated as one person. Contractor overlap is uncommon, but leaving both rows in the golden set double-counts headcount and can open two benefits records. The surviving key is the GlobalTech id, because payroll migration targets the GlobalTech platform. The AcquiredCo id is remapped so that person's pay and benefits still attach.

An 88% name match is not strong enough to change pay. Those pairs are flagged `probable_match` and written to `probable_matches.csv` for HR to confirm or reject.

### Parquet partitioned by company origin

Day-1 planning constantly filters GlobalTech versus AcquiredCo. Partitioning the golden dataset by `company_origin` lets downstream jobs read one company without scanning the other. Parquet is columnar, so headcount and salary aggregates do not have to read name and address columns. Ghost employees and probable matches stay in CSV because HR opens those files in a spreadsheet.

### Validation gate: more than two failed checks

A single failing check, such as a handful of malformed emails, is reported and does not block the 10-day extract. More than two failed checks means several rule families are broken at once (identity, pay, and jurisdiction, for example). That extract is not safe to load into payroll. The gate counts failed checks, not a zero-tolerance row rate. A missing column is a failed check. It is not reported as a 100% pass.

### Namespaced ids on every source

GlobalTech ids are `GT-######` and AcquiredCo ids are `AC-######`, including payroll and benefits. Leaving those systems on the raw number would make employee 1042 in both companies look like one person. Benefits covers GlobalTech only, so those ids use the `GT-` namespace.

### Fixed exchange rates

USD 1.00, EUR 1.08, GBP 1.27. Rates are constants so a rerun next month produces the same salary bands. Treasury can replace the table in `config/exchange_rates.py` when they want a new lock date. Original salary and currency are kept beside `salary_usd_annual`.

## How to run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On Linux or macOS, activate with `source .venv/bin/activate`.

`main.py` is the entry point. Optional output directory:

```bash
python main.py --output outputs
```

Tests:

```bash
pytest
```

## Pipeline

1. Ingest each source with its own loader. AcquiredCo JSON is read in pages. A bad file is dead-lettered and re-raised with the source name.
2. Align every source to the employee schema and set `source_systems`, `company_origin`, and `dedup_method=single_source`.
3. Clean names, dates, departments, salaries, and namespaced ids.
4. Deduplicate: exact id with HRIS priority, then cross-company email, then fuzzy review. Payroll rows with no HRIS id become the ghost report.
5. Validate. Halt only when more than two checks fail.
6. Write the partitioned golden dataset, the ghost report, the probable-match review, validation CSV/HTML, and the chart pack.

## Inputs

| File | Loader | Notes |
|---|---|---|
| `data/raw/globaltech_hris.csv` | `load_globaltech_hris` | Dates as `YYYY-MM-DD` |
| `data/raw/acquiredco_api.json` | `load_acquiredco_hris` | Dates as `MM/DD/YYYY`; paged reads |
| `data/raw/payroll_data.xlsx` | `load_payroll` | Salary strings and mixed currency |
| `data/raw/benefits_enrollment.xml` | `load_benefits` | Dates as `15-Jan-2022` |

`data/raw/` is gitignored. The files contain names, emails, and salaries and should stay on the machine that runs the pipeline.

## Outputs

| Path | Format | Contents |
|---|---|---|
| `outputs/golden_employee_dataset/` | Parquet, partitioned by `company_origin` | Deduplicated employees |
| `outputs/ghost_employees.csv` | CSV | Payroll rows with no HRIS match: `payroll_employee_id`, `name`, `salary_usd_annual`, `ghost_flag_reason` |
| `outputs/probable_matches.csv` | CSV | Fuzzy pairs for HR: `record_1_id`, `record_2_id`, `similarity_score`, `hire_date_diff_days`, `recommended_action` |
| `outputs/validation_report.csv` and `.html` | CSV, HTML | Check, totals, pass rate, status |
| `outputs/charts/` | PNG | Headcount, salary, tenure, benefits, quality |

Column definitions for the golden dataset are in `docs/data_dictionary.md`.

## Project layout

```text
main.py                 CLI entry point
config/                 Rules, rates, department maps, logging
src/ingest.py           Four source loaders and schema alignment
src/clean.py            Cleaning orchestration
src/deduplicate.py      Three-pass matching and ghost detection
src/validate.py         Quality checks and delivery gate
src/pipeline.py         End-to-end run
src/matching/           Exact, email, fuzzy, ghost
src/transformers/       Names, ids, dates, salary, departments
src/validators/         Check implementations used by validate.py
src/enrichment/         Payroll and benefits attachment
docs/                   Data dictionary, business rules, flow
tests/                  Unit and pipeline tests
```

## Assumptions and limitations

- Exchange rates are locked. They are not a daily feed.
- Fuzzy pairs wait for HR. They are not merged.
- Benefits enrollment exists for GlobalTech employees only.
- AcquiredCo pagination reads a JSON file in pages. It is not a live BambooHR client.
- Hire dates before 1970-01-01 or after today fail validation.
- Salary outside $15,000 to $2,000,000 USD annual fails validation. Missing salary does not, because some HRIS rows exist before payroll migration.

## Change log

- Deduplication now applies exact-id priority and cross-company email collapse, and writes the fuzzy review file instead of leaving those passes unused.
- Validation halts only after more than two failed checks. A missing column fails its check.
- Payroll and benefits ids are namespaced. The golden dataset is partitioned by company origin.
- Source dates are parsed as `YYYY-MM-DD`, `MM/DD/YYYY`, and `DD-Mon-YYYY` before generic inference.
