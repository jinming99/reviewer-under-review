# Overall Feedback

This paper presents a substantial empirical contribution: a large-scale dataset of open-ended queries, a taxonomy of query types, and systematic evidence of mode collapse both within and across language models. The 'Artificial Hivemind' framing is vivid and well-supported by the core experiments. The human annotation effort (31,250 labels with 25 annotators per example) is commendable and enables meaningful analysis of distributional preferences. However, the paper contains a clear inconsistency between the correlation metric named in the main text versus the figures and tables, a problematic disagreement metric that conflates consensus on ties with genuine disagreement, and a taxonomy count that does not straightforwardly match the presented hierarchy. These issues, while not undermining the central thesis, reduce confidence in the precision of the reported analyses.

# Detailed Comments


## Comment 1: Correlation metric inconsistency: text says Pearson, figures/tables say Spearman


> We then compute Pearson correlations between model and human absolute ratings on the full set and these filtered subsets, as shown in Figure 10 (a).


The main text in Section 4.3 consistently refers to 'Pearson correlations' in at least four places (for both absolute and pairwise setups, for both similar-quality and disagreement analyses). However, Figure 10's caption states 'We compute Spearman's correlation coefficients,' Figure 11's caption likewise says 'Spearman's correlation coefficients,' Table 19 reports 'Spearman correlation coefficients,' and Tables 23-26 all report 'Spearman's correlation coefficients.' Pearson and Spearman correlations measure different things—Pearson captures linear association while Spearman captures monotonic rank association—and can yield meaningfully different values, especially when distributions are skewed or contain outliers, both of which are likely given the data structure. Since every quantitative table and figure consistently says Spearman, the actual computation almost certainly used Spearman, and the main text's references to Pearson appear to be erroneous. This should be corrected to avoid confusion about which statistical test was actually performed.


*Type: technical*


## Comment 2: Percentage disagreement formula assigns 50% disagreement to unanimous tie annotations


> Pdisagree = 1 −max(Cprefer 1,Cprefer 2)+0.5·Ctie / Ctotal


The formula weights tie annotations at 0.5 in the numerator. Consider the case where all 25 annotators rate two responses as similar quality (C_tie = 25, C_prefer1 = C_prefer2 = 0). The formula gives P_disagree = 1 − (0 + 0.5 × 25)/25 = 0.5. This means that perfect annotator consensus—everyone agrees neither response is better—registers as 50% disagreement. The issue is that the metric conflates 'no clear preference winner' with 'annotators disagree about which is better.' A triplet where all 25 annotators independently agree the responses are equivalent should arguably have near-zero disagreement, yet this formula places it squarely in the middle of the disagreement range. This has downstream consequences: when selecting the 'top 60% most disagreed examples,' truly consensual-tie examples would be included alongside genuinely contested ones, potentially diluting the analysis of how models handle real annotator disagreement. The authors should either justify why unanimous ties should count as partially disagreed or adopt a metric that distinguishes consensus-on-tie from split-preference cases.


*Type: technical*


## Comment 3: Claim of inter-model similarity sometimes exceeding intra-model similarity is not well-supported by aggregate data


> indicating distinct models frequently generate highly similar content, sometimes resulting in higher inter- than intra-model similarity


This claim follows the analysis of Figure 8, which counts unique models among the top-N most similar responses per query. The finding that ~8 unique models appear in the top-50 cluster does show cross-model overlap at the instance level. However, the inter-model similarity matrices in Tables 7-11 consistently show that diagonal values (intra-model similarity, ranging roughly 65-90%) exceed off-diagonal values (inter-model similarity, ranging roughly 60-82%) for virtually every model pair. The authors qualify with 'sometimes,' which could refer to individual query instances where a specific cross-model response pair happens to be more similar than some within-model pairs. But the phrasing 'resulting in higher inter- than intra-model similarity' is likely to be read as a more general claim. A more precise statement would clarify that this occurs at the individual response-pair level for specific queries, not at the aggregate model level, where intra-model similarity systematically exceeds inter-model similarity.


*Type: logical*


## Comment 4: Taxonomy claimed to have 17 subcategories but only 15 are true subcategories


> comprising 6 top-level categories (e.g., creative content generation, brainstorm & ideation) that further breaks down to 17 subcategories


Figure 2 and Table 2 show the full taxonomy. Four of the six top-level categories have subcategories: Open-Endedness (5), Alternative Perspectives (2), Alternative Styles (2), Information-Seeking (6), totaling 15 subcategories. The remaining two top-level categories—Creative Content Generation and Brainstorm & Ideation—have no subcategories (Table 2 marks them with '-' under 'Sub Cat.'). The count of 17 appears to be reached by including these two standalone top-level categories as their own 'subcategories,' which is inconsistent: the abstract says the 6 top-level categories 'further break down to 17 subcategories,' but 2 of the 6 do not break down at all. This is a minor but noticeable inconsistency that could confuse readers trying to reconcile the stated count with the actual taxonomy structure.


*Type: logical*


## Comment 5: Min-p caption says similarity 'typically exceeds 0.8' but only 61.2% of cases do


> Using min-p sampling with parameters (top-p = 1.0, min-p = 0.1, temperature = 2.0), the average pairwise similarity among responses to the same prompt typically exceeds 0.8.


The Figure 5 caption claims similarity 'typically exceeds 0.8' under min-p sampling. However, the main text reports that only '61.2% exceed 0.8' under these settings. While 61.2% is a majority, characterizing it as 'typically' is imprecise—nearly 40% of cases fall below 0.8. By contrast, the standard top-p setting description uses '79% of cases' to support a similar 'typically exceeds 0.8' claim, which is more defensible. The min-p caption should more accurately reflect that a substantial minority of cases do not exceed 0.8 similarity, or the qualifier should be adjusted. This matters because the min-p analysis is meant to show that even diversity-oriented decoding fails to resolve mode collapse, and overstating the similarity under min-p weakens the precision of this comparison.


*Type: logical*
