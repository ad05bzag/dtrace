# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.3'
#       jupytext_version: 1.0.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %matplotlib inline
# %autosave 0
# %load_ext autoreload
# %autoreload 2

import textwrap
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from crispy.Utils import Utils
from scipy.stats import ttest_ind
from dtrace.DTracePlot import DTracePlot
from dtrace.DTraceUtils import rpath, dpath
from dtrace.Associations import Association
from dtrace.TargetBenchmark import TargetBenchmark


# ### Import data-sets and associations

assoc = Association(dtype="ic50", load_associations=True, load_ppi=True)

target = TargetBenchmark(assoc=assoc, fdr=0.1)


# ## Drug-response and gene-essentiality associations

# Top associations between drug-response and gene-essentiality

assoc.lmm_drug_crispr.head(15)


# Top associations between drug-response and gene-expression

assoc.lmm_drug_gexp.head(15)


# Surrogate pathway adj. p-value ratio

pratio = target.surrogate_pathway_ratio()
pratio.to_excel(f"{dpath}/drug_target_proxy_fdr_ratio.xlsx")


# Manhattan plot of the drug-gene associations, x-axis represents the gene genomic coordinate (obtained from the sgRNAs)
# and y-axis represent the -log10 association p-value.

# Spikes on the same genomic location represent associations with multiple inhibitors with the same target/
# mode-of-action.

target.manhattan_plot(n_genes=20)
plt.savefig(
    f"{rpath}/target_benchmark_manhattan.png",
    bbox_inches="tight",
    transparent=True,
    dpi=300,
)
plt.show()


# Volcano plot of the significant associations.

plt.figure(figsize=(3, 1.5), dpi=300)
target.signif_volcano()
plt.savefig(
    f"{rpath}/target_benchmark_volcano.pdf", bbox_inches="tight", transparent=True
)
plt.show()


# Top 50 most strongly correlated drugs

target.top_associations_barplot()
plt.savefig(
    f"{rpath}/target_benchmark_associations_barplot.pdf",
    bbox_inches="tight",
    transparent=True,
)


# Representative examples of the drug-gene associations.

dgs = [
    ("Alpelisib", "PIK3CA"),
    ("Nutlin-3a (-)", "MDM2"),
    ("MCL1_1284", "MCL1"),
    ("MCL1_1284", "MARCH5"),
    ("Venetoclax", "BCL2"),
    ("AZD4320", "BCL2"),
    ("Volasertib", "PLK1"),
    ("Rigosertib", "PLK1"),
    ("Linsitinib", "CNPY2"),
    ("Cetuximab", "EGFR"),
    ("Olaparib", "PARP1"),
    ("Olaparib", "PARP2"),
]

dg = ("Vandetinib", "RBM14")
for dg in dgs:
    pair = assoc.by(assoc.lmm_drug_crispr, drug_name=dg[0], gene_name=dg[1]).iloc[0]

    drug = tuple(pair[assoc.dcols])

    dmax = np.log(assoc.drespo_obj.maxconcentration[drug])
    annot_text = f"Beta={pair['beta']:.2g}, FDR={pair['fdr']:.1e}"

    plot_df = assoc.build_df(drug=[drug], crispr=[dg[1]], sinfo=["institute"]).dropna()
    plot_df = plot_df.rename(columns={drug: "drug"})

    g = target.plot_corrplot(
        f"crispr_{dg[1]}",
        "drug",
        "institute",
        plot_df,
        add_hline=False,
        add_vline=False,
        annot_text=annot_text,
    )
    g.ax_joint.axhline(
        y=dmax, linewidth=0.3, color=target.PAL_DTRACE[2], ls=":", zorder=0
    )
    g.set_axis_labels(f"{dg[1]} (scaled log2 FC)", f"{dg[0]} (ln IC50)")
    plt.gcf().set_size_inches(1.5, 1.5)
    plt.savefig(
        f"{rpath}/association_drug_scatter_{dg[0]}_{dg[1]}.pdf",
        bbox_inches="tight",
        transparent=True,
    )
    plt.show()


