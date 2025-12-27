#!/usr/bin/env python3
"""Calculate margins for Wardwise template based on page 3 EPIC positions."""

# From analyze_wardwise_epic_positions.py on page 3:
# Row 1: 2 EPICs at y≈364.5, x=[1227, 2004]
# Row 2: 3 EPICs at y≈658.5, x=[442, 1218, 1996]
# Row 3: 3 EPICs at y≈952.0, x=[441, 1219, 1996]
# Row 4: 3 EPICs at y≈1246.8, x=[441, 1218, 1995]
# Row 5: 2 EPICs at y≈1543.0, x=[442, 1218]
#
# Page dimensions: 2480 x 3509 px (same as ZP Boothwise: 2479 x 3508)
# Average row spacing: 294.4 px (same as ZP Boothwise: 294 px)
# Column positions: x≈442, 1218, 1996

page_width = 2480
page_height = 3509

# EPIC positions
first_epic_y = 364.5
last_epic_y = 1543.0
leftmost_epic_x = 441.0
rightmost_epic_x = 2004.5

row_spacing = 294.4
rows = 10  # Standard 3×10 grid
cols = 3

# Calculate margins (similar approach to ZP Boothwise)
# ZP Boothwise: L=65, R=366, T=390, B=138, first EPIC at y=421
# Wardwise: first EPIC at y=364.5 (earlier than ZP), leftmost at x=441

# Use same left margin as ZP Boothwise since column structure is similar
left_margin = 65

# Top: First EPIC at 364.5, give ~30px buffer above
top_margin = int(first_epic_y - 30)  # 364.5 - 30 = 334

# Right: Rightmost EPIC at 2004.5, page width 2480
# For ZP Boothwise: R=366, page width 2479, rightmost EPIC was around 2113
# For Wardwise: rightmost at 2004.5, so R = 2480 - 2004.5 - buffer
# Let's use similar proportion: ZP had ~366 right margin with rightmost ~2113
# Wardwise rightmost is at 2004.5, so: 2480 - 2004.5 ≈ 475
# But to account for column centers, use ~275-366
right_margin = 275

# Bottom: Expected 10 rows with 294px spacing
# Row 1 at 364.5 (after top margin 334), row 10 should be at 364.5 + 9*294 = 3009.5
# Bottom margin: 3509 - 3009.5 - half_row ≈ 3509 - 3009.5 - 150 = ~350
# Let's calculate precisely for 10 rows
expected_usable_height = rows * row_spacing  # 10 * 294 = 2940
bottom_margin = int(page_height - top_margin - expected_usable_height)  # 3509 - 334 - 2940 = 235

print("=" * 60)
print("Wardwise Template Margins Calculation")
print("=" * 60)
print(f"Page dimensions: {page_width} x {page_height} px")
print(f"First EPIC Y: {first_epic_y}")
print(f"Last observed EPIC Y (row 5): {last_epic_y}")
expected_row10_y = first_epic_y + (rows - 1) * row_spacing
print(f"Expected row 10 Y: {expected_row10_y:.1f}")
print(f"Row spacing: {row_spacing} px")
print(f"Leftmost EPIC X: {leftmost_epic_x}")
print(f"Rightmost EPIC X: {rightmost_epic_x}")
print()
print(f"Calculated Margins:")
print(f"  Left:   {left_margin} (from 0 to first column)")
print(f"  Right:  {right_margin} (from last column to {page_width})")
print(f"  Top:    {top_margin} (from 0 to first row)")
print(f"  Bottom: {bottom_margin} (from last row to {page_height})")
print(f"  Rows:   {rows}")
print(f"  Cols:   {cols}")
print()

# Validate: check if these margins make sense
print("Validation:")
usable_width = page_width - left_margin - right_margin
usable_height = page_height - top_margin - bottom_margin
col_width = usable_width / cols
row_height = usable_height / rows

print(f"  Usable width: {usable_width} px → {col_width:.1f} px per column")
print(f"  Usable height: {usable_height} px → {row_height:.1f} px per row")
print(f"  Expected row height (from spacing): {row_spacing} px")

if abs(row_height - row_spacing) < 10:
    print(f"  ✅ Row height matches spacing!")
else:
    print(f"  ⚠️ Row height mismatch: {row_height:.1f} vs {row_spacing}")
    # Adjust bottom margin
    print()
    print("Adjusting bottom margin for exact row spacing...")
    target_usable_height = rows * row_spacing
    adjusted_bottom = int(page_height - top_margin - target_usable_height)
    print(f"  Adjusted Bottom: {adjusted_bottom}")
    bottom_margin = adjusted_bottom

print()
print("=" * 60)
print("FINAL Template Configuration:")
print("=" * 60)
print(f"'wardwise': {{")
print(f"    'name': 'Ward Wise Voter List',")
print(f"    'left': {left_margin},")
print(f"    'right': {right_margin},")
print(f"    'top': {top_margin},")
print(f"    'bottom': {bottom_margin},")
print(f"    'rows': {rows},")
print(f"    'cols': {cols},")
print(f"    'dpi': 300,")
print(f"    'min_word_annotations': 100,")
print(f"    'min_valid_blocks_for_page': 3")
print(f"}}")
