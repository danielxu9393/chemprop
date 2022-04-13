from typing import Iterator, List

import numpy as np
from scipy.special import erf

from chemprop.data import MoleculeDataset, StandardScaler, MoleculeDataLoader
from chemprop.models import MoleculeModel
from chemprop.train import predict

# Should there be an intermediate class inheritor for dataset type?
class UncertaintyPredictor:
    def __init__(self, test_data: MoleculeDataset,
                       models: Iterator[MoleculeModel],
                       scalers: Iterator[StandardScaler],
                       dataset_type: str,
                       loss_function: str,
                       batch_size: int,
                       num_workers: int,
                       dropout_sampling_size: int,
                       ):
        self.test_data = test_data
        self.models = models
        self.scalers = scalers
        self.dataset_type = dataset_type
        self.loss_function = loss_function
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.uncal_preds = None
        self.uncal_vars = None
        self.uncal_confidence = None
        self.uncal_output = None
        self.individual_vars = None
        self.num_models = len(self.models)
        self.dropout_sampling_size = dropout_sampling_size

        self.raise_argument_errors()
        self.test_data_loader=MoleculeDataLoader(
            dataset=self.test_data,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
        )
        self.calculate_predictions()
    
    def raise_argument_errors(self):
        """
        Raise errors for incompatible dataset types or uncertainty methods, etc.
        """
        pass

    def calculate_predictions(self):
        """
        Calculate the uncalibrated predictions and store them as attributes
        """
        pass
    
    def get_uncal_preds(self):
        """Return the predicted values for the test data."""
        return self.uncal_preds

    def get_uncal_vars(self):
        """Return the uncalibrated variances for the test data"""
        return self.uncal_vars

    def get_uncal_confidence(self):
        """Return the uncalibrated confidences for the test data"""
        return self.uncal_confidence
    
    def get_individual_vars(self):
        """Return the variances predicted by each individual model in an ensemble."""
        return self.individual_vars
    
    def get_uncal_output(self):
        """Return the uncalibrated uncertainty outputs for the test data"""
        pass

class MVEPredictor(UncertaintyPredictor):
    def __init__(self, test_data: MoleculeDataset, models: Iterator[MoleculeModel], scalers: Iterator[StandardScaler], dataset_type: str, loss_function: str, batch_size: int, num_workers: int, dropout_sampling_size: int):
        super().__init__(test_data, models, scalers, dataset_type, loss_function, batch_size, num_workers, dropout_sampling_size)
        self.label = 'mve_uncal_var'

    def raise_argument_errors(self):
        super().raise_argument_errors()
        if self.loss_function != 'mve':
            raise ValueError('In order to use mve uncertainty, trained models must have used mve loss function.')

    def calculate_predictions(self):
        for i in range(self.num_models):

            scaler, features_scaler, atom_descriptor_scaler, bond_feature_scaler = self.scalers[i]
            if features_scaler is not None or atom_descriptor_scaler is not None or bond_feature_scaler is not None:
                self.test_data.reset_features_and_targets()
                if features_scaler is not None:
                    self.test_data.normalize_features(features_scaler)
                if atom_descriptor_scaler is not None:
                    self.test_data.normalize_features(atom_descriptor_scaler, scale_atom_descriptors=True)
                if bond_feature_scaler is not None:
                    self.test_data.normalize_features(bond_feature_scaler, scale_bond_features=True)

            preds, var = predict(
                model=self.models[i],
                data_loader=self.test_data_loader,
                scaler=scaler,
                return_unc_parameters=True,
            )
            if i == 0:
                sum_preds = np.array(preds)
                sum_squared = np.square(preds)
                sum_vars = np.array(var)
                individual_vars = [var]
            else:
                sum_preds += np.array(preds)
                sum_squared += np.square(preds)
                sum_vars += np.array(var)
                individual_vars.append(var)

        uncal_preds = sum_preds / self.num_models
        uncal_vars = (sum_vars + sum_squared) / self.num_models - np.square(sum_preds / self.num_models)
        self.uncal_preds, self.uncal_vars = uncal_preds.tolist(), uncal_vars.tolist()
        self.individual_vars = individual_vars

    def get_uncal_output(self):
        return self.uncal_vars


