export interface EDAReport {
  meta: { source: string; generated_at: string }
  schema: {
    n_rows: number; n_cols: number; memory_mb: number
    columns: Array<{
      name: string; dtype: string; inferred_type: string
      n_nulls: number; n_unique: number; first_10_unique_values: any[]
    }>
  }
  missing_and_duplicates: {
    duplicate_rows: number; duplicate_pct: number
    columns: Record<string, { null_count: number; null_pct: number }>
  }
  univariate: {
    numeric: Record<string, {
      mean: number; median: number; std: number
      min: number; max: number; p25: number; p75: number
      skewness: number; kurtosis: number
      zeros_pct: number; outlier_count: number; outlier_pct: number
    }>
    categorical: Record<string, {
      cardinality: number; entropy: number; mode: string; rare_pct: number
      top_values: Array<{ value: string; count: number; pct: number }>
    }>
  }
  datetime: Record<string, {
    min_date: string; max_date: string; date_range_days: number
    inferred_freq: string | null; gaps_count: number | null
    seasonality_hint: string; timezone: string
  }>
  correlations: {
    pearson: Record<string, number>
    cramers_v: Record<string, number>
    top_corr_pairs: Array<{ col_a: string; col_b: string; method: string; value: number }>
  }
  distributions: Record<string, {
    normality_test: { method: string; p_value: number; is_normal: boolean }
    dist_type_hint: string
    histogram_bins: Array<{ range: string; count: number }>
    outlier_summary: {
      count: number
      pct: number
      lower_fence: number
      upper_fence: number
      preview_idx: number[]
    }
  }>
  data_quality_score: {
    completeness: number; consistency: number; uniqueness: number; timeliness: number
    overall_score: number; flags: string[]
  }
}