#!/usr/bin/env python
# Copyright (C) 2018 Emanuel Goncalves

import cdrug
import textwrap
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import cdrug.associations as lr_files
from sklearn.decomposition import PCA
from cdrug.plot.corrplot import plot_corrplot
from cdrug.associations import multipletests_per_drug, ppi_annotation
from sklearn.metrics import roc_auc_score, recall_score, precision_score, f1_score


if __name__ == '__main__':
    # - Imports
    # Linear regressions
    lm_df_crispr = pd.read_csv(lr_files.LR_DRUG_CRISPR)

    # - Compute FDR per drug
    lm_df_crispr = multipletests_per_drug(lm_df_crispr)

    # - Annotate regressions with Drug -> Target -> Protein (in PPI)
    lm_df_crispr = ppi_annotation(lm_df_crispr, exp_type={'Affinity Capture-MS', 'Affinity Capture-Western'}, int_type={'physical'}, target_thres=3)

    # - Create unique ID for drug
    lm_df_crispr = lm_df_crispr.assign(DrugId=['|'.join(map(str, i)) for i in lm_df_crispr[cdrug.DRUG_INFO_COLUMNS].values])

    # - Build betas matrix
    lm_betas = pd.pivot_table(lm_df_crispr, index='GeneSymbol', columns='DrugId', values='beta')

    # - Drug with significant associations
    drugs = list(set(lm_df_crispr[(lm_df_crispr['beta'].abs() > .25) & (lm_df_crispr['lr_fdr'] < .1)]['DrugId']))
    genes = list(set(lm_df_crispr[(lm_df_crispr['beta'].abs() > .25) & (lm_df_crispr['lr_fdr'] < .1)]['GeneSymbol']))
    drugs_screen = lm_df_crispr.groupby('DrugId')['VERSION'].first().loc[drugs]

    # -
    df = lm_betas.loc[genes, drugs].T

    # TSNE
    perplexity, learning_rate, n_iter = 20, 400, 1000

    tsne_dict = {}
    for s in set(drugs_screen):
        tsne_df = df.loc[drugs_screen[drugs_screen == s].index]
        tsne_df = pd.DataFrame(PCA(n_components=50).fit_transform(tsne_df), index=tsne_df.index)

        tsne = TSNE(perplexity=perplexity, learning_rate=learning_rate, n_iter=n_iter).fit_transform(tsne_df)

        tsne = pd.DataFrame(tsne, index=tsne_df.index, columns=['P1', 'P2'])
        tsne = tsne.assign(version=list(map(lambda v: v.split('|')[2], tsne.index)))
        tsne = tsne.assign(target=tsne.index.isin(set(lm_df_crispr.query('target == 0')['DrugId'])).astype(int))

        tsne_dict[s] = tsne

    #
    f, axs = plt.subplots(1, 2)

    for i, s in enumerate(tsne_dict):
        for t in [0, 1]:
            plot_df = tsne_dict[s].query('target == {}'.format(t))

            axs[i].scatter(plot_df['P1'], plot_df['P2'], c=cdrug.PAL_BIN[t], label='W/Target' if t else 'No Target', edgecolors='white', lw=.3, alpha=.8, s=10)

        axs[i].get_xaxis().set_visible(False)
        axs[i].get_yaxis().set_visible(False)

        label = 'Perplexity={}; Learning Rate={}'.format(perplexity, learning_rate)
        axs[i].text(axs[i].get_xlim()[0], axs[i].get_ylim()[0], label, fontsize=3, ha='left', va='bottom')

        axs[i].set_title(s)
        axs[i].legend()

    plt.suptitle('t-SNE projection of drug associations')

    plt.gcf().set_size_inches(6, 3)
    plt.savefig('reports/lr_tsne_perscreen_pairplot.pdf', bbox_inches='tight')
    plt.close('all')
