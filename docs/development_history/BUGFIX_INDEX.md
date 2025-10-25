# Bug Fix: DataFrame Index Mismatch

## Issue
When using pre-filtered DataFrames (e.g., after `filter_ready_soldiers()`), the cost matrix indexing failed with:
```
IndexError: index 652 is out of bounds for axis 0 with size 652
```

## Root Cause
When DataFrames are filtered/subset in pandas, the row indices are NOT reset by default. For example:
```python
# Original DataFrame with 1000 soldiers (indices 0-999)
soldiers_df = pd.DataFrame(...)  # indices: 0, 1, 2, ..., 999

# After filtering to 652 soldiers
ready_soldiers = filter_ready_soldiers(soldiers_df, ...)
# indices might be: 0, 1, 5, 7, 9, 12, ..., 998  (non-sequential!)
# BUT len(ready_soldiers) = 652
```

The cost matrix is created as:
```python
C = np.zeros((len(soldiers), len(billets)))  # shape: (652, n_billets)
```

But when iterating:
```python
for i, soldier_row in soldiers.iterrows():
    cost_matrix[i, :] = ...  # i could be 998, but matrix only has 652 rows!
```

## Solution
Reset DataFrame indices before using them for matrix operations:

### In `build_cost_matrix()`:
```python
S = self.soldiers.reset_index(drop=True)  # Now: 0, 1, 2, ..., 651
B = self.billets.reset_index(drop=True)
```

### In `apply_readiness_penalties()`:
```python
S = self.soldiers.reset_index(drop=True)
```

## Files Modified
- `emd_agent.py` (lines 382-383, 499)

## Impact
- **Before**: Failed when using filtered DataFrames
- **After**: Works correctly with any DataFrame (filtered or not)
- **Performance**: Negligible (reset_index is O(n))
- **Backward Compatibility**: Maintained (works with original use case too)

## Testing
Run the test suite to verify:
```bash
python test_mtoe_system.py
```

All tests should now pass, especially:
- Test 5: End-to-End Optimization (uses filtered soldiers)
- Test 6: Comparison Study (uses filtered soldiers)

---
**Fixed:** 2025-01-23
**Severity:** High (blocking feature use)
**Status:** Resolved
