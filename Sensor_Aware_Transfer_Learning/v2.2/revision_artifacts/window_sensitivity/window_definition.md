# Window-position sensitivity

The private NH3/H2 workbook supplies each complete exposure as a sequence of L samples. The revised study uses the same exposure roles, seeds, scaler-fitting role, 64-sample input size, training epochs, and full calibration budget for four definitions:

- Early: fitting/pretraining start positions 0 through 4; test start 0.
- Middle: start floor((L-68)/2) through that value plus 4; test uses the first of these.
- Late: start L-68 through L-64; test start L-68, retaining the same five-offset training augmentation convention.
- Full: linear interpolation to 64 points over [offset, L-1], with offsets 0 through 4 for fitting/pretraining and offset 0 for testing.

Scalers are refitted on the appropriate pretraining windows for each definition. The early full-budget result is reused from the fixed-split suite. No test-based choice changes the predefined early-window primary protocol. The analysis concerns sample positions; elapsed seconds cannot be asserted without an authoritative sampling frequency. Full-exposure sensitivity is not claimed for the CO/ethylene cached-window dataset because complete source exposures are not supplied by that cache.