class EvidentialTotalPredictor(UncertaintyPredictor):
    def __init__(self, test_data: MoleculeDataset, models: Iterator[MoleculeModel], scalers: Iterator[StandardScaler], dataset_type: str, loss_function: str, batch_size: int, num_workers: int):
        super().__init__(test_data, models, scalers, dataset_type, loss_function, batch_size, num_workers)
        self.label = 'evidential_total_uncal_var'

    def raise_argument_errors(self):
        super().raise_argument_errors()
        if self.loss_function != 'evidential':
            raise ValueError('In order to use evidential uncertainty, trained models must have used evidential regression loss function.')
        if self.dataset_type != 'regression':
            raise ValueError('Evidential total uncertainty is only compatible with regression dataset types.')


    def calculate_predictions(self):
        for i in range(self.num_models):

            scaler, features_scaler, atom_descriptor_scaler, bond_feature_scaler = self.scalers[i]
            if features_scaler is not None or atom_descriptor_scaler is not None or bond_feature_scaler is not None:
                self.test_data.reset_features_and_targets()
                if features_scaler is not None:
                    self.test_data.normalize_features(features_scaler)
                if atom_descriptor_scaler is not None:
                    self.test_data.normalize_features(atom_descriptor_scaler, scale_atom_descriptors=True)
                if bond_feature_scaler is not None:
                    self.test_data.normalize_features(bond_feature_scaler, scale_bond_features=True)

            preds, lambdas, alphas, betas = predict(
                model=self.models[i],
                data_loader=self.test_data_loader,
                scaler=scaler,
                return_unc_parameters=True,
            )
            if i == 0:
                var = np.array(betas) * (1 + 1 / np.array(lambdas)) / (np.array(alphas) - 1)
                sum_preds = np.array(preds)
                sum_squared = np.square(preds)
                sum_vars = np.array(var)
                individual_vars = [var]
            else:
                var = np.array(betas) * (1 + 1 / np.array(lambdas)) / (np.array(alphas) - 1)
                sum_preds += np.array(preds)
                sum_squared += np.square(preds)
                sum_vars += np.array(var)
                individual_vars.append(var)

        uncal_preds = sum_preds / self.num_models
        uncal_vars = (sum_vars + sum_squared) / self.num_models - np.square(sum_preds / self.num_models)
        self.uncal_preds, self.uncal_vars = uncal_preds.tolist(), uncal_vars.tolist()
        self.individual_vars = individual_vars

    def get_uncal_output(self):
        return self.uncal_vars


class EvidentialAleatoricPredictor(UncertaintyPredictor):
    def __init__(self, test_data: MoleculeDataset, models: Iterator[MoleculeModel], scalers: Iterator[StandardScaler], dataset_type: str, loss_function: str, batch_size: int, num_workers: int):
        super().__init__(test_data, models, scalers, dataset_type, loss_function, batch_size, num_workers)
        self.label = 'evidential_aleatoric_uncal_var'

    def raise_argument_errors(self):
        super().raise_argument_errors()
        if self.loss_function != 'evidential':
            raise ValueError('In order to use evidential uncertainty, trained models must have used evidential regression loss function.')
        if self.dataset_type != 'regression':
            raise ValueError('Evidential aleatoric uncertainty is only compatible with regression dataset types.')


    def calculate_predictions(self):
        for i in range(self.num_models):

            scaler, features_scaler, atom_descriptor_scaler, bond_feature_scaler = self.scalers[i]
            if features_scaler is not None or atom_descriptor_scaler is not None or bond_feature_scaler is not None:
                self.test_data.reset_features_and_targets()
                if features_scaler is not None:
                    self.test_data.normalize_features(features_scaler)
                if atom_descriptor_scaler is not None:
                    self.test_data.normalize_features(atom_descriptor_scaler, scale_atom_descriptors=True)
                if bond_feature_scaler is not None:
                    self.test_data.normalize_features(bond_feature_scaler, scale_bond_features=True)

            preds, lambdas, alphas, betas = predict(
                model=self.models[i],
                data_loader=self.test_data_loader,
                scaler=scaler,
                return_unc_parameters=True,
            )
            if i == 0:
                var = np.array(betas) / (np.array(alphas) - 1)
                sum_preds = np.array(preds)
                sum_squared = np.square(preds)
                sum_vars = np.array(var)
                individual_vars = [var]
            else:
                var = np.array(betas) / (np.array(alphas) - 1)
                sum_preds += np.array(preds)
                sum_squared += np.square(preds)
                sum_vars += np.array(var)
                individual_vars.append(var)

        uncal_preds = sum_preds / self.num_models
        uncal_vars = (sum_vars + sum_squared) / self.num_models - np.square(sum_preds / self.num_models)
        self.uncal_preds, self.uncal_vars = uncal_preds.tolist(), uncal_vars.tolist()
        self.individual_vars = individual_vars

    def get_uncal_output(self):
        return self.uncal_vars