# Kinobeads drug-protein affinity measurements for 84 kinase inhibitors were obtained from an independent study [1] as
# aparent pKd (nM). These were ploted for the signifincant associations versus non-significant (Log-ratio test BH-FDR)
# found in our study.
#
#
# [1] Klaeger S, Heinzlmeir S, Wilhelm M, Polzer H, Vick B, Koenig P-A, Reinecke M, Ruprecht B, Petzoldt S, Meng C,
# Zecha J, Reiter K, Qiao H, Helm D, Koch H, Schoof M, Canevari G, Casale E, Depaolini SR, Feuchtinger A, et al. (2017)
# The target landscape of clinical kinase drugs. Science 358: eaan4368

plt.figure(figsize=(0.75, 2.0), dpi=300)
target.boxplot_kinobead()
plt.savefig(
    f"{rpath}/target_benchmark_kinobeads.pdf", bbox_inches="tight", transparent=True
)


# Association effect sizes with between drugs and their know targets

plt.figure(figsize=(2, 2), dpi=300)
target.beta_histogram()
plt.savefig(
    f"{rpath}/target_benchmark_beta_histogram.pdf",
    bbox_inches="tight",
    transparent=True,
)


# P-value histogram of the Drug-Genes associations highlighting Drug-Target associations.

plt.figure(figsize=(2, 1), dpi=300)
target.pval_histogram()
plt.savefig(
    f"{rpath}/target_benchmark_pval_histogram.pdf",
    bbox_inches="tight",
    transparent=True,
)


# Distribution of the signifcant Drug-Gene associations across a protein-protein interaction network, with
# gene-essentiality and gene-expression.

for dtype in ["crispr", "gexp"]:
    fig, axs = plt.subplots(2, 1, figsize=(1.5, 3), dpi=300)

    # Boxplot
    target.drugs_ppi(dtype, ax=axs[0])

    axs[0].set_xlabel("Associated gene position in PPI")
    axs[0].set_ylabel("Bonferroni adj. p-value")
    axs[0].set_title("Significant associations\n(adj. p-value < 10%)")

    # Count plot
    target.drugs_ppi_countplot(dtype, ax=axs[1])

    axs[1].set_xlabel("Associated gene position in PPI")
    axs[1].set_ylabel("Number of associations")

    plt.savefig(
        f"{rpath}/target_benchmark_ppi_distance_{dtype}.pdf",
        bbox_inches="tight",
        transparent=True,
    )


# Background distribution of all Drug-Gene associations tested.

plt.figure(figsize=(2.5, 2.5), dpi=300)
target.drugs_ppi_countplot_background()
plt.savefig(
    f"{rpath}/target_benchmark_ppi_distance_{dtype}_countplot_bkg.pdf",
    bbox_inches="tight",
    transparent=True,
)


# Breakdown numbers of (i) all the drugs screened, (ii) unique drugs, (iii) their annotation status, and (iv) those
# which at least one of the canonical targets were targeted with the CRISPR-Cas9 screen.

plt.figure(figsize=(2, 0.75), dpi=300)
target.countplot_drugs()
plt.savefig(
    f"{rpath}/target_benchmark_association_countplot.pdf",
    bbox_inches="tight",
    transparent=True,
)


# Histogram of drugs with at least one significant association across the protein-protein network

plt.figure(figsize=(2, 1), dpi=300)
target.countplot_drugs_significant()
plt.savefig(
    f"{rpath}/target_benchmark_association_signif_countplot.pdf",
    bbox_inches="tight",
    transparent=True,
)


# Pie chart of significant associations per unique durgs ordered by distance in the PPI

plt.figure(figsize=(2, 2), dpi=300)
target.pichart_drugs_significant()
plt.savefig(
    f"{rpath}/target_benchmark_association_signif_piechart.pdf",
    bbox_inches="tight",
    transparent=True,
)


# Heatmap counting the number of drugs which have a significant association with CRISPR and/or target a core-essential
# gene.

plt.figure(figsize=(1, 1), dpi=300)
target.signif_essential_heatmap()
plt.savefig(
    f"{rpath}/target_benchmark_signif_essential_heatmap.pdf",
    bbox_inches="tight",
    transparent=True,
)


