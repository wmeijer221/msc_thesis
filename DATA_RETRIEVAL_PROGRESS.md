

# NPM

## Collection

- [x] Collect core prs
- [x] Collect core issues
- [~] Collect core ``closed_by`` data (To be re-ran; somehow this data magically disappeared.)
    - [~] and merged with the dataset.
- [x] collect periphery core-to-other prs
    - [x] 196087 PRs that satisfy requirements, spread across 2905 projects, where each project has at least 5 PRs.
- [x] collect periphery core-to-other issues
- [ ] collect periphery core-to-other ``closed_by`` data (To be re-ran; somehow 18% of the data is missing.)
    - [ ] and merged with the dataset.
- [x] collect periphery other-to-core prs
- [~] collect periphery other-to-core issues.
    - [x] (First Run) 94413 PRs that satisfy requirements, spread across 1474 projects, where each project has at least 5 PRs.
    - [ ] (Second run) Collect data of an additional 22254 randomly sampled projects.
- [ ] collect periphery other-to-core ``closed_by`` data
    - [ ] and merged it with the dataset.

## Preprocessing

- [ ] Merge the chronological datasets.
- [ ] Remove all pull requests without either a ``closed_by`` or a ``merged_by`` field. (Earlier pull requests don't have this data apparently.)
- [ ] Apply the min (5) PR requirement on the chronological datasets.
- [ ] Bot filtering 
- [ ] Alias unmasking
- [ ] Sliding window
