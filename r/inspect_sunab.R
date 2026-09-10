data("base_stagg", package = "fixest")
fit <- fixest::feols(
  y ~ x1 + sunab(year_treated, year) | id + year,
  data = base_stagg,
  cluster = ~id
)
aggregated <- summary(fit, agg = "ATT")
print(aggregated)
print(stats::coef(aggregated))
str(aggregated$coefficients)
