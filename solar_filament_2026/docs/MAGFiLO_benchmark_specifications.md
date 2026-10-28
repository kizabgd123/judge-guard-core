# 🌞 MAGFiLO Benchmark Specifications & Solar Filament Science

## 1. Overview of the MAGFiLO Dataset
**MAGFiLO** (*Manually Annotated GONG Filaments in H-alpha Observations*) is the largest scientific benchmark dataset for solar filament detection, segmentation, and morphology characterization.
- **Telescope Network**: Global Oscillation Network Group (GONG), operated by the National Solar Observatory (NSO).
- **Wavelength**: H-alpha ($\text{H}\alpha$ line at $656.28\text{ nm}$), observing the solar chromosphere.
- **Dataset Composition**: 10,244 manually annotated solar filaments across 1,593 full-disk observations (2011–2022).
- **Label Structure**:
  - Pixel-precise binary segmentation masks for individual filament instances.
  - Spines / medial skeletons representing filament axis trajectories.
  - Minimum bounding boxes.
  - Magnetic chirality (dextral vs sinistral orientation).

## 2. Solar Filament Physical Characteristics
- **Nature**: Cool ($10^4\text{ K}$), dense plasma clouds suspended above the solar photosphere inside the hot ($10^6\text{ K}$) solar corona by magnetic flux ropes.
- **Appearance in $\text{H}\alpha$**: Appear as dark, absorption absorption features against the bright solar disk, and as bright "prominences" when seen at the solar limb.
- **Morphology Challenges**:
  - Extreme aspect ratios: long, thread-like filaments with narrow widths (often 2–10 pixels wide at full disk resolution).
  - Fractured appearances: filaments frequently break into distinct segments due to magnetic topology or optical limb effects.
  - Inter-annotator variance: Ground truth exhibits human disagreement regarding whether two nearby threads belong to a single continuous filament or separate structures.

## 3. Kaggle Competition Context (`filament-segmentation-2026`)
- **Image Resolution**: $2048 \times 2048$ pixels, grayscale or single-channel compressed JPEG.
- **Evaluation Set**: 180 full-disk test images.
- **Inference Constraints**: Strictly offline; only test directory $\text{H}\alpha$ images allowed.
- **Primary Metric**: Panoptic Quality (PQ) combining Segmentation Quality (SQ) and Recognition Quality (RQ) over instances with $\text{IoU} \ge 0.5$.
