args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) {
  stop("usage: install_dependencies.R DEPENDENCY_LIBRARY")
}
dependency_library <- args[[1]]
dir.create(dependency_library, recursive = TRUE, showWarnings = FALSE)
if (!requireNamespace("LiblineaR", quietly = TRUE, lib.loc = dependency_library)) {
  install.packages(
    "LiblineaR",
    lib = dependency_library,
    repos = "https://cloud.r-project.org",
    dependencies = FALSE
  )
}
cat("LiblineaR", as.character(utils::packageVersion("LiblineaR", lib.loc = dependency_library)), "\n")
