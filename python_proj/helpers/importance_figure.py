
from python_proj.utils.util import safe_save_fig
from typing import Iterator, Any
import numpy as np
import matplotlib.pyplot as plt
from python_proj.utils.util import SafeDict
scores_full = """ln(1 + ControlPullRequestLifeTimeInMinutes): 0.3098
ln(1 + ControlIntraProjectPullRequestExperienceOfIntegrator): 0.1149
IntraProjectSubmitterPullRequestSuccessRate: 0.0794
ln(1 + IntraProjectSubmitterPullRequestSubmissionCount): 0.0756
ln(1 + WeightedFirstOrderInDegreeCentrality): 0.0486
ControlIntegratedBySameUser: 0.0455
ln(1 + WeightedFirstOrderOutDegreeCentrality): 0.0403
ln(1 + ControlNumberOfCommitsInPullRequest): 0.0330
EcosystemExperienceSubmitterPullRequestSuccessRate: 0.0312
ln(1 + EcosystemExperienceSubmitterIssueCommentCount): 0.0248
ControlPullRequestHasComments: 0.0227
ln(1 + IntraProjectSubmitterPullRequestCommentCount): 0.0218
ln(1 + EcosystemExperienceSubmitterPullRequestCommentCount): 0.0195
ln(1 + EcosystemExperienceSubmitterPullRequestSubmissionCount): 0.0185
ln(1 + EcosystemExperienceSubmitterIssueSubmissionCount): 0.0167
ln(1 + IntraProjectSubmitterIssueCommentCount): 0.0160
ln(1 + SubmitterToIntegratorLinkIntensity): 0.0157
SubmitterIsFirstTimeContributor: 0.0123
ln(1 + IntraProjectSubmitterIssueSubmissionCount): 0.0096
ln(1 + IntegratorToSubmitterLinkIntensity): 0.0094
ControlHasHashTagInDescription: 0.0094
ControlPullRequestHasCommentByExternalUser: 0.0092
ln(1 + DependencyEcosystemExperienceSubmitterPullRequestSubmissionCount): 0.0021
ln(1 + DependencyEcosystemExperienceSubmitterPullRequestCommentCount): 0.0020
ln(1 + DependencyEcosystemExperienceSubmitterIssueCommentCount): 0.0018
ln(1 + InversedDependencyEcosystemExperienceSubmitterIssueCommentCount): 0.0017
ln(1 + InversedDependencyEcosystemExperienceSubmitterPullRequestSubmissionCount): 0.0016
DependencyEcosystemExperienceSubmitterPullRequestSuccessRate: 0.0016
ln(1 + InversedDependencyEcosystemExperienceSubmitterPullRequestCommentCount): 0.0015
InversedDependencyEcosystemExperienceSubmitterPullRequestSuccessRate: 0.0014
ln(1 + DependencyEcosystemExperienceSubmitterIssueSubmissionCount): 0.0012
ln(1 + InversedDependencyEcosystemExperienceSubmitterIssueSubmissionCount): 0.0010"""


scores_ftc = """ln(1 + ControlPullRequestLifeTimeInMinutes): 0.4083
ControlIntegratedBySameUser: 0.1020
ln(1 + ControlIntraProjectPullRequestExperienceOfIntegrator): 0.0853
ln(1 + WeightedFirstOrderInDegreeCentrality): 0.0553
ln(1 + WeightedFirstOrderOutDegreeCentrality): 0.0426
ln(1 + ControlNumberOfCommitsInPullRequest): 0.0408
EcosystemExperienceSubmitterPullRequestSuccessRate: 0.0352
ControlPullRequestHasComments: 0.0335
ln(1 + EcosystemExperienceSubmitterIssueCommentCount): 0.0322
ln(1 + EcosystemExperienceSubmitterPullRequestCommentCount): 0.0241
ln(1 + EcosystemExperienceSubmitterPullRequestSubmissionCount): 0.0220
ln(1 + EcosystemExperienceSubmitterIssueSubmissionCount): 0.0219
ln(1 + IntraProjectSubmitterPullRequestCommentCount): 0.0170
ControlHasHashTagInDescription: 0.0131
ControlPullRequestHasCommentByExternalUser: 0.0130
ln(1 + SubmitterToIntegratorLinkIntensity): 0.0118
ln(1 + IntraProjectSubmitterIssueCommentCount): 0.0113
ln(1 + IntraProjectSubmitterIssueSubmissionCount): 0.0078
ln(1 + IntegratorToSubmitterLinkIntensity): 0.0075
DependencyEcosystemExperienceSubmitterPullRequestSuccessRate: 0.0020
ln(1 + InversedDependencyEcosystemExperienceSubmitterIssueCommentCount): 0.0019
InversedDependencyEcosystemExperienceSubmitterPullRequestSuccessRate: 0.0017
ln(1 + InversedDependencyEcosystemExperienceSubmitterPullRequestSubmissionCount): 0.0016
ln(1 + InversedDependencyEcosystemExperienceSubmitterPullRequestCommentCount): 0.0016
ln(1 + DependencyEcosystemExperienceSubmitterPullRequestSubmissionCount): 0.0015
ln(1 + DependencyEcosystemExperienceSubmitterIssueCommentCount): 0.0014
ln(1 + DependencyEcosystemExperienceSubmitterPullRequestCommentCount): 0.0014
ln(1 + InversedDependencyEcosystemExperienceSubmitterIssueSubmissionCount): 0.0011
ln(1 + DependencyEcosystemExperienceSubmitterIssueSubmissionCount): 0.0009
ln(1 + IntraProjectSubmitterPullRequestSubmissionCount): 0.0000
IntraProjectSubmitterPullRequestSuccessRate: 0.0000"""

