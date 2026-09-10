args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) {
  stop("usage: diagnose_ordering.R COMPATIBILITY_LIBRARY OUTPUT_JSON")
}
.libPaths(c(normalizePath(args[[1]], mustWork = TRUE), .libPaths()))
suppressPackageStartupMessages(library(GeoLift))
suppressPackageStartupMessages(library(augsynth))

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
    Y_id = "Y", data = panel, locations = locations,
    treatment_start_time = 91, treatment_end_time = 105
  )
}

forward <- fit_case(c("chicago", "portland"))
reversed <- fit_case(c("portland", "chicago"))
numeric_difference <- function(left, right) {
  left <- as.numeric(left)
  right <- as.numeric(right)
  list(
    length_left = length(left),
    length_right = length(right),
    max_absolute_difference = if (length(left) == length(right)) {
      max(abs(left - right), na.rm = TRUE)
    } else {
      NA_real_
    },
    left = left,
    right = right
  )
}

payload <- list(
  evidence_class = "UPSTREAM_PINNED",
  forward_test_ids = as.character(forward$test_id$name),
  reversed_test_ids = as.character(reversed$test_id$name),
  forward_model_treated_units = as.character(forward$results$trt_unit),
  reversed_model_treated_units = as.character(reversed$results$trt_unit),
  y_hat = numeric_difference(forward$y_hat, reversed$y_hat),
  att = numeric_difference(forward$ATT, reversed$ATT),
  incremental = numeric_difference(forward$incremental, reversed$incremental),
  inference_att = numeric_difference(forward$inference$ATT, reversed$inference$ATT),
  inference_lift = numeric_difference(forward$inference$Perc.Lift, reversed$inference$Perc.Lift),
  inference_pvalue = numeric_difference(forward$inference$pvalue, reversed$inference$pvalue),
  inference_lower = numeric_difference(forward$inference$Lower.Conf.Int,
                                       reversed$inference$Lower.Conf.Int),
  inference_upper = numeric_difference(forward$inference$Upper.Conf.Int,
                                       reversed$inference$Upper.Conf.Int),
  summary_estimate = numeric_difference(forward$summary$att$Estimate,
                                        reversed$summary$att$Estimate),
  summary_lower = numeric_difference(forward$summary$att$lower_bound,
                                     reversed$summary$att$lower_bound),
  summary_upper = numeric_difference(forward$summary$att$upper_bound,
                                     reversed$summary$att$upper_bound),
  summary_pvalue = numeric_difference(forward$summary$att$p_val,
                                      reversed$summary$att$p_val)
)
dir.create(dirname(args[[2]]), recursive = TRUE, showWarnings = FALSE)
jsonlite::write_json(payload, args[[2]], pretty = TRUE, auto_unbox = TRUE,
                     digits = 16, na = "null")
cat("ORDERING_DIAGNOSTIC_WRITTEN", args[[2]], "\n")
