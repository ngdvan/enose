# Source description and translation

Source file in the project: `2407/Mô tả bộ dữ liệu hỗn hợp 2 khí NH3 và H2.docx`.
The file is copied byte-for-byte here as `source_description_vi.docx`. Text below was extracted from its document body. The source does not name its author in the body; no authorship is inferred from file properties.

## Vietnamese source text

Mô tả bộ dữ liệu hỗn hợp 2 khí NH3 và H2:

- Gôm 63 tổ hợp hỗn hợp khí NH3 và H2 từ 25 ppm – 500 ppm, đo lặp lại 6 lần thành 378 tổ hợp nồng độ hỗn hợp khí.
- Dư liệu gồm 23 cột: 20 cảm biến khí công nghệ Nano MEMS, cột nồng độ NH3, cột nồng độ H2, cột Combination(số lần đo)
- Mỗi tổ hợp nồng độ đo khoảng 429-430 dòng dữ liệu thành tổng 162404 dòng
- Mỗi hỗn hợp khí có thể cắt từ dòng đầu đến 100 dòng dữ liệu (thử 16,32,64,128)

## English translation

Description of the two-gas NH3 and H2 mixture dataset:

- Contains 63 NH3/H2 gas-mixture combinations from 25 to 500 ppm, measured six times for a total of 378 gas-mixture concentration measurements.
- The data have 23 columns: 20 Nano MEMS gas-sensor channels, an NH3 concentration column, an H2 concentration column, and Combination (measurement number).
- Each concentration combination has approximately 429–430 data rows, giving 162,404 rows in total.
- Each gas-mixture record can be cropped from its beginning to 100 rows (try 16, 32, 64, 128).

The last sentence is a suggested analysis approach, with both 100 and 128 appearing in the source. This package does not impose a crop length or treat this as a measurement-duration specification.

## Evidence and discrepancies

The workbook verifies 23 columns, 20 response channels, 162,404 rows, and 378 contiguous Combination IDs. ppm and Nano MEMS are supported by this companion description. Exact response units, normalization, model names, dates, and collection protocol are not specified.

The workbook contains zero-valued target annotations as well as the stated positive range. There are 57 distinct recorded concentration pairs, not 63 unique pairs. Six inferred blocks of 63 consecutive IDs each contain the same 57 modal pairs; repeated pure-gas exposures explain the extra six exposures per block. Inferred blocks are not independently verified physical sessions.

Observed sequence lengths range from 398 to 481 rows. Eleven rows in IDs 167 and 168 differ from their respective sequence's modal concentration pair. Audit summaries identify this without correcting the supplied data. See reports/DATA_QUALITY.md and reports/label_inconsistencies.csv.

An existing project analysis, `Sensor_Aware_Transfer_Learning/reports/NH3_H2_DETAILED_REPORT.md`, also discusses modal-label correction and inferred sessions. This submission package independently audits the original workbook and does not import that analysis's corrected labels or performance results.
