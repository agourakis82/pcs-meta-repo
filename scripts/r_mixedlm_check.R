#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(lme4)
  library(broom.mixed)
  library(readr)
  library(ggplot2)
})

proc <- file.path('data','processed')
merged_csv <- file.path(proc, 'zuco_kec_merged.csv')
rpts <- 'reports'
dir.create(rpts, showWarnings = FALSE, recursive = TRUE)

if (!file.exists(merged_csv)) {
  cat(sprintf('[r_mixedlm_check] INFO: missing %s; skipping\n', merged_csv))
  quit(save='no', status=0)
}

df <- tryCatch(readr::read_csv(merged_csv, show_col_types = FALSE), error=function(e) NULL)
if (is.null(df) || nrow(df) == 0) {
  cat('[r_mixedlm_check] INFO: empty input; skipping\n')
  quit(save='no', status=0)
}

# Ensure needed columns
needed <- c('TRT','log_TRT','entropy','length','log_freq','Subject','SentenceID')
missing <- setdiff(needed, colnames(df))
if (length(missing) > 0) {
  cat(sprintf('[r_mixedlm_check] WARN: missing columns: %s\n', paste(missing, collapse=', ')))
  # Create safe fallbacks
  if (!'log_TRT' %in% colnames(df) && 'TRT' %in% colnames(df)) {
    df$log_TRT <- log1p(pmax(df$TRT, 0))
  }
}

df <- df[complete.cases(df[, intersect(c('log_TRT','entropy','Subject','SentenceID'), colnames(df))]), ]
if (nrow(df) < 200) {
  cat(sprintf('[r_mixedlm_check] INFO: not enough rows after filtering: %d\n', nrow(df)))
  quit(save='no', status=0)
}

# Mixed model with random intercepts
form <- as.formula('log_TRT ~ entropy + (1|Subject) + (1|SentenceID)')
mod <- tryCatch(lmer(form, data=df), error=function(e) NULL)

if (is.null(mod)) {
  cat('[r_mixedlm_check] WARN: MixedLM failed; skipping outputs\n')
  quit(save='no', status=0)
}

sum_txt <- capture.output(summary(mod))
writeLines(sum_txt, file.path(rpts, 'r_mixedlm_trt_summary.txt'))

coef_df <- broom.mixed::tidy(mod, effects='fixed')
readr::write_csv(coef_df, file.path(rpts, 'r_mixedlm_trt_coef.csv'))

cat('[r_mixedlm_check] Wrote reports/r_mixedlm_trt_{summary.txt,coef.csv}\n')
