# Run from the repository root. Each RData file is read in isolation.
args <- commandArgs(trailingOnly = TRUE)
input <- if (length(args) >= 1L) args[1] else "data/raw"
out <- if (length(args) >= 2L) args[2] else "results/inventory"
files <- list.files(input, pattern = "\\.[Rr][Dd]ata$", full.names = TRUE)
if (!length(files)) stop("No RData files found in ", input)
dir.create(out, recursive = TRUE, showWarnings = FALSE)
rows <- list()
for (file in files) {
  env <- new.env(parent = baseenv())
  objects <- load(file, envir = env)
  for (name in objects) {
    x <- get(name, envir = env, inherits = FALSE)
    rows[[length(rows) + 1L]] <- data.frame(
      file = basename(file), object = name, class = paste(class(x), collapse = ";"),
      nrow = if (is.data.frame(x)) nrow(x) else NA_integer_,
      ncol = if (is.data.frame(x)) ncol(x) else NA_integer_)
    if (is.data.frame(x)) {
      safe <- gsub("[^A-Za-z0-9_.-]", "_", paste(basename(file), name, sep = "_"))
      capture.output({
        print(names(x))
        for (v in intersect(c("SEX", "MARSTAT", "AGYOWNKN", "LFSSTAT", "NAICS_18"), names(x))) {
          cat("\nFIELD:", v, "\n")
          print(attributes(x[[v]]))
          print(base::table(x[[v]], useNA = "always"))
        }
      }, file = file.path(out, paste0(safe, "_fields.txt")))
    }
  }
}
write.csv(do.call(rbind, rows), file.path(out, "objects.csv"), row.names = FALSE)
capture.output(sessionInfo(), file = file.path(out, "sessionInfo.txt"))
