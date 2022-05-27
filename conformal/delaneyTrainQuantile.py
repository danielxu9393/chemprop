arguments = [
    '--data_path', 'data/delaney.csv',
    '--dataset_type', 'regression',
    '--save_dir', 'delaney_checkpoints_quantile09',
    '--loss_function', 'quantile'
]
if __name__ ==  '__main__':
    import sys
    sys.path.append('../')
    import chemprop
    args = chemprop.args.TrainArgs().parse_args(arguments)
    mean_score, std_score = chemprop.train.cross_validate(args=args, train_func=chemprop.train.run_training)


#python3 ../predict.py --test_path data/delaney.csv --checkpoint_dir delaney_checkpoints_quantile01 --preds_path delaney_preds_quantile01.csv
#python3 ../predict.py --test_path data/delaney.csv --checkpoint_dir delaney_checkpoints_quantile09 --preds_path delaney_preds_quantile09.csv