import numpy as np
import pandas as pd
import seaborn as sns
from tqdm.notebook import tqdm
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, random_split
from sklearn.metrics import roc_auc_score, average_precision_score
from fig3_update.data_utils_PCA import BreastCancerDataset, EarlyStopping
from models import MLCModel
import time
import glob
import copy
import argparse
# import auxlearn scripts
from task_weighter import task_weighter
import pickle

# Initialize an empty list to store alpha values
alpha_values = []

parser = argparse.ArgumentParser(description='Run model with different seeds.')
parser.add_argument('--mccv', type=int, default=1, help='Seed for the random number generator', required=True)
parser.add_argument('--main_task_file', type=str, default='GSE164458_paclitaxel.csv' ,help='File name for the main task', required=True)
args = parser.parse_args()
def generate_test_indices(first_file_path, test_size_fraction,seed):
        """
        Generate indices for a test set based on the first file.

        Args:
            first_file_path (str): The file path for the first dataset.
            test_size_fraction (float): The fraction of the first file's samples to use for the test set.

        Returns:
            np.array: An array of indices for the test set.
        """
        # Read the first file to get the sample size
        df_first_file = pd.read_csv(first_file_path)
        total_samples = len(df_first_file)
        
        # Calculate the number of test samples
        test_samples_count = int(total_samples * test_size_fraction)
        
        # Generate random indices for the test set
        # Ensure reproducibility with np.random.seed
        np.random.seed(seed)  # Or any seed of your choice
        test_indices = np.random.choice(range(total_samples), size=test_samples_count, replace=False)
        
        return test_indices

# Define the file paths to your datasets
file_paths_unsorted = glob.glob('/home/cimoon/multi_label_classification/bing_tnbc_analysis/alpha_analysis/input/*.csv')
file_paths = sorted(file_paths_unsorted, key=lambda x: (x != 'GSE164458_veliparib_carboplatin_paclitaxel.csv', x))

# Create the dataset
dataset = BreastCancerDataset(file_paths=file_paths)

# Load the main task data
main_task_file = '/home/cimoon/multi_label_classification/bing_tnbc_analysis/alpha_analysis/input/GSE164458_veliparib_carboplatin_paclitaxel.csv'
main_task_data = pd.read_csv(main_task_file)
num_main_task_samples = len(main_task_data)

# Ensure reproducibility
np.random.seed(42)

# Shuffle the indices
shuffled_indices = np.random.permutation(num_main_task_samples)

# Split the indices into train, pseudo, and test
train_indices = shuffled_indices[:100]
pseudo_indices = shuffled_indices[100:200]
test_indices = shuffled_indices[200:]

# Combine train and pseudo indices
combined_train_indices = np.concatenate((train_indices, pseudo_indices))

# Create subset datasets for train, validation, and test
train_val_indices = np.setdiff1d(np.arange(num_main_task_samples), test_indices)
np.random.shuffle(train_val_indices)

# Calculate the split size for 50% train, 50% validation
num_train_val = len(train_val_indices)
num_train = num_train_val // 2

train_indices = train_val_indices[:num_train]
val_indices = train_val_indices[num_train:]

# Add pseudo indices to train_indices
train_indices = np.concatenate((train_indices, pseudo_indices))

# Create subset datasets for train, validation, and test
train_subset = torch.utils.data.Subset(dataset, train_indices)
val_subset = torch.utils.data.Subset(dataset, val_indices)
test_subset = torch.utils.data.Subset(dataset, test_indices)

# Create DataLoaders for train, validation, and test sets
train_loader = DataLoader(train_subset, batch_size=50, shuffle=True)
val_loader = DataLoader(val_subset, batch_size=50, shuffle=False)
test_loader = DataLoader(test_subset, batch_size=37, shuffle=False)  # Batch size is the size of the test set

# Now the DataLoaders train_loader, pseudo_loader, and test_loader are ready for use
print(f'Train indices: {train_indices}')
print(f'Pseudo indices: {pseudo_indices}')
print(f'Test indices: {test_indices}')

# Instantiate the model
num_features = dataset.features.shape[1]
num_labels = len(file_paths)
model = MLCModel(num_features, num_labels)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Initialize Task Weighter
task_weighter = task_weighter(num_labels).to(device)  # +1 if considering an additional task or just use num_labels based on your setup
optimizer_task_weighter = optim.SGD(task_weighter.parameters(), lr=0.1)  # Adjust learning rate as needed # default is 0.01

# Define the criterion and optimizer
criterion = nn.BCEWithLogitsLoss()
# optimizer = optim.SGD(model.parameters(), lr=0.1)
# Add L2 regularization via weight_decay
optimizer = optim.SGD(model.parameters(), lr=0.1, weight_decay=1e-4)
# Define a learning rate scheduler
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=1e-3)

# ARML parameters
iteration = 0
num_epochs = 100