# Number of significant associations found with drugs from the two different types of screening proceedures, i.e. RS
# and V17.

plt.figure(figsize=(0.75, 1.5), dpi=300)
target.signif_per_screen()
plt.savefig(
    f"{rpath}/target_benchmark_significant_by_screen.pdf",
    bbox_inches="tight",
    transparent=True,
)


# Heatmap counting the number of drugs which have a significant association with CRISPR and/or with a genomic marker

plt.figure(figsize=(1, 1), dpi=300)
target.signif_genomic_markers()
plt.savefig(
    f"{rpath}/target_benchmark_signif_genomic_heatmap.pdf",
    bbox_inches="tight",
    transparent=True,
)


# Significant associations p-value (y-axis) spread across the number of times a drug displayed an IC50 lower than the
# maximum screened concentration.

target.signif_maxconcentration_scatter()
plt.gcf().set_size_inches(2.5, 2.5)
plt.savefig(
    f"{rpath}/target_benchmark_signif_scatter_maxconcentration.pdf",
    bbox_inches="tight",
    transparent=True,
)


# Drug-Gene CRISPR associations p-value (-log10) versus Drug-Genomic associations p-value (-log10).

plt.figure(figsize=(2, 2), dpi=300)
target.signif_fdr_scatter()
plt.savefig(
    f"{rpath}/target_benchmark_signif_fdr_scatter.pdf",
    bbox_inches="tight",
    transparent=True,
)


# Top associations

drugs = [
    "SN1021632995",
    "AZD5582",
    "SN1043546339",
    "VE-821",
    "AZ20",
    "VE821",
    "VX-970",
    "AZD6738",
    "VE-822",
    "Cetuximab",
]

for d in drugs:
    plt.figure(figsize=(1.5, 2), dpi=300)
    target.drug_top_associations(d, fdr_thres=0.25)
    plt.savefig(
        f"{rpath}/target_benchmark_{d}_top_associations_barplot.pdf",
        bbox_inches="tight",
        transparent=True,
        dpi=600,
    )
    plt.show()


# PARP inhibitors (olaparib and talazoparib) associations

genes = ["STAG1", "LIG1", "FLI1", "PARP1", "PARP2", "PARP3", "PCGF5", "XRCC1", "RHNO1"]

for drug in ["Olaparib", "Talazoparib"]:
    plt.figure(figsize=(2, 1.5), dpi=300)
    target.drug_notarget_barplot(drug, genes)
    plt.savefig(
        f"{rpath}/target_benchmark_drug_notarget_{drug}.pdf",
        bbox_inches="tight",
        transparent=True,
    )
    plt.show()


# Clustermap of drug association betas

betas_crispr = pd.pivot_table(
    assoc.lmm_drug_crispr.query("VERSION == 'RS'"),
    index=["DRUG_ID", "DRUG_NAME"],
    columns="GeneSymbol",
    values="beta",
)


target.lmm_betas_clustermap(betas_crispr)
plt.gcf().set_size_inches(8, 8)
plt.savefig(
    f"{rpath}/target_benchmark_clustermap_betas_crispr.png",
    bbox_inches="tight",
    dpi=300,
)


plt.figure(figsize=(2, 2), dpi=300)
target.lmm_betas_clustermap_legend()
plt.axis("off")
plt.savefig(
    f"{rpath}/target_benchmark_clustermap_betas_crispr_legend.pdf", bbox_inches="tight"
)


# Drug association with gene-expression

