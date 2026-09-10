options(repos = c(CRAN = "https://cloud.r-project.org"))

required <- c(
  synthdid = "synth-inference/synthdid@70c1ce3eac58e28c30b67435ca377bb48baa9b8a",
  augsynth = "ebenmichael/augsynth@7e70072232fe75057aa8b5d7af08c7e1aef53ae8",
  GeoLift = "facebookincubator/GeoLift@db34ea4299ff0e28515ebac502b78c076c93c905"
)

for (package in names(required)) {
  if (!requireNamespace(package, quietly = TRUE)) {
    remotes::install_github(
      required[[package]],
      dependencies = NA,
      upgrade = "never",
      build_vignettes = FALSE
    )
  }
}

versions <- vapply(
  c("did", "fixest", "CausalImpact", names(required)),
  function(package) {
    if (requireNamespace(package, quietly = TRUE)) {
      as.character(utils::packageVersion(package))
    } else {
      "GATED_NOT_INSTALLED"
    }
  },
  character(1)
)
print(versions)
