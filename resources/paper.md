---
title: 'PAM: Population Activity Modeller'
tags:
  - Python
  - Activity model
  - Synthetic population
  - MATSim
authors:
  - name: Fred Shone
    orcid: 0009-0008-1079-0081
    affiliation: 1 # (Multiple affiliations must be quoted)
  - name: Theodore Chatziioannou
    affiliation: 1
  - name: Bryn Pickering
    affiliation: 1
  - name: Kasia Kozlowska
    affiliation: 1
  - names: Michael Fitzmaurice
    affiliation: 1
affiliations:
 - name: Arup, City Modelling Lab
   index: 1
date: 12 September 2023
bibliography: paper.bib

---

# Summary

Modelling how a population of people will behave in some future scenario is a critical tool in policy, operational and infrastructure decision making. In the transport domain, this might be predicting how many people will buy an electric vehicle, so that future energy demand can be planned, or predicting how many people will use a new train station so that a new rail line can be funded.

Activity modelling is a growing paradigm used for these models, in which individuals are explicitly represented and their movements are based on predicting sequences of activities connected by trips. Where activities have a type or 'purpose', such as "work" and a location. This is a key shift from more simplified approaches, which can be used to potentially create more useful and more accurate predictions.

Activity modelling is also a key component of agent-based modelling approaches such as MATSim [@MATSim:2016].

# Statement of need

`PAM` is a python package providing a pythonic API for creating and/or working with activity-based sythetic populations. `PAM` provides read/write functionality for common data formats, such as travel diaries and full support for MATSim formats. The `PAM` API allows creation and/or manipulation of activity sequences using intutive objects and methods. This allows users to create more complex models faster.

`PAM` is intended for use by those wanting to (i) building their own activity model, (ii) read, modify and/or write existing synthetic populations to create new scenarios, and (ii) work with the agent-based modelling tool MATSim. `PAM` provides example notebooks of these applications, and common features are exposed via a CLI.

# Acknowledgements

We acknowledge all past, present, and future contributions, including code, documentation, issues and feedback. We also acknowledge funding and support from Arup.

# References