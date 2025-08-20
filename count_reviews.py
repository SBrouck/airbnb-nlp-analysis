import pandas as pd

# Read the reviews file
reviews_df = pd.read_csv('cleaned_reviews.csv')

# Count the number of reviews
num_reviews = len(reviews_df)

print(f"Number of reviews in cleaned_reviews.csv: {num_reviews:,}")

# Optional: Show some basic info about the dataset
print(f"\nDataset shape: {reviews_df.shape}")
print(f"Columns: {list(reviews_df.columns)}") 