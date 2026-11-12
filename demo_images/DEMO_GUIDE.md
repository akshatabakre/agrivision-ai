# AgriVision AI - demo images

All images are from the held-out **test sets** (never used in training) and were verified with the current model exactly as the Android app sends them, with **Crop = Auto-detect** and no field context.

| File | Source dataset | Expected diagnosis | Confidence | Severity | Health score |
|---|---|---|---|---|---|
| 01_tomato_early_blight.jpg | PlantDoc (field) | Tomato - Early Blight (Disease) | 92% | Moderate | 62/100 |
| 02_maize_common_rust.jpg | PlantDoc (field) | Maize (Corn) - Common Rust (Disease) | 99% | Mild | 89/100 |
| 03_apple_cedar_apple_rust.jpg | PlantDoc (field) | Apple - Cedar Apple Rust (Disease) | 95% | Mild | 85/100 |
| 04_grape_black_rot.jpg | PlantDoc (field) | Grape - Black Rot (Disease) | 99% | Mild | 79/100 |
| 05_squash_powdery_mildew.jpg | PlantDoc (field) | Squash - Powdery Mildew (Disease) | 100% | Mild | 87/100 |
| 06_potato_late_blight.jpg | PlantVillage (lab) | Potato - Late Blight (Disease) | 100% | Moderate | 69/100 |
| 07_tomato_spider_mite_damage.jpg | PlantVillage (lab) | Tomato - Spider Mite Damage (Pest) | 84% | Mild | 89/100 |
| 08_bell_pepper_bacterial_spot.jpg | PlantVillage (lab) | Bell Pepper - Bacterial Spot (Disease) | 89% | Mild | 89/100 |
| 09_citrus_huanglongbing_citrus_greening.jpg | PlantVillage (lab) | Citrus (Orange) - Huanglongbing (Citrus Greening) (Disease) | 100% | Severe | 39/100 |
| 10_strawberry_healthy_strawberry.jpg | PlantVillage (lab) | Strawberry - Healthy Strawberry (Healthy) | 98% | Healthy | 100/100 |

## extra_safety_checks

- **A_not_a_leaf.jpg** - Rejected: 'No crop leaf was recognised'
- **B_uncertain_recapture.jpg** - Abstains (55% confidence): asks for a re-capture; true class Tomato - Late Blight is its top guess

Confidence can differ by a percent or two from this table because the phone re-compresses the photo.
