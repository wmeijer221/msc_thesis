


Initial Observations of the model results:
- It immediately stands out that the MDA scores are very, very low, suggesting the existence of redundant information in the dataset; i.e., that multiple features include the same or similar information, and consequently, removing a single feature from the list will not affect the outcome as much as others can somewhat account for it.

- the control variables are not all that important, nor are they equally important when compared to each other.
    - this holds for each of the models, and can be observed from the coefficients and the MDA scores.
    - Althgouh the integrator experience consistently has a created coefficient than the PR age, PR age's MDA score is consistently higher.

- In the general case, we can see that intra-project features are quite important
    - it's pull request submission count and success rataio having a substantial MDA (both top 5)
    - Their effect suggestively are positive as per the measured multicollinear field's coefficient and the ascending line in the log-odds diagrams.
    - However, when observing the partial dependence plot, it is very clear that the effect of the count data is generally inhibitory, while only success rate is positive.


- In the general case, ecosystem experience is definitely not negligable, having a positive effect, of consistant importance.
    - this is different from intra-project variables and PR submission count and PR success rate are significantly more important there.
    - similarly to the intra-project factors, pull request success rate has a generally monotonic positive influence, whilst most of the counts have a negative monotonic effect. An exception to this  are the comment count entries, which seem to have a positive effect up to a certain point, and after, become negative, in an inversed U-curve.
    - These findings are interesting as they directly contradict the estimated coefficients in the logistic regression model.

- The results of dependency and inverse dependency factors are quite consistent. They have very little importance in the general model.
    - The MDA identifies this as they only contribute one-thousandth
    - The logit results show this as incoming dependency experience is rendered to have an insignificant effect, and the outgoing dependency experience a very small effect.
    - the partial dependency plots follow more-or-less the same shapes as the ecosystem one, with the exception that issue comment count in incoming dependent projects is non-monotonic as well here and for outgoing dependencies each of the predictors have a monotonic relationship and the comment counts monotonic positive ones.

- Shared experience predictors introduce some inconsistencies.
    - Looking at the MDA scores, the importance of most of the factors is relatively minimal (excluding degree centrality for now), and negligably higher than dependency experience, even though the measured coefficients are substantially greater.
    - In this case, the coefficients do well represent the relationship measured by the random forest model, as all of them seem to have a monotonically negative effect, just like the coefficients.

- FO-degree centrality.
    - When observing the weighted first-order degree centrality, it immediatlye stands out taht the MDA scores are substantially higher, the in-degree even being in the top-5 most important features.
    - When comparing the measured coefficients with the partial dependency plots, then, it becomes visible the partial dependence shows a monotonic negative relationship, while the coefficient is positive.


- Dependency model.
    - In the control variables, not a whole lot changed beyond that self-integration and comments have slightly less impact. The signs of the effects are all the same.
    - Here, the ecosystem variables were left out because they correlated too much with the incoming / outgoing dependency experiences.
    - The importance of ecosystem variables is noticeably higher here, though, when compared to the full model. Pull request success ratio is even part of the top-5 predictive important features here.
    - The partial dependence observations are very similar to those in the general model, where the comment count features follow a reverse-U shape, the success rate a monotonic positive effect, and the counts a monotonic negative.