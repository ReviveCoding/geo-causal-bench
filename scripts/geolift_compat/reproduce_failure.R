args <- commandArgs(trailingOnly = TRUE)
output_dir <- if (length(args) >= 1) args[[1]] else "evidence/geolift_compatibility/baseline"
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
log_path <- file.path(output_dir, "complete_traceback.log")
log_connection <- file(log_path, open = "wt")
sink(log_connection, split = TRUE)
sink(log_connection, type = "message")

sha256_file <- function(path) {
  output <- system2("sha256sum", path, stdout = TRUE, stderr = TRUE)
  sub(" .*", "", output[[1]])
}

package_identity <- function(package) {
  description_path <- file.path(find.package(package), "DESCRIPTION")
  description <- read.dcf(description_path)
  fields <- c("Package", "Version", "RemoteType", "RemoteHost", "RemoteRepo",
              "RemoteUsername", "RemoteRef", "RemoteSha", "GithubSHA1")
  values <- setNames(rep(NA_character_, length(fields)), fields)
  present <- intersect(fields, colnames(description))
  values[present] <- description[1, present]
  list(
    fields = as.list(values),
    path = find.package(package),
    description_sha256 = sha256_file(description_path)
  )
}

close_log <- function() {
  sink(type = "message")
  sink()
  close(log_connection)
}

options(error = function() {
  cat("\n=== COMPLETE TRACEBACK ===\n")
  traceback(100)
  cat("\n=== SESSION INFO AT FAILURE ===\n")
  print(sessionInfo())
  close_log()
  quit(save = "no", status = 2, runLast = FALSE)
})

suppressPackageStartupMessages(library(GeoLift))
suppressPackageStartupMessages(library(augsynth))

cat("=== INVESTIGATION CLASS ===\nUPSTREAM_UNMODIFIED\n")
cat("=== PACKAGE IDENTITIES ===\n")
print(package_identity("GeoLift"))
print(package_identity("augsynth"))
cat("=== SESSION INFO BEFORE FAILURE ===\n")
print(sessionInfo())

data("GeoLift_Test", package = "GeoLift")
raw_temp <- tempfile(fileext = ".rds")
saveRDS(GeoLift_Test, raw_temp, version = 3)
cat("=== RAW DATA ===\n")
cat("dim:", paste(dim(GeoLift_Test), collapse = " x "), "\n")
cat("serialized_sha256:", sha256_file(raw_temp), "\n")
unlink(raw_temp)

GeoTestData_Test <- GeoLift::GeoDataRead(
  data = GeoLift_Test,
  date_id = "date",
  location_id = "location",
  Y_id = "Y",
  X = c(),
  format = "yyyy-mm-dd",
  summary = FALSE
)
processed_temp <- tempfile(fileext = ".rds")
saveRDS(GeoTestData_Test, processed_temp, version = 3)
cat("=== PROCESSED DATA ===\n")
cat("dim:", paste(dim(GeoTestData_Test), collapse = " x "), "\n")
cat("locations:", length(unique(GeoTestData_Test$location)), "\n")
cat("times:", length(unique(GeoTestData_Test$time)), "\n")
cat("duplicate_location_time:", anyDuplicated(GeoTestData_Test[c("location", "time")]), "\n")
cat("serialized_sha256:", sha256_file(processed_temp), "\n")
unlink(processed_temp)

trace(
  "treated_table",
  where = asNamespace("augsynth"),
  print = FALSE,
  tracer = quote({
    diagnostic_trt_index <- which(augsynth$data$trt == 1)
    diagnostic_df <- dplyr::bind_cols(augsynth$data$X, augsynth$data$y)
    cat("=== TREATED_TABLE ENTRY SHAPES ===\n")
    cat("X:", paste(dim(augsynth$data$X), collapse = " x "), "\n")
    cat("y:", paste(dim(augsynth$data$y), collapse = " x "), "\n")
    cat("combined:", paste(dim(diagnostic_df), collapse = " x "), "\n")
    cat("treated_rows:", length(diagnostic_trt_index), "\n")
    cat("time_length:", ncol(diagnostic_df), "\n")
    cat("flattened_Yobs_length:",
        length(as.numeric(t(diagnostic_df[diagnostic_trt_index, , drop = FALSE]))), "\n")
    cat("treated_mean_length:",
        length(colMeans(diagnostic_df[diagnostic_trt_index, , drop = FALSE])), "\n")
    cat("Yhat_length:", length(predict(augsynth)), "\n")
    cat("raw_average_length:",
        length(colMeans(diagnostic_df[-diagnostic_trt_index, , drop = FALSE])), "\n")
  })
)

cat("=== EXACT OFFICIAL TWO-LOCATION CALL ===\n")
withCallingHandlers(
  GeoLift::GeoLift(
    Y_id = "Y",
    data = GeoTestData_Test,
    locations = c("chicago", "portland"),
    treatment_start_time = 91,
    treatment_end_time = 105
  ),
  error = function(error) {
    cat("\n=== ERROR CONDITION ===\n")
    cat(conditionMessage(error), "\n")
    cat("\n=== ACTIVE CALL STACK ===\n")
    print(sys.calls())
    cat("\n=== RLANG TRACE ===\n")
    print(rlang::trace_back())
  }
)

close_log()