dgs = [
    ("Nutlin-3a (-)", "MDM2"),
    ("Poziotinib", "ERBB2"),
    ("Afatinib", "ERBB2"),
    ("WEHI-539", "BCL2L1"),
]
for dg in dgs:
    pair = assoc.by(assoc.lmm_drug_crispr, drug_name=dg[0], gene_name=dg[1]).iloc[0]

    drug = tuple(pair[assoc.dcols])

    dmax = np.log(assoc.drespo_obj.maxconcentration[drug])
    annot_text = f"Beta={pair['beta']:.2g}, FDR={pair['fdr']:.1e}"

    plot_df = assoc.build_df(drug=[drug], crispr=[dg[1]]).dropna()
    plot_df = plot_df.rename(columns={drug: "drug"})
    plot_df["Institute"] = "Sanger"

    g = target.plot_corrplot(
        f"crispr_{dg[1]}",
        "drug",
        "Institute",
        plot_df,
        add_hline=False,
        add_vline=False,
        annot_text=annot_text,
    )

    g.ax_joint.axhline(
        y=dmax, linewidth=0.3, color=target.PAL_DTRACE[2], ls=":", zorder=0
    )

    g.set_axis_labels(f"{dg[1]} (voom)", f"{dg[0]} (ln IC50)")

    plt.gcf().set_size_inches(2, 2)
    plt.savefig(
        f"{rpath}/association_drug_gexp_scatter_{dg[0]}_{dg[1]}.pdf",
        bbox_inches="tight",
        transparent=True,
    )
    plt.show()


# CRISPR correlation profiles

for gene_x, gene_y in [("MARCH5", "MCL1"), ("SHC1", "EGFR")]:
    plot_df = assoc.build_df(crispr=[gene_x, gene_y], sinfo=["institute"]).dropna()

    g = target.plot_corrplot(
        f"crispr_{gene_x}", f"crispr_{gene_y}", "institute", plot_df, add_hline=True
    )

    g.set_axis_labels(f"{gene_x} (scaled log2 FC)", f"{gene_y} (scaled log2 FC)")

    plt.gcf().set_size_inches(1.5, 1.5)
    plt.savefig(
        f"{rpath}/association_scatter_{gene_x}_{gene_y}.pdf",
        bbox_inches="tight",
        transparent=True,
    )
    plt.show()


# PPI weighted network

ppi_examples = [
    ("Nutlin-3a (-)", 0.4, 1, ["RPL37", "UBE3B"]),
    ("AZD3759", 0.3, 1, None),
    ("Cetuximab", 0.3, 1, None),
]
for d, t, o, e in ppi_examples:
    graph = assoc.ppi.plot_ppi(
        d,
        assoc.lmm_drug_crispr,
        assoc.ppi_string_corr,
        corr_thres=t,
        norder=o,
        fdr=0.05,
        exclude_nodes=e,
    )
    graph.write_pdf(f"{rpath}/association_ppi_{d}.pdf")


# Surrogate pathway histogram

plt.figure(figsize=(2.0, 2.0), dpi=600)

sns.distplot(
    pratio["ratio_fdr"],
    color=target.PAL_DTRACE[2],
    kde=False,
    hist_kws={"lw": 0},
    bins=45,
)

plt.axvline(0, linewidth=0.1, color="#e1e1e1", ls="-", zorder=0)

plt.title("Drug-response pathway surrogate")
plt.xlabel("Target / Proxy (log ratio adj. p-value)")
plt.ylabel("Count")

plt.savefig(f"{rpath}/target_benchmark_fdr_ratio_histogram.pdf", bbox_inches="tight")


# Drug-target CRISPR variability between drug significant association

plot_df = assoc.lmm_drug_crispr.query("target == 'T'")
plot_df["crispr_std"] = assoc.crispr.loc[plot_df["GeneSymbol"]].std(1).values
plot_df["drug_std"] = (
    assoc.drespo.loc[[tuple(v) for v in plot_df[target.dinfo].values]].std(1).values
)
plot_df["signif"] = plot_df["fdr"].apply(lambda v: "Yes" if v < target.fdr else "No")

pal = {"No": target.PAL_DTRACE[1], "Yes": target.PAL_DTRACE[2]}

