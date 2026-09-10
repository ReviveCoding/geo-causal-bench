suppressPackageStartupMessages(library(augsynth))
data("kansas", package = "augsynth")
fit <- augsynth::augsynth(
  lngdpcapita ~ treated, fips, year_qtr, kansas,
  progfunc = "None", scm = TRUE
)
cat("AUGSYNTH_NAMES\n")
print(names(fit))
cat("AUGSYNTH_ATT\n")
str(fit$att)
cat("AUGSYNTH_SUMMARY\n")
summary_fit <- summary(fit)
print(summary_fit)
str(summary_fit)

data("GeoLift_Test", package = "GeoLift")
cat("GEOLIFT_TEST\n")
print(dim(GeoLift_Test))
print(names(GeoLift_Test))
print(utils::head(GeoLift_Test))
test_data <- GeoLift::GeoDataRead(
  data = GeoLift_Test, date_id = "date", location_id = "location",
  Y_id = "Y", X = c(), format = "yyyy-mm-dd", summary = FALSE
)
cat("GEOLIFT_PROCESSED\n")
print(dim(test_data))
print(table(test_data$location %in% c("chicago", "portland")))
print(anyDuplicated(test_data[c("location", "time")]))
cat("GEOLIFT_FORMALS\n")
print(formals(GeoLift::GeoLift))
cat("GEOLIFT_CALL\n")
options(error = function() {
  traceback(30)
  quit(status = 2)
})
GeoLift::GeoLift(
  Y_id = "Y", time_id = "time", location_id = "location",
  data = test_data, locations = c("chicago", "portland"),
  treatment_start_time = 91, treatment_end_time = 105
)
