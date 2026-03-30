# EKCC vs LGD Comparison Tool

This project compares EKCC and LGD administrative data for:

- `state`
- `district`
- `subdistrict`
- `village`

It extracts only the required columns, maps hierarchy using codes, and generates comparison files for:

- `insert`
- `rename`
- `update`

## Files

- [app.py](/Users/palrpatel/Desktop/FINALFIX/app.py): Streamlit frontend
- [extract.py](/Users/palrpatel/Desktop/FINALFIX/extract.py): extracts required columns from uploaded files
- [compare.py](/Users/palrpatel/Desktop/FINALFIX/compare.py): compares EKCC vs LGD outputs
- [load.py](/Users/palrpatel/Desktop/FINALFIX/load.py): loads all source files into individual DataFrames

## Features

- Upload files manually in the frontend
- Works with full upload of all 8 files
- Works with partial matching uploads like:
  - only `district`
  - only `subdistrict`
  - only `village`
  - `district + subdistrict + village`
- Generates extracted output files
- Generates comparison output files
- Lets you preview and download CSVs from the UI

## Run Locally

From the project folder:

```bash
cd /Users/palrpatel/Desktop/FINALFIX
streamlit run app.py
```

## Upload Flow

In the Streamlit app:

1. Upload the EKCC and LGD files you want to compare
2. Click `Save Uploaded Files`
3. Click `Generate Required Columns`
4. Click `Generate Comparison Files`
5. Preview or download the results

## Upload File Names

These are the file headers / file names expected by the app upload flow:

### EKCC

- `ekcc_state.csv`
- `ekcc_district.csv`
- `ekcc_subdistrict.csv`
- `ekcc_village.csv`

### LGD

- `lgd_state.csv`
- `lgd_district.csv`
- `lgd_subdistrict.csv`
- `lgd_village.csv`

## Comparison Logic

### Insert

Rows present in LGD but not present in EKCC by code.

### Rename

Rows where the main code is the same in EKCC and LGD, but the name is different.

### Update

Rows where the main code is the same in EKCC and LGD, but mapped parent code values are different.

Examples:

- district update compares `State Code`
- subdistrict update compares `District Code`
- village update compares:
  - `Village Census Code`
  - `Sub District Code`
  - `District Code`

## Output Folders

- `required_columns_output/`
- `comparison_output/`
- `streamlit_workspace/`

These are ignored in Git by [.gitignore](/Users/palrpatel/Desktop/FINALFIX/.gitignore).

## Notes

- LGD files may be uploaded with `.csv` names even when they are actually Excel workbooks.
- Missing code values are filled as `code is not mention`.
- Mapping is based on code or source ID relationships, not name-based matching.
