required <- c(
  "r/inspect_qualification_objects.R",
  "r/inspect_sunab.R",
  "r/qualify_methods.R",
  "scripts/convert_rdata.R",
  "scripts/geolift_compat/candidate_smoke.R",
  "scripts/geolift_compat/compare_fresh_sessions.R",
  "scripts/geolift_compat/diagnose_ordering.R",
  "scripts/geolift_compat/install_dependencies.R",
  "scripts/geolift_compat/reproduce_failure.R",
  "scripts/install_r_packages.R",
  "scripts/post_audit_geolift_operations.R",
  "scripts/snapshot_renv.R",
  "scripts/verify_r_integrity.R"
)

inventory <- sort(c(
  list.files("r", pattern = "[.]R$", recursive = TRUE, full.names = TRUE),
  list.files("scripts", pattern = "[.]R$", recursive = TRUE, full.names = TRUE)
))
stopifnot(identical(sort(required), inventory))
invisible(lapply(inventory, parse))

lock <- paste(readLines("configs/geolift_compatibility.lock.json"), collapse = "\n")
summary <- paste(
  readLines("evidence/geolift_compatibility/qualification_summary.json"),
  collapse = "\n"
)
stopifnot(
  grepl("db34ea4299ff0e28515ebac502b78c076c93c905", lock, fixed = TRUE),
  grepl("65c5a6f34f4e4a8b1011182fe12309ef022d992f", lock, fixed = TRUE),
  grepl("UPSTREAM_PINNED", summary, fixed = TRUE)
)
cat(length(inventory), "R files parsed; compatibility pins verified\n")
