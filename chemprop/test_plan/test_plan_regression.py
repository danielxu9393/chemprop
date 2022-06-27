import os

os.system("python3 ../predict.py --test_path data/tox21.csv --checkpoint_dir tox21_checkpoints2 --preds_path tox21_preds_conformal_multilabel_new.csv --calibration_method conformal --calibration_path data/tox21small.csv")

