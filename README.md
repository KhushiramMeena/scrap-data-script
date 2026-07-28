# S&P 500 Companies by Founding Year

A shell script that fetches the S&P 500 constituents CSV and prints each company's name, headquarters location, and founding year, sorted by year (oldest first).

## Requirements

- `bash`
- `curl`
- `python3`

## Usage

```bash
# Use the default S&P 500 CSV URL
./sp500_by_founding_year.sh

# Or pass a custom CSV URL
./sp500_by_founding_year.sh "https://example.com/constituents.csv"
```

## Example Output

```
Year    Company                                   Location
----    -------                                   --------
1784    BNY Mellon                                New York City, New York
1792    State Street Corporation                  Boston, Massachusetts
1806    Colgate-Palmolive                         New York City, New York
...
```

## Data Source

Default CSV: [S&P 500 Companies dataset](https://github.com/datasets/s-and-p-500-companies)

## Notes

- The script uses Python for CSV parsing because location fields contain commas inside quoted values.
- Founding years like `2013 (1888)` are sorted by the first 4-digit year in the field.