for l in ["crispr_std", "drug_std"]:
    plt.figure(figsize=(1.0, 1.5), dpi=600)

    ax = sns.boxplot(
        "signif",
        l,
        data=plot_df,
        palette=pal,
        linewidth=0.3,
        fliersize=1.5,
        flierprops=target.FLIERPROPS,
        showcaps=False,
        notch=True,
    )

    t, p = ttest_ind(
        plot_df.query(f"signif == 'Yes'")[l],
        plot_df.query(f"signif == 'No'")[l],
        equal_var=False,
    )

    ax.text(
        0.95,
        0.05,
        f"Welch's t-test p={p:.1e}",
        fontsize=4,
        transform=ax.transAxes,
        ha="right",
    )

    if l == "crispr_std":
        ness_std = assoc.crispr.loc[Utils.get_non_essential_genes()].std(1).median()
        plt.axhline(ness_std, ls=":", lw=0.3, c="k", zorder=0)

        ess_std = assoc.crispr.loc[Utils.get_essential_genes()].std(1).median()
        plt.axhline(ess_std, ls=":", lw=0.3, c="k", zorder=0)

    plt.title("Drug ~ Gene association")
    plt.xlabel("Significant association\n(adj. p-value < 10%)")
    plt.ylabel(
        "Drug-target fold-change\nstandard deviation"
        if l == "crispr_std"
        else "Drug IC50 (ln)\nstandard deviation"
    )

    plt.savefig(
        f"{rpath}/target_benchmark_drug_signif_{l}_boxplot.pdf", bbox_inches="tight"
    )


# Drug

d_info = assoc.drespo_obj.drugsheet.groupby("Name")[["Pathway", "Drug Type"]].first()
d_info = d_info.replace({"Drug Type": {"targeted": "Targeted"}})

plot_df = pd.DataFrame(
    [
        dict(
            drug=d,
            signif=int(d in target.d_sets_name["significant"]),
            dtype=d_info.loc[d, "Drug Type"],
            pathway=d_info.loc[d, "Pathway"],
        )
        for d in target.d_targets
        if d in target.d_sets_name["all"]
    ]
)


# Core-essential analysis

ess_genes = assoc.crispr_obj.import_sanger_essential_genes()
plot_df = assoc.lmm_drug_crispr.query(f"fdr < {target.fdr}")
plot_df["essential"] = plot_df["GeneSymbol"].isin(ess_genes).values


#

plot_df = pd.concat(
    [
        assoc.genomic.loc["BRCA1_mut"],
        assoc.genomic.loc["BRCA2_mut"],
        (assoc.genomic.loc["BRCA1_mut"] | assoc.genomic.loc["BRCA2_mut"]).rename(
            "BRCA_mut"
        ),
        assoc.crispr.loc["PARP1"],
        assoc.crispr.loc["PARP2"],
        assoc.samplesheet.samplesheet["cancer_type"],
    ],
    axis=1,
    sort=False,
).dropna()

tissues = [{"Breast Carcinoma", "Ovarian Carcinoma"}, {"Ewing's Sarcoma"}]

f, axs = plt.subplots(2, len(tissues), sharex="none", sharey="all", figsize=(1.5, 2.), dpi=600)

for j, t in enumerate(tissues):
    for i, g_crispr in enumerate(["PARP1", "PARP2"]):
        ax = axs[i][j]

        df = plot_df[plot_df["cancer_type"].isin(t)]
        x, y = df["BRCA_mut"], df[g_crispr]

        sns.boxplot(
            x=x,
            y=y,
            palette=DTracePlot.PAL_1_0,
            data=df,
            linewidth=0.1,
            fliersize=1,
            saturation=1.0,
            showcaps=False,
            boxprops=dict(linewidth=.3),
            whiskerprops=dict(linewidth=.3),
            flierprops=DTracePlot.FLIERPROPS,
            sym="",
            medianprops=dict(linestyle="-", linewidth=.3),
            ax=ax,
        )

        sns.stripplot(
            x=x,
            y=y,
            palette=DTracePlot.PAL_1_0,
            data=df,
            edgecolor="white",
            linewidth=0.1,
            s=1.5,
            alpha=.8,
            ax=ax,
        )

        ax.set_title("\n".join(t) if i == 0 else "")
        ax.set_xlabel("BRCA1/2 mut" if i == 1 else "")
        ax.set_ylabel(g_crispr if j == 0 else "")
        ax.grid(True, ls="-", lw=0.1, alpha=1.0, zorder=0, axis="y")

plt.subplots_adjust(hspace=0.05, wspace=0.05)
plt.savefig(
    f"{rpath}/genomic_boxplot_BRCA.pdf",
    bbox_inches="tight",
    transparent=True,
)

plt.close("all")


# Copyright (C) 2019 Emanuel Goncalves
