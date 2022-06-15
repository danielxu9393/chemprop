arguments = [
    '--data_path', 'data/delaney.csv',
    '--dataset_type', 'regression',
    '--save_dir', 'delaney_checkpoints_quantile_interval',
    '--loss_function', 'quantile_interval',
    #'--alpha', '0.5'
]
if __name__ ==  '__main__':
    import sys
    sys.path.append('../')
    import chemprop
    args = chemprop.args.TrainArgs().parse_args(arguments)
    mean_score, std_score = chemprop.train.cross_validate(args=args, train_func=chemprop.train.run_training)


#python3 ../predict.py --test_path data/delaney.csv --checkpoint_dir delaney_checkpoints_quantile_interval --preds_path delaney_preds_conformal_quantile_interval.csv --calibration_method conformal_quantile_regression --calibration_path data/delaneysmall.csv
#python3 ../predict.py --test_path data/delaney.csv --checkpoint_dir delaney_checkpoints_quantile_interval --preds_path delaney_preds_conformal_quantile_interval_new.csv --calibration_method conformal_quantile_regression --calibration_path data/delaneysmall.csv

#python3 ../predict.py --test_path data/delaney.csv --checkpoint_dir delaney_checkpoints_quantile_interval05 --preds_path delaney_preds_conformal_quantile_interval05.csv --calibration_method conformal_quantile_regression --alpha 0.5 --calibration_path data/delaneysmall.csv