args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) {
  stop("usage: test_upstream_pin.R COMPATIBILITY_LIBRARY OUTPUT_JSON")
}
compatibility_library <- normalizePath(args[[1]], mustWork = TRUE)
output_json <- args[[2]]
.libPaths(c(compatibility_library, .libPaths()))

suppressPackageStartupMessages(library(GeoLift))
suppressPackageStartupMessages(library(augsynth))

assert_close <- function(actual, expected, tolerance = 1e-8, label = "value") {
  if (length(actual) != length(expected) ||
      any(!is.finite(actual)) ||
      max(abs(as.numeric(actual) - as.numeric(expected))) > tolerance) {
    stop(label, " invariant failed")
  }
}

assert_equal_with_na <- function(actual, expected, tolerance = 1e-8,
                                 label = "value") {
  actual <- as.numeric(actual)
  expected <- as.numeric(expected)
  if (length(actual) != length(expected) ||
      !identical(is.na(actual), is.na(expected))) {
    stop(label, " NA/dimension invariant failed")
  }
  finite <- !is.na(actual)
  if (any(finite) && max(abs(actual[finite] - expected[finite])) > tolerance) {
    stop(label, " numeric invariant failed")
  }
}

data("GeoLift_Test", package = "GeoLift")
panel <- GeoLift::GeoDataRead(
  data = GeoLift_Test,
  date_id = "date",
  location_id = "location",
  Y_id = "Y",
  X = c(),
  format = "yyyy-mm-dd",
  summary = FALSE
)

fit_case <- function(locations) {
  set.seed(20260909)
  GeoLift::GeoLift(
    Y_id = "Y",
    data = panel,
    locations = locations,
    treatment_start_time = 91,
    treatment_end_time = 105
  )
}

validate_case <- function(fit, locations) {
  stopifnot(inherits(fit, "GeoLift"))
  model <- fit$results
  observed <- cbind(model$data$X, model$data$y)
  treated_rows <- which(model$data$trt == 1)
  time_count <- ncol(observed)
  treated_count <- length(treated_rows)
  post <- 91:105
  stopifnot(treated_count == length(locations))
  stopifnot(time_count == 105L)

  manual_observed_average <- colMeans(observed[treated_rows, , drop = FALSE])
  manual_synthetic_average <- as.numeric(predict(model, att = FALSE))
  manual_att <- manual_observed_average - manual_synthetic_average
  manual_incremental <- sum(observed[treated_rows, post, drop = FALSE]) -
    treated_count * sum(manual_synthetic_average[post])
  manual_lift <- 100 * round(
    (sum(manual_observed_average[post]) - sum(manual_synthetic_average[post])) /
      abs(sum(manual_synthetic_average[post])),
    3
  )

  stopifnot(length(fit$y_obs) == treated_count * time_count)
  observed_from_output <- colMeans(matrix(fit$y_obs, nrow = treated_count))
  assert_close(observed_from_output, manual_observed_average,
               label = "observed treated aggregation")
  assert_close(fit$y_hat, manual_synthetic_average,
               label = "synthetic series aggregation")
  assert_close(fit$ATT, manual_att, label = "ATT time series")
  assert_close(fit$incremental, manual_incremental, tolerance = 1e-6,
               label = "aggregate incremental effect")
  assert_close(fit$inference$Perc.Lift, manual_lift, tolerance = 1e-8,
               label = "percent lift")
  stopifnot(nrow(fit$summary$att) == time_count)
  stopifnot(length(fit$summary$att$Estimate) == time_count)
  stopifnot(all(c("lower_bound", "upper_bound", "p_val") %in%
                names(fit$summary$att)))
  stopifnot(length(fit$summary$att$lower_bound) == time_count)
  stopifnot(length(fit$summary$att$upper_bound) == time_count)
  stopifnot(length(fit$summary$att$p_val) == time_count)
  stopifnot(length(fit$lower_bound) == 1L, length(fit$upper_bound) == 1L)

  list(
    locations = locations,
    treated_count = treated_count,
    time_count = time_count,
    y_obs_length = length(fit$y_obs),
    y_hat_length = length(fit$y_hat),
    att_length = length(fit$ATT),
    inference_time_rows = nrow(fit$summary$att),
    inference_standard_error_length = length(fit$ATT_se),
    average_att = unname(fit$inference$ATT),
    percent_lift = unname(fit$inference$Perc.Lift),
    incremental = unname(fit$incremental),
    lower_bound = unname(fit$lower_bound),
    upper_bound = unname(fit$upper_bound)
  )
}

third_location <- setdiff(sort(unique(panel$location)), c("chicago", "portland"))[[1]]
single_fit <- fit_case("chicago")
two_fit <- fit_case(c("chicago", "portland"))
three_fit <- fit_case(c("chicago", "portland", third_location))
reversed_fit <- fit_case(c("portland", "chicago"))

single <- validate_case(single_fit, "chicago")
two <- validate_case(two_fit, c("chicago", "portland"))
three <- validate_case(three_fit, c("chicago", "portland", third_location))
reversed <- validate_case(reversed_fit, c("portland", "chicago"))

assert_close(two_fit$y_hat, reversed_fit$y_hat,
             label = "ordering-invariant synthetic series")
assert_close(two_fit$ATT, reversed_fit$ATT,
             label = "ordering-invariant ATT series")
assert_close(two_fit$incremental, reversed_fit$incremental, tolerance = 1e-6,
             label = "ordering-invariant incremental effect")
for (field in names(two_fit$inference)) {
  assert_equal_with_na(
    two_fit$inference[[field]], reversed_fit$inference[[field]],
    tolerance = 1e-6, label = paste("ordering-invariant inference", field)
  )
}
stopifnot(abs(two_fit$incremental - 4667) <= 10)

description_hash <- function(package) {
  path <- file.path(find.package(package), "DESCRIPTION")
  sub(" .*", "", system2("sha256sum", path, stdout = TRUE)[[1]])
}

result <- list(
  evidence_class = "UPSTREAM_PINNED",
  extension_id = "GEOLIFT-COMPAT-001",
  status = "PASS",
  seed = 20260909,
  package_versions = list(
    GeoLift = as.character(utils::packageVersion("GeoLift")),
    augsynth = as.character(utils::packageVersion("augsynth"))
  ),
  package_paths = list(
    GeoLift = normalizePath(find.package("GeoLift")),
    augsynth = normalizePath(find.package("augsynth"))
  ),
  description_sha256 = list(
    GeoLift = description_hash("GeoLift"),
    augsynth = description_hash("augsynth")
  ),
  cases = list(single = single, two = two, three = three, reversed = reversed),
  invariants = list(
    single_location_regression = "PASS",
    multiple_treated_dimensions = "PASS",
    manual_aggregation = "PASS",
    treatment_ordering = "PASS",
    inference_time_dimension = "PASS"
  )
)

dir.create(dirname(output_json), recursive = TRUE, showWarnings = FALSE)
jsonlite::write_json(result, output_json, pretty = TRUE, auto_unbox = TRUE,
                     digits = 16)
cat("GEOLIFT_COMPATIBILITY_PASS", output_json, "\n")
