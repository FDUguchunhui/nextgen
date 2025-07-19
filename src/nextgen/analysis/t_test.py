import pandas as pd
from scipy.stats import ttest_ind
import numpy as np

def perform_t_test(df):
    import pandas as pd
    import matplotlib.pyplot as plt
    from scipy.stats import ttest_ind

    # Pre-group all relevant data
    grouped = df.groupby(['protein_group', 'cancer_type'])['intensity'].apply(list).unstack()

    results = []
    for protein, row in grouped.iterrows():
        if pd.isnull(protein):
            continue
        # Ensure two groups exist
        if row.count() < 2:
            continue
        group_values = row.dropna()
        if len(group_values) != 2:
            continue
        group1, group2 = group_values.values
        if len(group1) < 2 or len(group2) < 2:
            continue
        t_stat, p_val = ttest_ind(group1, group2)
        results.append({'protein_group': protein, 't_stat': t_stat, 'p_val': p_val})

    result_df = pd.DataFrame(results)
    plt.hist(result_df['p_val'], bins=50)
    plt.xlabel('p-value')
    plt.ylabel('Frequency')
    plt.title('Histogram of p-values')
    plt.savefig('/Users/cgu3/Documents/nextgen/exports/charts/temp_chart.png')

    return {'type': 'dataframe', 'value': result_df}



if __name__ == "__main__":
    df = pd.read_csv("data/test_statistician.csv")
    result = perform_t_test(df)