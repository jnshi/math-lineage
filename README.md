&emsp;*Quick links: [To read](#to-read) · [To contribute](#to-contribute) · [About the skill](#about-the-skill) · [Reviewed preprints](#reviewed-preprints) · [List of missing attributions](#list-of-missing-attributions)*

On October 6, 2026, OpenAI released a [repository](https://github.com/openai/math) of 722 machine-generated manuscripts presenting solutions to major open problems across many fields of mathematics. A week earlier, the [Advisory Group on Mathematics and Artificial Intelligence](https://agmai.org) (AGMAI), a group of mathematicians that advises AI companies, had [recommended](https://agmai.org/general-sep29/) that a lab releasing such results first search the literature for related ideas and "cite the papers in which the ideas were first introduced". On the day of the release, AGMAI [left it to the mathematical community](https://agmai.org/#openai-release) to assess how far its recommendations had been followed.

When a manuscript uses ideas and techniques from earlier papers without citing them, it removes the landmarks that normally help readers navigate a new paper, obscures what is truly new in it, and withholds credit from the people who introduced those ideas. Proper citation is therefore not considered optional in published works.

The goal of this repository is to search for and document some of this missing attribution, and so to help the community with its assessment and aid in understanding the new solutions. The approach uses LLM agents to handle this task at scale. Each report lists earlier works used by a preprint without citation, with locators in both papers so that readers can check each finding.

So far, 3 of the 719 preprints [have reports](#reviewed-preprints) in the current format. They list 30 findings, of which 19 are attribution gaps and 2 show overstated novelty:
- by relationship: 10 same result, 5 same technique, 10 adapted, 1 same route, 3 fragment and 1 weaker result;
- by centrality: 1 main result, 17 central, 10 supporting and 2 peripheral.

Across all 4 reports, the findings involve 74 earlier works; for 69 of them, a preprint [uses their content without fully crediting it](#list-of-missing-attributions).

## To read

In each reviewed manuscript's folder under [`preprints/`](preprints/), the report `precedence-findings.pdf` sits next to OpenAI's original manuscript, usually `paper.pdf` or `main.pdf`. The folder's `README.md` also summarizes the report in a table. The reviewed manuscripts are listed under [Reviewed preprints](#reviewed-preprints). The reports make no claim of completeness, do not judge whether the manuscript is correct, and generally have not been human-vetted.

This repository is a fork of [openai/math](https://github.com/openai/math). The manuscripts and their supporting material (`preprints/`, `lean/`, `reasoning_traces/`, [`CONTENTS.md`](CONTENTS.md), [`overview.pdf`](overview.pdf), [`history.md`](history.md)) are as released there; see [its README](https://github.com/openai/math#readme) for how they were produced.

## To contribute

To review a preprint that doesn't have a review yet (see [Reviewed preprints](#reviewed-preprints)):
1. Make a slim clone of this repository, without `lean/` and the PDFs: about 270 MB instead of 3 GB. On Windows, run these commands in Git Bash.
   ```bash
   git clone -c core.longpaths=true --filter=blob:none --sparse https://github.com/jnshi/math-lineage
   cd math-lineage
   git sparse-checkout set --no-cone --stdin <<'EOF'
   /*
   !/lean/
   !*.pdf
   EOF
   ```
2. Start an agent that reads [`AGENTS.md`](AGENTS.md) in the `math-lineage` folder, and ask it for a precedence review of the preprint. Use Claude Opus 5.5, GPT 5.6 Sol or a stronger model; weaker models have not been evaluated yet. If you want to read a file that the slim clone left out, such as the preprint's PDF, ask the agent to check it out. The agent asks a few questions first, shows you the report before anything is published, and asks before opening a pull request against this repository.

A 27-page preprint took about 350M tokens (97% cache reads) and 4 hours. Expect a 50-page preprint to take 50–100% of the weekly usage limit of a basic paid subscription.

To request a review of a preprint, open an issue that names it. To report an error in a report, open an issue that names the preprint and the finding's ID.

The plan is also to collect findings, corrections and vetting from experts, alongside the machine-sourced findings, but the format for them is not settled yet. Suggestions are welcome on the [discussions page](https://github.com/jnshi/math-lineage/discussions). For now, they can go in an issue.

## About the skill

The [precedence-review skill](.agents/skills/precedence-review/SKILL.md) reads a preprint section by section and searches for earlier papers that already contain the techniques, constructions and results it uses. Each candidate is checked against the earlier paper itself. A separate agent then reviews each finding from the preprint author's point of view, and decides whether citing the earlier work would help an expert reader or is owed as credit.

Pull requests that improve the skill are welcome; please include a before-and-after of two preprint reviews in the PR, with the [SK model spectral gap](preprints/A-spectral-gap-throughout-the-high-temperature-Sherrington-Kirkpatrick-phase-September-24-2026/) as one of them.

**License.** The precedence-review skill is licensed under a mix of the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0) and the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0). See the LICENSE files in the [skill folder](.agents/skills/precedence-review/) for details.

## Reviewed preprints

*One row per reviewed preprint, in the numbered order of [`overview.pdf`](overview.pdf) (by result number, then in the order the result lists its manuscripts), under the overview's field headings. Fields with no reviewed preprint are left out.*

<table>
<thead><tr><th>Result</th><th>Preprint</th><th>Report date</th><th>Findings</th><th>Attribution gaps</th></tr></thead>
<tbody>
<tr><th colspan="5">Probability and statistical mechanics</th></tr>
<tr><td>227</td><td><a href="preprints/A-spectral-gap-throughout-the-high-temperature-Sherrington-Kirkpatrick-phase-September-24-2026/">A spectral gap throughout the high-temperature Sherrington–Kirkpatrick phase</a></td><td>October 13, 2026</td><td>16</td><td>10</td></tr>
<tr><td>227</td><td><a href="preprints/Critical-mixing-in-the-Sherrington-Kirkpatrick-model-September-25-2026/">Critical mixing in the Sherrington–Kirkpatrick model</a></td><td>October 8, 2026</td><td>12†</td><td>—†</td></tr>
<tr><th colspan="5">Mathematical physics</th></tr>
<tr><td>281</td><td><a href="preprints/Full-support-of-the-zero-temperature-Sherrington-Kirkpatrick-order-parameter-September-27-2026/">Full support of the zero-temperature Sherrington-Kirkpatrick order parameter</a></td><td>October 13, 2026</td><td>7</td><td>4</td></tr>
<tr><th colspan="5">Operator algebras</th></tr>
<tr><td>298</td><td><a href="preprints/A-finite-entropy-separation-of-microstates-and-nonmicrostates-free-entropy-September-25-2026/">A finite-entropy separation of microstates and nonmicrostates free entropy</a></td><td>October 12, 2026</td><td>7</td><td>5</td></tr>
</tbody>
</table>

*† Reviewed with an earlier version of the skill, whose report grades its findings (5 strong, 6 partial, 1 major) rather than giving relationships, centralities and attribution gaps.*

## List of missing attributions

- N. Anari, F. Koehler and T.-D. Vuong. Trickle-down in localization schemes and applications. STOC 2024. [arXiv:2407.16104](https://arxiv.org/abs/2407.16104) · [doi:10.1145/3618260.3649622](https://doi.org/10.1145/3618260.3649622)
- Antonio Auffinger and Wei-Kuo Chen. On properties of Parisi measures. Probab. Theory Related Fields (2015). [arXiv:1303.3573](https://arxiv.org/abs/1303.3573) · [doi:10.1007/s00440-014-0563-y](https://doi.org/10.1007/s00440-014-0563-y)
- Antonio Auffinger, Wei-Kuo Chen and Qiang Zeng. The SK model is infinite step replica symmetry breaking at zero temperature. Comm. Pure Appl. Math. (2020). [arXiv:1703.06872](https://arxiv.org/abs/1703.06872) · [doi:10.1002/cpa.21886](https://doi.org/10.1002/cpa.21886)
- J. Baik, E. Collins-Woodfin, P. Le Doussal and H. Wu. Spherical spin glass model with external field. J. Stat. Phys. (2021). [arXiv:2010.06123](https://arxiv.org/abs/2010.06123)
- J. Baik and J. O. Lee. Fluctuations of the free energy of the spherical Sherrington–Kirkpatrick model. J. Stat. Phys. 165 (2016). [arXiv:1505.07349](https://arxiv.org/abs/1505.07349)
- D. Bakry, T. Coulhon, M. Ledoux and L. Saloff-Coste. Sobolev inequalities in disguise. Indiana Univ. Math. J. 44(4) (1995) 1033–1074. [doi:10.1512/iumj.1995.44.2019](https://doi.org/10.1512/iumj.1995.44.2019)
- A. S. Bandeira, A. El Alaoui and A. Rödder. Mixing of Glauber dynamics on high overlap Gibbs measures. Preprint, 2026. [arXiv:2607.06813](https://arxiv.org/abs/2607.06813)
- F. Barthe, P. Cattiaux and C. Roberto. Interpolated inequalities between exponential and Gaussian, Orlicz hypercontractivity and isoperimetry. Rev. Mat. Iberoam. 22(3) (2006) 993–1067. [arXiv:math/0407219](https://arxiv.org/abs/math/0407219)
- F. Barthe and C. Roberto. Sobolev inequalities for probability measures on the real line. Studia Math. 159(3) (2003) 481–497. [doi:10.4064/sm159-3-9](https://doi.org/10.4064/sm159-3-9)
- R. Bauerschmidt and T. Bodineau. Log-Sobolev inequality for the continuum sine-Gordon model. Comm. Pure Appl. Math. 74 (2021). [arXiv:1907.12308](https://arxiv.org/abs/1907.12308)
- R. Bauerschmidt, T. Bodineau and B. Dagallier. Stochastic dynamics and the Polchinski equation: an introduction. Probab. Surveys (2024). [arXiv:2307.07619](https://arxiv.org/abs/2307.07619)
- R. Bauerschmidt and B. Dagallier. Log-Sobolev inequality for near critical Ising models. Comm. Pure Appl. Math. (2024). [arXiv:2202.02301](https://arxiv.org/abs/2202.02301)
- M. Bayati, M. Lelarge and A. Montanari. Universality in polytope phase transitions and message passing algorithms. Ann. Appl. Probab. 25 (2015) 753–822. [arXiv:1207.7321](https://arxiv.org/abs/1207.7321) · [doi:10.1214/14-AAP1010](https://doi.org/10.1214/14-AAP1010)
- D. Belius, F. Concetti and G. Genovese. On the determinant in Bray–Moore's TAP complexity formula. Preprint, 2024. [arXiv:2401.08529](https://arxiv.org/abs/2401.08529)
- B. B. Bhattacharya and S. Sen. High temperature asymptotics of orthogonal mean-field spin glasses. J. Stat. Phys. (2016). [arXiv:1507.05067](https://arxiv.org/abs/1507.05067)
- P. Biane. Entropie libre et algèbres d'opérateurs. Séminaire Bourbaki, exp. 889, Astérisque 282 (2002) 279–300.
- P. Biane and R. Speicher. Stochastic calculus with respect to free Brownian motion and analysis on Wigner space. Probab. Theory Related Fields 112 (1998) 373–409. [doi:10.1007/s004400050194](https://doi.org/10.1007/s004400050194)
- S. G. Bobkov, A. A. Naumov and V. V. Ulyanov. Two-sided bounds for PDF's maximum of a sum of weighted chi-square variables. Springer Proc. Math. Stat. 371 (2021). [arXiv:2012.10747](https://arxiv.org/abs/2012.10747) · [doi:10.1007/978-3-030-83266-7_13](https://doi.org/10.1007/978-3-030-83266-7_13)
- J. Boursier. The Legendre structure of the TAP complexity for the Ising spin glass. Preprint, 2026. [arXiv:2604.20660](https://arxiv.org/abs/2604.20660)
- M. Bożejko, B. Kümmerer and R. Speicher. q-Gaussian processes: non-commutative and classical aspects. Comm. Math. Phys. 185 (1997) 129–154. [doi:10.1007/s002200050084](https://doi.org/10.1007/s002200050084)
- C. Brennecke, C. Xu and H.-T. Yau. Operator norm bounds on the correlation matrix of the SK model at high temperature. Preprint, 2023. [arXiv:2307.12535](https://arxiv.org/abs/2307.12535)
- E. Brézin and S. Hikami. Characteristic polynomials of real symmetric random matrices. Commun. Math. Phys. 223 (2001) 363–382. [arXiv:math-ph/0103012](https://arxiv.org/abs/math-ph/0103012) · [doi:10.1007/s002200100547](https://doi.org/10.1007/s002200100547)
- G. Cébron. A quantitative fourth moment theorem in free probability theory. Adv. Math. 380 (2021) 107579. [arXiv:1803.09669](https://arxiv.org/abs/1803.09669)
- M. Celentano. Sudakov–Fernique post-AMP, and a new proof of the local convexity of the TAP free energy. Ann. Probab. 52 (2024). [arXiv:2208.09550](https://arxiv.org/abs/2208.09550)
- M. Celentano, Z. Fan and S. Mei. Local convexity of the TAP free energy and AMP convergence for Z2-synchronization. Ann. Statist. 51 (2023). [arXiv:2106.11428](https://arxiv.org/abs/2106.11428)
- ChatGPT. FRSB in the SK spin glass: convergence to full-interval support at zero temperature. aiXiv preprint aixiv.260716.000001 (earlier version of Chen 2026, arXiv 2607.18032).
- S. Chatterjee. Spin glasses and Stein's method. Preprint (journal version: Probab. Theory Related Fields, 2010). [arXiv:0706.3500](https://arxiv.org/abs/0706.3500)
- Hong-Bin Chen. FRSB in the SK spin glass: convergence to full-interval support at zero temperature. arXiv preprint, 2026. [arXiv:2607.18032](https://arxiv.org/abs/2607.18032)
- Y. Chen and R. Eldan. Localization schemes: A framework for proving mixing bounds for Markov chains. Duke Math. J. 174 (2025). [arXiv:2203.04163](https://arxiv.org/abs/2203.04163)
- Wei-Kuo Chen, Madeline Handschy and Gilad Lerman. On the energy landscape of the mixed even p-spin model. Probab. Theory Related Fields (2018). [arXiv:1609.04368](https://arxiv.org/abs/1609.04368) · [doi:10.1007/s00440-017-0773-1](https://doi.org/10.1007/s00440-017-0773-1)
- E. Davies, H. Lee, J. S. Sandhu and J. Shi. Potential Hessian Ascent III: Sampling the Sherrington–Kirkpatrick model at β < 1/2. Preprint, 2026. [arXiv:2605.03718](https://arxiv.org/abs/2605.03718)
- E. Davies, H. Lee, J. S. Sandhu and J. Shi. Weak Poincaré inequalities via approximate stochastic localization: application to sampling the Sherrington–Kirkpatrick model. Preprint, 2026. [arXiv:2607.08160](https://arxiv.org/abs/2607.08160)
- Y. Deshpande, E. Abbe and A. Montanari. Asymptotic mutual information for the two-groups stochastic block model. Information and Inference 6 (2017) 125–170, as Asymptotic mutual information for the balanced binary stochastic block model. [arXiv:1507.08685](https://arxiv.org/abs/1507.08685) · [doi:10.1093/imaiai/iaw017](https://doi.org/10.1093/imaiai/iaw017)
- P. Diaconis and L. Saloff-Coste. Logarithmic Sobolev inequalities for finite Markov chains. Ann. Appl. Probab. 6(3) (1996) 695–750. [doi:10.1214/aoap/1034968224](https://doi.org/10.1214/aoap/1034968224)
- C.-P. Diez. Free Stein kernels, free moment maps, and higher order derivatives. Preprint, 2023. [arXiv:2306.00967](https://arxiv.org/abs/2306.00967)
- H. Du and B. Huang. Fluctuations of the Sherrington–Kirkpatrick free energy at critical temperature. Preprint, 2026. [arXiv:2607.02172](https://arxiv.org/abs/2607.02172)
- K. Dykema. Two applications of free entropy. Math. Ann. 308 (1997) 547–558. [arXiv:funct-an/9605005](https://arxiv.org/abs/funct-an/9605005)
- E. G. Effros and M. Popa. Feynman diagrams and Wick products associated with q-Fock space. Proc. Natl. Acad. Sci. USA 100 (2003) 8629–8633. [arXiv:math/0303045](https://arxiv.org/abs/math/0303045) · [doi:10.1073/pnas.1531460100](https://doi.org/10.1073/pnas.1531460100)
- A. El Alaoui, R. Eldan, R. Gheissari and A. Piana. Fast relaxation of the random field Ising dynamics. Preprint, 2023. [arXiv:2311.06171](https://arxiv.org/abs/2311.06171)
- A. El Alaoui and J. Gaitonde. Bounds on the covariance matrix of the Sherrington–Kirkpatrick model. Preprint, 2022. [arXiv:2212.02445](https://arxiv.org/abs/2212.02445)
- Ahmed El Alaoui, Andrea Montanari and Mark Sellke. Optimization of mean-field spin glasses. Ann. Probab. 49(6) (2021). [arXiv:2001.00904](https://arxiv.org/abs/2001.00904) · [doi:10.1214/21-AOP1519](https://doi.org/10.1214/21-AOP1519)
- A. El Alaoui, A. Montanari and M. Sellke. Sampling from the Sherrington–Kirkpatrick Gibbs measure via algorithmic stochastic localization. FOCS 2022. [arXiv:2203.05093](https://arxiv.org/abs/2203.05093)
- R. Eldan. Thin shell implies spectral gap up to polylog via a stochastic localization scheme. Geom. Funct. Anal. 23 (2013). [arXiv:1203.0893](https://arxiv.org/abs/1203.0893)
- Z. Fan, S. Mei and A. Montanari. TAP free energy, spin glasses, and variational inference. Ann. Probab. 49 (2021). [arXiv:1808.07890](https://arxiv.org/abs/1808.07890)
- M. Fathi and B. Nelson. Free Stein kernels and an improvement of the free logarithmic Sobolev inequality. Adv. Math. 317 (2017) 193–223. [arXiv:1605.05828](https://arxiv.org/abs/1605.05828)
- L. Ge. Prime factors. Proc. Natl. Acad. Sci. USA 93 (1996) 12762–12763. [doi:10.1073/pnas.93.23.12762](https://doi.org/10.1073/pnas.93.23.12762)
- S. Goel, R. Montenegro and P. Tetali. Mixing time bounds via the spectral profile. Electron. J. Probab. 11 (2006) 1–26. [arXiv:math/0505690](https://arxiv.org/abs/math/0505690) · [doi:10.1214/EJP.v11-300](https://doi.org/10.1214/EJP.v11-300)
- F. Götze, A. Naumov, V. Spokoiny and V. Ulyanov. Large ball probabilities, Gaussian comparison and anti-concentration. Bernoulli 25(4A) (2019) 2538–2563. [arXiv:1708.08663](https://arxiv.org/abs/1708.08663)
- J. Hermon and Y. Peres. A characterization of L2 mixing and hypercontractivity via hitting times and maximal inequalities. Probab. Theory Related Fields 170 (2018) 769–800. [arXiv:1609.07557](https://arxiv.org/abs/1609.07557)
- B. Huang, S. Mohanty, A. Rajaraman and D. X. Wu. Weak Poincaré inequalities, simulated annealing, and sampling from spherical spin glasses. Preprint, 2024. [arXiv:2411.09075](https://arxiv.org/abs/2411.09075)
- B. Huang, A. Montanari and H. T. Pham. Sampling from spherical spin glasses in total variation via algorithmic stochastic localization. Preprint, 2024. [arXiv:2404.15651](https://arxiv.org/abs/2404.15651)
- B. Huang and M. Sellke. Strong topological trivialization of multi-species spherical spin glasses. Preprint, 2023. [arXiv:2308.09677](https://arxiv.org/abs/2308.09677)
- D. Jekel. Information geometry for types in the large-n limit of random matrices. Comm. Math. Phys. 406 (2025), no. 11, Art. 272. [arXiv:2501.00703](https://arxiv.org/abs/2501.00703) · [doi:10.1007/s00220-025-05451-x](https://doi.org/10.1007/s00220-025-05451-x)
- D. Jekel, J. S. Sandhu and J. Shi. Potential Hessian Ascent: The Sherrington–Kirkpatrick Model. Preprint, 2024. [arXiv:2408.02360](https://arxiv.org/abs/2408.02360)
- K. Jung. A free entropy dimension lemma. Pacific J. Math. 211 (2003). [arXiv:math/0207149](https://arxiv.org/abs/math/0207149)
- T. Kemp, I. Nourdin, G. Peccati and R. Speicher. Wigner chaos and the fourth moment. Ann. Probab. 40 (2012) 1577–1635. [arXiv:1009.3949](https://arxiv.org/abs/1009.3949)
- J. M. Kosterlitz, D. J. Thouless and R. C. Jones. Spherical model of a spin-glass. Phys. Rev. Lett. 36 (1976) 1217–1220. [doi:10.1103/PhysRevLett.36.1217](https://doi.org/10.1103/PhysRevLett.36.1217)
- B. Landon. Free energy fluctuations of the two-spin spherical SK model at critical temperature. J. Math. Phys. 63 (2022) 033301. [arXiv:2010.06691](https://arxiv.org/abs/2010.06691) · [doi:10.1063/5.0054298](https://doi.org/10.1063/5.0054298)
- J. A. Mingo and R. Speicher. Free Probability and Random Matrices. Fields Institute Monographs 35, Springer, 2017.
- A. Montanari. Optimization of the Sherrington–Kirkpatrick Hamiltonian. Preprint, 2018. [arXiv:1812.10897](https://arxiv.org/abs/1812.10897)
- V. L. Nguyen and P. Sosoe. Central limit theorem near the critical temperature for the overlap in the 2-spin spherical SK model. J. Math. Phys. 60 (2019). [arXiv:1809.03675](https://arxiv.org/abs/1809.03675) · [doi:10.1063/1.5065525](https://doi.org/10.1063/1.5065525)
- R. Speicher. Combinatorial theory of the free product with amalgamation and operator-valued free probability theory. Mem. Amer. Math. Soc. 132 (1998), no. 627. [doi:10.1090/memo/0627](https://doi.org/10.1090/memo/0627)
- S. J. Szarek. Metric entropy of homogeneous spaces. Banach Center Publ. 43 (1998) 395–410. [arXiv:math/9701213](https://arxiv.org/abs/math/9701213)
- D. Voiculescu. Circular and semicircular systems and free product factors. Operator Algebras, Unitary Representations, Enveloping Algebras, and Invariant Theory (Paris, 1989), Progr. Math. 92, Birkhäuser (1990) 45–60.
- D. Voiculescu. The analogues of entropy and of Fisher's information measure in free probability theory, II. Invent. Math. 118 (1994) 411–440. [doi:10.1007/BF01231539](https://doi.org/10.1007/BF01231539)
- D. Voiculescu. The analogues of entropy and of Fisher's information measure in free probability theory III: The absence of Cartan subalgebras. Geom. Funct. Anal. 6 (1996) 172–199. [doi:10.1007/BF02246772](https://doi.org/10.1007/BF02246772)
- D. Voiculescu. The analogues of entropy and of Fisher's information measure in free probability theory. V. Noncommutative Hilbert transforms. Invent. Math. 132 (1998) 189–227. [doi:10.1007/s002220050222](https://doi.org/10.1007/s002220050222)
- Yuxin Zhou. Existence of full replica symmetry breaking for the Sherrington-Kirkpatrick model at low temperature. Comm. Pure Appl. Math. 79(7) (2026). [arXiv:2504.00269](https://arxiv.org/abs/2504.00269) · [doi:10.1002/cpa.70038](https://doi.org/10.1002/cpa.70038)
- Yuxin Zhou. On the Gardner transition in the Ising pure p-spin glass II. arXiv preprint, 2026. [arXiv:2608.06523](https://arxiv.org/abs/2608.06523)
