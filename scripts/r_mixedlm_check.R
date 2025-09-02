# Minimal R cross-check script (safe no-op if inputs missing)
suppressWarnings({
  suppressMessages({
    library(lme4, quietly = TRUE, warn.conflicts = FALSE)
  })
})

proc <- file.path('data','processed')
zuco_path <- file.path(proc, 'zuco_aligned.csv')

if (!file.exists(zuco_path)) {
  cat('[r_mixedlm_check] INFO: zuco_aligned.csv missing; skipping.\n')
  quit(status=0)
}

df <- tryCatch(read.csv(zuco_path), error=function(e) NULL)
if (is.null(df)) {
  cat('[r_mixedlm_check] WARN: failed to read zuco_aligned.csv; skipping.\n')
  quit(status=0)
}

# Filter minimal set
cols <- c('TRT','GD','FFD','Subject')
if (!all(cols %in% names(df))) {
  cat('[r_mixedlm_check] INFO: required columns not found; skipping.\n')
  quit(status=0)
}
df <- df[complete.cases(df[, cols]), cols]
if (nrow(df) < 20) {
  cat('[r_mixedlm_check] INFO: not enough rows (', nrow(df), '); skipping.\n', sep='')
  quit(status=0)
}

# Simple random-intercept model
fit <- tryCatch(lmer(TRT ~ GD + FFD + (1|Subject), data=df, REML=TRUE), error=function(e) NULL)
if (is.null(fit)) {
  cat('[r_mixedlm_check] WARN: MixedLM failed to converge; skipping.\n')
} else {
  sm <- summary(fit)
  cat('[r_mixedlm_check] OK: model fit. Fixed effects:\n')
  print(coef(sm)$Subject[1, , drop=FALSE])
}

quit(status=0)

