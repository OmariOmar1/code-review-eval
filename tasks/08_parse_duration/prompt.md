# Parse Duration

Write `parse_duration(text)`.

Convert a duration such as `"1h30m"` to a number of seconds (an `int`). The
string is one or more `<integer><unit>` groups, where the unit is `d`, `h`,
`m` or `s`. Units are case-insensitive, groups may be separated by spaces, and
leading or trailing whitespace is ignored. Raise `ValueError` for anything
else, including an empty string, a missing unit, or an unknown unit.
