# Reproduction audit — 11 October 2026 (Singapore)

## Verified results

The Python workflow inspected all twelve supplied monthly RData files. Each contains a single `table` data frame. The September file has 102,095 rows and 79 columns. The January tabular subset equals the corresponding January RData columns, including missingness and row order.

With September data and the effective coding in the original R formulas, all ten coefficients and ten standard errors in the paper's two regression tables are reproduced to their displayed precision. `results/verified/paper_comparison.csv` records the numbers and comparison flags. This establishes numerical reproduction of those tables, not validity of every substantive interpretation in the paper.

Python packages and versions are recorded in `verification.json`. The R companion has not been executed here; this is independent Python reproduction, not an assertion that the entire original R script runs unchanged.

## Why the original script behaves this way

1. **Monthly overwrite:** `load()` restores a named object. Every uploaded monthly file contains `table`; September is loaded last. Earlier months are overwritten. The reported sample therefore corresponds to September, not a combined annual sample.
2. **Sex coding:** The global `SEX` vector is recoded to 0/1, but `glm(..., data = table)` finds the original `table$SEX` first. It uses 1/2. The baseline intercept is consequently the extrapolated intercept at SEX=0. In the interaction model, raw family main effects also correspond to SEX=0, which is not an observed sex category. A future 0/1 recoding changes those coefficients while preserving predictions for otherwise identical models.
3. **Unsuccessful fit:** The first extended formula includes an extra comma and undefined predictors. It is retained in the archive only. Running the entire original file without intervention will not reliably reach the later successful fit.
4. **Historical class weights:** The second successful model weights positive outcomes by 1 and negatives by `n_positive/n_negative`. Python `freq_weights` reproduces its coefficients and model-based standard errors. This is not the LFS `FWEIGHT` survey weighting or survey-design-adjusted inference. No causal or population probability interpretation should be attached to the class-balanced predictions.

## Substantive corrections needed for an extension

### Outcome scope

Embedded labels identify `LFSSTAT=1` as employed and at work and `NAICS_18=11` as professional/scientific/technical services. The rule excludes employed people temporarily absent from work and does not capture all STEM occupations across industries. It also includes an industry rather than selecting occupations. The repository's displayed title and chart therefore use precise industry wording while the archived essay retains its original title.

### Child-age indicator

The historical `c(3,5)` group includes ages 6–12 and 16–17 but excludes ages 13–15 (code 4). There are 3,280 code-4 records in September. The reproduction preserves this error transparently. A new analysis intending ages 6–17 should use `c(3,4,5)` and report the change.

The source's `%in%` expressions put blank child-age entries into the zero category for two indicators, whereas its equality expression for ages 18–24 produces missing values. September has 73,285 unrecorded child-age entries. This is an applicability question, not evidence that all those respondents failed to answer. Historical documentation restricts this field to parent records. Dropping all blanks would change the target sample substantially; do not do so automatically.

### Association and inference

The project is cross-sectional and contains no DID design. Marital status combines married and common-law respondents, so the alternative group is not simply 'single'. Logit interaction coefficients are on the log-odds scale; probability contrasts require full predictions. Controls such as age and education, survey weights and design, and the eligible population should be selected and justified before presenting an extended substantive model. Combining monthly files would additionally require a plan for repeated respondents and dependence.

## What was changed for the repository

- Original source is archived; executable scripts use relative or explicit command-line paths.
- Fresh environments isolate monthly RData objects.
- The reproduction uses explicit column names and preserves historical 1/2 sex coding, the incomplete child-age grouping, and historical class weights to match the report.
- The script fails on unexpected source structure and checks each printed coefficient and standard error against the paper.
- Only aggregate outputs and input file fingerprints are packaged; no respondent-level data are exported.
- The PDF's student-number line was redacted, its metadata cleared, and its cover inspected. The research text and tables were not rewritten.

## Validation limits

All monthly files were read and inventoried; the original September model tables, descriptive figures and January subset were checked. No corrected or survey-design-aware model is claimed. No R runtime validation, causal identification, external peer review, or public GitHub publication is claimed.
