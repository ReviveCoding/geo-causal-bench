packages <- c(
  "did", "fixest", "CausalImpact", "synthdid", "augsynth", "GeoLift",
  "jsonlite", "renv"
)
renv::snapshot(
  project = getwd(),
  packages = packages,
  lockfile = file.path(getwd(), "renv.lock"),
  prompt = FALSE,
  force = TRUE
)
