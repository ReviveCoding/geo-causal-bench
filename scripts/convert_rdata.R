args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) {
  stop("usage: convert_rdata.R INPUT OUTPUT")
}

loaded <- load(args[[1]])
frames <- loaded[vapply(loaded, function(name) is.data.frame(get(name)), logical(1))]
if (length(frames) == 0) {
  stop("R data file contains no data.frame")
}
if (length(frames) > 1) {
  warning("multiple data.frames found; exporting first: ", frames[[1]])
}
write.csv(get(frames[[1]]), args[[2]], row.names = FALSE)
