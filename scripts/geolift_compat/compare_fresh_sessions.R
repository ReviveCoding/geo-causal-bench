args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) {
  stop("usage: compare_fresh_sessions.R FIRST_JSON SECOND_JSON OUTPUT_JSON")
}
first <- jsonlite::read_json(args[[1]], simplifyVector = TRUE)
second <- jsonlite::read_json(args[[2]], simplifyVector = TRUE)

canonical <- function(result) {
  list(
    package_versions = result$package_versions,
    description_sha256 = result$description_sha256,
    cases = result$cases,
    invariants = result$invariants
  )
}

identical_results <- identical(canonical(first), canonical(second))
payload <- list(
  evidence_class = "UPSTREAM_PINNED",
  extension_id = "GEOLIFT-COMPAT-001",
  status = if (identical_results) "PASS" else "FAIL",
  fresh_session_reproducible = identical_results,
  first = args[[1]],
  second = args[[2]]
)
dir.create(dirname(args[[3]]), recursive = TRUE, showWarnings = FALSE)
jsonlite::write_json(payload, args[[3]], pretty = TRUE, auto_unbox = TRUE)
if (!identical_results) {
  stop("fresh-session results differ")
}
cat("FRESH_SESSION_REPRODUCIBILITY_PASS\n")
