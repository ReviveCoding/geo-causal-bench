#!/usr/bin/env Rscript

# Official pinned GeoLift operational design study. This runs only in the
# GEOLIFT-COMPAT-001 overlay and writes separate post-audit evidence.
suppressPackageStartupMessages(library(GeoLift))
suppressPackageStartupMessages(library(jsonlite))

args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args) >= 1) args[[1]] else normalizePath(".")
input <- file.path(root, "data", "staged", "D1_PRE", "GeoLift_PreTest.csv")
output <- file.path(root, "evidence", "operations", "geolift_official_operations.json")
data <- read.csv(input, stringsAsFactors = FALSE)
data[["time"]] <- as.integer(as.Date(data[["date"]]) - min(as.Date(data[["date"]]))) + 1L

started <- proc.time()[["elapsed"]]
errors <- list()
selection <- tryCatch(
  GeoLiftMarketSelection(
    data = data,
    treatment_periods = 10,
    N = c(1, 2, 3),
    effect_size = c(0.05, 0.10),
    lookback_window = 1,
    cpic = 1,
    alpha = 0.1,
    ProgressBar = FALSE,
    print = FALSE,
    run_stochastic_process = FALSE,
    parallel = FALSE,
    conformal_type = "iid",
    ns = 100
  ),
  error = function(error) {
    errors[["market_selection"]] <<- paste(class(error)[[1]], conditionMessage(error), sep = ": ")
    NULL
  }
)

power <- tryCatch(
  GeoLiftPower(
    data = data,
    locations = c("chicago", "portland"),
    effect_size = c(0, 0.05, 0.10, 0.15),
    treatment_periods = c(10, 15),
    lookback_window = 1,
    cpic = 1,
    alpha = 0.1,
    ProgressBar = FALSE,
    parallel = FALSE,
    conformal_type = "iid",
    ns = 100
  ),
  error = function(error) {
    errors[["power"]] <<- paste(class(error)[[1]], conditionMessage(error), sep = ": ")
    NULL
  }
)

compact <- function(value) {
  if (is.null(value)) return(NULL)
  if (is.data.frame(value)) return(value)
  if (is.atomic(value)) return(value)
  if (is.list(value)) {
    keep <- vapply(value, function(item) is.atomic(item) || is.data.frame(item), logical(1))
    return(lapply(value[keep], compact))
  }
  as.character(value)
}

payload <- list(
  extension_id = "OPERATIONS-STUDY-001",
  evidence_class = "MEASURED",
  status = if (is.null(selection) && is.null(power)) "GATED" else "PASS_WITH_LIMITATIONS",
  geolift_version = as.character(packageVersion("GeoLift")),
  geolift_commit = "db34ea4299ff0e28515ebac502b78c076c93c905",
  augsynth_version = as.character(packageVersion("augsynth")),
  augsynth_commit = "65c5a6f34f4e4a8b1011182fe12309ef022d992f",
  local_patch = FALSE,
  input_rows = nrow(data),
  input_locations = length(unique(data[["location"]])),
  input_days = length(unique(data[["time"]])),
  runtime_sec = proc.time()[["elapsed"]] - started,
  market_selection_class = class(selection),
  market_selection_names = names(selection),
  market_selection = compact(selection),
  power_class = class(power),
  power_names = names(power),
  power = compact(power),
  errors = errors,
  limitations = c(
    "Tool-native GeoLift metrics are not numerically equated with GeoX metrics.",
    "This is the exact UPSTREAM_PINNED overlay, not current augsynth HEAD.",
    "Aggregate confidence intervals remain outside the compatibility qualification."
  )
)
write_json(payload, output, pretty = TRUE, auto_unbox = TRUE, na = "string", digits = 16)
cat(toJSON(list(status = payload$status, selection_names = names(selection), power_names = names(power), errors = errors), pretty = TRUE, auto_unbox = TRUE), "\n")
