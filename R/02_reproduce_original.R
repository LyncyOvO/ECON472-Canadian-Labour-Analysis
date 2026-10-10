# Reproduce the historical specifications without silently changing the research design.
# Run from the repository root. Requires base R only.
# Numeric source SEX is deliberately retained (1=male, 2=female).
args <- commandArgs(trailingOnly = TRUE)
file <- if (length(args)) args[1] else "data/raw/lfs-71M0001XCB-E-2015-September_F1.RData"
out <- if (length(args) >= 2L) args[2] else "results/r_reproduction"
env <- new.env(parent = baseenv())
objects <- load(file, envir = env)
if (!"table" %in% objects) stop("Expected object 'table' in the supplied source file.")
x <- get("table", envir = env, inherits = FALSE)
required <- c("SEX", "MARSTAT", "AGYOWNKN", "LFSSTAT", "NAICS_18")
if (!is.data.frame(x) || !all(required %in% names(x))) stop("Missing required columns.")
if (!all(vapply(x[required], is.numeric, logical(1)))) stop("Survey codes must be numeric.")
d <- data.frame(
  outcome_proxy = as.integer(x$LFSSTAT == 1 & x$NAICS_18 == 11),
  SEX = as.numeric(x$SEX),
  child05_original = as.integer(x$AGYOWNKN %in% c(1, 2)),
  partnered = as.integer(x$MARSTAT %in% c(1, 2)),
  child617_original = as.integer(x$AGYOWNKN %in% c(3, 5))
)
if (anyNA(d)) stop("Unexpected missing model values: inspect rather than drop silently.")
if (!all(d$SEX %in% 1:2) || length(unique(d$outcome_proxy)) != 2L) stop("Unexpected source coding.")
dir.create(out, recursive = TRUE, showWarnings = FALSE)
baseline <- glm(outcome_proxy ~ SEX, data = d, family = binomial())
d$class_weight <- ifelse(d$outcome_proxy == 1, 1,
                         sum(d$outcome_proxy == 1) / sum(d$outcome_proxy == 0))
# These are historical class weights, not FWEIGHT survey weights.
# The binomial non-integer-count warning is expected and is not suppressed.
extended <- glm(outcome_proxy ~ SEX * (child05_original + partnered + child617_original),
                data = d, family = binomial(), weights = class_weight)
export <- function(m, name) {
  if (!m$converged || anyNA(coef(m))) stop("Unidentified or unconverged model: ", name)
  z <- coef(summary(m))
  write.csv(data.frame(term = rownames(z), coefficient = z[, 1], standard_error = z[, 2],
                      z_value = z[, 3], p_value = z[, 4]),
            file.path(out, paste0(name, ".csv")), row.names = FALSE)
}
export(baseline, "stage1_historical")
export(extended, "stage2_historical_class_weighted")
capture.output(sessionInfo(), file = file.path(out, "sessionInfo.txt"))
message("Historical models fitted. Read docs/reproduction_notes.md before interpretation.")
