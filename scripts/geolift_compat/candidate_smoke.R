args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) {
  stop("usage: candidate_smoke.R CANDIDATE_LIBRARY")
}
.libPaths(c(normalizePath(args[[1]], mustWork = TRUE), .libPaths()))

suppressPackageStartupMessages(library(GeoLift))
suppressPackageStartupMessages(library(augsynth))

candidate_path <- normalizePath(find.package("augsynth"), mustWork = TRUE)
if (!startsWith(candidate_path, normalizePath(args[[1]], mustWork = TRUE))) {
  stop("candidate augsynth library did not take precedence")
}

data("GeoLift_Test", package = "GeoLift")
GeoTestData_Test <- GeoLift::GeoDataRead(
  data = GeoLift_Test,
  date_id = "date",
  location_id = "location",
  Y_id = "Y",
  X = c(),
  format = "yyyy-mm-dd",
  summary = FALSE
)

fit <- GeoLift::GeoLift(
  Y_id = "Y",
  data = GeoTestData_Test,
  locations = c("chicago", "portland"),
  treatment_start_time = 91,
  treatment_end_time = 105
)

stopifnot(inherits(fit, "GeoLift"))
stopifnot(length(fit$y_hat) == 105L)
stopifnot(length(fit$ATT) == 105L)
stopifnot(nrow(fit$summary$att) == 105L)
cat("CANDIDATE_PASS", as.character(utils::packageVersion("augsynth")), candidate_path, "\n")