class EvidentialEpistemicPredictor(UncertaintyPredictor):
    def __init__(self, test_data: MoleculeDataset, models: Iterator[MoleculeModel], scalers: Iterator[StandardScaler], dataset_type: str, loss_function: str, batch_size: int, num_workers: int):
        super().__init__(test_data, models, scalers, dataset_type, loss_function, batch_size, num_workers)
        self.label = 'evidential_epistemic_uncal_var'

    def raise_argument_errors(self):
        super().raise_argument_errors()
        if self.loss_function != 'evidential':
            raise ValueError('In order to use evidential uncertainty, trained models must have used evidential regression loss function.')
        if self.dataset_type != 'regression':
            raise ValueError('Evidential epistemic uncertainty is only compatible with regression dataset types.')


    def calculate_predictions(self):
        for i in range(self.num_models):

            scaler, features_scaler, atom_descriptor_scaler, bond_feature_scaler = self.scalers[i]
            if features_scaler is not None or atom_descriptor_scaler is not None or bond_feature_scaler is not None:
                self.test_data.reset_features_and_targets()
                if features_scaler is not None:
                    self.test_data.normalize_features(features_scaler)
                if atom_descriptor_scaler is not None:
                    self.test_data.normalize_features(atom_descriptor_scaler, scale_atom_descriptors=True)
                if bond_feature_scaler is not None:
                    self.test_data.normalize_features(bond_feature_scaler, scale_bond_features=True)

            preds, lambdas, alphas, betas = predict(
                model=self.models[i],
                data_loader=self.test_data_loader,
                scaler=scaler,
                return_unc_parameters=True,
            )
            if i == 0:
                var = np.array(betas) / (np.array(lambdas) * (np.array(alphas) - 1))
                sum_preds = np.array(preds)
                sum_squared = np.square(preds)
                sum_vars = np.array(var)
                individual_vars = [var]
            else:
                var = np.array(betas) / (np.array(lambdas) * (np.array(alphas) - 1))
                sum_preds += np.array(preds)
                sum_squared += np.square(preds)
                sum_vars += np.array(var)
                individual_vars.append(var)

        uncal_preds = sum_preds / self.num_models
        uncal_vars = (sum_vars + sum_squared) / self.num_models - np.square(sum_preds / self.num_models)
        self.uncal_preds, self.uncal_vars = uncal_preds.tolist(), uncal_vars.tolist()
        self.individual_vars = individual_vars

    def get_uncal_output(self):
        return self.uncal_vars


class EnsemblePredictor(UncertaintyPredictor):
    def __init__(self, test_data: MoleculeDataset, models: Iterator[MoleculeModel], scalers: Iterator[StandardScaler], dataset_type: str, loss_function: str, batch_size: int, num_workers: int, dropout_sampling_size: int):
        super().__init__(test_data, models, scalers, dataset_type, loss_function, batch_size, num_workers, dropout_sampling_size)
        self.label = 'ensemble_uncal_var'

    def raise_argument_errors(self):
        super().raise_argument_errors()
        if len(self.models) == 1:
            raise ValueError('Ensemble method for uncertainty is only available when multiple models are provided.')
    
    def calculate_predictions(self):
        for i in range(self.num_models):
            scaler, features_scaler, atom_descriptor_scaler, bond_feature_scaler = self.scalers[i]
            if features_scaler is not None or atom_descriptor_scaler is not None or bond_feature_scaler is not None:
                self.test_data.reset_features_and_targets()
                if features_scaler is not None:
                    self.test_data.normalize_features(features_scaler)
                if atom_descriptor_scaler is not None:
                    self.test_data.normalize_features(atom_descriptor_scaler, scale_atom_descriptors=True)
                if bond_feature_scaler is not None:
                    self.test_data.normalize_features(bond_feature_scaler, scale_bond_features=True)
            preds = predict(
                model=self.models[i],
                data_loader=self.test_data_loader,
                scaler=scaler,
                return_unc_parameters=False,
            )
            if i == 0:
                sum_preds = np.array(preds)
                sum_squared = np.square(preds)
            else:
                sum_preds += np.array(preds)
                sum_squared += np.square(preds)
        self.uncal_preds = sum_preds / self.num_models
        self.uncal_vars = sum_squared / self.num_models - np.square(sum_preds) / self.num_models ** 2
    
    def get_uncal_output(self):
        return self.uncal_vars