scores_non_ftc = """ln(1 + ControlIntraProjectPullRequestExperienceOfIntegrator): 0.1678
ln(1 + IntraProjectSubmitterPullRequestSubmissionCount): 0.1616
IntraProjectSubmitterPullRequestSuccessRate: 0.1530
ln(1 + ControlPullRequestLifeTimeInMinutes): 0.1518
ln(1 + WeightedFirstOrderInDegreeCentrality): 0.0472
ln(1 + WeightedFirstOrderOutDegreeCentrality): 0.0421
ln(1 + IntraProjectSubmitterPullRequestCommentCount): 0.0302
ln(1 + ControlNumberOfCommitsInPullRequest): 0.0298
ln(1 + IntraProjectSubmitterIssueCommentCount): 0.0222
ln(1 + SubmitterToIntegratorLinkIntensity): 0.0209
ln(1 + EcosystemExperienceSubmitterIssueCommentCount): 0.0204
ControlIntegratedBySameUser: 0.0181
ln(1 + EcosystemExperienceSubmitterPullRequestCommentCount): 0.0176
EcosystemExperienceSubmitterPullRequestSuccessRate: 0.0171
ln(1 + EcosystemExperienceSubmitterPullRequestSubmissionCount): 0.0161
ControlPullRequestHasComments: 0.0137
ln(1 + EcosystemExperienceSubmitterIssueSubmissionCount): 0.0132
ln(1 + IntraProjectSubmitterIssueSubmissionCount): 0.0125
ln(1 + IntegratorToSubmitterLinkIntensity): 0.0119
ControlHasHashTagInDescription: 0.0071
ControlPullRequestHasCommentByExternalUser: 0.0067
ln(1 + DependencyEcosystemExperienceSubmitterPullRequestCommentCount): 0.0028
ln(1 + DependencyEcosystemExperienceSubmitterPullRequestSubmissionCount): 0.0027
ln(1 + DependencyEcosystemExperienceSubmitterIssueCommentCount): 0.0022
DependencyEcosystemExperienceSubmitterPullRequestSuccessRate: 0.0020
ln(1 + InversedDependencyEcosystemExperienceSubmitterIssueCommentCount): 0.0017
ln(1 + InversedDependencyEcosystemExperienceSubmitterPullRequestCommentCount): 0.0017
ln(1 + InversedDependencyEcosystemExperienceSubmitterPullRequestSubmissionCount): 0.0017
ln(1 + DependencyEcosystemExperienceSubmitterIssueSubmissionCount): 0.0016
InversedDependencyEcosystemExperienceSubmitterPullRequestSuccessRate: 0.0013
ln(1 + InversedDependencyEcosystemExperienceSubmitterIssueSubmissionCount): 0.0010"""

importances = SafeDict(default_value=dict)

for label, scores in [('Full', scores_full), ('FTC', scores_ftc), ("Non-FTC", scores_non_ftc)]:
    for entry in scores.split("\n"):
        elements = entry.split(":")
        field = elements[0].strip()
        score = float(elements[1].strip())
        importances[label][field] = score

full_importances = importances['Full']
ftc_importances = importances['FTC']
non_ftc_importances = importances['Non-FTC']


# Dot plot


sorted_full_importances = {k: v for k, v in sorted(
    full_importances.items(), key=lambda item: -item[1])}
sorted_full_importances = {k: v for i, (k, v) in enumerate(
    sorted_full_importances.items()) if i < 10}
sorted_ftc_importances = [ftc_importances[k] if k in non_ftc_importances else 0
                          for k in sorted_full_importances.keys()]
sorted_non_ftc_importances = [non_ftc_importances[k] if k in non_ftc_importances else 0
                              for k in sorted_full_importances.keys()]
sorted_full_importances_keys = sorted_full_importances.keys()
sorted_full_importances = sorted_full_importances.values()

def inverse(series: list[Any]) -> list[Any]:
    new_list = []
    series = list(series)
    length = len(series)
    for i in range(length - 1, -1, -1):
        new_list.append(series[i])
    return new_list


predictor_labels = [
    'PR lifetime',
    'Integrator exp.',
    'Intra PR merge rate',
    'Intra PR count',
    'FO in-degree',
    'Self-integrated',
    'FO out-degree',
    'Commit Count',
    'Eco PR merge rate',
    'Eco issue comm.',
]
predictor_labels = inverse(predictor_labels)


# Increased width to provide more space for the left side
plt.figure(figsize=(5.35, 3))

# Plot each data series
plt.plot(inverse(sorted_full_importances), predictor_labels,
         'o', fillstyle='none', markersize=6, label='Full')
plt.plot(inverse(sorted_ftc_importances), predictor_labels,
         's', fillstyle='none', markersize=6, label='FTC')
plt.plot(inverse(sorted_non_ftc_importances), predictor_labels,
         'D', fillstyle='none', markersize=6, label='Non-FTC')

# Add labels and title
plt.xlabel('Mean Decrease in Gini')
plt.ylabel('Predictors')
plt.subplots_adjust(left=0.45)

# Add a legend
plt.legend()

# Display the plot
plt.tight_layout()
# plt.show()


output_path = './data/figures/importance_figure.png'
safe_save_fig(output_path)

# plt.show()
