args <- commandArgs(trailingOnly = TRUE)
output <- if (length(args) >= 1) args[[1]] else "evidence/package_qualification.json"

result <- list()

qualify <- function(id, expected, tolerance, expression) {
  started <- Sys.time()
  value <- tryCatch(
    {
      observed <- force(expression)
      list(
        method_id = id,
        expected = expected,
        observed = as.numeric(observed),
        tolerance = tolerance,
        status = if (abs(as.numeric(observed) - expected) <= tolerance) "PASS" else "FAIL",
        failure_category = NULL,
        failure_reason = NULL,
        runtime_sec = as.numeric(difftime(Sys.time(), started, units = "secs"))
      )
    },
    error = function(error) {
      list(
        method_id = id,
        expected = expected,
        observed = NULL,
        tolerance = tolerance,
        status = "GATED",
        failure_category = "PACKAGE_INCOMPATIBILITY",
        failure_reason = conditionMessage(error),
        runtime_sec = as.numeric(difftime(Sys.time(), started, units = "secs"))
      )
    }
  )
  result[[id]] <<- value
}

package_names <- c("did", "fixest", "CausalImpact", "synthdid", "augsynth", "GeoLift")
package_versions <- setNames(
  lapply(package_names, function(package) {
    if (requireNamespace(package, quietly = TRUE)) {
      as.character(utils::packageVersion(package))
    } else {
      NULL
    }
  }),
  package_names
)

qualify("synthdid_prop99", -15.604, 0.02, {
  data("california_prop99", package = "synthdid")
  setup <- synthdid::panel.matrices(california_prop99)
  as.numeric(synthdid::synthdid_estimate(setup$Y, setup$N0, setup$T0))
})

qualify("did_mpdta_dynamic_att", -0.0772, 0.01, {
  data("mpdta", package = "did")
  fit <- did::att_gt(
    yname = "lemp", gname = "first.treat", idname = "countyreal",
    tname = "year", xformla = ~1, data = mpdta, est_method = "reg",
    bstrap = FALSE
  )
  did::aggte(fit, type = "dynamic", bstrap = FALSE)$overall.att
})

qualify("sunab_official_base_stagg_att", -1.133749, 0.00001, {
  data("base_stagg", package = "fixest")
  fit <- fixest::feols(
    y ~ x1 + sunab(year_treated, year) | id + year,
    data = base_stagg,
    cluster = ~id
  )
  as.numeric(stats::coef(summary(fit, agg = "ATT"))["ATT"])
})

qualify("augsynth_kansas_scm", -0.0294, 0.005, {
  data("kansas", package = "augsynth")
  fit <- augsynth::augsynth(
    lngdpcapita ~ treated, fips, year_qtr, kansas,
    progfunc = "None", scm = TRUE
  )
  as.numeric(summary(fit)$average_att$Estimate)
})

qualify("causalimpact_official_toy", 10.0, 3.0, {
  set.seed(1)
  x1 <- 100 + stats::arima.sim(model = list(ar = 0.999), n = 100)
  y <- 1.2 * x1 + stats::rnorm(100)
  y[71:100] <- y[71:100] + 10
  impact <- CausalImpact::CausalImpact(cbind(y, x1), c(1, 70), c(71, 100),
                                      model.args = list(niter = 1000))
  as.numeric(impact$summary["Average", "AbsEffect"])
})

qualify("geolift_official_example", 4667, 10, {
  data("GeoLift_Test", package = "GeoLift")
  test_data <- GeoLift::GeoDataRead(
    data = GeoLift_Test, date_id = "date", location_id = "location",
    Y_id = "Y", X = c(), format = "yyyy-mm-dd", summary = FALSE
  )
  fit <- GeoLift::GeoLift(
    Y_id = "Y", data = test_data, locations = c("chicago", "portland"),
    treatment_start_time = 91, treatment_end_time = 105
  )
  lines <- capture.output(summary(fit))
  target <- lines[grepl("Incremental Y:", lines)][1]
  as.numeric(gsub("[^0-9.-]", "", sub(".*Incremental Y:", "", target)))
})

payload <- list(
  r_version = as.character(getRversion()),
  package_versions = package_versions,
  results = unname(result),
  all_pass = all(vapply(result, function(item) identical(item$status, "PASS"), logical(1)))
)
dir.create(dirname(output), recursive = TRUE, showWarnings = FALSE)
jsonlite::write_json(payload, output, pretty = TRUE, auto_unbox = TRUE, null = "null")
print(payload)
