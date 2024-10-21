# DeepAux_TxPred_TNBC

This repository contains code and data for applying deep auxiliary task reweighting learning methods to improve treatment response prediction for Triple-Negative Breast Cancer (TNBC). By leveraging transcriptomics data from clinical trials, the study explores auxiliary learning techniques such as ARML, AdaLoss, GradNorm, and OL_AUX to enhance the predictive accuracy of models. These methods are benchmarked against traditional supervised learning and single-task learning baselines, demonstrating superior performance in predicting pathological complete response (pCR) in TNBC patients, even with limited data.

## Data Availability
The RNA-Seq data for TNBC, as well as the corresponding clincial trial treatment labels, can be obtained from the [ClinicalOmicsDB](https://trials.linkedomics.org/) platform.

## Installation

To install the required dependencies, use the `requirements.txt` file provided. Run the following command in your terminal:

```bash
pip install -r requirements.txt
```

This will install all the necessary packages for running the code.

## Running the Code

### Running the Main Pipeline
To run the deep auxiliary task reweighting model with Monte Carlo cross-validation, execute the following bash script:

```bash
bash batch_run_pca_aux.sh
```

This script will run 30 Monte Carlo cross-validation iterations across the datasets available in the `input` directory. Ensure that your input datasets are properly formatted and placed in the appropriate directory before running the script.

### Input Directory
Ensure your RNA-Seq datasets and label files are stored in the `input` folder inside the project structure. The script expects the input files to be in a specific format. You can modify the code if your data has a different format.

### Customizing Parameters
If you want to change the learning parameters, model architecture, or number of cross-validation folds, you can modify the `.sh` scripts or the relevant sections in the Python files located in the main directory.

## Parameter Grids for Baseline Models
The following parameter grids were used for hyperparameter tuning of the baseline models during grid search:

```python
randomforest_grid = {
    "classifier__max_depth": [3, 5, 10],
    "classifier__n_estimators": [50, 100, 200],
    "classifier__min_samples_split": [2, 5, 10],
    "classifier__min_samples_leaf": [1, 2, 5],
    "classifier__max_leaf_nodes": [None, 10, 20],
    "classifier__n_jobs": [10],
}

mlp_grid = {
    "classifier__hidden_layer_sizes": [(5,), (10,)],
    "classifier__alpha": [0.001, 0.01, 0.1],
    "classifier__activation": ["relu"],
    "classifier__solver": ["lbfgs", "adam"],
    "classifier__max_iter": [500, 1000],
    "classifier__learning_rate_init": [0.001, 0.01],
}

logisticregression_grid = {
    "classifier__penalty": ['l2'],
    "classifier__solver": ['saga'],
    "classifier__max_iter": [10000],
    "classifier__class_weight": ['balanced'],
    "classifier__C": [0.01, 0.1, 1, 10],
}

xgboost_grid = {
    "classifier__max_depth": [3, 5, 7, 9],
    "classifier__n_estimators": [50, 100, 200],
    "classifier__learning_rate": [0.01, 0.05, 0.1],
    "classifier__subsample": [0.6, 0.8, 1.0],
    "classifier__colsample_bytree": [0.6, 0.8, 1.0],
}
```

### Preprocessing Pipeline
The following preprocessing pipeline was used before training the models:

```python
preprocessing_pipeline = Pipeline([
    ('variance_threshold', VarianceThreshold(threshold=0)),
    ('select_k_best', SelectKBest(f_classif, k=500)),
    ('scaler', StandardScaler()),
    ('pca', PCA(n_components=10))
])
```

## Reproducing Figures
Each figure related to the study can be reproduced by running the codes or using the pickle model provided in their respective directories:

- **Figure 2**: `fig2_alpha_analysis`
- **Figures 3 & 4**: `fig3_4_update`
- **Figure 5**: `fig5_scatterplot`
- **Figure 6**: `fig6_ind_validation`

To generate figures, navigate into the respective folder and run the associated Python or shell scripts.

## Directory Structure
- `batch_run_pca_aux.sh`: Main bash script to run the Monte Carlo cross-validation.
- `PCA_MLC_*`: Python scripts implementing different auxiliary learning methods (e.g., ARML, GradNorm, etc.).
- `data_utils_PCA.py`: Utility functions for data preprocessing and loading.
- `models.py`: Implementation of the MLCModel used in the experiments.
- `lib`: Collection of auxiliary reweighting algorithms are defined here.


## Contributing
If you would like to contribute to this project, feel free to open a pull request or submit issues if you encounter any bugs.

## Contact
For further information or questions, please contact the repository owner at moonchangin@gmail.com.