# Early stopping parameters
early_stopping = EarlyStopping(patience = 10, verbose=True, chkpoint_name = "./tmp/best.pt")

for epoch in range(num_epochs):
    model.train()  # Set model to training mode
    for l_data in train_loader:
        iteration += 1
        l_input, target = l_data
        l_input, target = l_input.to(device).float(), target.to(device).float()
        outputs = model(l_input)  # Get model predictions

        losses = []  # List to accumulate task-specific losses
        for i in range(num_labels):  # Calculate loss for each label (task)
            cls_loss = criterion(outputs[:, i], target[:, i])
            losses.append(cls_loss)  # Store each task loss directly as a tensor
        loss = task_weighter(tuple(losses))  # Apply task weighting by converting list to tuple
        # update model / task_weighter
        if iteration % 5 != 0: #default is 20
            optimizer.zero_grad()
            loss.backward()
            if iteration < 40: # Add noise to gradients for Lagrange method # default is 50000 
                task_weighter.inject_grad_noise(model, 2 * optimizer.param_groups[0]['lr'] * (1 - 0.9) / len(l_input),
                                                optimizer.param_groups[0]['lr'], 0.9)
            optimizer.step()
            scheduler.step()
        if iteration % 5 == 0: #default is 20
            optimizer.zero_grad()  # clear gradient in model params
            weight_loss = task_weighter.weight_loss(model, losses, 'arml') # default is 'arml'
            for param in model.parameters():
                param.requires_grad = False
            optimizer_task_weighter.zero_grad()
            weight_loss.backward()
            optimizer_task_weighter.step()
            task_weighter.alpha.data = task_weighter.alpha.data + (num_labels - task_weighter.alpha.data.sum()) / num_labels
            for param in model.parameters():
                param.requires_grad = True
            task_weighter.alpha.data = torch.clamp(task_weighter.alpha.data, 0)
            # Collect the alpha values [check this!]
            alpha_values.append(task_weighter.alpha.data.cpu().numpy())
    # Validation
    model.eval()  # Set model to evaluation mode
    val_loss = 0.0
    val_steps = 0
    val_targets = []
    val_outputs = []
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels.squeeze(1))  # Calculate the loss
            val_loss += loss.item()
            val_steps += 1
            val_outputs.extend(outputs.sigmoid().cpu().numpy())
            val_targets.extend(labels.cpu().numpy())

    # Calculate the average validation loss
    validation_binary_loss_entropy_loss = val_loss / val_steps
    print(f'Validation Loss: {validation_binary_loss_entropy_loss}')

    # Call EarlyStopping
    early_stopping(validation_binary_loss_entropy_loss, model)

    if early_stopping.early_stop:
        print("Early stopping")
        break

# After completing the training loop, or if early stopping was triggered,
# you may want to load the best model state for further use or evaluation:
checkpoint = torch.load("./tmp/best.pt")
model.load_state_dict(checkpoint)

# test
print("### Test Evaluation ###")
test_targets = []
test_outputs = []
with torch.no_grad():
    model.eval()  # Ensure model is in evaluation mode
    # Iterate over the test dataset
    for data in test_loader:
        inputs, targets = data
        inputs = inputs.to(device).float()
        targets = targets.to(device).float()
        # Forward pass to get outputs
        outputs = model(inputs)
        # Apply sigmoid to the outputs to get probabilities since BCEWithLogitsLoss was used during training
        probabilities = torch.sigmoid(outputs)
        # Collect the probabilities and true labels
        test_outputs.append(probabilities.cpu().numpy())
        test_targets.append(targets.cpu().numpy())
    # Convert lists of arrays into single numpy arrays
    test_outputs_np = np.vstack(test_outputs)  # Stack arrays vertically
    test_targets_np = np.vstack(test_targets)
        
    # Compute AUROC and AUPR for only the main task
    test_auroc = roc_auc_score(test_targets_np[:, 0], test_outputs_np[:, 0])
    test_aupr = average_precision_score(test_targets_np[:, 0], test_outputs_np[:, 0])

    print(f'AUROC for main task: {test_auroc:.4f}')
    print(f'AUPR for main task: {test_aupr:.4f}')

# Once all iterations are complete, create a DataFrame from the lists
results_df = pd.DataFrame({
    'AUROC': [test_auroc],  
    'AUPR': [test_aupr]  
}, index=[0]) 

# # Save the DataFrame to a CSV file
# remove .csv
main_task_name = args.main_task_file.replace('.csv', '')
# results_df.to_csv(f'./output/MCCV_PCA_aux_learn_{main_task_name}_{args.mccv}.csv', index=False)
# results_df.to_csv(f'./output/MCCV_PCA_aux_learn_{args.mccv}.csv', index=False)

# Save the alpha values to a pickle file
alpha_filename = f'/home/cimoon/multi_label_classification/bing_tnbc_analysis/alpha_analysis/alpha_output.pkl'
with open(alpha_filename, 'wb') as f:
    pickle.dump(alpha_values, f)