alpha_list = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
#alpha_list = [0.1]

if __name__ ==  '__main__':
    import sys
    sys.path.append('../')
    import chemprop

    for alpha in alpha_list:
        arguments = [
                        '--data_path', 'data/delaney3class1.csv',
                        '--dataset_type', 'regression',
                        '--save_dir', f'quantile_regression/delaney_checkpoints_3class1_quantile_{alpha}',
                        '--loss_function', 'quantile_interval',
                        '--quantile_loss_alpha', f'{alpha}'
                    ]

        args = chemprop.args.TrainArgs().parse_args(arguments)
        mean_score, std_score = chemprop.train.cross_validate(args=args, train_func=chemprop.train.run_training)