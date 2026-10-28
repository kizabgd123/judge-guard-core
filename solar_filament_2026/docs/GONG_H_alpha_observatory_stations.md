# 🔭 GONG Observatory Network & Station Encodings

## 1. Network Topology & Filename Schema
The Global Oscillation Network Group (GONG) consists of six identical observing stations positioned longitudinally around Earth to provide 24-hour continuous monitoring of the Sun.

In the competition dataset, every image filename encodes the exact capture timestamp and telescope site:
Example: `20110120105534Ch.jpeg`
- `20110120`: Year 2011, Month 01, Day 20
- `105534`: Time 10:55:34 UT
- `C`: Station Site Code
- `h`: Observation mode ($\text{H}\alpha$)

## 2. Participating Stations
| Code | Station Name | Location | Climate & Optical Characteristics |
| :--- | :--- | :--- | :--- |
| **B** | Big Bear Solar Observatory | California, USA | High-altitude lake site; sharp seeing, high contrast. |
| **C** | Cerro Tololo Inter-American Obs. | Chile (Atacama) | Dry desert mountain; very low water vapor, stable sky. |
| **L** | Learmonth Solar Observatory | Western Australia | Desert coastal; high solar elevation, occasional marine haze. |
| **M** | Mauna Loa Solar Observatory | Hawaii, USA | Volcano summit ($3,400\text{ m}$); pristine atmospheric transparency. |
| **T** | Observatorio del Teide | Tenerife, Canary Islands | Island volcano peak; minimal atmospheric turbulence. |
| **U** | Udaipur Solar Observatory | Rajasthan, India | Island in lake; tropical monsoon cycles, variable contrast. |

## 3. Implications for Machine Learning Pipelines
1. **Limb Darkening Variations**: Each site exhibits subtle instrument calibration differences and atmospheric scattering that alters disk center-to-limb brightness ratios.
2. **Station Stratification in Cross-Validation**: Validation folds must stratify by station and group by date to prevent data leakage and guarantee that models generalize across all six telescopes.
3. **Contrast Calibration**: Preprocessing must normalize intensity histograms per station to maintain consistent filament absorption profiles across different observatories.
