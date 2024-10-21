# Identifying studies that are within the upper and lower bounds (within +-0.1 of the 1:1 line)
within_bounds = df[(df['Best_Auxiliary'] <= df['Best_Baseline'] + 0.1) & 
                   (df['Best_Auxiliary'] >= df['Best_Baseline'] - 0.1)]

# Identifying studies that are outside of these bounds (to label them)
label_outside_bounds = df[~df.index.isin(within_bounds.index)]

# Plot the updated scatterplot, labeling studies outside the bounds
plt.figure(figsize=(8, 8))
plt.scatter(df['Best_Baseline'], df['Best_Auxiliary'], color='blue', label='Study Points')

# Plot the 1:1 line (y = x)
plt.plot([0, 1], [0, 1], color='black', linestyle='-', linewidth=1, label='1:1 Line')

# Adding two dotted lines for the expected ±0.1 range parallel to the 1:1 line
plt.plot([0, 1], [0.1, 1.1], color='black', linestyle='--', linewidth=1, label='Upper Bound (+0.1)')
plt.plot([0, 1], [-0.1, 0.9], color='black', linestyle='--', linewidth=1, label='Lower Bound (-0.1)')

# Label only the studies that are outside the bounds
for _, row in label_outside_bounds.iterrows():
    plt.text(row['Best_Baseline'], row['Best_Auxiliary'], row['Study'], fontsize=8, color='red')

# Add labels and title
plt.xlabel('Best Baseline AUC')
plt.ylabel('Best Auxiliary AUC')
plt.title('Scatterplot of Best Baseline vs Best Auxiliary AUC (Labeled Outside Bounds)')

# Set X and Y axis limits from 0 to 1
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.grid(True)
plt.legend()

# Save the updated plot with labels to a PDF
outside_bounds_pdf_path = '/mnt/data/scatterplot_outside_bounds_baseline_auxiliary_AUC.pdf'
plt.savefig(outside_bounds_pdf_path)

# Show the plot
plt.show()

outside_bounds_pdf_path  # Return the path to the updated PDF for downloading

