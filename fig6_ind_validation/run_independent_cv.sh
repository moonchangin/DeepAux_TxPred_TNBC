#!/bin/bash
# run_independent_cv.sh will accept argument file directory such as "/home/cimoon/multi_label_classification/clindb_breast_TNBC/processed_TNBC_CV_GSE163882_train_GSE123845_ind"
# then the bash file will recognize GSE163882 and GSE123845 as main task file and ind task file and replace on the file names below
# mccv can be inputed as a arugment to update each file mccv

# Usage: ./run_independent_cv.sh <directory> <mccv>
# Example: ./run_independent_cv.sh /home/cimoon/multi_label_classification/clindb_breast_TNBC/processed_TNBC_CV_GSE163882_train_GSE123845_ind 1

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <directory> <mccv>"
    exit 1
fi

DIRECTORY=$1
MCCV=$2

# Extract the main task file and independent task file names from the directory
IFS='_' read -r -a array <<< "$(basename $DIRECTORY)"
MAIN_TASK_FILE=${array[3]}
IND_TASK_FILE=${array[5]}

# Construct the file paths
MAIN_TASK_PATH="/home/cimoon/multi_label_classification/clindb_breast_TNBC/processed_TNBC_CV_${MAIN_TASK_FILE}_train_${IND_TASK_FILE}_ind/${MAIN_TASK_FILE}_filtered.csv"
IND_TASK_PATH="/home/cimoon/multi_label_classification/clindb_breast_TNBC/processed_TNBC_CV_${MAIN_TASK_FILE}_train_${IND_TASK_FILE}_ind/${IND_TASK_FILE}_filtered.csv"
# /home/cimoon/multi_label_classification/clindb_breast_TNBC/processed_TNBC_CV_GSE163882_train_GSE123845_ind/GSE163882_filtered.csv

# Run the python scripts with the correct file paths
python /home/cimoon/multi_label_classification/bing_tnbc_analysis/PCA_baseline_SL.py --mccv=${MCCV} --main_task_file=${MAIN_TASK_PATH} --ind_task_file=${IND_TASK_PATH}
python /home/cimoon/multi_label_classification/bing_tnbc_analysis/PCA_MLC_adaloss.py --mccv=${MCCV} --main_task_file=${MAIN_TASK_PATH} --ind_task_file=${IND_TASK_PATH}
python /home/cimoon/multi_label_classification/bing_tnbc_analysis/PCA_MLC_aux_learn.py --mccv=${MCCV} --main_task_file=${MAIN_TASK_PATH} --ind_task_file=${IND_TASK_PATH}
python /home/cimoon/multi_label_classification/bing_tnbc_analysis/PCA_MLC_gradnorm.py --mccv=${MCCV} --main_task_file=${MAIN_TASK_PATH} --ind_task_file=${IND_TASK_PATH}
python /home/cimoon/multi_label_classification/bing_tnbc_analysis/PCA_MLC_ol_aux.py --mccv=${MCCV} --main_task_file=${MAIN_TASK_PATH} --ind_task_file=${IND_TASK_PATH}
python /home/cimoon/multi_label_classification/bing_tnbc_analysis/PCA_single_task_learn.py --mccv=${MCCV} --main_task_file=${MAIN_TASK_PATH} --ind_task_file=${IND_TASK_PATH}

# Create the output directory
OUTPUT_DIR="/home/cimoon/multi_label_classification/output/bing_tnbc/${MAIN_TASK_FILE}_train_${IND_TASK_FILE}_ind"
mkdir -p ${OUTPUT_DIR}

# Move only files (not directories) created in the output directory
find /home/cimoon/multi_label_classification/output/bing_tnbc/ -maxdepth 1 -type f -exec mv {} ${OUTPUT_DIR}/ \;

echo "All files have been moved to ${OUTPUT_DIR}"