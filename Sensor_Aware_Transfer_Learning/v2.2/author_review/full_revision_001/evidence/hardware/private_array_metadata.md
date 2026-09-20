# Private NH3/H2 array: source-grounded metadata status

Source inspected: `2407/TONG_NH3H2_CHUAN.xlsx`, the companion dataset description (`UCI_ENose_NH3_H2/provenance/source_description.md` and its original DOCX), existing repository Markdown documentation, and supplied V2.2 manuscript. The workbook establishes 20 response columns and concentration targets; it does not establish the physical details below. The manuscript is a statement of the existing method, not an independent laboratory record.

| Field | Verified status |
|---|---|
| Number of recorded channels | 20, from Response1 through Response20 |
| Gas targets | NH3 and H2, from workbook target columns |
| Concentration range | 0–500 ppm as represented in the supplied manuscript and model scaling; inspect workbook audit for actual coordinates |
| Sensor manufacturer/model | Unavailable in inspected authoritative acquisition records |
| Sensing material/technology | Companion description identifies Nano MEMS technology; channel-specific material remains unverified |
| Number/type of each sensor | Unavailable; channel count alone does not identify sensor types |
| Operating/heater temperature | Unavailable |
| Acquisition circuit | Unavailable |
| Sampling frequency | Unavailable; do not convert samples into seconds |
| Chamber volume | Unavailable |
| Gas source | Unavailable |
| Flow controller | Unavailable |
| Flow rate | Unavailable |
| Carrier/baseline gas | Unavailable |
| Baseline convention | Unavailable; numerical robust scaling is not a physical baseline convention |
| Exposure duration | Sample count can be audited; duration in seconds unavailable |
| Purge duration | Unavailable |
| Ambient temperature | Unavailable |
| Relative humidity | Unavailable |
| Humidity control | Unavailable |
| Reference concentration accuracy | Unavailable |
| Independent physical repetition | Requires acquisition-record confirmation; distinct workbook IDs alone are insufficient |

Manuscript limitation: the missing environmental and acquisition metadata limits reproducibility and prevents attributing gas-dependent channel effects to sensing chemistry. The concentration range is a controlled calibration benchmark and does not validate low-concentration ambient environmental monitoring. No missing value should be invented.

## Sensor-design citation update (2026-09-19)

The author supplied: Dang Thi Thu Ha, Nguyen Dinh Van, Nguyen Duc Hoa, and Nguyen Van Duy, “Design and Analysis of a Volatile Organic Compounds Mixture Dataset for Indoor Air Quality Monitoring,” Springer, 2025, pp. 85–92. DOI: https://doi.org/10.1007/978-3-031-93816-0_11.

Publisher page inspected: https://link.springer.com/chapter/10.1007/978-3-031-93816-0_11. The accessible abstract describes nano-SnO2 sensor-array design for ethanol/acetone/methanol mixtures. Full chapter text was not available through the accessible page. No numerical operating settings were extracted. This supports a related design citation, not an independently verified correspondence to the 20-channel NH3/H2 hardware. Author clarification about that correspondence is pending. The companion NH3/H2 description separately supports the Nano MEMS technology designation. No new physical characterization or experiment was performed.