class DropoutPredictor(UncertaintyPredictor):
    def __init__(self, test_data: MoleculeDataset, models: Iterator[MoleculeModel], scalers: Iterator[StandardScaler], dataset_type: str, loss_function: str, batch_size: int, num_workers: int, dropout_sampling_size: int):
        super().__init__(test_data, models, scalers, dataset_type, loss_function, batch_size, num_workers, dropout_sampling_size)
        self.label = "dropout_uncal_var"

    def raise_argument_errors(self):
        super().raise_argument_errors()
        if self.num_models > 1:
            raise ValueError('Dropout method for uncertainty should be used for a single model rather than an ensemble.')

    def calculate_predictions(self):
        for i in range(self.dropout_sampling_size):
            scaler, features_scaler, atom_descriptor_scaler, bond_feature_scaler = self.scalers[0]
            if features_scaler is not None or atom_descriptor_scaler is not None or bond_feature_scaler is not None:
                self.test_data.reset_features_and_targets()
                if features_scaler is not None:
                    self.test_data.normalize_features(features_scaler)
                if atom_descriptor_scaler is not None:
                    self.test_data.normalize_features(atom_descriptor_scaler, scale_atom_descriptors=True)
                if bond_feature_scaler is not None:
                    self.test_data.normalize_features(bond_feature_scaler, scale_bond_features=True)
            preds = predict(
                model=self.models[0],
                data_loader=self.test_data_loader,
                scaler=scaler,
                return_unc_parameters=False,
            )
            if i == 0:
                sum_preds = np.array(preds)
                sum_squared = np.square(preds)
            else:
                sum_preds += np.array(preds)
                sum_squared += np.square(preds)
        self.uncal_preds = sum_preds / self.dropout_sampling_size
        self.uncal_vars = sum_squared / self.dropout_sampling_size - np.square(sum_preds) / self.dropout_sampling_size**2

    def get_uncal_output(self):
        return self.uncal_vars


class ClassPredictor(UncertaintyPredictor):
    """
    Class uses the [0,1] range of results from classification or multiclass models as the indicator of confidence.
    """
    def __init__(self, test_data: MoleculeDataset, models: Iterator[MoleculeModel], scalers: Iterator[StandardScaler], dataset_type: str, loss_function: str, batch_size: int, num_workers: int):
        super().__init__(test_data, models, scalers, dataset_type, loss_function, batch_size, num_workers)
        self.label = 'classification_uncal_confidence'

    def raise_argument_errors(self):
        super().raise_argument_errors()
        if self.dataset_type not in ['classification', 'multiclass']:
            raise ValueError('Classification output uncertainty method must be used with dataset types classification or multiclass.')
    
    def calculate_predictions(self):
        for i in range(self.num_models):
            scaler, features_scaler, atom_descriptor_scaler, bond_feature_scaler = self.scalers[i]
            if features_scaler is not None or atom_descriptor_scaler is not None or bond_feature_scaler is not None:
                self.test_data.reset_features_and_targets()
                if features_scaler is not None:
                    self.test_data.normalize_features(features_scaler)
                if atom_descriptor_scaler is not None:
                    self.test_data.normalize_features(atom_descriptor_scaler, scale_atom_descriptors=True)
                if bond_feature_scaler is not None:
                    self.test_data.normalize_features(bond_feature_scaler, scale_bond_features=True)
            preds = predict(
                model=self.models[i],
                data_loader=self.test_data_loader,
                scaler=scaler,
                return_unc_parameters=False,
            )
            if i == 0:
                sum_preds = np.array(preds)
            else:
                sum_preds += np.array(preds)
        self.uncal_preds = sum_preds / self.num_models
        self.uncal_confidence = self.uncal_preds
    
    def get_uncal_output(self):
        return self.uncal_confidence


def uncertainty_predictor_builder(uncertainty_method: str,
                                  test_data: MoleculeDataset,
                                  models: Iterator[MoleculeModel],
                                  scalers: Iterator[StandardScaler],
                                  dataset_type: str,
                                  loss_function: str,
                                  batch_size: int,
                                  num_workers: int,
                                  dropout_sampling_size: int,
                                  ) -> UncertaintyPredictor:
    """
    
    """
    if uncertainty_method is None:
        if loss_function == 'mve':
            uncertainty_method = 'mve'
        elif dataset_type == 'regression':
            if loss_function == 'evidential':
                uncertainty_method = 'evidential_epistemic'
            elif len(models) > 1:
                uncertainty_method = 'ensemble'
            else:
                uncertainty_method = 'dropout'
        elif dataset_type == 'classification':
            uncertainty_method = 'classification'
        elif dataset_type == 'multiclass':
            uncertainty_method = 'sigmoid'
        elif dataset_type == 'spectra':
            raise ValueError('Uncertainty quantification not currently enabled for spectra')

    supported_predictors = {
        'mve': MVEPredictor,
        'ensemble': EnsemblePredictor,
        'classification': ClassPredictor,
        'evidential_total': EvidentialTotalPredictor,
        'evidential_epistemic': EvidentialEpistemicPredictor,
        'evidential_aleatoric': EvidentialAleatoricPredictor,
        "dropout": DropoutPredictor,
    }

    estimator_class = supported_predictors.get(uncertainty_method, None)
    
    if estimator_class is None:
        raise NotImplementedError(f'Uncertainty estimator type {uncertainty_method} is not currently supported. Avalable options are: {list(supported_predictors.keys())}')
    else:
        estimator = estimator_class(
            test_data=test_data,
            models=models,
            scalers=scalers,
            dataset_type=dataset_type,
            loss_function=loss_function,
            batch_size=batch_size,
            num_workers=num_workers,
            dropout_sampling_size=dropout_sampling_size,
        )
    return estimator