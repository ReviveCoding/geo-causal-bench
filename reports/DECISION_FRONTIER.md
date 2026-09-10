# Decision Frontier

This is POST-HOC POLICY SENSITIVITY only. The frozen threshold 1.25 is unchanged. Thresholds above 1.25 are partially identified because historically abstained worlds have no committed selected estimate.

| threshold | is_original_frozen_threshold | n | retained_fraction | abstention_rate | coverage | false_launch | false_stop | mean_regret | p95_regret | cvar95_regret | clean_world_retention | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | False | 0 | 0 | 1 | nan | nan | nan | nan | nan | nan | 0 | SUCCESS |
| 0.1 | False | 1 | 0.002 | 0.998 | 1 | 0 | 0 | 0.4 | 0.4 | 0.4 | 0.0104167 | SUCCESS |
| 0.2 | False | 8 | 0.016 | 0.984 | 1 | 0 | 0 | 0.4 | 0.4 | 0.4 | 0.0208333 | SUCCESS |
| 0.3 | False | 41 | 0.082 | 0.918 | 0.95122 | 0.0243902 | 0 | 0.478374 | 0.4 | 0.478374 | 0.125 | SUCCESS |
| 0.4 | False | 120 | 0.24 | 0.76 | 0.933333 | 0.0333333 | 0 | 0.509135 | 0.405 | 2.5827 | 0.28125 | SUCCESS |
| 0.5 | False | 247 | 0.494 | 0.506 | 0.906883 | 0.0364372 | 0 | 0.518282 | 0.47 | 2.64736 | 0.5 | SUCCESS |
| 0.6 | False | 368 | 0.736 | 0.264 | 0.918478 | 0.0271739 | 0 | 0.486994 | 0.4 | 0.488321 | 0.729167 | SUCCESS |
| 0.7 | False | 450 | 0.9 | 0.1 | 0.917778 | 0.0222222 | 0 | 0.471586 | 0.4 | 0.472636 | 0.927083 | SUCCESS |
| 0.8 | False | 480 | 0.96 | 0.04 | 0.908333 | 0.0229167 | 0 | 0.474393 | 0.4 | 0.475383 | 0.979167 | SUCCESS |
| 0.9 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | SUCCESS |
| 1 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | SUCCESS |
| 1.1 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | SUCCESS |
| 1.2 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | SUCCESS |
| 1.25 | True | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | SUCCESS |
| 1.3 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | PARTIAL_IDENTIFICATION_ABOVE_FROZEN_LIMIT |
| 1.4 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | PARTIAL_IDENTIFICATION_ABOVE_FROZEN_LIMIT |
| 1.5 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | PARTIAL_IDENTIFICATION_ABOVE_FROZEN_LIMIT |
| 1.6 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | PARTIAL_IDENTIFICATION_ABOVE_FROZEN_LIMIT |
| 1.7 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | PARTIAL_IDENTIFICATION_ABOVE_FROZEN_LIMIT |
| 1.8 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | PARTIAL_IDENTIFICATION_ABOVE_FROZEN_LIMIT |
| 1.9 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | PARTIAL_IDENTIFICATION_ABOVE_FROZEN_LIMIT |
| 2 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | PARTIAL_IDENTIFICATION_ABOVE_FROZEN_LIMIT |
| 2.25 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | PARTIAL_IDENTIFICATION_ABOVE_FROZEN_LIMIT |
| 2.5 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | PARTIAL_IDENTIFICATION_ABOVE_FROZEN_LIMIT |
| 3 | False | 483 | 0.966 | 0.034 | 0.908903 | 0.0227743 | 0 | 0.473931 | 0.4 | 0.474914 | 0.979167 | PARTIAL_IDENTIFICATION_ABOVE_FROZEN_LIMIT |
