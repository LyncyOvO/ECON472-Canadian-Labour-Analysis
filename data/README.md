# Data inputs and definitions

Place authorized copies of the twelve supplied files in `data/raw/`:

`lfs-71M0001XCB-E-2015-<Month>_F1.RData`

Months: January, February, March, April, May, June, July, August, September, October, November, December.

The optional `lfs-71M0001XCB-E-2015-January_F1-subset.tab` contains seven columns and matches the January RData exactly for those columns. Do not include these microdata in a public commit by accident; the supplied `.gitignore` excludes them.

All twelve RData files contain `table`, so loading them successively into one environment replaces that object. September is the final file in the original code and reproduces the paper. The project does not pool respondents across months.

## Codes verified from the uploaded September file's metadata

| Field | Meaning / relevant codes |
|---|---|
| `SEX` | 1 male; 2 female |
| `MARSTAT` | 1 married; 2 common-law; 3 widowed; 4 separated; 5 divorced; 6 never married |
| `AGYOWNKN` | 1 under 3; 2 ages 3–5; 3 ages 6–12; 4 ages 13–15; 5 ages 16–17; 6 ages 18–24 |
| `LFSSTAT` | 1 employed at work; 2 employed absent; 3–5 unemployment categories; 6 not in labour force |
| `NAICS_18` | 18-group NAICS 2007 main-job industry; 11 is professional/scientific/technical services |
| `FWEIGHT` | Final individual or family weight |

The complete relevant value labels are exported in `results/verified/embedded_labels.txt`. These come from the supplied file, not a newer revised release.

## Source references and remaining documentation

- Original paper: Statistics Canada Labour Force Survey (2015), accessed via ODESI.
- [Official PUMF catalogue](https://www150.statcan.gc.ca/n1/en/catalogue/71M0001X).
- [Historical Statistics Canada record layout](https://www23.statcan.gc.ca/imdb-bmdi/pub/document/3701_DLI_D3_T22_V1-eng.pdf), for supplementary definitions. This older layout describes an earlier NAICS vintage; the supplied file's labels are authoritative for the values audited here. The layout notes that youngest-child age is on parent records only.

Use the exact supplied files for reproduction: later revised releases may have different row counts or schemas. SHA-256 fingerprints are recorded in the inventory. Data acquisition, redistribution terms, the precise reasons for non-applicable child-age entries, and suitable survey variance estimation need separate documentation before extending the project.
