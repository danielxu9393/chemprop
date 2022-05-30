arguments = [
    '--data_path', 'data/delaney.csv',
    '--dataset_type', 'regression',
    '--save_dir', 'delaney_checkpoints_quantile_interval',
    '--loss_function', 'quantile_interval',
    '--alpha', '0.1'
]
if __name__ ==  '__main__':
    import sys
    sys.path.append('../')
    import chemprop
    args = chemprop.args.TrainArgs().parse_args(arguments)
    mean_score, std_score = chemprop.train.cross_validate(args=args, train_func=chemprop.train.run_training)

