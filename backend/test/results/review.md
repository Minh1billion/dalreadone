# EDA Review — data.csv
> 50 rows · 11 columns · quality score 0.9956

## Data Quality Issues

### 🟡 `region` — MEDIUM
**What:** 8.0% null values
**Impact:** may lead to biased analysis if left unaddressed

### 🟢 `customer_name` — LOW
**What:** 4.0% null values
**Impact:** may affect customer-level analysis

### 🟢 `quantity` — LOW
**What:** 4.0% outliers
**Impact:** may affect distribution-based analysis

### 🟡 `unit_price` — MEDIUM
**What:** 12.0% outliers
**Impact:** may significantly affect distribution-based analysis

### 🟢 `discount` — LOW
**What:** 32.0% zeros
**Impact:** may indicate a special case or require special handling

## Preprocessing Recommendations

**[MUST]** `handle_nulls` → dataset
replace null values in 'region' and 'customer_name' to prevent biased analysis

**[MUST]** `convert_to_datetime` → `order_date`
enable date-based analysis and filtering

**[SHOULD]** `transform_to_normal` → `quantity`
stabilize variance for more accurate modeling

**[SHOULD]** `remove_outliers` → `unit_price`
prevent outliers from dominating analysis results

**[OPTIONAL]** `handle_zeros` → `discount`
investigate and potentially impute or transform zero discount values

## Analytical Opportunities

- Analyze regional sales trends and preferences
- Investigate customer purchase behavior and loyalty
- Identify top-selling products and categories
- Model the relationship between quantity, unit price, and discount
- Explore seasonality and date-based patterns in sales data